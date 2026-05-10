from __future__ import annotations

import builtins
import os
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer
from ltclaw_gy_x.game.knowledge_rag_external_model_client import ExternalRagModelClient, ExternalRagModelClientConfig
from ltclaw_gy_x.game.knowledge_rag_model_client import (
    DeterministicMockRagModelClient,
    DisabledRagModelClient,
)
from ltclaw_gy_x.game.knowledge_rag_model_registry import (
    RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
    RAG_MODEL_PROVIDER_DISABLED,
    RAG_MODEL_PROVIDER_FUTURE_EXTERNAL,
    SUPPORTED_RAG_MODEL_PROVIDERS,
    get_rag_model_client,
)


def _context():
    return {
        'mode': 'context',
        'release_id': 'release-001',
        'built_at': '2026-01-01T00:00:00Z',
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'citation_id': 'citation-001',
                'rank': 1,
                'score': 4.0,
                'text': 'Combat damage uses the current release formula.',
            }
        ],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-001',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
            }
        ],
    }


def test_get_rag_model_client_defaults_to_deterministic_mock_for_none():
    resolved = get_rag_model_client(None)

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK
    assert isinstance(resolved.client, DeterministicMockRagModelClient)
    assert resolved.warnings == ()


def test_get_rag_model_client_defaults_to_deterministic_mock_for_empty_string():
    resolved = get_rag_model_client('   ')

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK
    assert isinstance(resolved.client, DeterministicMockRagModelClient)


def test_get_rag_model_client_returns_deterministic_mock_provider():
    resolved = get_rag_model_client(RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK)

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK
    assert isinstance(resolved.client, DeterministicMockRagModelClient)


def test_get_rag_model_client_returns_disabled_provider():
    resolved = get_rag_model_client(RAG_MODEL_PROVIDER_DISABLED)

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DISABLED
    assert isinstance(resolved.client, DisabledRagModelClient)


def test_disabled_provider_returns_empty_answer_and_warning():
    response = get_rag_model_client(RAG_MODEL_PROVIDER_DISABLED).client.generate_answer(
        {
            'query': 'combat',
            'release_id': 'release-001',
            'built_at': '2026-01-01T00:00:00Z',
            'chunks': [],
            'citations': [],
            'policy_hints': [],
        }
    )

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['Model provider is disabled.'],
    }


def test_get_rag_model_client_raises_for_unknown_provider():
    with pytest.raises(ValueError, match='Unsupported RAG model provider: unsupported_provider'):
        get_rag_model_client('unsupported_provider')


def test_get_rag_model_client_returns_future_external_provider_when_backend_owned_config_is_present():
    resolved = get_rag_model_client(
        RAG_MODEL_PROVIDER_FUTURE_EXTERNAL,
        external_config=ExternalRagModelClientConfig(
            enabled=False,
            provider_name=RAG_MODEL_PROVIDER_FUTURE_EXTERNAL,
        ),
    )

    assert resolved.provider_name == RAG_MODEL_PROVIDER_FUTURE_EXTERNAL
    assert isinstance(resolved.client, ExternalRagModelClient)
    assert resolved.warnings == ()


def test_get_rag_model_client_raises_for_future_external_without_backend_owned_config():
    with pytest.raises(ValueError, match='RAG model provider is not configured: future_external'):
        get_rag_model_client(RAG_MODEL_PROVIDER_FUTURE_EXTERNAL)


def test_get_rag_model_client_falls_back_to_disabled_on_factory_failure():
    def _fail_factory():
        raise RuntimeError('boom')

    resolved = get_rag_model_client(
        RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
        factories={
            RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: _fail_factory,
            RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
        },
    )

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DISABLED
    assert isinstance(resolved.client, DisabledRagModelClient)
    assert resolved.warnings == (
        "Failed to initialize RAG model provider 'deterministic_mock': boom. Falling back to disabled provider.",
    )


def test_get_rag_model_client_does_not_read_files_or_env(monkeypatch):
    def _forbid_open(*args, **kwargs):
        raise AssertionError('registry must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('registry must not touch Path I/O')

    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('registry must not read environment variables')

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)
    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)

    resolved = get_rag_model_client(None)

    assert resolved.provider_name == RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK
    assert isinstance(resolved.client, DeterministicMockRagModelClient)


def test_supported_providers_include_future_external_runtime_provider():
    assert SUPPORTED_RAG_MODEL_PROVIDERS == (
        RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
        RAG_MODEL_PROVIDER_DISABLED,
        RAG_MODEL_PROVIDER_FUTURE_EXTERNAL,
    )
    assert len(SUPPORTED_RAG_MODEL_PROVIDERS) == 3


def test_returned_provider_can_be_used_by_build_rag_answer():
    resolved = get_rag_model_client(RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK)

    payload = build_rag_answer(
        'How does combat damage work?',
        _context(),
        model_client=resolved.client,
    )

    assert payload['mode'] == 'answer'
    assert [citation['citation_id'] for citation in payload['citations']] == ['citation-001']
    assert 'Grounded answer from the provided current-release context' in payload['answer']
