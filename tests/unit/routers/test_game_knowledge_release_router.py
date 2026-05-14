from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_knowledge_release as release_router_module
from ltclaw_gy_x.app.routers.game_knowledge_release import router
from ltclaw_gy_x.game.knowledge_release_service import KnowledgeReleaseBuildResult, KnowledgeReleasePrerequisiteError
from ltclaw_gy_x.game.models import (
    KnowledgeDocRef,
    KnowledgeIndexArtifact,
    KnowledgeManifest,
    KnowledgeMap,
    KnowledgeReleasePointer,
    KnowledgeSystem,
)


_CAPABILITY_UNSET = object()


def _build_app(workspace, capabilities=_CAPABILITY_UNSET):
    app = FastAPI()
    if capabilities is not _CAPABILITY_UNSET:
        app.state.capabilities = capabilities
    app.include_router(router, prefix='/api')
    return app


def _workspace(service):
    return SimpleNamespace(
        game_service=service,
        workspace_dir='/tmp/workspace',
        service_manager=SimpleNamespace(services=({'game_service': service} if service else {})),
    )


def _service(project_root: Path | None):
    return SimpleNamespace(
        _runtime_svn_root=(lambda: project_root),
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=SimpleNamespace(svn=SimpleNamespace(root=None)),
    )


def _manifest(release_id: str) -> KnowledgeManifest:
    return KnowledgeManifest(
        release_id=release_id,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source_snapshot_hash='sha256:snapshot',
        map_hash='sha256:map',
        systems=[KnowledgeSystem(system_id='combat', title='Combat')],
    )


def _knowledge_map(release_id: str) -> KnowledgeMap:
    return KnowledgeMap(
        release_id=release_id,
        systems=[KnowledgeSystem(system_id='combat', title='Combat')],
        docs=[
            KnowledgeDocRef(
                doc_id='combat-doc',
                title='Combat Doc',
                source_path='Docs/Combat.md',
                source_hash='sha256:doc',
                system_id='combat',
            )
        ],
    )


def test_build_release_forwards_project_root_and_payload(monkeypatch, tmp_path):
    captured = {}
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _build(project_root, release_id, knowledge_map, **kwargs):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        captured['knowledge_map'] = knowledge_map
        captured['kwargs'] = kwargs
        return KnowledgeReleaseBuildResult(
            release_dir=tmp_path / 'release-001',
            manifest=_manifest('release-001'),
            knowledge_map=knowledge_map,
            artifacts={
                'doc_knowledge': KnowledgeIndexArtifact(
                    path='indexes/doc_knowledge.jsonl',
                    hash='sha256:index',
                    count=1,
                )
            },
            build_mode='strict',
            status='ready',
            map_source='provided',
            warnings=(),
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-001',
                'knowledge_map': _knowledge_map('release-001').model_dump(mode='json'),
                'release_notes': '# note\n',
            },
        )

    assert response.status_code == 200
    assert response.json()['release_dir'].endswith('release-001')
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['release_id'] == 'release-001'
    assert captured['knowledge_map'].release_id == 'release-001'
    assert captured['kwargs']['release_notes'] == '# note\n'
    assert response.json()['build_mode'] == 'strict'
    assert response.json()['status'] == 'ready'
    assert response.json()['map_source'] == 'provided'
    assert response.json()['warnings'] == []


