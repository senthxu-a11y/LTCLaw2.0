from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from ltclaw_gy_x.game import knowledge_rag_answer as answer_module
from ltclaw_gy_x.game.knowledge_rag_external_model_client import (
    ExternalRagModelClientConfig,
    ExternalRagModelClientSkeleton,
)
from ltclaw_gy_x.game.knowledge_rag_answer import (
    build_rag_answer,
    build_rag_answer_with_provider,
    build_rag_answer_with_service_config,
)
from ltclaw_gy_x.game.knowledge_rag_model_client import DisabledRagModelClient
from ltclaw_gy_x.game.knowledge_rag_model_registry import (
    RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
    RAG_MODEL_PROVIDER_DISABLED,
)


def _context(*, mode: str = 'context', release_id: str | None = 'release-001', chunks=None, citations=None):
    return {
        'mode': mode,
        'release_id': release_id,
        'built_at': '2026-01-01T00:00:00Z',
        'chunks': list(chunks or []),
        'citations': list(citations or []),
    }


def _grounded_context():
    return _context(
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
                'source_path': 'Docs/Combat.md',
                'title': 'Combat Overview',
            }
        ],
    )


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


def test_build_rag_answer_sorts_grounded_chunks_before_composing_answer():
    payload = build_rag_answer(
        'How does combat damage work?',
        _context(
            chunks=[
                {
                    'chunk_id': 'chunk-003',
                    'citation_id': 'citation-003',
                    'rank': 2,
                    'score': 9.0,
                    'text': 'Third ranked evidence should not lead the answer.',
                },
                {
                    'chunk_id': 'chunk-002',
                    'citation_id': 'citation-002',
                    'rank': 1,
                    'score': 1.0,
                    'text': 'Second strongest evidence should be summarized second.',
                },
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'rank': 1,
                    'score': 5.0,
                    'text': 'Strongest evidence should be summarized first.',
                },
            ],
            citations=[
                {'citation_id': 'citation-001', 'release_id': 'release-001'},
                {'citation_id': 'citation-002', 'release_id': 'release-001'},
                {'citation_id': 'citation-003', 'release_id': 'release-001'},
            ],
        ),
    )

    assert payload['mode'] == 'answer'
    assert payload['answer'].index('Strongest evidence') < payload['answer'].index('Second strongest evidence')
    assert 'Third ranked evidence' not in payload['answer']
    assert [citation['citation_id'] for citation in payload['citations']] == [
        'citation-001',
        'citation-002',
        'citation-003',
    ]


def test_build_rag_answer_does_not_treat_general_numbered_status_query_as_structured_fact():
    payload = build_rag_answer(
        'What is P3.7 status?',
        _grounded_context(),
    )

    assert payload['mode'] == 'answer'
    assert 'For exact numeric or row-level facts, use the structured query flow.' not in payload['warnings']


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


def test_build_rag_answer_with_provider_defaults_to_deterministic_mock_and_returns_grounded_answer():
    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
    )

    assert payload['mode'] == 'answer'
    assert [citation['citation_id'] for citation in payload['citations']] == ['citation-001']
    assert 'Grounded answer from the provided current-release context' in payload['answer']
    assert payload['warnings'] == []


def test_build_rag_answer_with_provider_disabled_provider_degrades_conservatively():
    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        provider_name=RAG_MODEL_PROVIDER_DISABLED,
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'Model provider is disabled.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_provider_reads_disabled_provider_from_service_config():
    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        config_or_service={'rag_model_provider': RAG_MODEL_PROVIDER_DISABLED},
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'Model provider is disabled.' in payload['warnings']


def test_build_rag_answer_with_service_config_defaults_to_deterministic_mock_and_returns_grounded_answer():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
    )

    assert payload['mode'] == 'answer'
    assert [citation['citation_id'] for citation in payload['citations']] == ['citation-001']
    assert 'Grounded answer from the provided current-release context' in payload['answer']


def test_build_rag_answer_with_service_config_reads_disabled_provider_from_service_config():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {'rag_model_provider': RAG_MODEL_PROVIDER_DISABLED},
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'Model provider is disabled.' in payload['warnings']


