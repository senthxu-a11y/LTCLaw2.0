from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping, Protocol, runtime_checkable
from urllib.parse import urlsplit, urlunsplit

import httpx

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

_WARNING_CODE_DISABLED = 'disabled'
_WARNING_CODE_NOT_CONFIGURED = 'not_configured'
_WARNING_CODE_NOT_CONNECTED = 'not_connected'
_WARNING_CODE_PROVIDER_NOT_ALLOWED = 'provider_not_allowed'
_WARNING_CODE_MODEL_NOT_ALLOWED = 'model_not_allowed'
_WARNING_CODE_TIMEOUT = 'timeout'
_WARNING_CODE_HTTP_ERROR = 'http_error'
_WARNING_CODE_INVALID_RESPONSE = 'invalid_response'
_WARNING_CODE_REQUEST_FAILED = 'request_failed'
_WARNING_CODE_SKELETON_REQUEST_FAILED = 'skeleton_request_failed'


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


class ExternalRagModelClientRequestFailedError(ExternalRagModelClientError):
    pass


@dataclass(frozen=True)
class ExternalRagModelParsedProviderResponse:
    candidate: RagModelClientResponse | None = None
    error_code: str | None = None


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

    def build_outbound_request(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> dict[str, Any]:
        return _build_outbound_request_contract(
            payload,
            config=config,
            credentials=credentials,
        )

    def build_request_preview(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> dict[str, Any]:
        request_contract = self.build_outbound_request(payload, config=config, credentials=credentials)
        request_body = request_contract.get('body', {}) if isinstance(request_contract, Mapping) else {}
        query = str(payload.get('query') or '') if isinstance(payload, Mapping) else ''
        chunks = payload.get('chunks') if isinstance(payload, Mapping) else []
        citations = payload.get('citations') if isinstance(payload, Mapping) else []
        policy_hints = payload.get('policy_hints') if isinstance(payload, Mapping) else []
        messages = request_body.get('messages', []) if isinstance(request_body, Mapping) else []

        return {
            'transport_kind': request_contract.get('transport_kind'),
            'provider_name': request_contract.get('provider_name'),
            'model_name': request_contract.get('model_name'),
            'base_url': _redact_transport_locator(config.base_url),
            'proxy': request_contract.get('proxy'),
            'timeout_seconds': request_contract.get('timeout_seconds'),
            'max_output_tokens': request_body.get('max_tokens'),
            'credentials': request_contract.get('credentials'),
            'request_shape': {
                'input_mode': 'normalized_rag_prompt',
                'message_count': len(messages) if isinstance(messages, list) else 0,
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


class ExternalRagModelHttpTransport(ExternalRagModelHttpTransportSkeleton):
    def __call__(
        self,
        payload: RagAnswerPromptPayload,
        *,
        config: ExternalRagModelClientConfig,
        credentials: ExternalRagModelClientCredentials,
    ) -> RagModelClientResponse:
        request_contract = self.build_outbound_request(payload, config=config, credentials=credentials)
        endpoint = _effective_endpoint(config=config, credentials=credentials)
        if endpoint is None:
            raise ExternalRagModelClientNotConfiguredError(_warning_for_error_code(_WARNING_CODE_NOT_CONFIGURED))

        request_body = request_contract.get('body', {}) if isinstance(request_contract, Mapping) else {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {credentials.api_key}',
        }

        try:
            with _create_http_transport_client(
                timeout_seconds=float(config.timeout_seconds),
                proxy=_normalize_optional_text(config.proxy),
            ) as client:
                response = client.post(
                    endpoint,
                    json=request_body,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError(_warning_for_error_code(_WARNING_CODE_TIMEOUT)) from exc
        except httpx.HTTPStatusError as exc:
            raise ExternalRagModelClientHttpError(_warning_for_error_code(_WARNING_CODE_HTTP_ERROR)) from exc
        except httpx.RequestError as exc:
            raise ExternalRagModelClientRequestFailedError(
                _warning_for_error_code(_WARNING_CODE_REQUEST_FAILED)
            ) from exc

        raw_provider_payload = _extract_provider_response_payload(response)
        parsed_response = _parse_provider_response_candidate(raw_provider_payload)
        if parsed_response.error_code is not None or parsed_response.candidate is None:
            raise TypeError(_warning_for_error_code(_WARNING_CODE_INVALID_RESPONSE))
        return parsed_response.candidate


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
        self._transport = transport or _wrap_responder_as_transport(responder) or ExternalRagModelHttpTransport()

    def generate_answer(self, payload: RagAnswerPromptPayload) -> RagModelClientResponse:
        if not self.config.enabled:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_DISABLED))
        if not self.config.transport_enabled:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_NOT_CONNECTED))

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
            parsed_response = _parse_provider_response_candidate(raw_response)
            if parsed_response.error_code is not None:
                return _warning_response(_warning_for_error_code(parsed_response.error_code))
            return _normalize_response(parsed_response.candidate, max_output_chars=self.config.max_output_chars)
        except ExternalRagModelClientNotConfiguredError as exc:
            return _warning_response(str(exc))
        except TimeoutError:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_TIMEOUT))
        except ExternalRagModelClientHttpError:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_HTTP_ERROR))
        except ExternalRagModelClientRequestFailedError:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_REQUEST_FAILED))
        except ExternalRagModelTransportSkeletonError:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_SKELETON_REQUEST_FAILED))
        except TypeError:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_INVALID_RESPONSE))
        except Exception:
            return _warning_response(_warning_for_error_code(_WARNING_CODE_REQUEST_FAILED))

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


