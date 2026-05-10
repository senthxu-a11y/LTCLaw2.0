from __future__ import annotations

import builtins
import os
import socket
from pathlib import Path

import httpx
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
    ExternalRagModelHttpTransport,
    ExternalRagModelHttpTransportSkeleton,
    _create_http_transport_client,
    _extract_provider_response_payload,
    _parse_provider_response_candidate,
    _redact_transport_locator,
    _warning_for_error_code,
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
        'transport_kind': 'backend_http',
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


def test_external_rag_model_http_transport_skeleton_builds_outbound_request_without_api_key_or_authorization():
    transport = ExternalRagModelHttpTransportSkeleton()
    payload = dict(_payload())
    payload['provider_name'] = 'request-provider'
    payload['model_name'] = 'request-model'
    payload['api_key'] = 'request-secret'
    payload['candidate_evidence'] = [{'ignored': True}]

    request_contract = transport.build_outbound_request(
        payload,
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            base_url='https://provider.example/v1/chat/completions?api_key=secret',
            proxy='https://user:pass@proxy.example/forward?token=secret',
            max_output_tokens=256,
        ),
        credentials=ExternalRagModelClientCredentials(
            api_key='placeholder-secret',
            endpoint='https://provider.example/runtime?sig=secret',
        ),
    )

    assert request_contract['transport_kind'] == 'backend_http'
    assert request_contract['provider_name'] == 'future_external'
    assert request_contract['model_name'] == 'backend-model'
    assert request_contract['endpoint'] == 'https://provider.example/runtime'
    assert request_contract['proxy'] == 'https://proxy.example/forward'
    assert request_contract['body']['model'] == 'backend-model'
    assert request_contract['body']['messages'][0]['role'] == 'user'
    assert request_contract['body']['max_tokens'] == 256
    assert 'request-provider' not in str(request_contract)
    assert 'request-model' not in str(request_contract)
    assert 'request-secret' not in str(request_contract)
    assert 'placeholder-secret' not in str(request_contract)
    assert 'Authorization' not in str(request_contract)
    assert 'candidate_evidence' not in str(request_contract)


def test_redact_transport_locator_removes_query_string_and_userinfo():
    assert _redact_transport_locator('https://provider.example/v1/chat/completions?api_key=secret') == (
        'https://provider.example/v1/chat/completions'
    )
    assert _redact_transport_locator('https://user:pass@proxy.example:8443/forward?token=secret') == (
        'https://proxy.example:8443/forward'
    )


@pytest.mark.parametrize(
    ('raw_response', 'expected_answer', 'expected_citation_ids'),
    [
        (
            {'answer': 'Grounded answer', 'citation_ids': ['citation-001'], 'warnings': []},
            'Grounded answer',
            ['citation-001'],
        ),
        (
            '{"answer": "Grounded answer", "citation_ids": ["citation-001"], "warnings": []}',
            'Grounded answer',
            ['citation-001'],
        ),
        (
            b'{"answer": "Grounded answer", "citation_ids": ["citation-001"], "warnings": []}',
            'Grounded answer',
            ['citation-001'],
        ),
    ],
)
def test_parse_provider_response_candidate_accepts_minimal_valid_shapes(
    raw_response,
    expected_answer,
    expected_citation_ids,
):
    parsed = _parse_provider_response_candidate(raw_response)

    assert parsed.error_code is None
    assert parsed.candidate == {
        'answer': expected_answer,
        'citation_ids': expected_citation_ids,
        'warnings': [],
    }


@pytest.mark.parametrize(
    'raw_response',
    [
        'not-json',
        '{"answer": "Grounded answer"}',
        '{"answer": "Grounded answer", "citation_ids": "bad", "warnings": []}',
        '{"answer": "   ", "citation_ids": ["citation-001"], "warnings": []}',
    ],
)
def test_parse_provider_response_candidate_rejects_invalid_provider_payloads(raw_response):
    parsed = _parse_provider_response_candidate(raw_response)

    assert parsed.candidate is None
    assert parsed.error_code == 'invalid_response'


