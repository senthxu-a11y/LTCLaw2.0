from __future__ import annotations

import re
from typing import Any, Mapping

from .knowledge_rag_model_client import RagModelClient, build_rag_model_prompt_payload
from .knowledge_rag_model_registry import get_rag_model_client


_NO_GROUNDED_CONTEXT_WARNING = 'No grounded context was available for a safe answer.'
_MISSING_CONTEXT_CITATION_WARNING = 'Ignored one or more context chunks without a matching citation.'
_MODEL_NOT_GROUNDED_WARNING = 'Model client output was not grounded in the provided context.'
_MODEL_OUT_OF_CONTEXT_CITATION_WARNING = 'Ignored one or more model citation ids outside the provided context.'
_CHANGE_QUERY_WARNING = 'For change proposals or edits, use the workbench flow.'
_STRUCTURED_FACT_WARNING = 'For exact numeric or row-level facts, use the structured query flow.'

MAX_SUMMARY_CHUNKS = 2
MAX_SUMMARY_CHARS = 220

_CHANGE_QUERY_PATTERN = re.compile(r'\b(change|edit|update|modify|set|adjust|rewrite|patch|delete|remove|add)\b', re.IGNORECASE)
_STRUCTURED_FACT_TERM_PATTERN = re.compile(
    r'\b(skilltable|primary key|id|row|rows|column|columns|field|fields|value|values)\b',
    re.IGNORECASE,
)
_STRUCTURED_FACT_NUMBER_PATTERN = re.compile(r'\d+')
_STRUCTURED_FACT_NUMBER_CONTEXT_PATTERN = re.compile(
    r'\b(table|skilltable|damage|value|field|row|column|id|primary key)\b',
    re.IGNORECASE,
)


def build_rag_answer(
    query: str,
    context: Mapping[str, Any],
    model_client: RagModelClient | None = None,
) -> dict[str, Any]:
    release_id = _normalize_release_id(context.get('release_id'))
    if _normalize_text(context.get('mode')) == 'no_current_release':
        return {
            'mode': 'no_current_release',
            'answer': '',
            'release_id': release_id,
            'citations': [],
            'warnings': [],
        }

    grounded_chunks, grounded_citations, warnings = _collect_grounded_context(context)
    if not grounded_chunks:
        return {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': release_id,
            'citations': [],
            'warnings': _dedupe_strings([*warnings, _NO_GROUNDED_CONTEXT_WARNING]),
        }

    policy_warnings = _policy_warnings_for_query(query)
    if model_client is None:
        answer_text = (
            'Based on the provided current-release context, the strongest grounded evidence is: '
            f'{_compose_answer_snippets(grounded_chunks)}'
        )
        return {
            'mode': 'answer',
            'answer': answer_text,
            'release_id': release_id,
            'citations': grounded_citations,
            'warnings': _dedupe_strings([*warnings, *policy_warnings]),
        }

    prompt_payload = build_rag_model_prompt_payload(
        query=_normalize_text(query),
        release_id=release_id,
        built_at=context.get('built_at'),
        chunks=grounded_chunks,
        citations=grounded_citations,
        policy_hints=policy_warnings,
    )
    raw_response = model_client.generate_answer(prompt_payload)
    return _build_model_client_answer(
        release_id=release_id,
        grounded_citations=grounded_citations,
        base_warnings=[*warnings, *policy_warnings],
        raw_response=raw_response,
    )