def _build_outbound_request_contract(
    payload: RagAnswerPromptPayload,
    *,
    config: ExternalRagModelClientConfig,
    credentials: ExternalRagModelClientCredentials,
) -> dict[str, Any]:
    prompt_content = _render_outbound_user_message(payload)
    request_body: dict[str, Any] = {
        'model': _normalize_optional_text(config.model_name),
        'messages': [
            {
                'role': 'user',
                'content': prompt_content,
            }
        ],
    }
    if config.max_output_tokens is not None:
        request_body['max_tokens'] = int(config.max_output_tokens)

    return {
        'transport_kind': 'backend_http',
        'provider_name': _normalize_optional_text(config.provider_name),
        'model_name': _normalize_optional_text(config.model_name),
        'endpoint': _redact_transport_locator(_effective_endpoint(config=config, credentials=credentials)),
        'proxy': _redact_transport_locator(config.proxy),
        'timeout_seconds': float(config.timeout_seconds),
        'credentials': {
            'has_credentials': bool(str(credentials.api_key or '').strip()),
            'has_endpoint': _normalize_optional_text(credentials.endpoint) is not None,
        },
        'body': request_body,
    }


def _render_outbound_user_message(payload: RagAnswerPromptPayload) -> str:
    query = _normalize_optional_text(payload.get('query')) or ''
    release_id = _normalize_optional_text(payload.get('release_id'))
    built_at = _normalize_optional_text(payload.get('built_at'))
    chunks = payload.get('chunks') if isinstance(payload, Mapping) else []
    citations = payload.get('citations') if isinstance(payload, Mapping) else []
    policy_hints = payload.get('policy_hints') if isinstance(payload, Mapping) else []

    lines = [
        'Use only the grounded release context below.',
        'Return a JSON object with keys "answer" and "citation_ids".',
    ]
    if release_id is not None:
        lines.append(f'Release ID: {release_id}')
    if built_at is not None:
        lines.append(f'Built At: {built_at}')
    lines.append(f'User Query: {query}')

    if isinstance(policy_hints, list) and policy_hints:
        lines.append('Policy Hints:')
        lines.extend(
            f'- {hint}'
            for hint in (
                _normalize_optional_text(raw_hint)
                for raw_hint in policy_hints
            )
            if hint is not None
        )

    grounded_citation_ids: list[str] = []
    if isinstance(citations, list):
        for raw_citation in citations:
            if not isinstance(raw_citation, Mapping):
                continue
            citation_id = _normalize_optional_text(raw_citation.get('citation_id'))
            if citation_id is not None and citation_id not in grounded_citation_ids:
                grounded_citation_ids.append(citation_id)

    if grounded_citation_ids:
        lines.append('Allowed Citation IDs:')
        lines.extend(f'- {citation_id}' for citation_id in grounded_citation_ids)

    lines.append('Grounded Chunks:')
    if isinstance(chunks, list) and chunks:
        for index, raw_chunk in enumerate(chunks, start=1):
            if not isinstance(raw_chunk, Mapping):
                continue
            citation_id = _normalize_optional_text(raw_chunk.get('citation_id')) or 'unknown-citation'
            text = _normalize_optional_text(raw_chunk.get('text')) or ''
            lines.append(f'[{index}] citation_id={citation_id} text={text}')
    else:
        lines.append('- none')

    return '\n'.join(lines)