@pytest.mark.parametrize(
    ('error_code', 'expected_warning'),
    [
        ('timeout', 'External provider adapter skeleton timed out.'),
        ('http_error', 'External provider adapter skeleton HTTP error.'),
        ('request_failed', 'External provider adapter skeleton request failed.'),
        ('skeleton_request_failed', 'External provider adapter skeleton request failed.'),
        ('not_configured', 'External provider adapter skeleton is not configured.'),
    ],
)
def test_warning_for_error_code_returns_fixed_safe_warnings(error_code, expected_warning):
    warning = _warning_for_error_code(error_code)

    assert warning == expected_warning
    assert 'secret' not in warning.lower()
    assert 'Authorization' not in warning
    assert 'api_key' not in warning


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

    assert preview['transport_kind'] == 'backend_http'


def test_external_rag_model_client_default_transport_returns_safe_warning_without_secret_leak(monkeypatch):
    monkeypatch.setenv('QWENPAW_RAG_API_KEY', 'placeholder-secret')

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            request = httpx.Request('POST', url)
            raise httpx.RequestError('network failed', request=request)

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
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


def test_default_config_does_not_call_httpx(monkeypatch):
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    response = ExternalRagModelClient().generate_answer(_payload())

    assert response['warnings'] == ['External provider adapter skeleton is disabled.']
    assert http_called is False


@pytest.mark.parametrize(
    ('config', 'payload', 'expected_warning'),
    [
        (
            ExternalRagModelClientConfig(enabled=False),
            object(),
            'External provider adapter skeleton is disabled.',
        ),
        (
            ExternalRagModelClientConfig(enabled=True, transport_enabled=False),
            object(),
            'External provider adapter skeleton transport is not connected.',
        ),
    ],
)
def test_kill_switch_gates_do_not_call_resolver_or_httpx_for_malformed_payload(
    monkeypatch,
    config,
    payload,
    expected_warning,
):
    resolver_called = False
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK')

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    client = ExternalRagModelClient(config=config, credential_resolver=_resolver)

    response = client.generate_answer(payload)

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': [expected_warning],
    }
    assert resolver_called is False
    assert http_called is False


def test_missing_endpoint_or_base_url_does_not_call_httpx(monkeypatch):
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert http_called is False


def test_blank_endpoint_or_base_url_does_not_call_httpx(monkeypatch):
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            base_url='   ',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert http_called is False


@pytest.mark.parametrize(
    ('allowed_providers', 'allowed_models', 'expected_warning'),
    [
        (None, ('stub-model',), 'External provider adapter skeleton provider is not allowed.'),
        ((), ('stub-model',), 'External provider adapter skeleton provider is not allowed.'),
        (('future_external',), None, 'External provider adapter skeleton model is not allowed.'),
        (('future_external',), (), 'External provider adapter skeleton model is not allowed.'),
    ],
)
def test_missing_or_empty_allowlists_do_not_call_resolver_or_httpx(
    monkeypatch,
    allowed_providers,
    allowed_models,
    expected_warning,
):
    resolver_called = False
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    def _resolver(request):
        nonlocal resolver_called
        resolver_called = True
        return ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK')

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=allowed_providers,
            allowed_models=allowed_models,
            base_url='https://provider.example/v1/chat/completions',
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
        ),
        credential_resolver=_resolver,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': [expected_warning],
    }
    assert resolver_called is False
    assert http_called is False


@pytest.mark.parametrize(
    ('env_config', 'env_value'),
    [
        (None, 'TEST_API_KEY_SHOULD_NOT_LEAK'),
        (ExternalRagModelEnvConfig(api_key_env_var=None), 'TEST_API_KEY_SHOULD_NOT_LEAK'),
        (ExternalRagModelEnvConfig(api_key_env_var='   '), 'TEST_API_KEY_SHOULD_NOT_LEAK'),
        (ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'), None),
        (ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'), '   '),
    ],
)
def test_default_env_credential_gate_blocks_httpx_for_missing_or_blank_metadata_or_value(
    monkeypatch,
    env_config,
    env_value,
):
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
    monkeypatch.setattr(os.environ, 'get', lambda name, default=None: env_value)

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            env=env_config,
            base_url='https://provider.example/v1/chat/completions',
        ),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert http_called is False
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)


