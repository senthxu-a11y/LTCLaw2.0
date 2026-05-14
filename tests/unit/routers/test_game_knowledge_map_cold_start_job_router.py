from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_map as map_router_module
from ltclaw_gy_x.app.routers.game_knowledge_map import router
from ltclaw_gy_x.game import cold_start_job as cold_start_job_module
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.paths import (
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_runtime_build_job_path,
)


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


def test_cold_start_job_succeeds_and_get_restores_persisted_state(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _create_minimal_project(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        create_response = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})

        assert create_response.status_code == 200
        create_payload = create_response.json()
        assert create_payload['reused_existing'] is False

        job_id = create_payload['job']['job_id']
        result = _await_job_terminal_state(client, job_id)

    job_path = get_project_runtime_build_job_path(project_root, job_id)
    assert job_path.exists()
    assert result['status'] == 'succeeded'
    assert result['stage'] == 'done'
    assert result['counts'] == {
        'discovered_table_count': 1,
        'raw_table_index_count': 1,
        'canonical_table_count': 1,
        'candidate_table_count': 1,
    }
    assert result['candidate_refs'] == ['table:HeroTable']
    assert result['next_action'] == 'review_candidate_map'
    assert result['partial_outputs']['raw_table_indexes_path'].endswith('table_indexes.json')
    assert result['partial_outputs']['canonical_tables_dir'].endswith('/indexes/canonical/tables')
    assert result['partial_outputs']['candidate_mode'] == 'candidate_map'
    assert result['partial_outputs']['diff_review']['candidate_source'] == 'source_canonical'
    assert not get_project_formal_map_canonical_path(project_root).exists()
    assert not get_project_current_release_path(project_root).exists()

    with TestClient(_build_app()) as client:
        restore_response = client.get(f'/api/game/knowledge/map/cold-start-jobs/{job_id}')

    assert restore_response.status_code == 200
    assert restore_response.json()['job_id'] == job_id
    assert restore_response.json()['status'] == 'succeeded'


def test_cold_start_job_cancel_marks_status_cancelled(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _create_minimal_project(project_root)
    workspace = _workspace(_service(project_root))
    original_discover = cold_start_job_module.discover_table_sources

    async def _get_agent(_request):
        return workspace

    def _slow_discover(project_root_arg, tables_config):
        time.sleep(0.3)
        return original_discover(project_root_arg, tables_config)

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(cold_start_job_module, 'discover_table_sources', _slow_discover)

    with TestClient(_build_app()) as client:
        create_response = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})
        job_id = create_response.json()['job']['job_id']

        cancel_response = client.post(f'/api/game/knowledge/map/cold-start-jobs/{job_id}/cancel')

        assert cancel_response.status_code == 200
        assert cancel_response.json()['status'] == 'cancelled'

        result = _await_job_terminal_state(client, job_id)

    assert result['status'] == 'cancelled'
    assert result['stage'] == 'cancelled'


def test_cold_start_job_reuses_existing_running_job(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _create_minimal_project(project_root)
    workspace = _workspace(_service(project_root))
    original_discover = cold_start_job_module.discover_table_sources

    async def _get_agent(_request):
        return workspace

    def _slow_discover(project_root_arg, tables_config):
        time.sleep(0.3)
        return original_discover(project_root_arg, tables_config)

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(cold_start_job_module, 'discover_table_sources', _slow_discover)

    with TestClient(_build_app()) as client:
        first = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})
        second = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()['reused_existing'] is True
        assert second.json()['job']['job_id'] == first.json()['job']['job_id']

        client.post(f"/api/game/knowledge/map/cold-start-jobs/{first.json()['job']['job_id']}/cancel")
        result = _await_job_terminal_state(client, first.json()['job']['job_id'])

    assert result['status'] == 'cancelled'


def test_cold_start_job_failure_keeps_stage_error_and_next_action(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True, exist_ok=True)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app()) as client:
        create_response = client.post('/api/game/knowledge/map/cold-start-jobs', json={'timeout_seconds': 30})
        job_id = create_response.json()['job']['job_id']
        result = _await_job_terminal_state(client, job_id)

    assert result['status'] == 'failed'
    assert result['stage'] == 'discovering_sources'
    assert result['next_action'] == 'configure_tables_source'
    assert result['errors'][0]['stage'] == 'discovering_sources'
    assert result['errors'][0]['error'] == 'tables_source_not_configured'