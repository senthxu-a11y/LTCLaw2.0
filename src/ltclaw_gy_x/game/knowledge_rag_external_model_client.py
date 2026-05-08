from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .knowledge_rag_model_client import RagAnswerPromptPayload, RagModelClientResponse


_SKELETON_WARNING = 'External provider adapter skeleton is not connected.'


@dataclass(frozen=True)
class ExternalRagModelClientConfig:
    timeout_seconds: float = 15.0
    max_prompt_chars: int = 12000
    max_output_chars: int = 2000
    max_retries: int = 0
    estimated_cost_limit: float = 0.0


@dataclass(frozen=True)
class ExternalRagModelClientSecrets:
    api_key: str | None = None
    model_name: str | None = None
    endpoint: str | None = None


ExternalRagModelResponder = Callable[[RagAnswerPromptPayload], RagModelClientResponse]


class ExternalRagModelClientSkeleton:
    def __init__(
        self,
        *,
        config: ExternalRagModelClientConfig | None = None,
        secrets: ExternalRagModelClientSecrets | None = None,
        responder: ExternalRagModelResponder | None = None,
    ) -> None:
        self.config = config or ExternalRagModelClientConfig()
        self.secrets = secrets or ExternalRagModelClientSecrets()
        self._responder = responder

    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        normalized_payload = _normalize_prompt_payload(payload, config=self.config)
        if self._responder is None:
            return {
                'answer': '',
                'citation_ids': [],
                'warnings': [_SKELETON_WARNING],
            }
        raw_response = self._responder(normalized_payload)
        return _normalize_response(raw_response, max_output_chars=self.config.max_output_chars)


def _normalize_prompt_payload(
    payload: RagAnswerPromptPayload,
    *,
    config: ExternalRagModelClientConfig,
) -> RagAnswerPromptPayload:
    if not isinstance(payload, Mapping):
        raise TypeError('RAG prompt payload must be a mapping.')

    query = str(payload.get('query') or '').strip()
    release_id = payload.get('release_id')
    built_at = payload.get('built_at')
    chunks = payload.get('chunks')
    citations = payload.get('citations')
    policy_hints = payload.get('policy_hints')

    if not isinstance(chunks, list):
        raise TypeError('RAG prompt payload chunks must be a list.')
    if not isinstance(citations, list):
        raise TypeError('RAG prompt payload citations must be a list.')
    if not isinstance(policy_hints, list):
        raise TypeError('RAG prompt payload policy_hints must be a list.')

    normalized_payload: RagAnswerPromptPayload = {
        'query': query,
        'release_id': str(release_id).strip() if release_id is not None else None,
        'built_at': str(built_at).strip() if built_at is not None else None,
        'chunks': [dict(chunk) for chunk in chunks if isinstance(chunk, Mapping)],
        'citations': [dict(citation) for citation in citations if isinstance(citation, Mapping)],
        'policy_hints': [str(hint).strip() for hint in policy_hints if str(hint or '').strip()],
    }

    prompt_char_count = len(normalized_payload['query'])
    prompt_char_count += sum(len(str(chunk.get('text') or '')) for chunk in normalized_payload['chunks'])
    prompt_char_count += sum(len(hint) for hint in normalized_payload['policy_hints'])
    if prompt_char_count > config.max_prompt_chars:
        raise ValueError(
            f'RAG prompt payload exceeds configured max_prompt_chars: {prompt_char_count} > {config.max_prompt_chars}'
        )

    return normalized_payload


def _normalize_response(raw_response: Any, *, max_output_chars: int) -> RagModelClientResponse:
    if not isinstance(raw_response, Mapping):
        raise TypeError('RAG model client response must be a mapping.')

    answer = str(raw_response.get('answer') or '').strip()
    if max_output_chars > 0 and len(answer) > max_output_chars:
        answer = answer[:max_output_chars]

    citation_ids = [
        str(citation_id).strip()
        for citation_id in raw_response.get('citation_ids', [])
        if str(citation_id or '').strip()
    ]
    warnings = [
        str(warning).strip()
        for warning in raw_response.get('warnings', [])
        if str(warning or '').strip()
    ]

    return {
        'answer': answer,
        'citation_ids': citation_ids,
        'warnings': warnings,
    }