def test_build_rag_answer_with_service_config_uses_backend_owned_external_disabled_config():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {
            'external_provider_config': {
                'enabled': False,
                'provider_name': 'future_external',
            }
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'External provider adapter skeleton is disabled.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_service_config_requires_explicit_transport_enable_before_credentials():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {
            'external_provider_config': {
                'enabled': True,
                'provider_name': 'future_external',
                'allowed_providers': ['future_external'],
            }
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'External provider adapter skeleton transport is not connected.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_service_config_degrades_when_allowed_providers_are_missing():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {
            'external_provider_config': {
                'enabled': True,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'stub-model',
                'allowed_models': ['stub-model'],
            }
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'External provider adapter skeleton provider is not allowed.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_service_config_degrades_when_allowed_models_are_missing():
    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {
            'external_provider_config': {
                'enabled': True,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'stub-model',
                'allowed_providers': ['future_external'],
            }
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'External provider adapter skeleton model is not allowed.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_service_config_raises_for_unknown_backend_owned_external_provider():
    with pytest.raises(ValueError, match='Unsupported RAG model provider: unsupported_external'):
        build_rag_answer_with_service_config(
            'How does combat damage work?',
            _grounded_context(),
            {
                'external_provider_config': {
                    'enabled': True,
                    'provider_name': 'unsupported_external',
                }
            },
        )


def test_build_rag_answer_with_service_config_raises_for_unknown_provider_from_service_config():
    with pytest.raises(ValueError, match='RAG model provider is not configured: future_external'):
        build_rag_answer_with_service_config(
            'How does combat damage work?',
            _grounded_context(),
            {'rag_model_provider': 'future_external'},
        )


def test_build_rag_answer_with_service_config_factory_failure_falls_back_to_disabled_with_warnings():
    def _fail_factory():
        raise RuntimeError('boom')

    payload = build_rag_answer_with_service_config(
        'How does combat damage work?',
        _grounded_context(),
        {'rag_model_provider': RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK},
        factories={
            RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: _fail_factory,
            RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert (
        "Failed to initialize RAG model provider 'deterministic_mock': boom. Falling back to disabled provider."
        in payload['warnings']
    )
    assert 'Model provider is disabled.' in payload['warnings']


def test_build_rag_answer_with_service_config_does_not_call_provider_factory_for_no_current_release(monkeypatch):
    called = False

    def _unexpected_resolver(*args, **kwargs):
        raise AssertionError('provider resolver should not be called')

    def _unexpected_registry(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider registry should not be called')

    monkeypatch.setattr(answer_module, 'resolve_rag_model_provider_name', _unexpected_resolver)
    monkeypatch.setattr(answer_module, 'get_rag_model_client', _unexpected_registry)

    payload = build_rag_answer_with_service_config(
        'combat damage',
        _context(mode='no_current_release', release_id=None),
        {'rag_model_provider': RAG_MODEL_PROVIDER_DISABLED},
    )

    assert payload['mode'] == 'no_current_release'
    assert called is False


def test_build_rag_answer_with_service_config_does_not_call_provider_factory_without_grounded_chunks(monkeypatch):
    called = False

    def _unexpected_resolver(*args, **kwargs):
        raise AssertionError('provider resolver should not be called')

    def _unexpected_registry(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider registry should not be called')

    monkeypatch.setattr(answer_module, 'resolve_rag_model_provider_name', _unexpected_resolver)
    monkeypatch.setattr(answer_module, 'get_rag_model_client', _unexpected_registry)

    payload = build_rag_answer_with_service_config(
        'combat damage',
        _context(chunks=[], citations=[]),
        {'rag_model_provider': RAG_MODEL_PROVIDER_DISABLED},
    )

    assert payload['mode'] == 'insufficient_context'
    assert called is False


def test_build_rag_answer_with_provider_ignores_request_like_provider_field_in_config():
    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        config_or_service={'provider_name': RAG_MODEL_PROVIDER_DISABLED},
    )

    assert payload['mode'] == 'answer'
    assert [citation['citation_id'] for citation in payload['citations']] == ['citation-001']
    assert 'Grounded answer from the provided current-release context' in payload['answer']


def test_build_rag_answer_with_provider_factory_failure_falls_back_to_disabled_with_warnings():
    def _fail_factory():
        raise RuntimeError('boom')

    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        provider_name=RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
        factories={
            RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: _fail_factory,
            RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert (
        "Failed to initialize RAG model provider 'deterministic_mock': boom. Falling back to disabled provider."
        in payload['warnings']
    )
    assert 'Model provider is disabled.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_provider_raises_for_unknown_provider_with_grounded_context():
    with pytest.raises(ValueError, match='RAG model provider is not configured: future_external'):
        build_rag_answer_with_provider(
            'How does combat damage work?',
            _grounded_context(),
            provider_name='future_external',
        )


def test_build_rag_answer_with_provider_raises_for_unknown_provider_from_service_config():
    with pytest.raises(ValueError, match='RAG model provider is not configured: future_external'):
        build_rag_answer_with_provider(
            'How does combat damage work?',
            _grounded_context(),
            config_or_service={'rag_model_provider': 'future_external'},
        )


def test_build_rag_answer_with_provider_does_not_call_provider_factory_for_no_current_release(monkeypatch):
    called = False

    def _unexpected_resolver(*args, **kwargs):
        raise AssertionError('provider resolver should not be called')

    def _unexpected_registry(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider registry should not be called')

    monkeypatch.setattr(answer_module, 'resolve_rag_model_provider_name', _unexpected_resolver)
    monkeypatch.setattr(answer_module, 'get_rag_model_client', _unexpected_registry)

    payload = build_rag_answer_with_provider(
        'combat damage',
        _context(mode='no_current_release', release_id=None),
    )

    assert payload['mode'] == 'no_current_release'
    assert called is False


def test_build_rag_answer_with_provider_does_not_call_provider_factory_without_grounded_chunks(monkeypatch):
    called = False

    def _unexpected_resolver(*args, **kwargs):
        raise AssertionError('provider resolver should not be called')

    def _unexpected_registry(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider registry should not be called')

    monkeypatch.setattr(answer_module, 'resolve_rag_model_provider_name', _unexpected_resolver)
    monkeypatch.setattr(answer_module, 'get_rag_model_client', _unexpected_registry)

    payload = build_rag_answer_with_provider(
        'combat damage',
        _context(chunks=[], citations=[]),
    )

    assert payload['mode'] == 'insufficient_context'
    assert called is False


def test_build_rag_answer_with_provider_filters_out_of_context_citations_and_degrades():
    class _OutOfContextModelClient:
        def generate_answer(self, payload):
            return {
                'answer': 'Unsupported answer.',
                'citation_ids': ['citation-999'],
                'warnings': [],
            }

    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        provider_name=RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
        factories={
            RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: _OutOfContextModelClient,
            RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'Ignored one or more model citation ids outside the provided context.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_external_adapter_skeleton_degrades_without_grounded_model_output():
    payload = build_rag_answer(
        'How does combat damage work?',
        _grounded_context(),
        model_client=ExternalRagModelClientSkeleton(),
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'External provider adapter skeleton is disabled.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_external_adapter_skeleton_rejects_out_of_context_citations():
    client = ExternalRagModelClientSkeleton(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
        ),
        responder=lambda payload: {
            'answer': 'Grounded-looking answer.',
            'citation_ids': ['citation-999'],
            'warnings': [],
        }
    )

    payload = build_rag_answer(
        'How does combat damage work?',
        _grounded_context(),
        model_client=client,
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert 'Ignored one or more model citation ids outside the provided context.' in payload['warnings']
    assert 'Model client output was not grounded in the provided context.' in payload['warnings']


def test_build_rag_answer_with_external_adapter_skeleton_preserves_structured_and_workbench_warnings():
    client = ExternalRagModelClientSkeleton(
        config=ExternalRagModelClientConfig(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='stub-model',
            allowed_providers=('future_external',),
            allowed_models=('stub-model',),
            max_prompt_chars=20000,
        ),
        responder=lambda payload: {
            'answer': 'Grounded adapter answer.',
            'citation_ids': ['citation-001'],
            'warnings': [],
        },
    )

    payload = build_rag_answer(
        'Change SkillTable 1029 damage to 120',
        _grounded_context(),
        model_client=client,
    )

    assert payload['mode'] == 'answer'
    assert [citation['citation_id'] for citation in payload['citations']] == ['citation-001']
    assert 'For change proposals or edits, use the workbench flow.' in payload['warnings']
    assert 'For exact numeric or row-level facts, use the structured query flow.' in payload['warnings']


@pytest.mark.parametrize(
    ('model_response', 'expected_warning'),
    [
        ({'answer': '', 'citation_ids': ['citation-001']}, 'Model client output was not grounded in the provided context.'),
        ({'answer': 'Grounded-looking answer.', 'citation_ids': []}, 'Model client output was not grounded in the provided context.'),
    ],
)
def test_build_rag_answer_with_provider_degrades_for_empty_answer_or_empty_citations(model_response, expected_warning):
    class _ModelClient:
        def generate_answer(self, payload):
            return model_response

    payload = build_rag_answer_with_provider(
        'How does combat damage work?',
        _grounded_context(),
        provider_name=RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK,
        factories={
            RAG_MODEL_PROVIDER_DETERMINISTIC_MOCK: _ModelClient,
            RAG_MODEL_PROVIDER_DISABLED: DisabledRagModelClient,
        },
    )

    assert payload['mode'] == 'insufficient_context'
    assert payload['answer'] == ''
    assert payload['citations'] == []
    assert expected_warning in payload['warnings']
