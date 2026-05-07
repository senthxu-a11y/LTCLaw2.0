from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_test_plans as test_plan_router_module
from ltclaw_gy_x.app.routers.game_knowledge_test_plans import router
from ltclaw_gy_x.game.models import WorkbenchTestPlan, WorkbenchTestPlanChange


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


def _plan(plan_id: str = 'plan-001') -> WorkbenchTestPlan:
    return WorkbenchTestPlan(
        id=plan_id,
        status='draft',
        title='Damage tuning',
        changes=[
            WorkbenchTestPlanChange(
                table='SkillTable',
                primary_key={'field': 'ID', 'value': '1029'},
                field='Damage',
                before='100',
                after='120',
                source_path='Tables/SkillTable.xlsx',
            )
        ],
        project_key='project-key',
        release_scope='not_in_release',
        test_scope='local_workbench',
        source_refs=['Tables/SkillTable.xlsx'],
        created_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        created_by='planner',
    )


def test_create_test_plan_forwards_project_root_and_payload(monkeypatch, tmp_path):
    captured = {}
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _append(project_root, plan):
        captured['project_root'] = project_root
        captured['plan'] = plan
        return _plan('plan-002')

    monkeypatch.setattr(test_plan_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(test_plan_router_module, 'append_test_plan', _append)

    with TestClient(_build_app(workspace)) as client:
        response = client.post('/api/game/knowledge/test-plans', json=_plan().model_dump(mode='json'))

    assert response.status_code == 200
    assert response.json()['id'] == 'plan-002'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['plan'].id == 'plan-001'


def test_list_test_plans_forwards_project_root(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    calls = []

    async def _get_agent(_request):
        return workspace

    def _list(project_root):
        calls.append(project_root)
        return [_plan()]

    monkeypatch.setattr(test_plan_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(test_plan_router_module, 'list_test_plans', _list)

    with TestClient(_build_app(workspace)) as client:
        response = client.get('/api/game/knowledge/test-plans')

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert calls == [tmp_path / 'project-root']


def test_test_plan_router_requires_game_service(monkeypatch):
    workspace = _workspace(None)

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(test_plan_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace)) as client:
        response = client.get('/api/game/knowledge/test-plans')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Game service not available'
