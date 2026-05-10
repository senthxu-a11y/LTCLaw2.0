from __future__ import annotations

import builtins
import os
import socket
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_rag_external_model_client import (
    ExternalRagModelClient,
    ExternalRagModelClientConfig,
    ExternalRagModelCredentialRequest,
    ExternalRagModelEnvCredentialResolver,
    ExternalRagModelCredentialResolverSkeleton,
    ExternalRagModelClientCredentials,
    ExternalRagModelEnvConfig,
    ExternalRagModelClientHttpError,
    ExternalRagModelHttpTransportSkeleton,
)
from ltclaw_gy_x.game.knowledge_rag_model_client import (
    RagModelClient,
    build_rag_model_prompt_payload,
)


def _payload(text: str = 'Combat damage uses the current release formula.'):
    return build_rag_model_prompt_payload(
        query='How does combat damage work?',
        release_id='release-001',
        built_at='2026-01-01T00:00:00Z',
        chunks=[
            {
                'chunk_id': 'chunk-001',
                'citation_id': 'citation-001',
                'rank': 1,
                'score': 4.0,
                'text': text,
            }
        ],
        citations=[
            {
                'citation_id': 'citation-001',
                'release_id': 'release-001',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
            }
        ],
        policy_hints=['Use only grounded citations.'],
    )


def test_external_rag_model_client_skeleton_implements_rag_model_client_shape():
    client = ExternalRagModelClient()

    assert isinstance(client, RagModelClient)


def test_external_rag_model_client_disabled_by_default_returns_empty_answer_and_warning():
    client = ExternalRagModelClient()

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is disabled.'],
    }


def test_external_rag_model_client_disabled_gate_returns_warning_for_non_mapping_payload_without_exception():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=False),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(object())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is disabled.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_disabled_gate_returns_warning_for_malformed_mapping_payload_without_exception():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=False),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(
        {
            'query': 'damage',
            'release_id': 'release-001',
            'built_at': '2026-01-01T00:00:00Z',
            'chunks': 'not-a-list',
            'citations': 'not-a-list',
            'policy_hints': 'not-a-list',
        }
    )

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is disabled.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_path_rejects_oversize_prompt_payload():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            max_prompt_chars=10,
        )
    )

    with pytest.raises(ValueError, match='RAG prompt payload exceeds configured max_prompt_chars'):
        client.generate_answer(_payload())


def test_external_rag_model_client_transport_enabled_path_rejects_non_mapping_payload():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        )
    )

    with pytest.raises(TypeError, match='RAG prompt payload must be a mapping.'):
        client.generate_answer(object())


def test_external_rag_model_client_transport_enabled_path_rejects_malformed_chunks_payload():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        )
    )

    with pytest.raises(TypeError, match='RAG prompt payload chunks must be a list.'):
        client.generate_answer(
            {
                'query': 'damage',
                'release_id': 'release-001',
                'built_at': '2026-01-01T00:00:00Z',
                'chunks': 'not-a-list',
                'citations': [],
                'policy_hints': [],
            }
        )


