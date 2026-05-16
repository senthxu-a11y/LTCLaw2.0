from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from .config import ProjectDocsSourceConfig
from .doc_source_discovery import discover_document_sources
from .models import CanonicalDocFacts, DocIndex
from .paths import get_project_canonical_doc_facts_path, get_project_raw_docs_dir


_HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
_RELATED_TABLE_PATTERN = re.compile(r'\b([A-Za-z][A-Za-z0-9_]*(?:Table|Config))\b')
_TAG_TOKEN_PATTERN = re.compile(r'[A-Za-z][A-Za-z0-9_-]{3,}')
_WORD_NAMESPACE = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + '.tmp')
    temp_path.write_text(content, encoding='utf-8')
    temp_path.replace(path)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text or '').strip())


def _sanitize_identifier(value: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9_-]+', '', str(value or '').strip())
    return cleaned or 'doc'


def _build_doc_id(source_path: str, seen_ids: set[str]) -> str:
    stem = _sanitize_identifier(Path(source_path).stem)
    candidate = stem
    if candidate not in seen_ids:
        seen_ids.add(candidate)
        return candidate
    suffix = hashlib.sha256(source_path.encode('utf-8')).hexdigest()[:8]
    candidate = f'{stem}-{suffix}'
    seen_ids.add(candidate)
    return candidate


def _split_markdown_chunks(content: str) -> list[str]:
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    chunks: list[str] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        text_parts = []
        if current_heading:
            text_parts.append(current_heading)
        body = '\n'.join(current_lines).strip()
        if body:
            text_parts.append(body)
        text = _normalize_whitespace('\n\n'.join(text_parts))
        if text:
            chunks.append(text)

    for raw_line in lines:
        line = raw_line.rstrip()
        match = _HEADING_PATTERN.match(line)
        if match:
            flush()
            current_heading = match.group(2).strip()
            current_lines = []
            continue
        if line.strip() or current_lines:
            current_lines.append(line)
    flush()

    if chunks:
        return chunks

    paragraphs = [_normalize_whitespace(part) for part in content.split('\n\n')]
    return [paragraph for paragraph in paragraphs if paragraph]


def _split_txt_chunks(content: str) -> list[str]:
    normalized = content.replace('\r\n', '\n').replace('\r', '\n')
    paragraphs = [_normalize_whitespace(part) for part in re.split(r'\n\s*\n', normalized) if _normalize_whitespace(part)]
    if not paragraphs:
        return []

    chunks: list[str] = []
    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        if index + 1 < len(paragraphs) and '\n' not in paragraph and len(paragraph.split()) <= 6:
            chunks.append(_normalize_whitespace(f'{paragraph}\n\n{paragraphs[index + 1]}'))
            index += 2
            continue
        chunks.append(paragraph)
        index += 1
    return chunks


def _extract_title(source_path: str, content: str) -> str:
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for line in lines:
        match = _HEADING_PATTERN.match(line.strip())
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    for line in lines:
        match = _HEADING_PATTERN.match(line.strip())
        if match:
            return match.group(2).strip()
    return Path(source_path).stem


def _extract_txt_title(source_path: str, content: str) -> str:
    for line in content.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        title = _normalize_whitespace(line)
        if title:
            return title
    return Path(source_path).stem


def _read_docx_paragraphs(source_file: Path) -> list[str]:
    try:
        with zipfile.ZipFile(source_file) as archive:
            document_xml = archive.read('word/document.xml')
    except Exception as exc:
        raise ValueError(f'unable to read docx file: {source_file}') from exc

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as exc:
        raise ValueError(f'invalid docx document xml: {source_file}') from exc

    body = root.find('w:body', _WORD_NAMESPACE)
    if body is None:
        return []

    paragraphs: list[str] = []
    for child in list(body):
        if child.tag != f"{{{_WORD_NAMESPACE['w']}}}p":
            continue
        text_parts = [node.text or '' for node in child.findall('.//w:t', _WORD_NAMESPACE)]
        text = _normalize_whitespace(''.join(text_parts))
        if text:
            paragraphs.append(text)
    return paragraphs


