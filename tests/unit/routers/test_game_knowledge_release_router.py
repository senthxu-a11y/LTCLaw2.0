from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_knowledge_release as release_router_module
from ltclaw_gy_x.app.routers.game_knowledge_release import router
from ltclaw_gy_x.game.knowledge_release_service import KnowledgeReleaseBuildResult
from ltclaw_gy_x.game.models import (
    KnowledgeDocRef,
    KnowledgeIndexArtifact,
    KnowledgeManifest,
    KnowledgeMap,
    KnowledgeReleasePointer,
    KnowledgeSystem,
)


def _build_app(workspace):
    app = FastAPI()
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
                    sha256='sha256:index',
                    count=1,
                )
            },
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
                    sha256='sha256:index',
                    count=2,
                )
            },
        )

    monkeypatch.setattr(release_router_module, 'build_knowledge_release_from_current_indexes', _build)
    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            '/api/game/knowledge/releases/build-from-current-indexes',
            json={
                'release_id': 'release-safe-001',
                'release_notes': '# safe build\n',
                'candidate_ids': ['combat-doc'],
            },
        )

    assert response.status_code == 200
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['workspace_dir'] == tmp_path / 'workspace-root'
    assert captured['release_id'] == 'release-safe-001'
    assert captured['kwargs']['candidate_ids'] == ['combat-doc']
    assert captured['kwargs']['release_notes'] == '# safe build\n'