def test_release_listing_and_lookup_endpoints_use_store(monkeypatch, tmp_path):
    manifest = _manifest('release-002')
    pointer = KnowledgeReleasePointer(
        release_id='release-002',
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    calls = []
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _list(project_root):
        calls.append(('list', project_root))
        return [manifest]

    def _current(project_root):
        calls.append(('current', project_root))
        return manifest

    def _set_current(project_root, release_id):
        calls.append(('set', project_root, release_id))
        return pointer

    def _load(project_root, release_id):
        calls.append(('manifest', project_root, release_id))
        return manifest

    monkeypatch.setattr(release_router_module, 'list_releases', _list)
    monkeypatch.setattr(release_router_module, 'get_current_release', _current)
    monkeypatch.setattr(release_router_module, 'set_current_release', _set_current)
    monkeypatch.setattr(release_router_module, 'load_manifest', _load)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        listed = client.get('/api/game/knowledge/releases')
        current = client.get('/api/game/knowledge/releases/current')
        updated = client.post('/api/game/knowledge/releases/release-002/current')
        detail = client.get('/api/game/knowledge/releases/release-002/manifest')

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert current.status_code == 200
    assert current.json()['release_id'] == 'release-002'
    assert updated.status_code == 200
    assert updated.json()['release_id'] == 'release-002'
    assert detail.status_code == 200
    assert detail.json()['release_id'] == 'release-002'
    assert calls == [
        ('list', tmp_path / 'project-root'),
        ('current', tmp_path / 'project-root'),
        ('set', tmp_path / 'project-root', 'release-002'),
        ('manifest', tmp_path / 'project-root', 'release-002'),
    ]


def test_build_release_requires_local_project_directory(monkeypatch):
    workspace = _workspace(_service(None))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-001',
                'knowledge_map': _knowledge_map('release-001').model_dump(mode='json'),
            },
        )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Local project directory not configured'


def test_build_release_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-001',
                'knowledge_map': _knowledge_map('release-001').model_dump(mode='json'),
            },
        )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'


def test_build_release_from_current_indexes_forwards_project_root_and_workspace(monkeypatch, tmp_path):
    captured = {}
    workspace = _workspace(_service(tmp_path / 'project-root'))
    workspace.workspace_dir = tmp_path / 'workspace-root'

    async def _get_agent(_request):
        return workspace

    def _build(project_root, workspace_dir, release_id, **kwargs):
        captured['project_root'] = project_root
        captured['workspace_dir'] = workspace_dir
        captured['release_id'] = release_id
        captured['kwargs'] = kwargs
        return KnowledgeReleaseBuildResult(
            release_dir=tmp_path / 'release-safe-001',
            manifest=_manifest('release-safe-001'),
            knowledge_map=_knowledge_map('release-safe-001'),
            artifacts={
                'doc_knowledge': KnowledgeIndexArtifact(
                    path='indexes/doc_knowledge.jsonl',
                    hash='sha256:index',
                    count=2,
                )
            },
            build_mode='bootstrap',
            status='bootstrap_warning',
            map_source='bootstrap_current_indexes',
            warnings=('Bootstrap release used current indexes.',),
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release_from_current_indexes', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build-from-current-indexes',
            json={
                'release_id': 'release-safe-001',
                'bootstrap': True,
                'release_notes': '# safe build\n',
                'candidate_ids': ['combat-doc'],
            },
        )

    assert response.status_code == 200
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['workspace_dir'] == tmp_path / 'workspace-root'
    assert captured['release_id'] == 'release-safe-001'
    assert captured['kwargs']['bootstrap'] is True
    assert captured['kwargs']['candidate_ids'] == ['combat-doc']
    assert captured['kwargs']['release_notes'] == '# safe build\n'
    assert response.json()['build_mode'] == 'bootstrap'
    assert response.json()['status'] == 'bootstrap_warning'
    assert response.json()['map_source'] == 'bootstrap_current_indexes'
    assert response.json()['warnings'] == ['Bootstrap release used current indexes.']


def test_build_release_from_current_indexes_returns_prerequisite_detail(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _build(*_args, **_kwargs):
        raise KnowledgeReleasePrerequisiteError(
            'No current indexes are available to build the first knowledge release'
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release_from_current_indexes', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build-from-current-indexes',
            json={'release_id': 'release-bootstrap-001'},
        )

    assert response.status_code == 400
    assert response.json()['detail'] == 'No current indexes are available to build the first knowledge release'


def test_build_release_requires_knowledge_build_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _build(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('build should be blocked before service call')

    monkeypatch.setattr(release_router_module, 'build_knowledge_release', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities=set())) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-guarded-001',
                'knowledge_map': _knowledge_map('release-guarded-001').model_dump(mode='json'),
            },
        )

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.build'
    assert called is False


