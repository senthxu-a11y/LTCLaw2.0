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
)
from .paths import get_release_dir

DEFAULT_TOP_K = 10
MAX_TOP_K = 50
SEARCHABLE_RELEASE_INDEXES = ('table_schema', 'doc_knowledge', 'script_evidence')


def query_current_release(
    project_root: Path,
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    mode: str = 'hybrid',
) -> dict[str, Any]:
    query_text = str(query or '').strip()
    limited_top_k = max(1, min(int(top_k or DEFAULT_TOP_K), MAX_TOP_K))

    try:
        manifest = get_current_release(project_root)
    except (CurrentKnowledgeReleaseNotSetError, KnowledgeReleaseNotFoundError):
        return {
            'mode': 'no_current_release',
            'query': query_text,
            'top_k': limited_top_k,
            'release_id': None,
            'built_at': None,
            'results': [],
            'count': 0,
        }

    if not query_text:
        return {
            'mode': 'current_release_keyword',
            'query': query_text,
            'top_k': limited_top_k,
            'release_id': manifest.release_id,
            'built_at': manifest.created_at,
            'results': [],
            'count': 0,
        }

    tokens = _tokenize(query_text)
    release_dir = get_release_dir(project_root, manifest.release_id)
    results: list[dict[str, Any]] = []

    for source_type in SEARCHABLE_RELEASE_INDEXES:
        artifact = manifest.indexes.get(source_type)
        if artifact is None:
            continue
        index_path = _resolve_release_index_path(release_dir, artifact.path)
        if index_path is None:
            continue
        if not index_path.exists() or not index_path.is_file():
            continue
        for record in _load_jsonl(index_path):
            score = _score_record(record, query_text, tokens)
            if score <= 0:
                continue
            results.append(_build_result_item(source_type, manifest.release_id, manifest.created_at, record, score))

    results.sort(
        key=lambda item: (
            -float(item.get('score') or 0.0),
            str(item.get('source_type') or ''),
            str(item.get('source_path') or ''),
            str(item.get('title') or ''),
        )
    )
    results = results[:limited_top_k]

    return {
        'mode': 'current_release_keyword',
        'query': query_text,
        'top_k': limited_top_k,
        'release_id': manifest.release_id,
        'built_at': manifest.created_at,
        'results': results,
        'count': len(results),
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    payload = path.read_text(encoding='utf-8')
    items: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        items.append(json.loads(line))
    return items


def _resolve_release_index_path(release_dir: Path, relative_path: str | None) -> Path | None:
    try:
        normalized_path = normalize_local_project_relative_path(relative_path, error_label='release index path')
    except ValueError:
        return None
    resolved = (release_dir / normalized_path).resolve(strict=False)
    release_root = release_dir.resolve(strict=False)
    try:
        resolved.relative_to(release_root)
    except ValueError:
        return None
    return resolved


def _tokenize(query_text: str) -> list[str]:
    return [token for token in re.findall(r'\w+', query_text.lower()) if token]


def _score_record(record: dict[str, Any], query_text: str, tokens: list[str]) -> float:
    haystack = _record_search_text(record)
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


def _record_search_text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, dict):
        return ' '.join(_record_search_text(item) for item in value.values() if item is not None).lower()
    if isinstance(value, list):
        return ' '.join(_record_search_text(item) for item in value if item is not None).lower()
    return str(value).lower()


def _build_result_item(
    source_type: str,
    release_id: str,
    built_at,
    record: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    item = {
        'source_type': source_type,
        'source_path': str(record.get('source_path') or ''),
        'release_id': release_id,
        'built_at': built_at,
        'score': score,
        'title': None,
        'summary': None,
        'tags': [],
    }
    if source_type == 'table_schema':
        item['title'] = record.get('table_name')
        item['summary'] = record.get('summary')
        item['table_name'] = record.get('table_name')
        item['system'] = record.get('system')
        item['primary_key'] = record.get('primary_key')
        item['row_count'] = record.get('row_count')
    elif source_type == 'doc_knowledge':
        item['title'] = record.get('title')
        item['summary'] = record.get('summary')
        item['category'] = record.get('category')
        item['tags'] = list(record.get('tags') or [])
    elif source_type == 'script_evidence':
        item['title'] = Path(str(record.get('source_path') or '')).name or None
        item['summary'] = record.get('summary')
        item['language'] = record.get('language')
        item['kind'] = record.get('kind')
    return item
