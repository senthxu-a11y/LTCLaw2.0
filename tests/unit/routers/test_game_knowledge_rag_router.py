from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ltclaw_gy_x.game import knowledge_rag_answer as answer_module
from ltclaw_gy_x.game.knowledge_rag_answer import RagAnswerConfigGenerationChangedError
from ltclaw_gy_x.game.knowledge_rag_external_model_client import ExternalRagModelHttpTransport

from ltclaw_gy_x.app.routers import game_knowledge_rag as rag_router_module
from ltclaw_gy_x.app.routers.game_knowledge_rag import router



def _build_app():
    app = FastAPI()
    app.include_router(router, prefix='/api')
    return app



def _workspace(service):
    return SimpleNamespace(
        game_service=service,
        service_manager=SimpleNamespace(services=({'game_service': service} if service else {})),
    )



def _service(project_root: Path | None):
    project_config = SimpleNamespace(svn=SimpleNamespace(root=None))
    return SimpleNamespace(
        config_generation=0,
        _runtime_svn_root=(lambda: project_root),
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=project_config,
        config=project_config,
    )



def test_rag_context_router_forwards_project_root_and_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_context(project_root, query, *, max_chunks, max_chars, focus_refs=None):
        captured['project_root'] = project_root
        captured['query'] = query
        captured['max_chunks'] = max_chunks
        captured['max_chars'] = max_chars
        captured['focus_refs'] = focus_refs
        return {
            'mode': 'context',
            'query': query,
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [
                {
                    'chunk_id': 'chunk-001',
                    'source_type': 'doc_knowledge',
                    'text': 'combat damage formula',
                    'score': 3.0,
                    'rank': 1,
                    'citation_id': 'citation-001',
                }
            ],
            'citations': [
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-001',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                    'source_path': 'Docs/Combat.md',
                    'title': 'Combat Overview',
                    'row': 1,
                    'field': None,
                    'source_hash': 'sha256:doc',
                    'ref': 'doc:combat-doc',
                }
            ],
            'allowed_refs': ['doc:combat-doc'],
            'map_hash': 'sha256:map',
            'map_source_hash': 'sha256:map-source',
            'reason': None,
        }

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)

    with TestClient(_build_app()) as client:
        response = client.post(
            '/api/game/knowledge/rag/context',
            json={'query': 'damage', 'max_chunks': 5, 'max_chars': 4096, 'focus_refs': ['doc:combat-doc']},
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'context'
    assert response.json()['chunks'][0]['source_type'] == 'doc_knowledge'
    assert response.json()['citations'][0]['field'] is None
    assert response.json()['citations'][0]['ref'] == 'doc:combat-doc'
    assert captured == {
        'project_root': tmp_path / 'project-root',
        'query': 'damage',
        'max_chunks': 5,
        'max_chars': 4096,
        'focus_refs': ['doc:combat-doc'],
    }



def test_rag_context_router_returns_no_current_release_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        rag_router_module,
        'build_current_release_context',
        lambda *args, **kwargs: {
            'mode': 'no_current_release',
            'query': 'damage',
            'release_id': None,
            'built_at': None,
            'chunks': [],
            'citations': [],
            'allowed_refs': [],
            'map_hash': None,
            'map_source_hash': None,
            'reason': 'no_current_release',
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_current_release'
    assert response.json()['chunks'] == []
    assert response.json()['citations'] == []


def test_rag_context_router_preserves_citation_locator_fields(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        rag_router_module,
        'build_current_release_context',
        lambda *args, **kwargs: {
            'mode': 'context',
            'query': 'damage',
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [
                {
                    'chunk_id': 'chunk-001',
                    'source_type': 'table_schema',
                    'text': 'combat damage schema',
                    'score': 3.0,
                    'rank': 1,
                    'citation_id': 'citation-001',
                }
            ],
            'citations': [
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-001',
                    'source_type': 'table_schema',
                    'table': 'SkillTable',
                    'artifact_path': 'indexes/table_schema.jsonl',
                    'source_path': 'Tables/SkillTable.xlsx',
                    'title': 'SkillTable',
                    'row': 1,
                    'field': 'Damage',
                    'source_hash': 'sha256:table',
                    'ref': 'table:SkillTable',
                }
            ],
            'allowed_refs': ['table:SkillTable'],
            'map_hash': 'sha256:map',
            'map_source_hash': 'sha256:map-source',
            'reason': None,
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['citations'] == [
        {
            'citation_id': 'citation-001',
            'release_id': 'release-001',
            'source_type': 'table_schema',
            'table': 'SkillTable',
            'artifact_path': 'indexes/table_schema.jsonl',
            'source_path': 'Tables/SkillTable.xlsx',
            'title': 'SkillTable',
            'row': 1,
            'field': 'Damage',
            'source_hash': 'sha256:table',
            'ref': 'table:SkillTable',
        }
    ]


def test_rag_answer_router_still_builds_answer_only_from_context(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {'context_calls': 0, 'answer_calls': 0}

    async def _get_agent(_request):
        return workspace

    def _build_context(project_root, query, *, max_chunks, max_chars, focus_refs=None):
        captured['context_calls'] += 1
        captured['focus_refs'] = focus_refs
        return {
            'mode': 'context',
            'query': query,
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [
                {
                    'chunk_id': 'chunk-001',
                    'source_type': 'doc_knowledge',
                    'text': 'combat damage formula',
                    'score': 3.0,
                    'rank': 1,
                    'citation_id': 'citation-001',
                }
            ],
            'citations': [
                {
                    'citation_id': 'citation-001',
                    'release_id': 'release-001',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                    'source_path': 'Docs/Combat.md',
                    'title': 'Combat Overview',
                    'row': 1,
                    'field': None,
                    'source_hash': 'sha256:doc',
                    'ref': 'doc:combat-doc',
                }
            ],
        }

    def _build_answer(query, context, service_config, **kwargs):
        captured['answer_calls'] += 1
        captured['answer_context'] = context
        return {
            'mode': 'answer',
            'answer': 'grounded answer',
            'release_id': 'release-001',
            'citations': context['citations'],
            'warnings': [],
        }

    def _forbid_read(*args, **kwargs):
        raise AssertionError('rag answer router must not read artifacts directly')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)
    monkeypatch.setattr(Path, 'read_text', _forbid_read)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage', 'focus_refs': ['doc:combat-doc']})

    assert response.status_code == 200
    assert response.json()['mode'] == 'answer'
    assert captured['context_calls'] == 1
    assert captured['answer_calls'] == 1
    assert captured['focus_refs'] == ['doc:combat-doc']
    assert captured['answer_context']['citations'][0]['ref'] == 'doc:combat-doc'



def test_rag_context_router_rejects_invalid_max_chunks():
    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage', 'max_chunks': 0, 'max_chars': 12000})

    assert response.status_code == 422



def test_rag_context_router_rejects_invalid_max_chars():
    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage', 'max_chunks': 8, 'max_chars': 999})

    assert response.status_code == 422



def test_rag_context_router_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'



def test_rag_context_router_requires_project_root(monkeypatch):
    workspace = _workspace(_service(None))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 400
    assert response.json()['detail'] == 'Local project directory not configured'


def test_rag_context_router_requires_injected_read_capabilities(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(request):
        request.state.capabilities = set()
        return workspace

    def _build_context(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('rag context should be blocked by injected capabilities')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.read'
    assert called is False



def test_rag_context_router_is_read_only_and_does_not_read_files(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        return {
            'mode': 'context',
            'query': 'damage',
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [],
            'citations': [],
        }

    def _forbid_read(*args, **kwargs):
        raise AssertionError('router must not read files directly')

    def _forbid_write(*args, **kwargs):
        raise AssertionError('router must be read-only')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(Path, 'read_text', _forbid_read)
    monkeypatch.setattr(Path, 'write_text', _forbid_write)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_write)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'context'



def test_rag_answer_router_builds_answer_from_context(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    context_payload = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-001',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'source_type': 'doc_knowledge',
                'text': 'combat damage formula',
                'score': 3.0,
                'rank': 1,
                'citation_id': 'citation-001',
            }
        ],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-001',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
                'source_path': 'Docs/Combat.md',
                'title': 'Combat Overview',
                'row': 1,
                'source_hash': 'sha256:doc',
            }
        ],
    }

    async def _get_agent(_request):
        return workspace

    def _build_context(project_root, query, *, max_chunks, max_chars):
        captured['project_root'] = project_root
        captured['query'] = query
        captured['max_chunks'] = max_chunks
        captured['max_chars'] = max_chars
        return context_payload

    def _build_answer(query, context, service_config, **kwargs):
        captured['answer_query'] = query
        captured['answer_context'] = context
        captured['service_config'] = service_config
        captured['expected_generation'] = kwargs.get('expected_generation')
        return {
            'mode': 'answer',
            'answer': 'Based on the provided current-release context, the strongest grounded evidence is: combat damage formula',
            'release_id': 'release-001',
            'citations': [context['citations'][0]],
            'warnings': [],
        }

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)

    with TestClient(_build_app()) as client:
        response = client.post(
            '/api/game/knowledge/rag/answer',
            json={'query': 'damage', 'max_chunks': 5, 'max_chars': 4096},
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'answer'
    assert response.json()['release_id'] == 'release-001'
    assert response.json()['citations'] == [context_payload['citations'][0]]
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['query'] == 'damage'
    assert captured['answer_query'] == 'damage'
    assert captured['answer_context'] is context_payload
    assert captured['service_config'] is workspace.game_service
    assert captured['expected_generation'] == 0


def test_rag_answer_router_rereads_context_when_generation_changes_once(monkeypatch, tmp_path):
    service = _service(tmp_path / 'project-root')
    workspace = _workspace(service)
    captured = {'context_calls': 0}

    first_context = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-stale',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [],
        'citations': [],
    }
    second_context = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-live',
        'built_at': datetime(2026, 1, 2, tzinfo=timezone.utc),
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'source_type': 'doc_knowledge',
                'text': 'live config grounded text',
                'score': 3.0,
                'rank': 1,
                'citation_id': 'citation-001',
            }
        ],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-live',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
            }
        ],
    }

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        captured['context_calls'] += 1
        if captured['context_calls'] == 1:
            service.config_generation = 1
            return first_context
        return second_context

    def _build_answer(query, context, service_config, **kwargs):
        captured['query'] = query
        captured['context'] = context
        captured['service_config'] = service_config
        captured['expected_generation'] = kwargs.get('expected_generation')
        return {
            'mode': 'answer',
            'answer': 'Grounded answer after reload',
            'release_id': context['release_id'],
            'citations': list(context['citations']),
            'warnings': [],
        }

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'answer'
    assert response.json()['release_id'] == 'release-live'
    assert captured['context_calls'] == 2
    assert captured['context'] is second_context
    assert captured['service_config'] is service
    assert captured['expected_generation'] == 1


def test_rag_answer_router_fails_closed_when_generation_keeps_changing(monkeypatch, tmp_path):
    service = _service(tmp_path / 'project-root')
    workspace = _workspace(service)
    captured = {'context_calls': 0, 'answer_calls': 0}

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        captured['context_calls'] += 1
        service.config_generation += 1
        return {
            'mode': 'context',
            'query': 'damage',
            'release_id': f'release-{captured["context_calls"]}',
            'built_at': datetime(2026, 1, captured['context_calls'], tzinfo=timezone.utc),
            'chunks': [],
            'citations': [],
        }

    def _build_answer(*args, **kwargs):
        captured['answer_calls'] += 1
        raise AssertionError('router must fail closed before building the answer')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'insufficient_context'
    assert response.json()['answer'] == ''
    assert response.json()['citations'] == []
    assert response.json()['release_id'] == 'release-2'
    assert response.json()['warnings'] == [
        'RAG answer config changed repeatedly during request. External transport was skipped until reload settles.'
    ]
    assert captured['context_calls'] == 2
    assert captured['answer_calls'] == 0


@pytest.mark.parametrize(
    ('updated_external_config', 'expected_warning'),
    [
        (
            {
                'enabled': False,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': ['backend-model'],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton is disabled.',
        ),
        (
            {
                'enabled': True,
                'transport_enabled': False,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': ['backend-model'],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton transport is not connected.',
        ),
        (
            {
                'enabled': True,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': [],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton model is not allowed.',
        ),
    ],
)
def test_rag_answer_router_generation_reread_uses_latest_disabled_external_config(
    monkeypatch,
    tmp_path,
    updated_external_config,
    expected_warning,
):
    service = _service(tmp_path / 'project-root')
    service.project_config = SimpleNamespace(
        svn=SimpleNamespace(root=None),
        external_provider_config=SimpleNamespace(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=['future_external'],
            allowed_models=['backend-model'],
            env=SimpleNamespace(api_key_env_var='QWENPAW_RAG_API_KEY'),
            base_url='http://127.0.0.1:8765/v1/chat/completions',
        ),
    )
    service.config = service.project_config
    workspace = _workspace(service)
    captured = {'context_calls': 0, 'transport_calls': 0}
    context_payload = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-live',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'source_type': 'doc_knowledge',
                'text': 'combat damage formula',
                'score': 3.0,
                'rank': 1,
                'citation_id': 'citation-001',
            }
        ],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-live',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
            }
        ],
    }

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        captured['context_calls'] += 1
        if captured['context_calls'] == 1:
            service.project_config = SimpleNamespace(
                svn=SimpleNamespace(root=None),
                external_provider_config=SimpleNamespace(**updated_external_config),
            )
            service.config = service.project_config
            service.config_generation = 1
        return context_payload

    def _forbid_transport(*args, **kwargs):
        captured['transport_calls'] += 1
        raise AssertionError('hot-reload kill switch should prevent external transport calls')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(ExternalRagModelHttpTransport, '__call__', _forbid_transport)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'insufficient_context'
    assert expected_warning in response.json()['warnings']
    assert 'Model client output was not grounded in the provided context.' in response.json()['warnings']
    assert captured['context_calls'] == 2
    assert captured['transport_calls'] == 0