def _parse_provider_response_candidate(raw_response: Any) -> ExternalRagModelParsedProviderResponse:
    response_mapping = _coerce_provider_response_mapping(raw_response)
    if response_mapping is None:
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)
    if 'answer' not in response_mapping:
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)
    if 'citation_ids' not in response_mapping:
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)

    answer = _normalize_optional_text(response_mapping.get('answer'))
    raw_citation_ids = response_mapping.get('citation_ids', [])
    raw_warnings = response_mapping.get('warnings', [])
    if answer is None:
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)
    if not isinstance(raw_citation_ids, list):
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)
    if not isinstance(raw_warnings, list):
        return ExternalRagModelParsedProviderResponse(error_code=_WARNING_CODE_INVALID_RESPONSE)

    candidate: RagModelClientResponse = {
        'answer': answer,
        'citation_ids': [
            str(citation_id).strip()
            for citation_id in raw_citation_ids
            if str(citation_id or '').strip()
        ],
        'warnings': [
            str(warning).strip()
            for warning in raw_warnings
            if str(warning or '').strip()
        ],
    }
    return ExternalRagModelParsedProviderResponse(candidate=candidate)


def _coerce_provider_response_mapping(raw_response: Any) -> Mapping[str, Any] | None:
    if isinstance(raw_response, Mapping):
        return raw_response

    text_payload: str | None = None
    if isinstance(raw_response, (bytes, bytearray)):
        try:
            text_payload = raw_response.decode('utf-8')
        except Exception:
            return None
    elif isinstance(raw_response, str):
        text_payload = raw_response

    if text_payload is None:
        return None

    normalized_payload = text_payload.strip()
    if not normalized_payload:
        return None

    try:
        parsed_payload = json.loads(normalized_payload)
    except Exception:
        return None
    if not isinstance(parsed_payload, Mapping):
        return None
    return parsed_payload


def _extract_provider_response_payload(response: Any) -> Any:
    try:
        response_payload = response.json()
    except Exception:
        try:
            response_payload = response.text
        except Exception:
            return None

    if isinstance(response_payload, Mapping):
        if 'answer' in response_payload or 'citation_ids' in response_payload:
            return response_payload

        choices = response_payload.get('choices')
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, Mapping):
                message = first_choice.get('message')
                if isinstance(message, Mapping):
                    content = message.get('content')
                    if isinstance(content, str):
                        return content
                text = first_choice.get('text')
                if isinstance(text, str):
                    return text

    return response_payload


def _warning_for_error_code(error_code: str) -> str:
    warning_map = {
        _WARNING_CODE_DISABLED: _DISABLED_WARNING,
        _WARNING_CODE_NOT_CONFIGURED: _NOT_CONFIGURED_WARNING,
        _WARNING_CODE_NOT_CONNECTED: _NOT_CONNECTED_WARNING,
        _WARNING_CODE_PROVIDER_NOT_ALLOWED: _PROVIDER_NOT_ALLOWED_WARNING,
        _WARNING_CODE_MODEL_NOT_ALLOWED: _MODEL_NOT_ALLOWED_WARNING,
        _WARNING_CODE_TIMEOUT: _TIMEOUT_WARNING,
        _WARNING_CODE_HTTP_ERROR: _HTTP_ERROR_WARNING,
        _WARNING_CODE_INVALID_RESPONSE: _INVALID_RESPONSE_WARNING,
        _WARNING_CODE_REQUEST_FAILED: _REQUEST_FAILED_WARNING,
        _WARNING_CODE_SKELETON_REQUEST_FAILED: _REQUEST_FAILED_WARNING,
    }
    return warning_map.get(str(error_code or '').strip(), _REQUEST_FAILED_WARNING)


def _effective_endpoint(
    *,
    config: ExternalRagModelClientConfig,
    credentials: ExternalRagModelClientCredentials,
) -> str | None:
    return _normalize_optional_text(credentials.endpoint) or _normalize_optional_text(config.base_url)


def _create_http_transport_client(*, timeout_seconds: float, proxy: str | None) -> httpx.Client:
    client_kwargs: dict[str, Any] = {
        'timeout': timeout_seconds,
        'trust_env': False,
    }
    normalized_proxy = _normalize_optional_text(proxy)
    if normalized_proxy is not None:
        client_kwargs['proxy'] = normalized_proxy
    return httpx.Client(**client_kwargs)


def _redact_url_for_preview(value: Any) -> str | None:
    return _redact_transport_locator(value)


def _redact_transport_locator(value: Any) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None

    split_value = urlsplit(normalized)
    if not split_value.scheme and not split_value.netloc:
        return split_value.path or normalized.split('?', 1)[0]

    hostname = split_value.hostname or ''
    port = split_value.port
    netloc = hostname
    if port is not None:
        netloc = f'{hostname}:{port}'

    return urlunsplit((split_value.scheme, netloc, split_value.path, '', ''))