def test_resolver_exception_does_not_call_httpx_and_does_not_leak_raw_text(monkeypatch):
    http_called = False

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            nonlocal http_called
            http_called = True
            return None

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    def _resolver(request):
        raise RuntimeError('raw secret value TEST_API_KEY_SHOULD_NOT_LEAK')

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            base_url='https://provider.example/v1/chat/completions',
        ),
        credential_resolver=_resolver,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }
    assert http_called is False
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)
    assert 'raw secret value' not in str(response)


def test_extract_provider_response_payload_accepts_openai_like_shape():
    class _FakeResponse:
        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"answer": "Grounded answer", "citation_ids": ["citation-001"], "warnings": []}'
                        }
                    }
                ],
                'usage': {'total_tokens': 10},
            }

    extracted = _extract_provider_response_payload(_FakeResponse())

    assert extracted == '{"answer": "Grounded answer", "citation_ids": ["citation-001"], "warnings": []}'


def test_real_http_transport_success_returns_normalized_response(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"answer": "Grounded answer from provider", "citation_ids": ["citation-001"], "warnings": []}'
                        }
                    }
                ]
            }

    class _FakeClient:
        def __init__(self, **kwargs):
            captured['client_kwargs'] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            captured['url'] = url
            captured['json'] = json
            captured['headers'] = headers
            return _FakeResponse()

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(**kwargs),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions?token=secret',
            timeout_seconds=7.5,
            max_output_tokens=256,
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': 'Grounded answer from provider',
        'citation_ids': ['citation-001'],
        'warnings': [],
    }
    assert captured['url'] == 'https://provider.example/v1/chat/completions?token=secret'
    assert captured['json']['model'] == 'backend-model'
    assert captured['json']['messages'][0]['role'] == 'user'
    assert captured['headers'] == {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer TEST_API_KEY_SHOULD_NOT_LEAK',
    }
    assert captured['client_kwargs'] == {
        'timeout_seconds': 7.5,
        'proxy': None,
    }
    preview = ExternalRagModelHttpTransport().build_request_preview(
        _payload(),
        config=client.config,
        credentials=ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(preview)
    assert 'Authorization' not in str(preview)
    assert 'token=secret' not in str(preview)


def test_real_http_transport_success_with_default_env_resolver_keeps_secret_only_at_http_boundary(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"answer": "Grounded answer from provider", "citation_ids": ["citation-001"], "warnings": []}'
                        }
                    }
                ]
            }

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            captured['url'] = url
            captured['json'] = json
            captured['headers'] = headers
            return _FakeResponse()

    monkeypatch.setattr(os.environ, 'get', lambda name, default=None: 'TEST_API_KEY_SHOULD_NOT_LEAK')
    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
            base_url='https://provider.example/v1/chat/completions?token=secret',
        ),
    )

    response = client.generate_answer(_payload())
    preview = ExternalRagModelHttpTransport().build_request_preview(
        _payload(),
        config=client.config,
        credentials=ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    assert response == {
        'answer': 'Grounded answer from provider',
        'citation_ids': ['citation-001'],
        'warnings': [],
    }
    assert captured['headers']['Authorization'] == 'Bearer TEST_API_KEY_SHOULD_NOT_LEAK'
    assert captured['json']['model'] == 'backend-model'
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(captured['json'])
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(preview)
    assert 'Authorization' not in str(preview)


def test_create_http_transport_client_sets_trust_env_false_and_only_uses_explicit_proxy(monkeypatch):
    captured_calls = []

    class _CapturedClient:
        def __init__(self, **kwargs):
            captured_calls.append(kwargs)

    monkeypatch.setattr('ltclaw_gy_x.game.knowledge_rag_external_model_client.httpx.Client', _CapturedClient)

    _create_http_transport_client(timeout_seconds=9.5, proxy=None)
    _create_http_transport_client(timeout_seconds=9.5, proxy='https://proxy.example:8443/forward?token=secret')

    assert captured_calls[0] == {
        'timeout': 9.5,
        'trust_env': False,
    }
    assert captured_calls[1] == {
        'timeout': 9.5,
        'trust_env': False,
        'proxy': 'https://proxy.example:8443/forward?token=secret',
    }


def test_real_http_transport_timeout_maps_to_safe_warning(monkeypatch):
    request = httpx.Request('POST', 'https://provider.example/v1/chat/completions')

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            raise httpx.TimeoutException('timeout with TEST_API_KEY_SHOULD_NOT_LEAK', request=request)

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions?token=secret',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton timed out.'],
    }
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)
    assert 'token=secret' not in str(response)


