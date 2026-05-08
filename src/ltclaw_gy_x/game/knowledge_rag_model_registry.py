from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .knowledge_rag_model_client import (
    DeterministicMockRagModelClient,
    DisabledRagModelClient,
    RagModelClient,
)


RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK = 'deterministic_mock'
RAG_MODEL_PROVIDER_DISABLED = 'disabled'

SUPPORTED_RAG_MODEL_PROVIDERS = (
    RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
    RAG_MODEL_PROVIDER_DISABLED,
)

RagModelClientFactory = Callable[[], RagModelClient]


@dataclass(frozen=True)
class ResolvedRagModelClient:
    provider_name: str
    client: RagModelClient
    warnings: tuple[str, ...] = ()


def get_rag_model_client(
    provider_name: str | None = None,
    *,
    factories: Mapping[str, RagModelClientFactory] | None = None,
) -> ResolvedRagModelClient:
    normalized_provider_name = _normalize_provider_name(provider_name)
    factory_map = dict(factories or _default_factories())

    if normalized_provider_name not in SUPPORTED_RAG_MODEL_PROVIDERS:
        raise ValueError(f'Unsupported RAG model provider: {normalized_provider_name}')
    if normalized_provider_name not in factory_map:
        raise ValueError(f'RAG model provider is not configured: {normalized_provider_name}')

    try:
        client = factory_map[normalized_provider_name]()
    except Exception as exc:
        fallback_client = DisabledRagModelClient()
        return ResolvedRagModelClient(
            provider_name=RAG_MODEL_PROVIDER_DISABLED,
            client=fallback_client,
            warnings=(
                f"Failed to initialize RAG model provider '{normalized_provider_name}': {exc}. "
                'Falling back to disabled provider.',
            ),
        )

    return ResolvedRagModelClient(
        provider_name=normalized_provider_name,
        client=client,
        warnings=(),
    )


def _normalize_provider_name(provider_name: str | None) -> str:
    normalized = str(provider_name or '').strip()
    return normalized or RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK


def _default_factories() -> dict[str, RagModelClientFactory]:
    return {
        RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: DeterministicMockRagModelClient,
        RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
    }