def test_external_rag_model_client_skeleton_default_implementation_performs_no_network_or_file_or_env_io(monkeypatch):
    resolver_called = False
    transport_called = False

    def _forbid_open(*args, **kwargs):
        raise AssertionError('external adapter skeleton must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('external adapter skeleton must not touch Path I/O')

    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('external adapter skeleton must not read environment variables')

    def _forbid_socket(*args, **kwargs):
        raise AssertionError('external adapter skeleton must not open sockets')

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)
    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    monkeypatch.setattr(socket, 'socket', _forbid_socket)

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        credential_resolver=_resolver,
        transport=_transport,
    )
    response = client.generate_answer(_payload())

    assert response['citation_ids'] == []
    assert response['warnings'] == ['External provider adapter skeleton is disabled.']
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_returns_not_configured_warning_without_credential_resolver():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_configured_warning_for_blank_env_var_name():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='   '),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_configured_warning_for_missing_env_value(monkeypatch):
    monkeypatch.delenv('QWENPAW_RAG_API_KEY', raising=False)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_configured_warning_for_blank_env_value(monkeypatch):
    monkeypatch.setenv('QWENPAW_RAG_API_KEY', '   ')
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_configured_warning_for_missing_credential():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=lambda request: None,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_credential_resolver_skeleton_returns_none_without_io_or_secret_imports(monkeypatch):
    resolver = ExternalRagModelCredentialResolverSkeleton()

    def _forbid_open(*args, **kwargs):
        raise AssertionError('credential resolver skeleton must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('credential resolver skeleton must not touch Path I/O')

    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('credential resolver skeleton must not read environment variables')

    def _forbid_socket(*args, **kwargs):
        raise AssertionError('credential resolver skeleton must not open sockets')

    original_import = builtins.__import__

    def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {
            'ltclaw_gy_x.security.secret_store',
            'ltclaw_gy_x.providers.provider_manager',
        }:
            raise AssertionError(f'credential resolver skeleton must not import {name}')
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(builtins, '__import__', _guarded_import)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)
    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    monkeypatch.setattr(socket, 'socket', _forbid_socket)

    credentials = resolver(
        ExternalRagModelCredentialRequest(
            provider_name='future_external',
            model_name='stub-model',
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    assert credentials is None


def test_external_rag_model_env_credential_resolver_returns_api_key_from_configured_env_var(monkeypatch):
    resolver = ExternalRagModelEnvCredentialResolver()
    monkeypatch.setenv('QWENPAW_RAG_API_KEY', ' env-secret ')

    credentials = resolver(
        ExternalRagModelCredentialRequest(
            provider_name='future_external',
            model_name='stub-model',
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    assert credentials == ExternalRagModelClientCredentials(api_key='env-secret')


def test_external_rag_model_env_credential_resolver_does_not_import_secret_store_or_provider_manager(monkeypatch):
    resolver = ExternalRagModelEnvCredentialResolver()
    original_import = builtins.__import__

    def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {
            'ltclaw_gy_x.security.secret_store',
            'ltclaw_gy_x.providers.provider_manager',
        }:
            raise AssertionError(f'env credential resolver must not import {name}')
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', _guarded_import)
    monkeypatch.setenv('QWENPAW_RAG_API_KEY', 'env-secret')

    credentials = resolver(
        ExternalRagModelCredentialRequest(
            provider_name='future_external',
            model_name='stub-model',
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    assert credentials == ExternalRagModelClientCredentials(api_key='env-secret')


def test_external_rag_model_http_transport_skeleton_builds_redacted_request_preview():
    transport = ExternalRagModelHttpTransportSkeleton()
    payload = dict(_payload())
    payload['provider_name'] = 'request-provider'
    payload['model_name'] = 'request-model'
    payload['api_key'] = 'request-secret'

    preview = transport.build_request_preview(
        payload,
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            base_url='https://provider.example/v1/chat/completions?api_key=secret',
            proxy='https://proxy.example/forward?token=secret',
            max_output_tokens=256,
        ),
        credentials=ExternalRagModelClientCredentials(
            api_key='placeholder-secret',
            endpoint='https://provider.example/runtime?sig=secret',
        ),
    )

    assert preview == {
        'transport_kind': 'http_skeleton',
        'provider_name': 'future_external',
        'model_name': 'backend-model',
        'base_url': 'https://provider.example/v1/chat/completions',
        'proxy': 'https://proxy.example/forward',
        'timeout_seconds': 15.0,
        'max_output_tokens': 256,
        'credentials': {
            'has_credentials': True,
            'has_endpoint': True,
        },
        'request_shape': {
            'input_mode': 'normalized_rag_prompt',
            'message_count': 1,
            'includes_authorization_header': False,
        },
        'payload': {
            'query_chars': len('How does combat damage work?'),
            'chunk_count': 1,
            'citation_count': 1,
            'policy_hint_count': 1,
            'release_id_present': True,
            'built_at_present': True,
        },
    }
    assert 'request-provider' not in str(preview)
    assert 'request-model' not in str(preview)
    assert 'request-secret' not in str(preview)
    assert 'placeholder-secret' not in str(preview)
    assert 'Authorization' not in str(preview)
    assert 'api_key' not in str(preview)
    assert 'sig=secret' not in str(preview)


def test_external_rag_model_http_transport_skeleton_performs_no_network_or_file_or_env_io(monkeypatch):
    transport = ExternalRagModelHttpTransportSkeleton()

    def _forbid_open(*args, **kwargs):
        raise AssertionError('transport skeleton must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('transport skeleton must not touch Path I/O')

    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('transport skeleton must not read environment variables')

    def _forbid_socket(*args, **kwargs):
        raise AssertionError('transport skeleton must not open sockets')

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)
    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    monkeypatch.setattr(socket, 'socket', _forbid_socket)

    preview = transport.build_request_preview(
        _payload(),
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
        ),
        credentials=ExternalRagModelClientCredentials(api_key='placeholder-secret'),
    )

    assert preview['transport_kind'] == 'http_skeleton'


def test_external_rag_model_client_default_transport_skeleton_returns_safe_warning_without_secret_leak(monkeypatch):
    monkeypatch.setenv('QWENPAW_RAG_API_KEY', 'placeholder-secret')
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
            base_url='https://provider.example/v1/chat/completions?api_key=secret',
        ),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton request failed.'],
    }
    assert 'secret' not in str(response).lower()
    assert 'api_key' not in str(response)


def test_external_rag_model_client_env_credential_success_uses_default_resolver_after_allowlist(monkeypatch):
    events = []

    def _env_get(name, default=None):
        events.append(('env', name))
        return 'env-secret'

    def _transport(payload, *, config, credentials):
        events.append(('transport', credentials.api_key))
        return {'answer': 'Grounded answer', 'citation_ids': ['citation-001'], 'warnings': []}

    monkeypatch.setattr(os.environ, 'get', _env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        ),
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': 'Grounded answer',
        'citation_ids': ['citation-001'],
        'warnings': [],
    }
    assert events == [('env', 'QWENPAW_RAG_API_KEY'), ('transport', 'env-secret')]


def test_external_rag_model_client_disabled_gate_does_not_read_env(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('disabled gate must not read environment variables')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=False,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is disabled.'],
    }


def test_external_rag_model_client_not_connected_gate_does_not_read_env(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('not connected gate must not read environment variables')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=False,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }


def test_external_rag_model_client_allowlist_failure_does_not_read_env(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('allowlist failure must not read environment variables')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='blocked-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton model is not allowed.'],
    }


