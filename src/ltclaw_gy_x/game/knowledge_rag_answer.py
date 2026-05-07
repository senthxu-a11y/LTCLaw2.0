from __future__ import annotations

import re
from typing import Any, Mapping


MAX_SUMMARY_CHUNKS = 2
MAX_SUMMARY_CHARS = 220

_PRECISION_HINT_RE = re.compile(
    r'\b(what is|exact|precise|specific|value|row|field|primary key|id)\b',
    re.IGNORECASE,
)
_MODIFICATION_HINT_RE = re.compile(
    r'\b(change|set|update|modify|edit|patch|write|commit|adjust|tune|increase|decrease)\b',
    re.IGNORECASE,
)


def build_rag_answer(query: str, context: Mapping[str, Any]) -> dict[str, Any]:
    query_text = str(query or '').strip()
    context_payload = context if isinstance(context, Mapping) else {}
    context_mode = str(context_payload.get('mode') or '').strip() or 'insufficient_context'
    release_id = context_payload.get('release_id')

    if context_mode == 'no_current_release':
        return {
            'mode': 'no_current_release',
            'answer': '',
            'release_id': release_id,
            'citations': [],
            'warnings': [],
        }

    citations_by_id = _index_citations(context_payload.get('citations'))
    valid_chunks, ordered_citation_ids, warnings = _select_grounded_chunks(
        context_payload.get('chunks'),
        citations_by_id,
    )
    warnings.extend(_build_query_warnings(query_text))
    warnings = _dedupe_strings(warnings)

    if context_mode != 'context' or not valid_chunks:
        if not valid_chunks:
            warnings = _dedupe_strings([
                'No grounded context was available for a safe answer.',
                *warnings,
            ])
        return {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': release_id,
            'citations': [],
            'warnings': warnings,
        }

    return {
        'mode': 'answer',
        'answer': _compose_answer(valid_chunks),
        'release_id': release_id,
        'citations': [dict(citations_by_id[citation_id]) for citation_id in ordered_citation_ids],
        'warnings': warnings,
    }


def _index_citations(raw_citations: Any) -> dict[str, dict[str, Any]]:
    citations_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_citations, list):
        return citations_by_id
    for raw_citation in raw_citations:
        if not isinstance(raw_citation, Mapping):
            continue
        citation_id = str(raw_citation.get('citation_id') or '').strip()
        if not citation_id:
            continue
        citations_by_id[citation_id] = dict(raw_citation)
    return citations_by_id


def _select_grounded_chunks(
    raw_chunks: Any,
    citations_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    valid_chunks: list[dict[str, Any]] = []
    ordered_citation_ids: list[str] = []
    warnings: list[str] = []
    if not isinstance(raw_chunks, list):
        return valid_chunks, ordered_citation_ids, warnings

    missing_citation_detected = False
    for raw_chunk in raw_chunks:
        if not isinstance(raw_chunk, Mapping):
            continue
        citation_id = str(raw_chunk.get('citation_id') or '').strip()
        chunk_text = _normalize_text(raw_chunk.get('text'))
        if not citation_id or citation_id not in citations_by_id or not chunk_text:
            missing_citation_detected = True
            continue
        valid_chunks.append(
            {
                'chunk_id': str(raw_chunk.get('chunk_id') or '').strip(),
                'citation_id': citation_id,
                'rank': int(raw_chunk.get('rank') or len(valid_chunks) + 1),
                'score': float(raw_chunk.get('score') or 0.0),
                'text': chunk_text,
            }
        )
        if citation_id not in ordered_citation_ids:
            ordered_citation_ids.append(citation_id)

    if missing_citation_detected:
        warnings.append('Ignored one or more context chunks without a matching citation.')

    valid_chunks.sort(key=lambda item: (item['rank'], -item['score'], item['chunk_id']))
    return valid_chunks, ordered_citation_ids, warnings


def _compose_answer(valid_chunks: list[dict[str, Any]]) -> str:
    snippets: list[str] = []
    for chunk in valid_chunks[:MAX_SUMMARY_CHUNKS]:
        snippet = _truncate_text(chunk['text'], MAX_SUMMARY_CHARS)
        if snippet and snippet not in snippets:
            snippets.append(snippet)
    if not snippets:
        return ''
    if len(snippets) == 1:
        return f'Based on the provided current-release context, the strongest grounded evidence is: {snippets[0]}'
    joined = ' '.join(f'({index}) {snippet}' for index, snippet in enumerate(snippets, start=1))
    return f'Based on the provided current-release context, the strongest grounded evidence is: {joined}'


def _build_query_warnings(query_text: str) -> list[str]:
    normalized_query = str(query_text or '').strip().lower()
    warnings: list[str] = []
    if _looks_like_precise_query(normalized_query):
        warnings.append('For exact numeric or row-level facts, use the structured query flow.')
    if _looks_like_modification_query(normalized_query):
        warnings.append('For change proposals or edits, use the workbench flow.')
    return warnings


def _looks_like_precise_query(query_text: str) -> bool:
    if not query_text:
        return False
    if _PRECISION_HINT_RE.search(query_text):
        return True
    has_digits = any(character.isdigit() for character in query_text)
    return has_digits and any(token in query_text for token in ('table', 'damage', 'value', 'row', 'field', 'id'))


def _looks_like_modification_query(query_text: str) -> bool:
    if not query_text:
        return False
    return bool(_MODIFICATION_HINT_RE.search(query_text))


def _normalize_text(value: Any) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + '...'


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped