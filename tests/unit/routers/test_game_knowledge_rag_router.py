from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

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
    return SimpleNamespace(
        _runtime_svn_root=(lambda: project_root),
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=SimpleNamespace(svn=SimpleNamespace(root=None)),
    )



def test_rag_context_router_forwards_project_root_and_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_context(project_root, query, *, max_chunks, max_chars):
        captured['project_root'] = project_root
        captured['query'] = query
        captured['max_chunks'] = max_chunks
        captured['max_chars'] = max_chars
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
                    'source_hash': 'sha256:doc',
                }
            ],
        }

    monkeypatch.setattr(rag_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(rag_router_module, 'build_current_release_context', _build_context)

    with TestClient(_build_app()) as client:
        response = client.post(
            '/api/game/knowledge/rag/context',
            json={'query': 'damage', 'max_chunks': 5, 'max_chars': 4096},
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'context'
    assert response.json()['chunks'][0]['source_type'] == 'doc_knowledge'
    assert captured == {
        'project_root': tmp_path / 'project-root',
        'query': 'damage',
        'max_chunks': 5,
        'max_chars': 4096,
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
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/rag/context', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_current_release'
    assert response.json()['chunks'] == []
    assert response.json()['citations'] == []



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

    def _build_answer(query, context, service_config):
        captured['answer_query'] = query
        captured['answer_context'] = context
        captured['service_config'] = service_config
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

    def _build_answer(query, context, service_config):
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
        lambda query, context, service_config: {
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
        lambda query, context, service_config: {
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
        lambda query, context, service_config: {
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
        lambda query, context, service_config: {
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
