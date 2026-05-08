from __future__ import annotations

from types import SimpleNamespace

from ltclaw_gy_x.game.knowledge_rag_provider_selection import resolve_rag_model_provider_name


def test_resolve_rag_model_provider_name_returns_none_without_config():
    assert resolve_rag_model_provider_name() is None


def test_resolve_rag_model_provider_name_uses_explicit_provider_name_first():
    provider_name = resolve_rag_model_provider_name(
        {'rag_model_provider': 'disabled'},
        provider_name='deterministic_mock',
    )

    assert provider_name == 'deterministic_mock'


def test_resolve_rag_model_provider_name_reads_direct_mapping_field():
    provider_name = resolve_rag_model_provider_name({'rag_model_provider': 'disabled'})

    assert provider_name == 'disabled'


def test_resolve_rag_model_provider_name_reads_nested_service_config_field():
    provider_name = resolve_rag_model_provider_name(
        SimpleNamespace(service_config=SimpleNamespace(rag_model_provider='deterministic_mock'))
    )

    assert provider_name == 'deterministic_mock'


def test_resolve_rag_model_provider_name_ignores_request_like_provider_field():
    provider_name = resolve_rag_model_provider_name({'provider_name': 'disabled'})

    assert provider_name is None


def test_resolve_rag_model_provider_name_ignores_blank_values():
    provider_name = resolve_rag_model_provider_name({'rag_model_provider': '   '})

    assert provider_name is None