def test_external_rag_model_client_payload_normalization_failure_does_not_read_env(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('payload normalization failure must not read environment variables')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    with pytest.raises(TypeError, match='RAG prompt payload must be a mapping.'):
        client.generate_answer(object())


def test_external_rag_model_client_env_read_exception_returns_not_configured_warning(monkeypatch):
    def _fail_env_get(*args, **kwargs):
        raise RuntimeError('raw env failure with test-api-key-placeholder')

    monkeypatch.setattr(os.environ, 'get', _fail_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        )
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert 'test-api-key-placeholder' not in str(response)


def test_external_rag_model_client_returns_not_connected_warning_without_transport():
    resolver_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder')

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=True),
        credential_resolver=_resolver,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }
    assert resolver_called is False


def test_external_rag_model_client_not_connected_gate_returns_warning_for_non_mapping_payload_without_exception():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=True, transport_enabled=False),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(object())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_not_connected_gate_returns_warning_for_malformed_mapping_payload_without_exception():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=True, transport_enabled=False),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(
        {
            'query': 'damage',
            'release_id': 'release-001',
            'built_at': '2026-01-01T00:00:00Z',
            'chunks': 'not-a-list',
            'citations': 'not-a-list',
            'policy_hints': 'not-a-list',
        }
    )

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_uses_fake_transport_seam_and_normalizes_response():
    captured = {}

    def _transport(payload, *, config, credentials):
        captured['payload'] = payload
        captured['model_name'] = config.model_name
        captured['api_key'] = credentials.api_key
        return {
            'answer': 'Grounded adapter answer that is intentionally longer than the configured output budget.',
            'citation_ids': ['citation-001', ' ', 'citation-002'],
            'warnings': ['Adapter warning', ' '],
        }

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
            max_output_chars=20,
        ),
        credential_resolver=lambda request: _capture_request(request, captured),
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert captured['payload']['query'] == 'How does combat damage work?'
    assert captured['credential_request'] == ExternalRagModelCredentialRequest(
        provider_name='future_external',
        model_name='stub-model',
        env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
    )
    assert captured['model_name'] == 'stub-model'
    assert captured['api_key'] == 'placeholder'
    assert response['answer'] == 'Grounded adapter ans'
    assert response['citation_ids'] == ['citation-001', 'citation-002']
    assert response['warnings'] == ['Adapter warning']


