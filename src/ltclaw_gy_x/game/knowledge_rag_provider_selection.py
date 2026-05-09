from __future__ import annotations

from dataclasses import fields
from typing import Any, Mapping

from .knowledge_rag_external_model_client import ExternalRagModelClientConfig, ExternalRagModelEnvConfig


_PROVIDER_FIELD_NAMES = (
    'rag_model_provider',
    'knowledge_rag_model_provider',
)

_NESTED_CONFIG_FIELD_NAMES = (
    'service_config',
    'app_config',
    'config',
)

_EXTERNAL_PROVIDER_CONFIG_FIELD_NAMES = (
    'external_provider_config',
)

_EXTERNAL_PROVIDER_NAME = 'future_external'


def resolve_rag_model_provider_name(
    config_or_service: Any = None,
    *,
    provider_name: str | None = None,
) -> str | None:
    explicit_provider_name = _normalize_provider_name(provider_name)
    if explicit_provider_name is not None:
        return explicit_provider_name

    resolved_provider_name = _resolve_provider_name(config_or_service, seen=set())
    if resolved_provider_name is not None:
        return resolved_provider_name

    external_config = resolve_external_rag_model_client_config(config_or_service)
    if external_config is None:
        return None

    return _normalize_provider_name(external_config.provider_name) or _EXTERNAL_PROVIDER_NAME


def resolve_external_rag_model_client_config(
    config_or_service: Any = None,
) -> ExternalRagModelClientConfig | None:
    return _resolve_external_rag_model_client_config(config_or_service, seen=set())


def _resolve_provider_name(config_or_service: Any, *, seen: set[int]) -> str | None:
    if config_or_service is None:
        return None

    object_id = id(config_or_service)
    if object_id in seen:
        return None
    seen.add(object_id)

    for field_name in _PROVIDER_FIELD_NAMES:
        provider_name = _normalize_provider_name(_read_field(config_or_service, field_name))
        if provider_name is not None:
            return provider_name

    for field_name in _NESTED_CONFIG_FIELD_NAMES:
        nested_config = _read_field(config_or_service, field_name)
        if nested_config is None:
            continue
        provider_name = _resolve_provider_name(nested_config, seen=seen)
        if provider_name is not None:
            return provider_name

    return None


def _resolve_external_rag_model_client_config(
    config_or_service: Any,
    *,
    seen: set[int],
) -> ExternalRagModelClientConfig | None:
    if config_or_service is None:
        return None

    if isinstance(config_or_service, ExternalRagModelClientConfig):
        return config_or_service

    object_id = id(config_or_service)
    if object_id in seen:
        return None
    seen.add(object_id)

    for field_name in _EXTERNAL_PROVIDER_CONFIG_FIELD_NAMES:
        external_config = _coerce_external_rag_model_client_config(_read_field(config_or_service, field_name))
        if external_config is not None:
            return external_config

    for field_name in _NESTED_CONFIG_FIELD_NAMES:
        nested_config = _read_field(config_or_service, field_name)
        if nested_config is None:
            continue
        external_config = _resolve_external_rag_model_client_config(nested_config, seen=seen)
        if external_config is not None:
            return external_config

    return None


def _read_field(config_or_service: Any, field_name: str) -> Any:
    if isinstance(config_or_service, Mapping):
        return config_or_service.get(field_name)
    return getattr(config_or_service, field_name, None)


def _coerce_external_rag_model_client_config(value: Any) -> ExternalRagModelClientConfig | None:
    if value is None:
        return None
    if isinstance(value, ExternalRagModelClientConfig):
        return value

    external_config_field_names = {field.name for field in fields(ExternalRagModelClientConfig)}
    if not any(_read_field(value, field_name) is not None for field_name in external_config_field_names):
        return None

    kwargs: dict[str, Any] = {}
    for field in fields(ExternalRagModelClientConfig):
        raw_field_value = _read_field(value, field.name)
        if raw_field_value is None:
            continue
        if field.name == 'env':
            coerced_env = _coerce_external_rag_model_env_config(raw_field_value)
            if coerced_env is not None:
                kwargs[field.name] = coerced_env
            continue
        if field.name in {'allowed_providers', 'allowed_models'}:
            kwargs[field.name] = _coerce_string_tuple(raw_field_value)
            continue
        kwargs[field.name] = raw_field_value

    return ExternalRagModelClientConfig(**kwargs)


def _coerce_external_rag_model_env_config(value: Any) -> ExternalRagModelEnvConfig | None:
    if value is None:
        return None
    if isinstance(value, ExternalRagModelEnvConfig):
        return value

    api_key_env_var = _normalize_provider_name(_read_field(value, 'api_key_env_var'))
    if api_key_env_var is None:
        return None
    return ExternalRagModelEnvConfig(api_key_env_var=api_key_env_var)


def _coerce_string_tuple(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = _normalize_provider_name(value)
        return (normalized,) if normalized is not None else None

    normalized_values = tuple(
        normalized
        for normalized in (_normalize_provider_name(item) for item in value)
        if normalized is not None
    )
    return normalized_values or None


def _normalize_provider_name(value: Any) -> str | None:
    normalized = str(value or '').strip()
    return normalized or None
