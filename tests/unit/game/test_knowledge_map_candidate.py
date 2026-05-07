from __future__ import annotations

import builtins
from pathlib import Path

from ltclaw_gy_x.game import knowledge_rag_answer as answer_module
from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer


def _context(*, mode: str = 'context', release_id: str | None = 'release-001', chunks=None, citations=None):
    return {
        'mode': mode,
        'release_id': release_id,
        'built_at': '2026-01-01T00:00:00Z',
        'chunks': list(chunks or []),
        'citations': list(citations or []),
    }


def test_build_rag_answer_returns_no_current_release():
    payload = build_rag_answer('combat damage', _context(mode='no_current_release', release_id=None))

    assert payload == {
        'mode': 'no_current_release',
        'answer': '',
        'release_id': None,
        'citations': [],
        'warnings': [],
    }


def test_build_rag_answer_returns_insufficient_context_for_empty_chunks():
    payload = build_rag_answer('combat damage', _context(chunks=[], citations=[]))

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['release_id'] == 'release-001'
    assert payload['citations'] == []
    assert 'No grounded context was available for a safe answer.' in payload['warnings']


def test_build_rag_answer_returns_grounded_answer_from_valid_chunks():
    payload = build_rag_answer(
        'How does combat damage work?',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Combat damage is summarized in the current release as a skill damage formula.',
                }
            ],
            citations=[
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-001',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                    'source_path': 'Docs/Combat.md',
                    'title': 'Combat Overview',
                }
            ],
        ),
    )

    assert payload['mode'] == 'answer'
    assert payload['release_id'] == 'release-001'
    assert payload['citations'] == [
        {
            'citation_id': 'citation-001',
            'release_id': 'release-001',
            'source_type': 'doc_knowledge',
            'artifact_path': 'indexes/doc_knowledge.jsonl',
            'source_path': 'Docs/Combat.md',
            'title': 'Combat Overview',
        }
    ]
    assert 'provided current-release context' in payload['answer']
    assert 'skill damage formula' in payload['answer']
    assert payload['warnings'] == []


def test_build_rag_answer_uses_only_context_citations():
    payload = build_rag_answer(
        'How does combat damage work?',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Chunk one text.',
                }
            ],
            citations=[
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-001',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                },
                {
                    'citation_id': 'citation-999',
                    'release_id': 'release-001',
                    'source_type': 'script_evidence',
                    'artifact_path': 'indexes/script_evidence.jsonl',
                },
            ],
        ),
    )

    assert payload['mode'] == 'answer'
    assert payload['citations'] == [
        {
            'citation_id': 'citation-001',
            'release_id': 'release-001',
            'source_type': 'doc_knowledge',
            'artifact_path': 'indexes/doc_knowledge.jsonl',
        }
    ]


def test_build_rag_answer_does_not_fabricate_missing_chunk_citations():
    payload = build_rag_answer(
        'How does combat damage work?',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-missing',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Missing citation chunk.',
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
        ),
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['citations'] == []
    assert 'Ignored one or more context chunks without a matching citation.' in payload['warnings']


def test_build_rag_answer_preserves_release_id_on_answer_and_warnings():
    payload = build_rag_answer(
        'What is SkillTable 1029 damage?',
        _context(
            release_id='release-precise',
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Skill damage is described in Combat Overview.',
                }
            ],
            citations=[
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-precise',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                }
            ],
        ),
    )

    assert payload['mode'] == 'answer'
    assert payload['release_id'] == 'release-precise'
    assert payload['citations'][0]['release_id'] == 'release-precise'
    assert 'For exact numeric or row-level facts, use the structured query flow.' in payload['warnings']


def test_build_rag_answer_emits_workbench_warning_for_modification_queries():
    payload = build_rag_answer(
        'Change SkillTable 1029 damage to 120',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Damage changes should be reviewed in the workbench flow.',
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
        ),
    )

    assert payload['mode'] == 'answer'
    assert 'For change proposals or edits, use the workbench flow.' in payload['warnings']
    assert 'For exact numeric or row-level facts, use the structured query flow.' in payload['warnings']


def test_build_rag_answer_does_not_read_or_write_files_or_use_model_client(monkeypatch):
    def _forbid_open(*args, **kwargs):
        raise AssertionError('answer adapter must not open files')

    def _forbid_path_call(*args, **kwargs):
        raise AssertionError('answer adapter must not touch Path I/O')

    class _ForbiddenModelClient:
        def generate(self, *args, **kwargs):
            raise AssertionError('answer adapter must not access any model client')

    monkeypatch.setattr(builtins, 'open', _forbid_open)
    monkeypatch.setattr(Path, 'read_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_text', _forbid_path_call)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_path_call)
    monkeypatch.setattr(answer_module, 'model_client', _ForbiddenModelClient(), raising=False)

    payload = build_rag_answer(
        'How does combat damage work?',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 4.0,
                    'text': 'Combat damage is summarized in the current release context.',
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
        ),
    )

    assert payload['mode'] == 'answer'
    assert payload['citations'][0]['citation_id'] == 'citation-001'