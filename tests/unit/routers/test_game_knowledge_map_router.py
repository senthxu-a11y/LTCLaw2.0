from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_map as map_router_module
from ltclaw_gy_x.app.routers.game_knowledge_map import router
from ltclaw_gy_x.game.knowledge_release_store import CurrentKnowledgeReleaseNotSetError
from ltclaw_gy_x.game.models import KnowledgeMap, KnowledgeRelationship, KnowledgeTableRef


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


def _map(release_id: str = 'release-001') -> KnowledgeMap:
    return KnowledgeMap(
        release_id=release_id,
        tables=[
            KnowledgeTableRef(
                table_id='Table_Player',
                title='Player Table',
                source_path='Tables/Player.xlsx',
                source_hash='sha256:player',
                system_id='combat',
            )
        ],
        source_hash='sha256:map-source',
    )


def test_candidate_map_router_forwards_project_root(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_candidate(project_root, release_id=None):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return _map()

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_release', _build_candidate)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 200
    assert response.json()['mode'] == 'candidate_map'
    assert response.json()['map']['release_id'] == 'release-001'
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': None}


def test_candidate_map_router_returns_no_current_release_detail(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _build_candidate(_project_root, release_id=None):
        raise CurrentKnowledgeReleaseNotSetError('No current knowledge release is set')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_release', _build_candidate)

    with TestClient(_build_app(), raise_server_exceptions=False) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 404
    assert response.json()['detail'] == 'No current knowledge release is set'


def test_formal_map_router_returns_empty_state_when_missing(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', lambda _root: None)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 200
    assert response.json() == {
        'mode': 'no_formal_map',
        'map': None,
        'map_hash': None,
        'updated_at': None,
        'updated_by': None,
    }


def test_formal_map_router_returns_saved_record(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    record = SimpleNamespace(
        knowledge_map=_map(),
        map_hash='sha256:formal',
        updated_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        updated_by='lead',
    )

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', lambda _root: record)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 200
    assert response.json()['mode'] == 'formal_map'
    assert response.json()['map_hash'] == 'sha256:formal'
    assert response.json()['updated_by'] == 'lead'


def test_save_formal_map_router_accepts_map_alias(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    record = SimpleNamespace(
        knowledge_map=_map(),
        map_hash='sha256:saved',
        updated_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        updated_by='designer-1',
    )

    async def _get_agent(_request):
        return workspace

    def _save(project_root, knowledge_map, *, updated_by=None):
        captured['project_root'] = project_root
        captured['knowledge_map'] = knowledge_map
        captured['updated_by'] = updated_by
        return record

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'save_formal_knowledge_map', _save)

    with TestClient(_build_app()) as client:
        response = client.put(
            '/api/game/knowledge/map',
            json={'map': _map().model_dump(mode='json'), 'updated_by': 'designer-1'},
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'formal_map_saved'
    assert response.json()['map_hash'] == 'sha256:saved'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['knowledge_map'].release_id == 'release-001'
    assert captured['updated_by'] == 'designer-1'


def test_save_formal_map_router_rejects_invalid_relationship(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    knowledge_map = _map()
    knowledge_map.relationships = [
        KnowledgeRelationship(
            relationship_id='rel-bad',
            from_ref='table:Table_Player',
            to_ref='doc:missing',
            relation_type='documented_by',
            source_hash='sha256:rel',
        )
    ]

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(), raise_server_exceptions=False) as client:
        response = client.put('/api/game/knowledge/map', json={'map': knowledge_map.model_dump(mode='json')})

    assert response.status_code == 400
    assert 'Unknown relationship target' in response.json()['detail']


def test_save_formal_map_router_rejects_source_path_escape(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    knowledge_map = _map()
    knowledge_map.tables[0].source_path = 'C:/abs/path.xlsx'

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(), raise_server_exceptions=False) as client:
        response = client.put('/api/game/knowledge/map', json={'map': knowledge_map.model_dump(mode='json')})

    assert response.status_code == 400
    assert 'Invalid local project relative path' in response.json()['detail']


def test_formal_map_router_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'


def test_formal_map_router_requires_project_root(monkeypatch):
    workspace = _workspace(_service(None))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 400
    assert response.json()['detail'] == 'Local project directory not configured'


def test_candidate_map_router_requires_knowledge_map_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _build_candidate(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('candidate map read should be blocked before builder call')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_release', _build_candidate)

    with TestClient(_build_app(capabilities=set())) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.map.read'
    assert called is False


def test_candidate_map_router_allows_knowledge_map_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_candidate(project_root, release_id=None):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return _map()

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_release', _build_candidate)

    with TestClient(_build_app(capabilities={'knowledge.map.read'})) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 200
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': None}


def test_formal_map_router_requires_knowledge_map_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _load(_root):
        nonlocal called
        called = True
        raise AssertionError('formal map read should be blocked before store call')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', _load)

    with TestClient(_build_app(capabilities=set())) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.map.read'
    assert called is False


def test_formal_map_router_allows_knowledge_map_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    record = SimpleNamespace(
        knowledge_map=_map(),
        map_hash='sha256:formal',
        updated_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        updated_by='lead',
    )

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', lambda _root: record)

    with TestClient(_build_app(capabilities={'knowledge.map.read'})) as client:
        response = client.get('/api/game/knowledge/map')

    assert response.status_code == 200
    assert response.json()['mode'] == 'formal_map'
    assert response.json()['map_hash'] == 'sha256:formal'


def test_save_formal_map_router_requires_knowledge_map_edit_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _save(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('formal map save should be blocked before store call')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'save_formal_knowledge_map', _save)

    with TestClient(_build_app(capabilities=set())) as client:
        response = client.put('/api/game/knowledge/map', json={'map': _map().model_dump(mode='json')})

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.map.edit'
    assert called is False


def test_save_formal_map_router_allows_knowledge_map_edit_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    record = SimpleNamespace(
        knowledge_map=_map(),
        map_hash='sha256:saved',
        updated_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        updated_by='designer-1',
    )

    async def _get_agent(_request):
        return workspace

    def _save(project_root, knowledge_map, *, updated_by=None):
        captured['project_root'] = project_root
        captured['knowledge_map'] = knowledge_map
        captured['updated_by'] = updated_by
        return record

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'save_formal_knowledge_map', _save)

    with TestClient(_build_app(capabilities={'knowledge.map.edit'})) as client:
        response = client.put(
            '/api/game/knowledge/map',
            json={'map': _map().model_dump(mode='json'), 'updated_by': 'designer-1'},
        )

    assert response.status_code == 200
    assert response.json()['mode'] == 'formal_map_saved'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['knowledge_map'].release_id == 'release-001'
    assert captured['updated_by'] == 'designer-1'