def test_build_release_requires_injected_viewer_capabilities(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(request):
        request.state.capabilities = {'knowledge.read'}
        return workspace

    def _build(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('build should be blocked by injected viewer capabilities')

    monkeypatch.setattr(release_router_module, 'build_knowledge_release', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-viewer-001',
                'knowledge_map': _knowledge_map('release-viewer-001').model_dump(mode='json'),
            },
        )

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.build'
    assert called is False


def test_build_release_allows_knowledge_build_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build(project_root, release_id, knowledge_map, **kwargs):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        captured['knowledge_map'] = knowledge_map
        return KnowledgeReleaseBuildResult(
            release_dir=tmp_path / 'release-guarded-001',
            manifest=_manifest('release-guarded-001'),
            knowledge_map=knowledge_map,
            artifacts={},
            build_mode='strict',
            status='ready',
            map_source='provided',
            warnings=(),
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/releases/build',
            json={
                'release_id': 'release-guarded-001',
                'knowledge_map': _knowledge_map('release-guarded-001').model_dump(mode='json'),
            },
        )

    assert response.status_code == 200
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['release_id'] == 'release-guarded-001'


def test_build_release_from_current_indexes_requires_knowledge_build_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _build(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('build should be blocked before service call')

    monkeypatch.setattr(release_router_module, 'build_knowledge_release_from_current_indexes', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities=[])) as client:
        response = client.post(
            '/api/game/knowledge/releases/build-from-current-indexes',
            json={'release_id': 'release-safe-guarded-001'},
        )

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.build'
    assert called is False


def test_build_release_from_current_indexes_allows_knowledge_build_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build(project_root, workspace_dir, release_id, **kwargs):
        captured['project_root'] = project_root
        captured['workspace_dir'] = workspace_dir
        captured['release_id'] = release_id
        return KnowledgeReleaseBuildResult(
            release_dir=tmp_path / 'release-safe-guarded-001',
            manifest=_manifest('release-safe-guarded-001'),
            knowledge_map=_knowledge_map('release-safe-guarded-001'),
            artifacts={},
            build_mode='strict',
            status='ready',
            map_source='formal_map',
            warnings=(),
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release_from_current_indexes', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/releases/build-from-current-indexes',
            json={'release_id': 'release-safe-guarded-001'},
        )

    assert response.status_code == 200
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['release_id'] == 'release-safe-guarded-001'


def test_release_read_routes_require_knowledge_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    calls = []

    async def _get_agent(_request):
        return workspace

    def _blocked(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError('read route should be blocked before store call')

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', _blocked)
    monkeypatch.setattr(release_router_module, 'get_current_release', _blocked)
    monkeypatch.setattr(release_router_module, 'load_manifest', _blocked)

    with TestClient(_build_app(workspace, capabilities={'knowledge.publish'})) as client:
        listed = client.get('/api/game/knowledge/releases')
        current = client.get('/api/game/knowledge/releases/current')
        detail = client.get('/api/game/knowledge/releases/release-002/manifest')

    assert listed.status_code == 403
    assert listed.json()['detail'] == 'Missing capability: knowledge.read'
    assert current.status_code == 403
    assert current.json()['detail'] == 'Missing capability: knowledge.read'
    assert detail.status_code == 403
    assert detail.json()['detail'] == 'Missing capability: knowledge.read'
    assert calls == []


def test_release_read_routes_allow_knowledge_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    manifest = _manifest('release-002')
    calls = []

    async def _get_agent(_request):
        return workspace

    def _list(project_root):
        calls.append(('list', project_root))
        return [manifest]

    def _current(project_root):
        calls.append(('current', project_root))
        return manifest

    def _load(project_root, release_id):
        calls.append(('manifest', project_root, release_id))
        return manifest

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', _list)
    monkeypatch.setattr(release_router_module, 'get_current_release', _current)
    monkeypatch.setattr(release_router_module, 'load_manifest', _load)

    with TestClient(_build_app(workspace, capabilities={'knowledge.read'})) as client:
        listed = client.get('/api/game/knowledge/releases')
        current = client.get('/api/game/knowledge/releases/current')
        detail = client.get('/api/game/knowledge/releases/release-002/manifest')

    assert listed.status_code == 200
    assert current.status_code == 200
    assert detail.status_code == 200
    assert calls == [
        ('list', tmp_path / 'project-root'),
        ('current', tmp_path / 'project-root'),
        ('manifest', tmp_path / 'project-root', 'release-002'),
    ]


def test_set_current_release_requires_knowledge_publish_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _set_current(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('publish should be blocked before store call')

    monkeypatch.setattr(release_router_module, 'set_current_release', _set_current)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/releases/release-002/current')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.publish'
    assert called is False


def test_set_current_release_allows_knowledge_publish_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    pointer = KnowledgeReleasePointer(
        release_id='release-002',
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    async def _get_agent(_request):
        return workspace

    def _set_current(project_root, release_id):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return pointer

    monkeypatch.setattr(release_router_module, 'set_current_release', _set_current)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.publish'})) as client:
        response = client.post('/api/game/knowledge/releases/release-002/current')

    assert response.status_code == 200
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': 'release-002'}


def test_set_current_release_allows_injected_wildcard_capabilities(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    pointer = KnowledgeReleasePointer(
        release_id='release-003',
        updated_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )

    async def _get_agent(request):
        request.state.capabilities = {'*'}
        return workspace

    def _set_current(project_root, release_id):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return pointer

    monkeypatch.setattr(release_router_module, 'set_current_release', _set_current)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post('/api/game/knowledge/releases/release-003/current')

    assert response.status_code == 200
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': 'release-003'}


def test_release_status_endpoint_returns_current_previous_and_history(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    release_old = _manifest('release-001').model_copy(update={'created_at': datetime(2026, 1, 1, tzinfo=timezone.utc)})
    release_current = _manifest('release-002').model_copy(update={'created_at': datetime(2026, 1, 2, tzinfo=timezone.utc)})
    release_newest = _manifest('release-003').model_copy(update={'created_at': datetime(2026, 1, 3, tzinfo=timezone.utc)})

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', lambda project_root: [release_old, release_newest, release_current])
    monkeypatch.setattr(release_router_module, 'get_current_release', lambda project_root: release_current)

    with TestClient(_build_app(workspace, capabilities={'knowledge.read'})) as client:
        response = client.get('/api/game/knowledge/releases/status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['current']['release_id'] == 'release-002'
    assert payload['current']['label'] == 'current'
    assert payload['current']['is_current'] is True
    assert payload['previous']['release_id'] == 'release-001'
    assert [item['release_id'] for item in payload['history']] == ['release-003', 'release-002', 'release-001']
    assert [item['is_current'] for item in payload['history']] == [False, True, False]


def test_release_status_endpoint_is_safe_when_no_previous_release(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    release_current = _manifest('release-001')

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', lambda project_root: [release_current])
    monkeypatch.setattr(release_router_module, 'get_current_release', lambda project_root: release_current)

    with TestClient(_build_app(workspace, capabilities={'knowledge.read'})) as client:
        response = client.get('/api/game/knowledge/releases/status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['current']['release_id'] == 'release-001'
    assert payload['previous'] is None
    assert len(payload['history']) == 1


def test_release_status_endpoint_requires_knowledge_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _list(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('status read should be blocked before store call')

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', _list)

    with TestClient(_build_app(workspace, capabilities=set())) as client:
        response = client.get('/api/game/knowledge/releases/status')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.read'
    assert called is False


def test_release_status_endpoint_hides_internal_metadata_error_details(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _list(project_root):
        raise ValueError(f'invalid metadata under {tmp_path / "project-root" / "secret"}')

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(release_router_module, 'list_releases', _list)

    with TestClient(_build_app(workspace, capabilities={'knowledge.read'})) as client:
        response = client.get('/api/game/knowledge/releases/status')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Knowledge release status is unavailable'
    assert str(tmp_path) not in response.json()['detail']


def test_set_current_release_returns_404_for_missing_release(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _set_current(project_root, release_id):
        raise release_router_module.KnowledgeReleaseNotFoundError(f'Knowledge release manifest not found: {release_id}')

    monkeypatch.setattr(release_router_module, 'set_current_release', _set_current)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.publish'})) as client:
        response = client.post('/api/game/knowledge/releases/release-missing/current')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Knowledge release manifest not found: release-missing'