def _extract_tags(title: str, chunks: list[str]) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []
    for token in _TAG_TOKEN_PATTERN.findall(' '.join([title, *chunks[:3]])):
        normalized = token.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        tags.append(normalized)
        if len(tags) >= 6:
            break
    return tags


def _extract_related_refs(content: str) -> list[str]:
    refs = {f'table:{match}' for match in _RELATED_TABLE_PATTERN.findall(content)}
    return sorted(refs)


def _build_summary(chunks: list[str]) -> str:
    summary = ' '.join(chunks[:3]).strip()
    if len(summary) <= 800:
        return summary
    return summary[:797].rstrip() + '...'


def _parse_docx_doc(source_path: str, source_file: Path, *, doc_id: str) -> tuple[DocIndex, CanonicalDocFacts]:
    normalized_source_path = source_path.replace('\\', '/').strip('/ ')
    source_hash = f"sha256:{hashlib.sha256(source_file.read_bytes()).hexdigest()}"
    paragraphs = _read_docx_paragraphs(source_file)
    if not paragraphs:
        raise ValueError(f'docx document has no readable paragraphs: {source_file}')

    title = paragraphs[0]
    chunks = paragraphs[1:]
    summary = _build_summary(chunks or [title])
    combined_text = '\n\n'.join(paragraphs)
    tags = _extract_tags(title, chunks or [title])
    related_refs = _extract_related_refs(combined_text)
    related_tables = sorted(ref.split(':', 1)[1] for ref in related_refs if ref.startswith('table:'))
    indexed_at = datetime.now(timezone.utc)

    doc_index = DocIndex(
        source_path=normalized_source_path,
        source_hash=source_hash,
        svn_revision=0,
        doc_type='docx',
        title=title,
        summary=summary,
        chunks=chunks,
        tags=tags,
        related_tables=related_tables,
        last_indexed_at=indexed_at,
    )
    canonical = CanonicalDocFacts(
        doc_id=doc_id,
        source_path=normalized_source_path,
        source_hash=source_hash,
        title=title,
        summary=summary,
        chunks=chunks,
        semantic_tags=tags,
        related_refs=related_refs,
        confidence=0.8,
        confirmed=False,
    )
    return doc_index, canonical


def _parse_txt_doc(source_path: str, content: str, *, doc_id: str) -> tuple[DocIndex, CanonicalDocFacts]:
    normalized_source_path = source_path.replace('\\', '/').strip('/ ')
    source_hash = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    title = _extract_txt_title(normalized_source_path, content)
    chunks = _split_txt_chunks(content)
    if chunks and chunks[0] == title:
        chunks = chunks[1:]
    summary = _build_summary(chunks or [title])
    tags = _extract_tags(title, chunks or [title])
    related_refs = _extract_related_refs(content)
    related_tables = sorted(ref.split(':', 1)[1] for ref in related_refs if ref.startswith('table:'))
    indexed_at = datetime.now(timezone.utc)

    doc_index = DocIndex(
        source_path=normalized_source_path,
        source_hash=source_hash,
        svn_revision=0,
        doc_type='text',
        title=title,
        summary=summary,
        chunks=chunks,
        tags=tags,
        related_tables=related_tables,
        last_indexed_at=indexed_at,
    )
    canonical = CanonicalDocFacts(
        doc_id=doc_id,
        source_path=normalized_source_path,
        source_hash=source_hash,
        title=title,
        summary=summary,
        chunks=chunks,
        semantic_tags=tags,
        related_refs=related_refs,
        confidence=0.8,
        confirmed=False,
    )
    return doc_index, canonical


def _parse_doc(source_path: str, content: str, source_file: Path, *, doc_id: str) -> tuple[DocIndex, CanonicalDocFacts]:
    suffix = Path(source_path).suffix.lower()
    if suffix == '.txt':
        return _parse_txt_doc(source_path, content, doc_id=doc_id)
    if suffix == '.docx':
        return _parse_docx_doc(source_path, source_file, doc_id=doc_id)
    return _parse_markdown_doc(source_path, content, doc_id=doc_id)


