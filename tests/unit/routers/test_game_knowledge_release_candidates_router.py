from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_release_candidates as candidate_router_module
from ltclaw_gy_x.app.routers.game_knowledge_release_candidates import router
from ltclaw_gy_x.game.models import ReleaseCandidate


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


def _candidate(candidate_id: str = 'candidate-001') -> ReleaseCandidate:
    return ReleaseCandidate(
        candidate_id=candidate_id,
        test_plan_id='plan-001',
        status='pending',
        title='Damage tuning candidate',
        project_key='project-key',
        source_refs=['Tables/SkillTable.xlsx'],
        source_hash='sha256:test-plan',
        created_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
    )


def test_create_release_candidate_forwards_project_root_and_payload(monkeypatch, tmp_path):
    captured = {}
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _append(project_root, candidate):
        captured['project_root'] = project_root
        captured['candidate'] = candidate
        return _candidate('candidate-002')

    monkeypatch.setattr(candidate_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(candidate_router_module, 'append_release_candidate', _append)

    with TestClient(_build_app(workspace)) as client:
        response = client.post('/api/game/knowledge/release-candidates', json=_candidate().model_dump(mode='json'))

    assert response.status_code == 200
    assert response.json()['candidate_id'] == 'candidate-002'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['candidate'].candidate_id == 'candidate-001'


def test_list_release_candidates_forwards_project_root(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _list(project_root, *, status=None, selected=None, test_plan_id=None):
        captured['project_root'] = project_root
        captured['status'] = status
        captured['selected'] = selected
        captured['test_plan_id'] = test_plan_id
        return [_candidate()]

    monkeypatch.setattr(candidate_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(candidate_router_module, 'list_release_candidates', _list)

    with TestClient(_build_app(workspace)) as client:
        response = client.get(
            '/api/game/knowledge/release-candidates',
            params={'status': 'accepted', 'selected': 'true', 'test_plan_id': 'plan-002'},
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert captured == {
        'project_root': tmp_path / 'project-root',
        'status': 'accepted',
        'selected': True,
        'test_plan_id': 'plan-002',
    }


def test_release_candidate_router_rejects_invalid_status(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(candidate_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.get('/api/game/knowledge/release-candidates', params={'status': 'draft'})

    assert response.status_code == 400
    assert 'status must be one of' in response.json()['detail']


def test_release_candidate_router_rejects_invalid_selected(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(candidate_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.get('/api/game/knowledge/release-candidates', params={'selected': 'not-a-bool'})

    assert response.status_code == 422



def test_release_candidate_router_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(candidate_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.get('/api/game/knowledge/release-candidates')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'
