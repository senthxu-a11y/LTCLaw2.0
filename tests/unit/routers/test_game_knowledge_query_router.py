from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_query as query_router_module
from ltclaw_gy_x.app.routers.game_knowledge_query import router


_CAPABILITY_UNSET = object()


def _build_app(capabilities=_CAPABILITY_UNSET):
    app = FastAPI()
    if capabilities is not _CAPABILITY_UNSET:
        app.state.capabilities = capabilities
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


def test_query_router_forwards_project_root_and_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _query(project_root, query, *, top_k, mode):
        captured['project_root'] = project_root
        captured['query'] = query
        captured['top_k'] = top_k
        captured['mode'] = mode
        return {
            'mode': 'current_release_keyword',
            'query': query,
            'top_k': top_k,
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'results': [
                {
                    'source_type': 'doc_knowledge',
                    'source_path': 'Docs/Combat.md',
                    'release_id': 'release-001',
                    'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
                    'score': 3.0,
                    'title': 'Combat Overview',
                    'summary': 'damage formula design',
                    'tags': [],
                }
            ],
            'count': 1,
        }

    monkeypatch.setattr(query_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(query_router_module, 'query_current_release', _query)

    with TestClient(_build_app()) as client:
        response = client.post(
            '/api/game/knowledge/query',
            json={'query': 'damage', 'top_k': 5, 'mode': 'hybrid'},
        )

    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['results'][0]['source_type'] == 'doc_knowledge'
    assert captured == {
        'project_root': tmp_path / 'project-root',
        'query': 'damage',
        'top_k': 5,
        'mode': 'hybrid',
    }


def test_query_router_returns_no_current_release_payload(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(query_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(
        query_router_module,
        'query_current_release',
        lambda *args, **kwargs: {
            'mode': 'no_current_release',
            'query': 'damage',
            'top_k': 10,
            'release_id': None,
            'built_at': None,
            'results': [],
            'count': 0,
        },
    )

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/query', json={'query': 'damage'})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_current_release'
    assert response.json()['results'] == []


def test_query_router_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(query_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        response = client.post('/api/game/knowledge/query', json={'query': 'damage'})

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'


def test_query_router_requires_knowledge_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _query(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('query should be blocked before service call')

    monkeypatch.setattr(query_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(query_router_module, 'query_current_release', _query)

    with TestClient(_build_app(capabilities=set())) as client:
        response = client.post('/api/game/knowledge/query', json={'query': 'damage'})

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.read'
    assert called is False


def test_query_router_allows_knowledge_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _query(project_root, query, *, top_k, mode):
        captured['project_root'] = project_root
        captured['query'] = query
        captured['top_k'] = top_k
        captured['mode'] = mode
        return {
            'mode': 'current_release_keyword',
            'query': query,
            'top_k': top_k,
            'release_id': 'release-001',
            'built_at': datetime(2026, 1, 1, tzinfo=timezone.utc),
            'results': [],
            'count': 0,
        }

    monkeypatch.setattr(query_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(query_router_module, 'query_current_release', _query)

    with TestClient(_build_app(capabilities={'knowledge.read'})) as client:
        response = client.post('/api/game/knowledge/query', json={'query': 'damage'})

    assert response.status_code == 200
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['query'] == 'damage'