def _parse_markdown_doc(source_path: str, content: str, *, doc_id: str) -> tuple[DocIndex, CanonicalDocFacts]:
    normalized_source_path = source_path.replace('\\', '/').strip('/ ')
    source_hash = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    chunks = _split_markdown_chunks(content)
    title = _extract_title(normalized_source_path, content)
    summary = _build_summary(chunks)
    tags = _extract_tags(title, chunks)
    related_refs = _extract_related_refs(content)
    related_tables = sorted(ref.split(':', 1)[1] for ref in related_refs if ref.startswith('table:'))
    indexed_at = datetime.now(timezone.utc)

    doc_index = DocIndex(
        source_path=normalized_source_path,
        source_hash=source_hash,
        svn_revision=0,
        doc_type='markdown',
        title=title,
        summary=summary,
        chunks=chunks,
        tags=tags,
        related_tables=related_tables,
        last_indexed_at=indexed_at,
    )
    canonical = CanonicalDocFacts(
        doc_id=doc_id,
        source_path=normalized_source_path,
        source_hash=source_hash,
        title=title,
        summary=summary,
        chunks=chunks,
        semantic_tags=tags,
        related_refs=related_refs,
        confidence=0.8,
        confirmed=False,
    )
    return doc_index, canonical


async def rebuild_markdown_doc_indexes(
    project_root: Path | None,
    docs_config: ProjectDocsSourceConfig | None,
) -> dict:
    result = {
        'success': False,
        'raw_doc_index_count': 0,
        'canonical_doc_count': 0,
        'indexed_docs': [],
        'errors': [],
        'next_action': 'run_canonical_rebuild',
    }
    discovery = discover_document_sources(project_root, docs_config)
    if project_root is None or not discovery['project_root']:
        result['errors'] = [{'error': 'project_root_not_configured'}]
        return result

    available_doc_items = [
        item
        for item in discovery.get('doc_files', [])
        if item.get('status') == 'available' and item.get('cold_start_supported', False)
    ]
    if not available_doc_items:
        result['errors'] = [
            {'source_path': item.get('source_path'), 'error': item.get('reason', 'doc_source_discovery_error')}
            for item in discovery.get('errors', [])
        ] or [{'error': 'no_supported_doc_files_available_for_rule_only_cold_start'}]
        result['next_action'] = str(discovery.get('next_action') or 'configure_docs_source')
        return result

    indexed_docs: list[dict] = []
    errors: list[dict] = []
    raw_count = 0
    canonical_count = 0
    seen_ids: set[str] = set()
    for item in available_doc_items:
        source_path = str(item['source_path'])
        source_file = project_root / source_path
        try:
            content = source_file.read_text(encoding='utf-8') if source_file.suffix.lower() != '.docx' else ''
            doc_id = _build_doc_id(source_path, seen_ids)
            doc_index, canonical = _parse_doc(source_path, content, source_file, doc_id=doc_id)
            raw_path = get_project_raw_docs_dir(project_root) / f'{doc_id}.json'
            _write_text_atomic(raw_path, doc_index.model_dump_json(indent=2))
            _write_text_atomic(
                get_project_canonical_doc_facts_path(project_root, canonical.doc_id),
                canonical.model_dump_json(indent=2),
            )
            raw_count += 1
            canonical_count += 1
            indexed_docs.append(
                {
                    'doc_id': canonical.doc_id,
                    'title': canonical.title,
                    'source_path': canonical.source_path,
                    'chunk_count': len(canonical.chunks),
                    'related_refs': list(canonical.related_refs),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({'source_path': source_path, 'error': str(exc)})

    manifest_path = get_project_raw_docs_dir(project_root) / 'doc_indexes.json'
    _write_text_atomic(
        manifest_path,
        json.dumps({'version': '1.0', 'docs': indexed_docs}, ensure_ascii=False, indent=2),
    )
    result.update(
        {
            'success': canonical_count > 0,
            'raw_doc_index_count': raw_count,
            'canonical_doc_count': canonical_count,
            'indexed_docs': indexed_docs,
            'errors': errors,
        }
    )
    return result
