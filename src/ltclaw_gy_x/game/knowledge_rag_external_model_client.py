from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from .knowledge_rag_model_client import RagAnswerPromptPayload, RagModelClientResponse


_DISABLED_WARNING = 'External provider adapter skeleton is disabled.'
_NOT_CONFIGURED_WARNING = 'External provider adapter skeleton is not configured.'
_NOT_CONNECTED_WARNING = 'External provider adapter skeleton transport is not connected.'
_PROVIDER_NOT_ALLOWED_WARNING = 'External provider adapter skeleton provider is not allowed.'
_MODEL_NOT_ALLOWED_WARNING = 'External provider adapter skeleton model is not allowed.'
_TIMEOUT_WARNING = 'External provider adapter skeleton timed out.'
_HTTP_ERROR_WARNING = 'External provider adapter skeleton HTTP error.'
_INVALID_RESPONSE_WARNING = 'External provider adapter skeleton returned an invalid response.'
_REQUEST_FAILED_WARNING = 'External provider adapter skeleton request failed.'


@dataclass(frozen=True)
class ExternalRagModelEnvConfig:
    api_key_env_var: str | None = None


@dataclass(frozen=True)
class ExternalRagModelClientConfig:
    provider_name: str = 'future_external'
    model_name: str | None = None
    timeout_seconds: float = 15.0
    max_output_tokens: int | None = None
    enabled: bool = False
    base_url: str | None = None
    proxy: str | None = None
    allowed_providers: tuple[str, ...] | None = None
    allowed_models: tuple[str, ...] | None = None
    env: ExternalRagModelEnvConfig | None = None
    max_prompt_chars: int = 12000
    max_output_chars: int = 2000


@dataclass(frozen=True)
class ExternalRagModelClientCredentials:
    api_key: str
    endpoint: str | None = None


@dataclass(frozen=True)
class ExternalRagModelCredentialRequest:
    provider_name: str
    model_name: str | None = None
    env: ExternalRagModelEnvConfig | None = None


class ExternalRagModelClientError(RuntimeError):
    pass


class ExternalRagModelClientNotConfiguredError(ExternalRagModelClientError):
    pass


class ExternalRagModelClientHttpError(ExternalRagModelClientError):
    pass


@runtime_checkable
class ExternalRagModelCredentialResolver(Protocol):
    def __call__(self, request: ExternalRagModelCredentialRequest) -> ExternalRagModelClientCredentials | None:
        ...


@runtime_checkable
class ExternalRagModelTransport(Protocol):
    def __call__(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> RagModelClientResponse:
        ...


class ExternalRagModelClient:
    def __init__(
        self,
        *,
        config: ExternalRagModelClientConfig | None = None,
        credential_resolver: ExternalRagModelCredentialResolver | None = None,
        transport: ExternalRagModelTransport | None = None,
        responder: Any | None = None,
    ) -> None:
        self.config = config or ExternalRagModelClientConfig()
        self._credential_resolver = credential_resolver or _wrap_responder_as_credential_resolver(responder)
        self._transport = transport or _wrap_responder_as_transport(responder)

    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        normalized_payload = _normalize_prompt_payload(payload, config=self.config)
        if not self.config.enabled:
            return _warning_response(_DISABLED_WARNING)

        selection_warning = self._validate_selection()
        if selection_warning is not None:
            return _warning_response(selection_warning)

        try:
            credentials = self._resolve_credentials()
        except ExternalRagModelClientNotConfiguredError as exc:
            return _warning_response(str(exc))

        if self._transport is None:
            return _warning_response(_NOT_CONNECTED_WARNING)

        try:
            raw_response = self._transport(
                normalized_payload,
                config=self.config,
                credentials=credentials,
            )
            return _normalize_response(raw_response, max_output_chars=self.config.max_output_chars)
        except ExternalRagModelClientNotConfiguredError as exc:
            return _warning_response(str(exc))
        except TimeoutError:
            return _warning_response(_TIMEOUT_WARNING)
        except ExternalRagModelClientHttpError:
            return _warning_response(_HTTP_ERROR_WARNING)
        except TypeError:
            return _warning_response(_INVALID_RESPONSE_WARNING)
        except Exception:
            return _warning_response(_REQUEST_FAILED_WARNING)

    def _validate_selection(self) -> str | None:
        provider_name = _normalize_optional_text(self.config.provider_name)
        model_name = _normalize_optional_text(self.config.model_name)
        allowed_providers = _normalize_allowed_values(self.config.allowed_providers)
        allowed_models = _normalize_allowed_values(self.config.allowed_models)

        if allowed_providers is not None and provider_name not in allowed_providers:
            return _PROVIDER_NOT_ALLOWED_WARNING
        if allowed_models is not None and model_name not in allowed_models:
            return _MODEL_NOT_ALLOWED_WARNING
        return None

    def _resolve_credentials(self) -> ExternalRagModelClientCredentials:
        if self._credential_resolver is None:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)

        credentials = self._credential_resolver(
            ExternalRagModelCredentialRequest(
                provider_name=_normalize_optional_text(self.config.provider_name) or 'future_external',
                model_name=_normalize_optional_text(self.config.model_name),
                env=self.config.env,
            )
        )
        if credentials is None:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)

        api_key = str(credentials.api_key or '').strip()
        if not api_key:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)

        endpoint = str(credentials.endpoint).strip() if credentials.endpoint is not None else None
        return ExternalRagModelClientCredentials(api_key=api_key, endpoint=endpoint)


ExternalRagModelClientSkeleton = ExternalRagModelClient


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

    raw_citation_ids = raw_response.get('citation_ids', [])
    raw_warnings = raw_response.get('warnings', [])
    if not isinstance(raw_citation_ids, list):
        raise TypeError('RAG model client response citation_ids must be a list.')
    if not isinstance(raw_warnings, list):
        raise TypeError('RAG model client response warnings must be a list.')

    citation_ids = [
        str(citation_id).strip()
        for citation_id in raw_citation_ids
        if str(citation_id or '').strip()
    ]
    warnings = [
        str(warning).strip()
        for warning in raw_warnings
        if str(warning or '').strip()
    ]

    return {
        'answer': answer,
        'citation_ids': citation_ids,
        'warnings': warnings,
    }


def _warning_response(warning: str) -> RagModelClientResponse:
    return {
        'answer': '',
        'citation_ids': [],
        'warnings': [str(warning or '').strip()],
    }


def _wrap_responder_as_transport(responder: Any | None) -> ExternalRagModelTransport | None:
    if responder is None:
        return None

    def _transport(
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> RagModelClientResponse:
        return responder(payload)

    return _transport


def _wrap_responder_as_credential_resolver(
    responder: Any | None,
) -> ExternalRagModelCredentialResolver | None:
    if responder is None:
        return None

    def _resolver(request: ExternalRagModelCredentialRequest) -> ExternalRagModelClientCredentials:
        return ExternalRagModelClientCredentials(api_key='local-responder-placeholder')

    return _resolver


def _normalize_optional_text(value: Any) -> str | None:
    normalized = str(value or '').strip()
    return normalized or None


def _normalize_allowed_values(values: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if values is None:
        return None
    normalized_values = tuple(
        normalized
        for normalized in (_normalize_optional_text(value) for value in values)
        if normalized is not None
    )
    return normalized_values