@pytest.mark.parametrize(
    ('updated_external_config', 'expected_warning'),
    [
        (
            {
                'enabled': False,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': ['backend-model'],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton is disabled.',
        ),
        (
            {
                'enabled': True,
                'transport_enabled': False,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': ['backend-model'],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton transport is not connected.',
        ),
        (
            {
                'enabled': True,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': [],
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            },
            'External provider adapter skeleton model is not allowed.',
        ),
    ],
)
def test_rag_answer_router_rereads_context_when_generation_changes_before_provider_selection(
    monkeypatch,
    tmp_path,
    updated_external_config,
    expected_warning,
):
    service = _service(tmp_path / 'project-root')
    service.project_config = SimpleNamespace(
        svn=SimpleNamespace(root=None),
        external_provider_config=SimpleNamespace(
            enabled=True,
            transport_enabled=True,
            provider_name='future_external',
            model_name='backend-model',
            allowed_providers=['future_external'],
            allowed_models=['backend-model'],
            env=SimpleNamespace(api_key_env_var='QWENPAW_RAG_API_KEY'),
            base_url='http://127.0.0.1:8765/v1/chat/completions',
        ),
    )
    service.config = service.project_config
    workspace = _workspace(service)
    captured = {'context_calls': 0, 'answer_calls': 0, 'transport_calls': 0}
    context_payload = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-live',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'source_type': 'doc_knowledge',
                'text': 'combat damage formula',
                'score': 3.0,
                'rank': 1,
                'citation_id': 'citation-001',
            }
        ],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-live',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
            }
        ],
    }

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        captured['context_calls'] += 1
        return context_payload

    original_build_answer = answer_module.build_rag_answer_with_service_config

    def _build_answer(query, context, service_config, **kwargs):
        captured['answer_calls'] += 1
        if captured['answer_calls'] == 1:
            service.project_config = SimpleNamespace(
                svn=SimpleNamespace(root=None),
                external_provider_config=SimpleNamespace(**updated_external_config),
            )
            service.config = service.project_config
            service.config_generation = kwargs['expected_generation'] + 1
            raise RagAnswerConfigGenerationChangedError('generation changed before provider selection')
        return original_build_answer(query, context, service_config, **kwargs)

    def _forbid_transport(*args, **kwargs):
        captured['transport_calls'] += 1
        raise AssertionError('hot-reload kill switch should prevent external transport calls')

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)
    monkeypatch.setattr(ExternalRagModelHttpTransport, '__call__', _forbid_transport)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'insufficient_context'
    assert expected_warning in response.json()['warnings']
    assert 'Model client output was not grounded in the provided context.' in response.json()['warnings']
    assert captured['context_calls'] == 2
    assert captured['answer_calls'] == 2
    assert captured['transport_calls'] == 0



