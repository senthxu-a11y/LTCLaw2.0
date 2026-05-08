from __future__ import annotations

from typing import Any, Mapping


_PROVIDER_FIELD_NAMES = (
    'rag_model_provider',
    'knowledge_rag_model_provider',
)

_NESTED_CONFIG_FIELD_NAMES = (
    'service_config',
    'app_config',
    'config',
)


def resolve_rag_model_provider_name(
    config_or_service: Any = None,
    *,
    provider_name: str | None = None,
) -> str | None:
    explicit_provider_name = _normalize_provider_name(provider_name)
    if explicit_provider_name is not None:
        return explicit_provider_name
    return _resolve_provider_name(config_or_service, seen=set())


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


def _read_field(config_or_service: Any, field_name: str) -> Any:
    if isinstance(config_or_service, Mapping):
        return config_or_service.get(field_name)
    return getattr(config_or_service, field_name, None)


def _normalize_provider_name(value: Any) -> str | None:
    normalized = str(value or '').strip()
    return normalized or None