@pytest.mark.parametrize(
    ('transport_exc', 'expected_warning'),
    [
        (TimeoutError('timeout'), 'External provider adapter skeleton timed out.'),
        (ExternalRagModelClientHttpError('503'), 'External provider adapter skeleton HTTP error.'),
    ],
)
def test_external_rag_model_client_converts_transport_failures_to_empty_answer(transport_exc, expected_warning):
    def _transport(payload, *, config, credentials):
        raise transport_exc

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='placeholder'),
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': [expected_warning],
    }


def test_external_rag_model_client_returns_invalid_response_warning_for_bad_transport_payload():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='placeholder'),
        transport=lambda payload, *, config, credentials: {'answer': 'x', 'citation_ids': 'bad', 'warnings': []},
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton returned an invalid response.'],
    }


def test_external_rag_model_client_disabled_even_with_fake_credential_does_not_call_transport():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=False),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is disabled.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_provider_not_in_allowlist_does_not_call_external_path():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            allowed_providers=('approved-provider',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton provider is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_allowed_providers_when_missing():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=None,
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton provider is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_allowed_providers_when_empty():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=(),
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton provider is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_model_not_in_allowlist_does_not_call_external_path():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='blocked-model',
            allowed_providers=('future_external',),
            allowed_models=('approved-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton model is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_allowed_models_when_missing():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=None,
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton model is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_allowed_models_when_empty():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=(),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton model is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_non_blank_provider_name():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='   ',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton provider is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_transport_enabled_requires_non_blank_model_name():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='   ',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton model is not allowed.'],
    }
    assert resolver_called is False
    assert transport_called is False


def test_external_rag_model_client_request_like_provider_fields_do_not_participate_in_selection():
    captured = {}
    payload = dict(_payload())
    payload['provider_name'] = 'request-provider'
    payload['model_name'] = 'request-model'
    payload['api_key'] = 'request-secret'

    def _transport(raw_payload, *, config, credentials):
        captured['payload'] = raw_payload
        captured['provider_name'] = config.provider_name
        captured['model_name'] = config.model_name
        return {'answer': 'Grounded answer', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='placeholder-secret'),
        transport=_transport,
    )

    response = client.generate_answer(payload)

    assert captured['provider_name'] == 'future_external'
    assert captured['model_name'] == 'backend-model'
    assert 'provider_name' not in captured['payload']
    assert 'model_name' not in captured['payload']
    assert 'api_key' not in captured['payload']
    assert response['answer'] == 'Grounded answer'


def test_external_rag_model_client_missing_credential_warning_does_not_leak_secret_like_value():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='   '),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert 'secret' not in str(response).lower()
    assert 'api_key' not in str(response)


def test_external_rag_model_client_resolver_exception_returns_not_configured_warning_without_secret_leak():
    def _resolver(request):
        raise RuntimeError('raw secret value: test-api-key-placeholder')

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert 'test-api-key-placeholder' not in str(response)
    assert 'raw secret value' not in str(response)


def test_external_rag_model_client_injected_resolver_overrides_default_env_source(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('injected resolver must override default env source')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='override-secret'),
        transport=lambda payload, *, config, credentials: {
            'answer': credentials.api_key,
            'citation_ids': ['citation-001'],
            'warnings': [],
        },
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': 'override-secret',
        'citation_ids': ['citation-001'],
        'warnings': [],
    }


def test_external_rag_model_client_responder_seam_overrides_default_env_source(monkeypatch):
    def _forbid_env_get(*args, **kwargs):
        raise AssertionError('responder seam must override default env source')

    monkeypatch.setattr(os.environ, 'get', _forbid_env_get)
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        ),
        responder=lambda payload: {'answer': 'Responder answer', 'citation_ids': ['citation-001'], 'warnings': []},
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': 'Responder answer',
        'citation_ids': ['citation-001'],
        'warnings': [],
    }


def _capture_request(request, captured):
    captured['credential_request'] = request
    return ExternalRagModelClientCredentials(api_key='placeholder')


def test_external_rag_model_client_requires_explicit_transport_enable_before_resolver_or_transport_runs():
    resolver_called = False
    transport_called = False

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='placeholder-secret')

    def _transport(payload, *, config, credentials):
        nonlocal transport_called
        transport_called = True
        return {'answer': 'unexpected', 'citation_ids': ['citation-001'], 'warnings': []}

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=False,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=_resolver,
        transport=_transport,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }
    assert resolver_called is False
    assert transport_called is False
