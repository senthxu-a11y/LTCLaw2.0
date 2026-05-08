from __future__ import annotations

import builtins
import os
import socket
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_rag_external_model_client import (
    ExternalRagModelClientConfig,
    ExternalRagModelClientSecrets,
    ExternalRagModelClientSkeleton,
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
    client = ExternalRagModelClientSkeleton()

    assert isinstance(client, RagModelClient)


def test_external_rag_model_client_skeleton_accepts_bounded_prompt_payload():
    client = ExternalRagModelClientSkeleton()

    response = client.generate_answer(_payload())

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['External provider adapter skeleton is not connected.'],
    }


def test_external_rag_model_client_skeleton_rejects_oversize_prompt_payload():
    client = ExternalRagModelClientSkeleton(config=ExternalRagModelClientConfig(max_prompt_chars=10))

    with pytest.raises(ValueError, match='RAG prompt payload exceeds configured max_prompt_chars'):
        client.generate_answer(_payload())


def test_external_rag_model_client_skeleton_default_implementation_performs_no_network_or_file_or_env_io(monkeypatch):
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

    client = ExternalRagModelClientSkeleton(
        secrets=ExternalRagModelClientSecrets(api_key='placeholder', model_name='stub-model')
    )
    response = client.generate_answer(_payload())

    assert response['citation_ids'] == []
    assert response['warnings'] == ['External provider adapter skeleton is not connected.']


def test_external_rag_model_client_skeleton_uses_mockable_responder_seam_and_normalizes_response():
    captured = {}

    def _responder(payload):
        captured['payload'] = payload
        return {
            'answer': 'Grounded adapter answer that is intentionally longer than the configured output budget.',
            'citation_ids': ['citation-001', ' ', 'citation-002'],
            'warnings': ['Adapter warning', ' '],
        }

    client = ExternalRagModelClientSkeleton(
        config=ExternalRagModelClientConfig(max_output_chars=20),
        responder=_responder,
    )

    response = client.generate_answer(_payload())

    assert captured['payload']['query'] == 'How does combat damage work?'
    assert response['answer'] == 'Grounded adapter ans'
    assert response['citation_ids'] == ['citation-001', 'citation-002']
    assert response['warnings'] == ['Adapter warning']