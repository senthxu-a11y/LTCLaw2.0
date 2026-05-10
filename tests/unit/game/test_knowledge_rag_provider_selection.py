from __future__ import annotations

from types import SimpleNamespace

from ltclaw_gy_x.game.config import FilterConfig, ProjectConfig, ProjectMeta, SvnConfig, TableConvention
from ltclaw_gy_x.game.knowledge_rag_external_model_client import ExternalRagModelClientConfig, ExternalRagModelEnvConfig
from ltclaw_gy_x.game.service import GameService
from ltclaw_gy_x.game.knowledge_rag_provider_selection import (
    resolve_external_rag_model_client_config,
    resolve_rag_model_provider_name,
)


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


def test_resolve_rag_model_provider_name_reads_external_provider_config_when_backend_owned():
    provider_name = resolve_rag_model_provider_name(
        {
            'external_provider_config': {
                'enabled': False,
                'provider_name': 'future_external',
            }
        }
    )

    assert provider_name == 'future_external'


def test_resolve_external_rag_model_client_config_reads_nested_backend_owned_config():
    external_config = resolve_external_rag_model_client_config(
        SimpleNamespace(
            service_config=SimpleNamespace(
                external_provider_config={
                    'enabled': True,
                    'transport_enabled': True,
                    'provider_name': 'future_external',
                    'model_name': 'stub-model',
                    'allowed_providers': ['future_external'],
                    'allowed_models': ('stub-model',),
                    'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                }
            )
        )
    )

    assert external_config == ExternalRagModelClientConfig(
        enabled=True,
        transport_enabled=True,
        provider_name='future_external',
        model_name='stub-model',
        allowed_providers=('future_external',),
        allowed_models=('stub-model',),
        env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
    )


def test_resolve_external_rag_model_client_config_ignores_request_like_shape_without_backend_field():
    external_config = resolve_external_rag_model_client_config(
        {
            'enabled': True,
            'provider_name': 'future_external',
            'model_name': 'stub-model',
        }
    )

    assert external_config is None


def test_resolve_rag_model_provider_name_ignores_request_like_provider_field():
    provider_name = resolve_rag_model_provider_name({'provider_name': 'disabled'})

    assert provider_name is None


def test_resolve_rag_model_provider_name_ignores_blank_values():
    provider_name = resolve_rag_model_provider_name({'rag_model_provider': '   '})

    assert provider_name is None


def test_resolve_external_rag_model_client_config_reads_game_service_config_bridge(tmp_path):
    service = GameService(tmp_path / 'workspace')
    service._project_config = ProjectConfig(
        project=ProjectMeta(name='Test Game', engine='Unity', language='zh-CN'),
        svn=SvnConfig(root=str(tmp_path / 'svn'), poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=['.xlsx'], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
        external_provider_config={
            'enabled': False,
            'transport_enabled': False,
            'provider_name': 'future_external',
            'allowed_providers': ['future_external'],
            'allowed_models': [],
            'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
        },
    )

    external_config = resolve_external_rag_model_client_config(service)

    assert external_config == ExternalRagModelClientConfig(
        enabled=False,
        transport_enabled=False,
        provider_name='future_external',
        allowed_providers=('future_external',),
        allowed_models=None,
        env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
    )