def test_rag_answer_router_ignores_provider_field_in_request_body(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    context_payload = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-001',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [
            {
                'chunk_id': 'chunk-001',
                'source_type': 'doc_knowledge',
                'text': 'combat damage formula',
                'score': 3.0,
                'rank': 1,
                'citation_id': 'citation-001',
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

    async def _get_agent(_request):
        return workspace

    def _build_context(*args, **kwargs):
        return context_payload

    def _build_answer(query, context, service_config, **kwargs):
        captured['query'] = query
        captured['context'] = context
        captured['service_config'] = service_config
        return {
            'mode': 'answer',
            'answer': 'Grounded answer',
            'release_id': 'release-001',
            'citations': list(context['citations']),
            'warnings': [],
        }

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)
    monkeypatch.setattr(rag_router_module, 'build_rag_answer_with_service_config', _build_answer)
    monkeypatch.setattr(
        rag_router_module,
        'get_rag_model_client',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('router must not call get_rag_model_client directly')),
        raising=False,
    )

    with TestClient(_build_app()) as client:
        response = client.post(
            '/api/game/knowledge/rag/answer',
            json={
                'query': 'damage',
                'provider': 'disabled',
                'model': 'ignored-model',
                'api_key': 'ignored-secret',
                'provider_hint': 'ignored-hint',
                'service_config': {'rag_model_provider': 'disabled'},
            },
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'answer'
    assert captured['query'] == 'damage'
    assert captured['context'] is context_payload
    assert captured['service_config'] is workspace.game_service



def test_rag_answer_router_returns_no_current_release_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        rag_router_module,
        'build_current_release_context',
        lambda *args, **kwargs: {
            'mode': 'no_current_release',
            'query': 'damage',
            'release_id': None,
            'built_at': None,
            'chunks': [],
            'citations': [],
        },
    )
    monkeypatch.setattr(
        rag_router_module,
        'build_rag_answer_with_service_config',
        lambda query, context, service_config, **kwargs: {
            'mode': 'no_current_release',
            'answer': '',
            'release_id': None,
            'citations': [],
            'warnings': ['No current knowledge release is set.'],
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_current_release'
    assert response.json()['release_id'] is None



def test_rag_answer_router_returns_insufficient_context_for_blank_query(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        rag_router_module,
        'build_current_release_context',
        lambda *args, **kwargs: {
            'mode': 'context',
            'query': '',
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [],
            'citations': [],
        },
    )
    monkeypatch.setattr(
        rag_router_module,
        'build_rag_answer_with_service_config',
        lambda query, context, service_config, **kwargs: {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': 'release-001',
            'citations': [],
            'warnings': ['Query is blank after trimming.'],
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': '   '})

    assert response.status_code == 200
    assert response.json()['mode'] == 'insufficient_context'
    assert response.json()['warnings'] == ['Query is blank after trimming.']



def test_rag_answer_router_uses_only_context_citations(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    context_payload = {
        'mode': 'context',
        'query': 'damage',
        'release_id': 'release-001',
        'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
        'chunks': [],
        'citations': [
            {
                'citation_id': 'citation-001',
                'release_id': 'release-001',
                'source_type': 'doc_knowledge',
                'artifact_path': 'indexes/doc_knowledge.jsonl',
                'source_path': 'Docs/Combat.md',
                'title': 'Combat Overview',
                'row': 1,
                'source_hash': 'sha256:doc',
            }
        ],
    }

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', lambda *args, **kwargs: context_payload)
    monkeypatch.setattr(
        rag_router_module,
        'build_rag_answer_with_service_config',
        lambda query, context, service_config, **kwargs: {
            'mode': 'answer',
            'answer': 'Grounded answer',
            'release_id': 'release-001',
            'citations': list(context['citations']),
            'warnings': [],
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['citations'] == context_payload['citations']



def test_rag_answer_router_rejects_invalid_max_chunks():
    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage', 'max_chunks': 0, 'max_chars': 12000})

    assert response.status_code == 422



def test_rag_answer_router_rejects_invalid_max_chars():
    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage', 'max_chunks': 8, 'max_chars': 999})

    assert response.status_code == 422



def test_rag_answer_router_is_read_only_and_does_not_read_files(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        rag_router_module,
        'build_current_release_context',
        lambda *args, **kwargs: {
            'mode': 'context',
            'query': 'damage',
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'chunks': [],
            'citations': [],
        },
    )
    monkeypatch.setattr(
        rag_router_module,
        'build_rag_answer_with_service_config',
        lambda query, context, service_config, **kwargs: {
            'mode': 'insufficient_context',
            'answer': '',
            'release_id': 'release-001',
            'citations': [],
            'warnings': [],
        },
    )

    def _forbid_read(*args, **kwargs):
        raise AssertionError('router must not read files directly')

    def _forbid_write(*args, **kwargs):
        raise AssertionError('router must be read-only')

    monkeypatch.setattr(Path, 'read_text', _forbid_read)
    monkeypatch.setattr(Path, 'write_text', _forbid_write)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_write)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/answer', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'insufficient_context'
