from __future__ import annotations

import builtins
from pathlib import Path

from ltclaw_gy_x.game.knowledge_rag_model_client import (
    DeterministicMockRagModelClient,
    DisabledRagModelClient,
    build_rag_model_prompt_payload,
)


def test_build_rag_model_prompt_payload_has_only_bounded_fields():
    payload = build_rag_model_prompt_payload(
        query='How does combat damage work?',
        release_id='release-001',
        built_at='2026-01-01T00:00:00Z',
        chunks=[
            {
                'chunk_id': 'chunk-001',
                'citation_id': 'citation-001',
                'rank': 1,
                'score': 4.0,
                'text': 'Combat damage uses the current release formula.',
                'unexpected_key': 'ignored',
            }
        ],
        citations=[
            {
                'citation_id': 'citation-001',
                'release_id': 'release-001',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
                'source_path': 'Docs/Combat.md',
            }
        ],
        policy_hints=['Use only grounded citations.'],
    )

    assert set(payload.keys()) == {
        'query',
        'release_id',
        'built_at',
        'chunks',
        'citations',
        'policy_hints',
    }
    assert payload['query'] == 'How does combat damage work?'
    assert payload['release_id'] == 'release-001'
    assert payload['built_at'] == '2026-01-01T00:00:00Z'
    assert payload['chunks'] == [
        {
            'chunk_id': 'chunk-001',
            'citation_id': 'citation-001',
            'rank': 1,
            'score': 4.0,
            'text': 'Combat damage uses the current release formula.',
        }
    ]
    assert payload['citations'][0]['artifact_path'] == 'indexes/doc_knowledge.jsonl'
    assert payload['citations'][0]['source_path'] == 'Docs/Combat.md'
    assert payload['policy_hints'] == ['Use only grounded citations.']
    assert 'candidate_evidence' not in str(payload)
    assert 'pending/test_plans.jsonl' not in str(payload)
    assert 'pending/release_candidates.jsonl' not in str(payload)
    assert 'svn' not in str(payload).lower()


def test_deterministic_mock_model_client_uses_only_payload(monkeypatch):
    def _forbid_open(*args, **kwargs):
        raise AssertionError('mock model client must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('mock model client must not touch Path I/O')

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)

    payload = build_rag_model_prompt_payload(
        query='How does combat damage work?',
        release_id='release-001',
        built_at='2026-01-01T00:00:00Z',
        chunks=[
            {
                'chunk_id': 'chunk-001',
                'citation_id': 'citation-001',
                'rank': 1,
                'score': 4.0,
                'text': 'Combat damage uses the current release formula.',
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

    response = DeterministicMockRagModelClient().generate_answer(payload)

    assert response['citation_ids'] == ['citation-001']
    assert response['warnings'] == []
    assert 'Grounded answer from the provided current-release context' in response['answer']
    assert 'current release formula' in response['answer']


def test_disabled_rag_model_client_returns_empty_answer_and_warning():
    response = DisabledRagModelClient().generate_answer(
        build_rag_model_prompt_payload(
            query='combat',
            release_id='release-001',
            built_at='2026-01-01T00:00:00Z',
            chunks=[],
            citations=[],
            policy_hints=[],
        )
    )

    assert response == {
        'answer': '',
        'citation_ids': [],
        'warnings': ['Model provider is disabled.'],
    }