def test_real_http_transport_non_2xx_maps_to_safe_http_error(monkeypatch):
    request = httpx.Request('POST', 'https://provider.example/v1/chat/completions')
    response = httpx.Response(503, request=request)

    class _FakeResponse:
        def raise_for_status(self):
            raise httpx.HTTPStatusError('503 TEST_API_KEY_SHOULD_NOT_LEAK', request=request, response=response)

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            return _FakeResponse()

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton HTTP error.'],
    }
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)


def test_real_http_transport_connection_error_maps_to_safe_request_failed(monkeypatch):
    request = httpx.Request('POST', 'https://provider.example/v1/chat/completions')

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            raise httpx.ConnectError('dns failed TEST_API_KEY_SHOULD_NOT_LEAK', request=request)

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton request failed.'],
    }
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)


@pytest.mark.parametrize(
    'response_payload',
    [
        {'choices': [{'message': {'content': 'not-json'}}]},
        {'choices': [{'message': {'content': '{"answer": "Grounded answer"}'}}]},
        {'choices': [{'message': {'content': '{"answer": "   ", "citation_ids": ["citation-001"], "warnings": []}'}}]},
    ],
)
def test_real_http_transport_invalid_provider_payload_maps_to_invalid_response(monkeypatch, response_payload):
    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return response_payload

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            return _FakeResponse()

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(),
    )
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton returned an invalid response.'],
    }
    assert 'TEST_API_KEY_SHOULD_NOT_LEAK' not in str(response)


def test_real_http_transport_explicit_proxy_is_passed_without_leaking_userinfo_or_query(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"answer": "Grounded answer from provider", "citation_ids": ["citation-001"], "warnings": []}'
                        }
                    }
                ]
            }

    class _FakeClient:
        def __init__(self, **kwargs):
            captured['client_kwargs'] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, json, headers):
            return _FakeResponse()

    monkeypatch.setattr(
        'ltclaw_gy_x.game.knowledge_rag_external_model_client._create_http_transport_client',
        lambda **kwargs: _FakeClient(**kwargs),
    )

    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=('future_external',),
            allowed_models=('backend-model',),
            base_url='https://provider.example/v1/chat/completions?query=secret',
            proxy='https://user:pass@proxy.example:8443/forward?token=secret',
        ),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )

    response = client.generate_answer(_payload())

    assert response['answer'] == 'Grounded answer from provider'
    assert captured['client_kwargs'] == {
        'timeout_seconds': 15.0,
        'proxy': 'https://user:pass@proxy.example:8443/forward?token=secret',
    }
    preview = ExternalRagModelHttpTransport().build_request_preview(
        _payload(),
        config=client.config,
        credentials=ExternalRagModelClientCredentials(api_key='TEST_API_KEY_SHOULD_NOT_LEAK'),
    )
    assert preview['proxy'] == 'https://proxy.example:8443/forward'
    assert 'user:pass' not in str(preview)
    assert 'token=secret' not in str(preview)


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