def build_rag_answer_with_provider(
    query: str,
    context: Mapping[str, Any],
    *,
    provider_name: str | None = None,
    factories: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if _normalize_text(context.get('mode')) == 'no_current_release':
        return build_rag_answer(query, context)

    grounded_chunks, _, warnings = _collect_grounded_context(context)
    if not grounded_chunks:
        return {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': _normalize_release_id(context.get('release_id')),
            'citations': [],
            'warnings': _dedupe_strings([*warnings, _NO_GROUNDED_CONTEXT_WARNING]),
        }

    resolved = get_rag_model_client(provider_name, factories=factories)
    payload = build_rag_answer(query, context, model_client=resolved.client)
    payload['warnings'] = _dedupe_strings([*resolved.warnings, *payload.get('warnings', [])])
    return payload


def _build_model_client_answer(
    *,
    release_id: str | None,
    grounded_citations: list[dict[str, Any]],
    base_warnings: list[str],
    raw_response: Any,
) -> dict[str, Any]:
    citations_by_id = _index_citations(grounded_citations)
    answer = ''
    if isinstance(raw_response, Mapping):
        answer = _normalize_text(raw_response.get('answer'))
        raw_citation_ids = raw_response.get('citation_ids')
        response_warnings = _coerce_warning_list(raw_response.get('warnings'))
    else:
        raw_citation_ids = []
        response_warnings = []

    valid_citation_ids, citation_warnings = _validate_model_citation_ids(raw_citation_ids, citations_by_id)
    warnings = _dedupe_strings([*base_warnings, *response_warnings, *citation_warnings])

    if not answer or not valid_citation_ids:
        return {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': release_id,
            'citations': [],
            'warnings': _dedupe_strings([*warnings, _MODEL_NOT_GROUNDED_WARNING]),
        }

    return {
        'mode': 'answer',
        'answer': answer,
        'release_id': release_id,
        'citations': [citations_by_id[citation_id] for citation_id in valid_citation_ids],
        'warnings': warnings,
    }


def _collect_grounded_context(context: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    citations_by_id = _index_citations(context.get('citations'))
    grounded_chunks: list[dict[str, Any]] = []
    grounded_citation_ids: list[str] = []
    ignored_missing_citation = False

    for raw_chunk in context.get('chunks', []):
        if not isinstance(raw_chunk, Mapping):
            continue
        citation_id = _normalize_text(raw_chunk.get('citation_id'))
        text = _normalize_text(raw_chunk.get('text'))
        if not citation_id or citation_id not in citations_by_id:
            if citation_id:
                ignored_missing_citation = True
            continue
        if not text:
            continue
        grounded_chunks.append(
            {
                'chunk_id': _normalize_text(raw_chunk.get('chunk_id')),
                'citation_id': citation_id,
                'rank': int(raw_chunk.get('rank') or 0),
                'score': float(raw_chunk.get('score') or 0.0),
                'text': text,
            }
        )
        if citation_id not in grounded_citation_ids:
            grounded_citation_ids.append(citation_id)

    grounded_chunks.sort(key=lambda item: (item['rank'], -item['score'], item['chunk_id']))
    grounded_citation_ids = []
    for chunk in grounded_chunks:
        citation_id = chunk['citation_id']
        if citation_id not in grounded_citation_ids:
            grounded_citation_ids.append(citation_id)
    warnings: list[str] = []
    if ignored_missing_citation:
        warnings.append(_MISSING_CONTEXT_CITATION_WARNING)

    grounded_citations = [citations_by_id[citation_id] for citation_id in grounded_citation_ids]
    return grounded_chunks, grounded_citations, warnings


def _index_citations(raw_citations: Any) -> dict[str, dict[str, Any]]:
    citations_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_citations, list):
        return citations_by_id
    for raw_citation in raw_citations:
        if not isinstance(raw_citation, Mapping):
            continue
        citation_id = _normalize_text(raw_citation.get('citation_id'))
        if not citation_id:
            continue
        citations_by_id[citation_id] = dict(raw_citation)
    return citations_by_id


def _policy_warnings_for_query(query: str) -> list[str]:
    normalized_query = _normalize_text(query)
    warnings: list[str] = []
    if _CHANGE_QUERY_PATTERN.search(normalized_query):
        warnings.append(_CHANGE_QUERY_WARNING)
    if _looks_like_structured_fact_query(normalized_query):
        warnings.append(_STRUCTURED_FACT_WARNING)
    return warnings


def _compose_answer_snippets(grounded_chunks: list[dict[str, Any]]) -> str:
    snippets: list[str] = []
    for chunk in grounded_chunks[:MAX_SUMMARY_CHUNKS]:
        snippet = _truncate_text(_normalize_text(chunk.get('text')), MAX_SUMMARY_CHARS)
        if snippet and snippet not in snippets:
            snippets.append(snippet)
    if not snippets:
        return ''
    if len(snippets) == 1:
        return snippets[0]
    return ' '.join(f'({index}) {snippet}' for index, snippet in enumerate(snippets, start=1))


def _looks_like_structured_fact_query(query: str) -> bool:
    if not query:
        return False
    if _STRUCTURED_FACT_TERM_PATTERN.search(query):
        return True
    return bool(
        _STRUCTURED_FACT_NUMBER_PATTERN.search(query)
        and _STRUCTURED_FACT_NUMBER_CONTEXT_PATTERN.search(query)
    )


def _normalize_release_id(value: Any) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_text(value: Any) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _coerce_warning_list(raw_warnings: Any) -> list[str]:
    if not isinstance(raw_warnings, list):
        return []
    return [str(warning).strip() for warning in raw_warnings if str(warning or '').strip()]


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + '...'


def _validate_model_citation_ids(
    raw_citation_ids: Any,
    citations_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[str], list[str]]:
    valid_citation_ids: list[str] = []
    ignored_invalid = False
    if not isinstance(raw_citation_ids, list):
        return valid_citation_ids, []
    for raw_citation_id in raw_citation_ids:
        citation_id = str(raw_citation_id or '').strip()
        if not citation_id:
            continue
        if citation_id not in citations_by_id:
            ignored_invalid = True
            continue
        if citation_id not in valid_citation_ids:
            valid_citation_ids.append(citation_id)
    warnings: list[str] = []
    if ignored_invalid:
        warnings.append(_MODEL_OUT_OF_CONTEXT_CITATION_WARNING)
    return valid_citation_ids, warnings


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped
