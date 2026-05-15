from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_map as map_router_module
from ltclaw_gy_x.app.routers.game_knowledge_map import router
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config


def _build_app(capabilities=None):
    app = FastAPI()
    if capabilities is not None:
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


def _create_minimal_project(project_root: Path) -> None:
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text('ID,Name,HP,Attack\n1,HeroA,100,20\n', encoding='utf-8')
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.csv'],
            exclude=['**/~$*', '**/.backup/**'],
            header_row=1,
            primary_key_candidates=['ID'],
        ),
    )


def _await_job_terminal_state(client: TestClient, job_id: str, *, timeout_seconds: float = 5.0):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f'/api/game/knowledge/map/cold-start-jobs/{job_id}')
        assert response.status_code == 200
        payload = response.json()
        if payload['status'] in {'succeeded', 'failed', 'cancelled'}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f'cold-start job did not reach terminal state: {job_id}')


def test_source_latest_router_returns_404_when_missing(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'}), raise_server_exceptions=False) as client:
        response = client.get('/api/game/knowledge/map/candidate/source-latest')

    assert response.status_code == 404
    assert response.json()['detail'] == 'No source candidate map is available'


def test_source_latest_router_returns_saved_cold_start_candidate(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _create_minimal_project(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read', 'knowledge.candidate.write'})) as client:
        create_response = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})
        assert create_response.status_code == 200
        job_id = create_response.json()['job']['job_id']

        result = _await_job_terminal_state(client, job_id)
        assert result['status'] == 'succeeded'

        response = client.get('/api/game/knowledge/map/candidate/source-latest')

    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'candidate_map'
    assert payload['candidate_source'] == 'source_canonical'
    assert payload['candidate_table_count'] == 1
    assert payload['candidate_refs'] == ['table:HeroTable']
    assert payload['map']['tables'][0]['table_id'] == 'HeroTable'
    assert payload['diff_review']['candidate_source'] == 'source_canonical'