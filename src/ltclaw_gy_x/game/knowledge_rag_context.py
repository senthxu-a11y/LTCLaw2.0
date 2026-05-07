from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .local_project_paths import normalize_local_project_relative_path
from .knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    KnowledgeReleaseNotFoundError,
    get_current_release,
    load_knowledge_map,
)
from .paths import get_release_dir

DEFAULT_MAX_CHUNKS = 8
DEFAULT_MAX_CHARS = 12000
MAX_MAX_CHUNKS = 50
MAX_MAX_CHARS = 50000
ALLOWED_RELEASE_CONTEXT_INDEXES = (
    ('table_schema', 'table_schema'),
    ('doc_knowledge', 'doc_knowledge'),
    ('script_evidence', 'script_evidence'),
)


class KnowledgeReleaseContextError(RuntimeError):
    pass


class KnowledgeReleaseContextPathError(KnowledgeReleaseContextError):
    pass


def build_current_release_context(
    project_root: Path,
    query: str,
    *,
    max_chunks: int = DEFAULT_MAX_CHUNKS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict[str, Any]:
    query_text = str(query or '').strip()
    limited_max_chunks = max(1, min(int(max_chunks or DEFAULT_MAX_CHUNKS), MAX_MAX_CHUNKS))
    limited_max_chars = max(1, min(int(max_chars or DEFAULT_MAX_CHARS), MAX_MAX_CHARS))

    try:
        manifest = get_current_release(project_root)
    except (CurrentKnowledgeReleaseNotSetError, KnowledgeReleaseNotFoundError):
        return {
            'mode': 'no_current_release',
            'query': query_text,
            'release_id': None,
            'built_at': None,
            'chunks': [],
            'citations': [],
        }

    if not query_text:
        return {
            'mode': 'context',
            'query': query_text,
            'release_id': manifest.release_id,
            'built_at': manifest.created_at,
            'chunks': [],
            'citations': [],
        }

    release_dir = get_release_dir(project_root, manifest.release_id)
    knowledge_map = load_knowledge_map(project_root, manifest.release_id)
    tokens = _tokenize(query_text)
    candidates: list[dict[str, Any]] = []

    manifest_text = _build_manifest_text(manifest)
    manifest_score = _score_text(manifest_text, query_text, tokens)
    if manifest_score > 0:
        candidates.append(
            {
                'source_type': 'manifest',
                'text': manifest_text,
                'score': manifest_score,
                'sort_ref': 'manifest.json',
                'citation': {
                    'artifact_path': 'manifest.json',
                    'source_path': None,
                    'title': f'Release {manifest.release_id}',
                    'row': None,
                    'source_hash': manifest.map_hash,
                },
            }
        )

    map_text = _build_map_text(knowledge_map)
    map_score = _score_text(map_text, query_text, tokens)
    if map_score > 0:
        candidates.append(
            {
                'source_type': 'map',
                'text': map_text,
                'score': map_score,
                'sort_ref': 'map.json',
                'citation': {
                    'artifact_path': 'map.json',
                    'source_path': None,
                    'title': f'Map {knowledge_map.release_id}',
                    'row': None,
                    'source_hash': knowledge_map.source_hash,
                },
            }
        )

    for source_type, manifest_key in ALLOWED_RELEASE_CONTEXT_INDEXES:
        artifact = manifest.indexes.get(manifest_key)
        if artifact is None:
            continue
        index_path = _resolve_release_artifact_path(release_dir, artifact.path)
        if not index_path.exists() or not index_path.is_file():
            continue
        for row_number, record in _load_jsonl_rows(index_path):
            text = _build_record_text(source_type, record)
            if not text:
                continue
            score = _score_text(text, query_text, tokens)
            if score <= 0:
                continue
            candidates.append(
                {
                    'source_type': source_type,
                    'text': text,
                    'score': score,
                    'sort_ref': str(record.get('source_path') or ''),
                    'citation': {
                        'artifact_path': artifact.path,
                        'source_path': str(record.get('source_path') or '') or None,
                        'title': _record_title(source_type, record),
                        'row': row_number,
                        'source_hash': record.get('source_hash'),
                    },
                }
            )

    candidates.sort(
        key=lambda item: (
            -float(item.get('score') or 0.0),
            str(item.get('source_type') or ''),
            str(item.get('sort_ref') or ''),
            str(item.get('citation', {}).get('title') or ''),
        )
    )

    chunks: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    used_chars = 0

    for candidate in candidates:
        if len(chunks) >= limited_max_chunks:
            break
        remaining_chars = limited_max_chars - used_chars
        if remaining_chars <= 0:
            break
        text = _truncate_text(str(candidate['text']), remaining_chars)
        if not text:
            break
        rank = len(chunks) + 1
        citation_id = f'citation-{rank:03d}'
        chunk_id = f'chunk-{rank:03d}'
        citations.append(
            {
                'citation_id': citation_id,
                'release_id': manifest.release_id,
                'source_type': candidate['source_type'],
                'artifact_path': candidate['citation']['artifact_path'],
                'source_path': candidate['citation']['source_path'],
                'title': candidate['citation']['title'],
                'row': candidate['citation']['row'],
                'source_hash': candidate['citation']['source_hash'],
            }
        )
        chunks.append(
            {
                'chunk_id': chunk_id,
                'source_type': candidate['source_type'],
                'text': text,
                'score': round(float(candidate['score']), 4),
                'rank': rank,
                'citation_id': citation_id,
            }
        )
        used_chars += len(text)

    return {
        'mode': 'context',
        'query': query_text,
        'release_id': manifest.release_id,
        'built_at': manifest.created_at,
        'chunks': chunks,
        'citations': citations,
    }


def _load_jsonl_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    payload = path.read_text(encoding='utf-8')
    rows: list[tuple[int, dict[str, Any]]] = []
    for row_number, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        rows.append((row_number, json.loads(line)))
    return rows


def _resolve_release_artifact_path(release_dir: Path, relative_path: str | None) -> Path:
    try:
        normalized_path = normalize_local_project_relative_path(relative_path, error_label='release artifact path')
    except ValueError as exc:
        raise KnowledgeReleaseContextPathError(f'Invalid release artifact path: {relative_path!r}') from exc
    resolved = (release_dir / normalized_path).resolve(strict=False)
    release_root = release_dir.resolve(strict=False)
    try:
        resolved.relative_to(release_root)
    except ValueError as exc:
        raise KnowledgeReleaseContextPathError(f'Invalid release artifact path: {relative_path!r}') from exc
    return resolved


def _tokenize(query_text: str) -> list[str]:
    return [token for token in re.findall(r'\w+', query_text.lower()) if token]


def _score_text(text: str, query_text: str, tokens: list[str]) -> float:
    haystack = str(text or '').lower()
    if not haystack:
        return 0.0
    score = 0.0
    phrase = query_text.lower()
    if phrase and phrase in haystack:
        score += 2.0
    for token in tokens:
        occurrences = haystack.count(token)
        if occurrences:
            score += 1.0 + min(occurrences - 1, 4) * 0.25
    return round(score, 4)


def _build_manifest_text(manifest) -> str:
    systems = ', '.join(system.title or system.system_id for system in manifest.systems[:6])
    tables = ', '.join(table.title or table.table_id for table in manifest.tables[:6])
    docs = ', '.join(doc.title or doc.doc_id for doc in manifest.docs[:6])
    scripts = ', '.join(script.title or script.script_id for script in manifest.scripts[:6])
    index_parts = []
    for index_name in ('table_schema', 'doc_knowledge', 'script_evidence'):
        artifact = manifest.indexes.get(index_name)
        if artifact is None:
            continue
        index_parts.append(f'{index_name}={artifact.count}')
    return ' '.join(
        part
        for part in (
            f'Release {manifest.release_id}.',
            f'Built at {manifest.created_at.isoformat()}.',
            f'Systems: {systems}.' if systems else '',
            f'Tables: {tables}.' if tables else '',
            f'Docs: {docs}.' if docs else '',
            f'Scripts: {scripts}.' if scripts else '',
            f'Indexes: {", ".join(index_parts)}.' if index_parts else '',
        )
        if part
    )


def _build_map_text(knowledge_map) -> str:
    systems = ', '.join(system.title or system.system_id for system in knowledge_map.systems[:6])
    tables = ', '.join(table.title or table.table_id for table in knowledge_map.tables[:8])
    docs = ', '.join(doc.title or doc.doc_id for doc in knowledge_map.docs[:8])
    scripts = ', '.join(script.title or script.script_id for script in knowledge_map.scripts[:8])
    relations = ', '.join(
        f'{relationship.from_ref} {relationship.relation_type} {relationship.to_ref}'
        for relationship in knowledge_map.relationships[:6]
    )
    return ' '.join(
        part
        for part in (
            f'Map for release {knowledge_map.release_id}.',
            f'Systems: {systems}.' if systems else '',
            f'Tables: {tables}.' if tables else '',
            f'Docs: {docs}.' if docs else '',
            f'Scripts: {scripts}.' if scripts else '',
            f'Relationships: {relations}.' if relations else '',
        )
        if part
    )


def _build_record_text(source_type: str, record: dict[str, Any]) -> str:
    if source_type == 'table_schema':
        field_text = ', '.join(
            f"{field.get('name') or ''} {field.get('type') or ''} {field.get('description') or ''}".strip()
            for field in list(record.get('fields') or [])[:10]
            if isinstance(field, dict)
        )
        parts = (
            f"Table {record.get('table_name') or ''}.",
            f"System {record.get('system') or ''}." if record.get('system') else '',
            f"Summary {record.get('summary') or ''}." if record.get('summary') else '',
            f"Primary key {record.get('primary_key') or ''}." if record.get('primary_key') else '',
            f"Fields {field_text}." if field_text else '',
        )
        return ' '.join(part for part in parts if part)
    if source_type == 'doc_knowledge':
        related_tables = ', '.join(str(item) for item in list(record.get('related_tables') or [])[:8] if item)
        tags = ', '.join(str(item) for item in list(record.get('tags') or [])[:8] if item)
        parts = (
            f"Document {record.get('title') or ''}.",
            f"Category {record.get('category') or ''}." if record.get('category') else '',
            f"Summary {record.get('summary') or ''}." if record.get('summary') else '',
            f"Related tables {related_tables}." if related_tables else '',
            f"Tags {tags}." if tags else '',
        )
        return ' '.join(part for part in parts if part)
    if source_type == 'script_evidence':
        symbol_names = ', '.join(
            str(symbol.get('name') or '')
            for symbol in list(record.get('symbols') or [])[:8]
            if isinstance(symbol, dict) and symbol.get('name')
        )
        reference_targets = ', '.join(
            str(reference.get('target_table') or reference.get('target_symbol') or reference.get('target_field') or '')
            for reference in list(record.get('references') or [])[:8]
            if isinstance(reference, dict)
            and (reference.get('target_table') or reference.get('target_symbol') or reference.get('target_field'))
        )
        parts = (
            f"Script {record.get('source_path') or ''}.",
            f"Language {record.get('language') or ''}." if record.get('language') else '',
            f"Kind {record.get('kind') or ''}." if record.get('kind') else '',
            f"Summary {record.get('summary') or ''}." if record.get('summary') else '',
            f"Symbols {symbol_names}." if symbol_names else '',
            f"References {reference_targets}." if reference_targets else '',
        )
        return ' '.join(part for part in parts if part)
    return ''


def _record_title(source_type: str, record: dict[str, Any]) -> str | None:
    if source_type == 'table_schema':
        return str(record.get('table_name') or '') or None
    if source_type == 'doc_knowledge':
        return str(record.get('title') or '') or None
    if source_type == 'script_evidence':
        return Path(str(record.get('source_path') or '')).name or None
    return None


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ''
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + '...'
