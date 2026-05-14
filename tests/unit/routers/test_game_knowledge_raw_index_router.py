from __future__ import annotations

import codecs
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_raw_index as raw_index_router_module
from ltclaw_gy_x.app.routers.game_knowledge_raw_index import router
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.paths import (
    get_project_raw_table_index_path,
    get_project_raw_table_indexes_path,
)


def _build_app(workspace, capabilities=None):
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
        user_config=SimpleNamespace(svn_local_root=str(project_root) if project_root is not None else None),
        project_config=None,
        model_router=SimpleNamespace(call_model=pytest.fail),
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_csv(path: Path, content: str, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if bom:
        path.write_bytes(codecs.BOM_UTF8 + content.encode('utf-8'))
    else:
        path.write_text(content, encoding='utf-8')


def _save_tables_config(project_root: Path, header_row: int = 1) -> None:
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.csv'],
            header_row=header_row,
            primary_key_candidates=['ID', 'Id', 'id'],
        ),
    )


def test_raw_index_rebuild_generates_minimal_project_table_index(monkeypatch, tmp_path):
    sample_root = _repo_root() / 'examples' / 'minimal_project'
    project_root = tmp_path / 'minimal_project'
    shutil.copytree(sample_root, project_root)
    _save_tables_config(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(raw_index_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/raw-index/rebuild', json={'scope': 'tables', 'rule_only': True})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        'success': True,
        'raw_table_index_count': 1,
        'indexed_tables': [
            {
                'table_id': 'HeroTable',
                'source_path': 'Tables/HeroTable.csv',
                'row_count': 1,
                'field_count': 4,
                'primary_key': 'ID',
            }
        ],
        'errors': [],
        'next_action': 'run_canonical_rebuild',
    }
    single_index_path = get_project_raw_table_index_path(project_root, 'HeroTable')
    aggregate_path = get_project_raw_table_indexes_path(project_root)
    assert single_index_path.exists()
    assert aggregate_path.exists()
    aggregate_payload = json.loads(aggregate_path.read_text(encoding='utf-8'))
    assert len(aggregate_payload['tables']) == 1


def test_raw_index_rebuild_supports_utf8_and_utf8_bom_csv(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_csv(project_root / 'Tables' / 'Utf8.csv', 'ID,Name\n1,英雄A\n')
    _write_csv(project_root / 'Tables' / 'Utf8Bom.csv', 'ID,Name\n2,英雄B\n', bom=True)
    _save_tables_config(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(raw_index_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/raw-index/rebuild', json={'scope': 'tables', 'rule_only': True})

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['raw_table_index_count'] == 2
    indexed = {item['table_id']: item for item in payload['indexed_tables']}
    assert indexed['Utf8']['primary_key'] == 'ID'
    assert indexed['Utf8Bom']['primary_key'] == 'ID'


def test_raw_index_rebuild_returns_file_level_errors_without_blocking_other_tables(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_csv(project_root / 'Tables' / 'HeroTable.csv', 'ID,Name\n1,HeroA\n')
    _write_csv(project_root / 'Tables' / 'Empty.csv', '')
    _write_csv(project_root / 'Tables' / 'NoHeader.csv', ',,,\n1,2,3,4\n')
    _save_tables_config(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(raw_index_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/raw-index/rebuild', json={'scope': 'tables', 'rule_only': True})

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['raw_table_index_count'] == 1
    assert payload['indexed_tables'][0]['table_id'] == 'HeroTable'
    errors = {item['source_path']: item['error'] for item in payload['errors']}
    assert errors['Tables/Empty.csv'] == '文件为空: ' + str(project_root / 'Tables' / 'Empty.csv')
    assert errors['Tables/NoHeader.csv'] == '未找到有效表头: ' + str(project_root / 'Tables' / 'NoHeader.csv')


def test_raw_index_rebuild_returns_file_error_when_header_row_is_invalid(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_csv(project_root / 'Tables' / 'HeroTable.csv', 'ID,Name\n1,HeroA\n')
    _save_tables_config(project_root, header_row=2)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(raw_index_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/raw-index/rebuild', json={'scope': 'tables', 'rule_only': True})

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is False
    assert payload['raw_table_index_count'] == 0
    assert payload['indexed_tables'] == []
    assert payload['errors'] == [
        {
            'source_path': 'Tables/HeroTable.csv',
            'error': '文件行数不足: ' + str(project_root / 'Tables' / 'HeroTable.csv'),
        }
    ]


def test_raw_index_rebuild_rejects_unsupported_scope(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir()
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(raw_index_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post('/api/game/knowledge/raw-index/rebuild', json={'scope': 'docs', 'rule_only': True})

    assert response.status_code == 400
    assert response.json()['detail'] == 'Only scope=tables is supported'