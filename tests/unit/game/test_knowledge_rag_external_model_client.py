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
    ExternalRagModelClientCredentials,
    ExternalRagModelEnvConfig,
    ExternalRagModelClientHttpError,
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


def test_external_rag_model_client_skeleton_rejects_oversize_prompt_payload():
    client = ExternalRagModelClient(config=ExternalRagModelClientConfig(max_prompt_chars=10))

    with pytest.raises(ValueError, match='RAG prompt payload exceeds configured max_prompt_chars'):
        client.generate_answer(_payload())


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
    client = ExternalRagModelClient(config=ExternalRagModelClientConfig(enabled=True))

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_configured_warning_for_missing_credential():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=True),
        credential_resolver=lambda request: None,
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not configured.'],
    }


def test_external_rag_model_client_returns_not_connected_warning_without_transport():
    client = ExternalRagModelClient(
        config=ExternalRagModelClientConfig(enabled=True),
        credential_resolver=lambda request: ExternalRagModelClientCredentials(api_key='placeholder'),
    )

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton transport is not connected.'],
    }


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
        config=ExternalRagModelClientConfig(enabled=True),
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
        config=ExternalRagModelClientConfig(enabled=True),
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
        config=ExternalRagModelClientConfig(enabled=True),
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


def _capture_request(request, captured):
    captured['credential_request'] = request
    return ExternalRagModelClientCredentials(api_key='placeholder')
