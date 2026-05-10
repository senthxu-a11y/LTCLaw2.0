from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping, Protocol, runtime_checkable
from urllib.parse import urlsplit, urlunsplit

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
    transport_enabled: bool = False
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


class ExternalRagModelTransportSkeletonError(ExternalRagModelClientError):
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


class ExternalRagModelCredentialResolverSkeleton:
    def __call__(
        self,
        request: ExternalRagModelCredentialRequest,
    ) -> ExternalRagModelClientCredentials | None:
        if _normalize_credential_request(request) is None:
            return None
        return None


class ExternalRagModelEnvCredentialResolver:
    def __call__(
        self,
        request: ExternalRagModelCredentialRequest,
    ) -> ExternalRagModelClientCredentials | None:
        normalized_request = _normalize_credential_request(request)
        if normalized_request is None or normalized_request.env is None:
            return None

        api_key_env_var = _normalize_optional_text(normalized_request.env.api_key_env_var)
        if api_key_env_var is None:
            return None

        try:
            api_key = _normalize_optional_text(os.environ.get(api_key_env_var))
        except Exception:
            return None

        if api_key is None:
            return None

        return ExternalRagModelClientCredentials(api_key=api_key)
        return None


class ExternalRagModelHttpTransportSkeleton:
    def __call__(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> RagModelClientResponse:
        self.build_request_preview(payload, config=config, credentials=credentials)
        raise ExternalRagModelTransportSkeletonError(_REQUEST_FAILED_WARNING)

    def build_request_preview(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> dict[str, Any]:
        query = str(payload.get('query') or '') if isinstance(payload, Mapping) else ''
        chunks = payload.get('chunks') if isinstance(payload, Mapping) else []
        citations = payload.get('citations') if isinstance(payload, Mapping) else []
        policy_hints = payload.get('policy_hints') if isinstance(payload, Mapping) else []

        return {
            'transport_kind': 'http_skeleton',
            'provider_name': _normalize_optional_text(config.provider_name),
            'model_name': _normalize_optional_text(config.model_name),
            'base_url': _redact_url_for_preview(config.base_url),
            'proxy': _redact_url_for_preview(config.proxy),
            'timeout_seconds': float(config.timeout_seconds),
            'max_output_tokens': config.max_output_tokens,
            'credentials': {
                'has_credentials': bool(str(credentials.api_key or '').strip()),
                'has_endpoint': _normalize_optional_text(credentials.endpoint) is not None,
            },
            'request_shape': {
                'input_mode': 'normalized_rag_prompt',
                'message_count': 1,
                'includes_authorization_header': False,
            },
            'payload': {
                'query_chars': len(query),
                'chunk_count': len(chunks) if isinstance(chunks, list) else 0,
                'citation_count': len(citations) if isinstance(citations, list) else 0,
                'policy_hint_count': len(policy_hints) if isinstance(policy_hints, list) else 0,
                'release_id_present': _normalize_optional_text(payload.get('release_id')) is not None,
                'built_at_present': _normalize_optional_text(payload.get('built_at')) is not None,
            },
        }


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
        self._credential_resolver = (
            credential_resolver
            or _wrap_responder_as_credential_resolver(responder)
            or ExternalRagModelEnvCredentialResolver()
        )
        self._transport = transport or _wrap_responder_as_transport(responder) or ExternalRagModelHttpTransportSkeleton()

    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        if not self.config.enabled:
            return _warning_response(_DISABLED_WARNING)
        if not self.config.transport_enabled:
            return _warning_response(_NOT_CONNECTED_WARNING)

        normalized_payload = _normalize_prompt_payload(payload, config=self.config)

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

        if not allowed_providers:
            return _PROVIDER_NOT_ALLOWED_WARNING
        if provider_name is None or provider_name not in allowed_providers:
            return _PROVIDER_NOT_ALLOWED_WARNING
        if not allowed_models:
            return _MODEL_NOT_ALLOWED_WARNING
        if model_name is None or model_name not in allowed_models:
            return _MODEL_NOT_ALLOWED_WARNING
        return None

    def _resolve_credentials(self) -> ExternalRagModelClientCredentials:
        if self._credential_resolver is None:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)

        try:
            credentials = self._credential_resolver(
                ExternalRagModelCredentialRequest(
                    provider_name=_normalize_optional_text(self.config.provider_name) or 'future_external',
                    model_name=_normalize_optional_text(self.config.model_name),
                    env=self.config.env,
                )
            )
        except ExternalRagModelClientNotConfiguredError:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)
        except Exception:
            raise ExternalRagModelClientNotConfiguredError(_NOT_CONFIGURED_WARNING)

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


def _normalize_credential_request(
    request: ExternalRagModelCredentialRequest,
) -> ExternalRagModelCredentialRequest | None:
    provider_name = _normalize_optional_text(getattr(request, 'provider_name', None))
    if provider_name is None:
        return None

    model_name = _normalize_optional_text(getattr(request, 'model_name', None))
    env = getattr(request, 'env', None)
    normalized_env = None
    if isinstance(env, ExternalRagModelEnvConfig):
        api_key_env_var = _normalize_optional_text(env.api_key_env_var)
        if api_key_env_var is not None:
            normalized_env = ExternalRagModelEnvConfig(api_key_env_var=api_key_env_var)

    return ExternalRagModelCredentialRequest(
        provider_name=provider_name,
        model_name=model_name,
        env=normalized_env,
    )


def _redact_url_for_preview(value: Any) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None

    split_value = urlsplit(normalized)
    if not split_value.scheme and not split_value.netloc:
        return split_value.path or normalized.split('?', 1)[0]

    return urlunsplit((split_value.scheme, split_value.netloc, split_value.path, '', ''))
