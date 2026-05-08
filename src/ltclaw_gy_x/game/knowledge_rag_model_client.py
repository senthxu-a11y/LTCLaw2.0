from __future__ import annotations

import re
from typing import Any, Mapping, Protocol, TypedDict


MAX_MODEL_SUMMARY_CHUNKS = 2
MAX_MODEL_SUMMARY_CHARS = 220


class RagAnswerPromptPayload(TypedDict):
    query: str
    release_id: str | None
    built_at: str | None
    chunks: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    policy_hints: list[str]


class RagModelClientResponse(TypedDict, total=False):
    answer: str
    citation_ids: list[str]
    warnings: list[str]


class RagModelClient(Protocol):
    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        ...


def build_rag_model_prompt_payload(
    *,
    query: str,
    release_id: str | None,
    built_at: Any,
    chunks: list[Mapping[str, Any]],
    citations: list[Mapping[str, Any]],
    policy_hints: list[str],
) -> RagAnswerPromptPayload:
    return {
        'query': str(query or '').strip(),
        'release_id': str(release_id).strip() if release_id is not None else None,
        'built_at': str(built_at).strip() if built_at is not None else None,
        'chunks': [_normalize_chunk(chunk) for chunk in chunks if isinstance(chunk, Mapping)],
        'citations': [dict(citation) for citation in citations if isinstance(citation, Mapping)],
        'policy_hints': [str(hint).strip() for hint in policy_hints if str(hint or '').strip()],
    }


class DeterministicMockRagModelClient:
    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        chunks = payload.get('chunks') if isinstance(payload.get('chunks'), list) else []
        citations_by_id = _index_citations(payload.get('citations'))

        snippets: list[str] = []
        citation_ids: list[str] = []
        for raw_chunk in chunks:
            if not isinstance(raw_chunk, Mapping):
                continue
            citation_id = str(raw_chunk.get('citation_id') or '').strip()
            text = _normalize_text(raw_chunk.get('text'))
            if not citation_id or citation_id not in citations_by_id or not text:
                continue
            if citation_id not in citation_ids:
                citation_ids.append(citation_id)
            snippet = _truncate_text(text, MAX_MODEL_SUMMARY_CHARS)
            if snippet and snippet not in snippets:
                snippets.append(snippet)
            if len(snippets) >= MAX_MODEL_SUMMARY_CHUNKS:
                break

        if not snippets or not citation_ids:
            return {
                'answer': '',
                'citation_ids': [],
                'warnings': ['Mock model client did not receive grounded context.'],
            }

        if len(snippets) == 1:
            answer = f'Grounded answer from the provided current-release context: {snippets[0]}'
        else:
            joined = ' '.join(f'({index}) {snippet}' for index, snippet in enumerate(snippets, start=1))
            answer = f'Grounded answer from the provided current-release context: {joined}'

        return {
            'answer': answer,
            'citation_ids': citation_ids,
            'warnings': [],
        }


class DisabledRagModelClient:
    def __init__(self, warning_message: str = 'Model provider is disabled.') -> None:
        self.warning_message = str(warning_message or 'Model provider is disabled.').strip()

    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        return {
            'answer': '',
            'citation_ids': [],
            'warnings': [self.warning_message],
        }


def _normalize_chunk(raw_chunk: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'chunk_id': str(raw_chunk.get('chunk_id') or '').strip(),
        'citation_id': str(raw_chunk.get('citation_id') or '').strip(),
        'rank': int(raw_chunk.get('rank') or 0),
        'score': float(raw_chunk.get('score') or 0.0),
        'text': _normalize_text(raw_chunk.get('text')),
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


def _normalize_text(value: Any) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + '...'
