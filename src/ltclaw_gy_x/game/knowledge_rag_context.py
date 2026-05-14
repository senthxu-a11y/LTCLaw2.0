from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    KnowledgeReleaseNotFoundError,
    get_current_release,
    load_knowledge_map,
)
from .local_project_paths import normalize_local_project_relative_path
from .paths import get_release_dir

DEFAULT_MAX_CHUNKS = 8
DEFAULT_MAX_CHARS = 12000
MAX_MAX_CHUNKS = 50
MAX_MAX_CHARS = 50000
_ARTIFACT_BY_REF_PREFIX = {
    'table': 'table_schema',
    'doc': 'doc_knowledge',
    'script': 'script_evidence',
}


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
    focus_refs: list[str] | None = None,
) -> dict[str, Any]:
    query_text = str(query or '').strip()
    limited_max_chunks = max(1, min(int(max_chunks or DEFAULT_MAX_CHUNKS), MAX_MAX_CHUNKS))
    limited_max_chars = max(1, min(int(max_chars or DEFAULT_MAX_CHARS), MAX_MAX_CHARS))

    try:
        manifest = get_current_release(project_root)
    except (CurrentKnowledgeReleaseNotSetError, KnowledgeReleaseNotFoundError):
        normalized_focus_refs = [str(ref).strip() for ref in list(focus_refs or []) if str(ref or '').strip()]
        return {
            'mode': 'no_current_release',
            'query': query_text,
            'release_id': None,
            'built_at': None,
            'chunks': [],
            'citations': [],
            'allowed_refs': [],
            'map_hash': None,
            'map_source_hash': None,
            'reason': 'no_current_release',
            'requested_focus_refs': normalized_focus_refs,
            'active_focus_refs': [],
        }

    knowledge_map = load_knowledge_map(project_root, manifest.release_id)
    routed = route_release_map_refs(query_text, manifest, knowledge_map, focus_refs=focus_refs)
    if not routed['allowed_refs']:
        reason = 'no_active_focus_refs' if routed.get('focus_filter_applied') else 'no_allowed_refs'
        return _insufficient_context_payload(query_text, manifest, routed, reason=reason)

    release_dir = get_release_dir(project_root, manifest.release_id)
    tokens = _tokenize(query_text)
    ref_catalog = _build_ref_catalog(knowledge_map)
    candidates = _collect_allowed_release_candidates(
        release_dir,
        manifest,
        routed=routed,
        ref_catalog=ref_catalog,
        query_text=query_text,
        tokens=tokens,
    )
    if not candidates:
        return _insufficient_context_payload(query_text, manifest, routed, reason='allowed_refs_without_evidence')

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
                'field': candidate['citation']['field'],
                'source_hash': candidate['citation']['source_hash'],
                'ref': candidate['citation']['ref'],
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

    if not chunks:
        return _insufficient_context_payload(query_text, manifest, routed, reason='allowed_refs_without_evidence')

    return {
        'mode': 'context',
        'query': query_text,
        'release_id': manifest.release_id,
        'built_at': manifest.created_at,
        'chunks': chunks,
        'citations': citations,
        'allowed_refs': routed['allowed_refs'],
        'map_hash': routed['map_hash'],
        'map_source_hash': routed['map_source_hash'],
        'reason': None,
        'requested_focus_refs': routed.get('requested_focus_refs', []),
        'active_focus_refs': routed.get('active_focus_refs', []),
    }


def route_release_map_refs(
    query: str,
    current_release,
    knowledge_map,
    *,
    focus_refs: list[str] | None = None,
) -> dict[str, Any]:
    query_text = str(query or '').strip()
    tokens = _tokenize(query_text)
    ref_catalog = _build_ref_catalog(knowledge_map)
    active_refs = {
        ref
        for ref in ref_catalog
        if _ref_is_active(ref, ref_catalog=ref_catalog, deprecated_refs=set(knowledge_map.deprecated or []))
    }
    normalized_focus_refs = [str(ref).strip() for ref in list(focus_refs or []) if str(ref or '').strip()]
    focus_set = {ref for ref in normalized_focus_refs if ref in active_refs}
    focus_filter_applied = bool(normalized_focus_refs)
    candidate_refs = set(focus_set) if focus_filter_applied else set(active_refs)
    seeded_refs = set(focus_set)

    for ref, meta in ref_catalog.items():
        if ref not in candidate_refs:
            continue
        if _score_text(_build_ref_route_text(meta), query_text, tokens) > 0:
            seeded_refs.add(ref)

    allowed_refs = set(seeded_refs)
    if seeded_refs and not focus_filter_applied:
        adjacency = _build_ref_adjacency(knowledge_map)
        for ref in list(seeded_refs):
            allowed_refs.update(neighbor for neighbor in adjacency.get(ref, set()) if neighbor in active_refs)

    return {
        'allowed_refs': sorted(allowed_refs),
        'release_id': current_release.release_id,
        'map_hash': getattr(current_release, 'map_hash', None),
        'map_source_hash': knowledge_map.source_hash,
        'focus_refs': sorted(focus_set),
        'requested_focus_refs': normalized_focus_refs,
        'active_focus_refs': sorted(focus_set),
        'focus_filter_applied': focus_filter_applied,
    }


def _collect_allowed_release_candidates(
    release_dir: Path,
    manifest,
    *,
    routed: dict[str, Any],
    ref_catalog: dict[str, dict[str, Any]],
    query_text: str,
    tokens: list[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    refs_by_artifact = _group_allowed_refs_by_artifact(routed['allowed_refs'])
    focused_refs = set(routed.get('focus_refs') or [])

    for source_type, allowed_refs in refs_by_artifact.items():
        if not allowed_refs:
            continue
        artifact = manifest.indexes.get(source_type)
        if artifact is None:
            continue
        artifact_path = _resolve_release_artifact_path(release_dir, artifact.path)
        if not artifact_path.exists() or not artifact_path.is_file():
            continue
        for row_number, ref, record in _iter_matching_artifact_rows(artifact_path, source_type, allowed_refs, ref_catalog):
            text = _build_record_text(source_type, record)
            if not text:
                continue
            score = _score_text(text, query_text, tokens)
            if ref in focused_refs:
                score = max(score, 1.0)
            if score <= 0:
                continue
            candidates.append(
                {
                    'source_type': source_type,
                    'text': text,
                    'score': score,
                    'sort_ref': ref,
                    'citation': {
                        'artifact_path': artifact.path,
                        'source_path': str(record.get('source_path') or '') or None,
                        'title': _record_title(source_type, record),
                        'row': row_number,
                        'field': _record_citation_field(source_type, record, query_text, tokens),
                        'source_hash': record.get('source_hash'),
                        'ref': ref,
                    },
                }
            )
    return candidates


def _insufficient_context_payload(query_text: str, manifest, routed: dict[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        'mode': 'insufficient_context',
        'query': query_text,
        'release_id': manifest.release_id,
        'built_at': manifest.created_at,
        'chunks': [],
        'citations': [],
        'allowed_refs': routed.get('allowed_refs', []),
        'map_hash': routed.get('map_hash'),
        'map_source_hash': routed.get('map_source_hash'),
        'reason': reason,
        'requested_focus_refs': routed.get('requested_focus_refs', []),
        'active_focus_refs': routed.get('active_focus_refs', []),
    }


def _iter_matching_artifact_rows(
    path: Path,
    source_type: str,
    allowed_refs: set[str],
    ref_catalog: dict[str, dict[str, Any]],
):
    pending_refs = set(allowed_refs)
    with path.open('r', encoding='utf-8') as handle:
        for row_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            ref = _record_ref(source_type, record, ref_catalog)
            if ref not in pending_refs:
                continue
            yield row_number, ref, record
            pending_refs.discard(ref)
            if not pending_refs:
                break


def _record_ref(source_type: str, record: dict[str, Any], ref_catalog: dict[str, dict[str, Any]]) -> str | None:
    source_path = _normalize_record_source_path(record.get('source_path'))
    if source_type == 'table_schema':
        table_name = str(record.get('table_name') or '').strip()
        if table_name:
            table_ref = f'table:{table_name}'
            if table_ref in ref_catalog:
                return table_ref
        if source_path:
            for ref, meta in ref_catalog.items():
                if meta['source_type'] == 'table_schema' and meta['source_path'] == source_path:
                    return ref
        return None
    if not source_path:
        return None
    for ref, meta in ref_catalog.items():
        if meta['source_type'] == source_type and meta['source_path'] == source_path:
            return ref
    return None


def _build_ref_catalog(knowledge_map) -> dict[str, dict[str, Any]]:
    systems = {
        system.system_id: system
        for system in list(getattr(knowledge_map, 'systems', []) or [])
        if getattr(system, 'system_id', None)
    }
    catalog: dict[str, dict[str, Any]] = {}
    for table in list(getattr(knowledge_map, 'tables', []) or []):
        ref = f'table:{table.table_id}'
        catalog[ref] = {
            'ref': ref,
            'source_type': 'table_schema',
            'title': table.title,
            'source_path': _normalize_record_source_path(table.source_path),
            'status': table.status,
            'system_title': getattr(systems.get(table.system_id), 'title', '') if table.system_id else '',
        }
    for doc in list(getattr(knowledge_map, 'docs', []) or []):
        ref = f'doc:{doc.doc_id}'
        catalog[ref] = {
            'ref': ref,
            'source_type': 'doc_knowledge',
            'title': doc.title,
            'source_path': _normalize_record_source_path(doc.source_path),
            'status': doc.status,
            'system_title': getattr(systems.get(doc.system_id), 'title', '') if doc.system_id else '',
        }
    for script in list(getattr(knowledge_map, 'scripts', []) or []):
        ref = f'script:{script.script_id}'
        catalog[ref] = {
            'ref': ref,
            'source_type': 'script_evidence',
            'title': script.title,
            'source_path': _normalize_record_source_path(script.source_path),
            'status': script.status,
            'system_title': getattr(systems.get(script.system_id), 'title', '') if script.system_id else '',
        }
    return catalog


def _build_ref_route_text(meta: dict[str, Any]) -> str:
    parts = [
        str(meta.get('ref') or ''),
        str(meta.get('title') or ''),
        str(meta.get('source_path') or ''),
        str(meta.get('system_title') or ''),
    ]
    return ' '.join(part for part in parts if part)


def _build_ref_adjacency(knowledge_map) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for relationship in list(getattr(knowledge_map, 'relationships', []) or []):
        from_ref = str(getattr(relationship, 'from_ref', '') or '').strip()
        to_ref = str(getattr(relationship, 'to_ref', '') or '').strip()
        if not from_ref or not to_ref:
            continue
        adjacency.setdefault(from_ref, set()).add(to_ref)
        adjacency.setdefault(to_ref, set()).add(from_ref)
    return adjacency


def _ref_is_active(ref: str, *, ref_catalog: dict[str, dict[str, Any]], deprecated_refs: set[str]) -> bool:
    meta = ref_catalog.get(ref)
    if meta is None:
        return False
    status = str(meta.get('status') or 'active').strip().lower()
    if status in {'deprecated', 'ignored'}:
        return False
    if ref in deprecated_refs:
        return False
    return True


def _group_allowed_refs_by_artifact(allowed_refs: list[str]) -> dict[str, set[str]]:
    grouped = {
        'table_schema': set(),
        'doc_knowledge': set(),
        'script_evidence': set(),
    }
    for ref in allowed_refs:
        prefix, _, _tail = str(ref).partition(':')
        artifact_key = _ARTIFACT_BY_REF_PREFIX.get(prefix)
        if artifact_key is not None:
            grouped[artifact_key].add(ref)
    return grouped


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


def _normalize_record_source_path(value: Any) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    try:
        return normalize_local_project_relative_path(text)
    except ValueError:
        return text.replace('\\', '/').strip('/ ')


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


def _record_citation_field(source_type: str, record: dict[str, Any], query_text: str, tokens: list[str]) -> str | None:
    if source_type != 'table_schema':
        return None
    best_name: str | None = None
    best_score = 0.0
    for field in list(record.get('fields') or []):
        if not isinstance(field, dict):
            continue
        field_name = str(field.get('name') or '').strip()
        if not field_name:
            continue
        field_text = ' '.join(
            str(part or '')
            for part in (field.get('name'), field.get('type'), field.get('description'))
            if part
        )
        score = _score_text(field_text, query_text, tokens)
        if score > best_score:
            best_score = score
            best_name = field_name
    if best_name:
        return best_name
    primary_key = str(record.get('primary_key') or '').strip()
    if primary_key:
        return primary_key
    for field in list(record.get('fields') or []):
        if isinstance(field, dict) and field.get('name'):
            return str(field['name'])
    return None


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ''
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + '...'
