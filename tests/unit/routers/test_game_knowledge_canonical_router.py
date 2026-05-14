from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_canonical as canonical_router_module
from ltclaw_gy_x.app.routers.game_knowledge_canonical import router
from ltclaw_gy_x.game.models import FieldConfidence, FieldInfo, TableIndex
from ltclaw_gy_x.game.paths import get_project_raw_table_indexes_path


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
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=SimpleNamespace(svn=SimpleNamespace(root=None)),
        model_router=SimpleNamespace(call_model=pytest.fail),
    )


def _table_index() -> TableIndex:
    return TableIndex(
        table_name='HeroTable',
        source_path='Tables/HeroTable.csv',
        source_hash='sha256:hero-table',
        svn_revision=7,
        system='combat',
        row_count=1,
        primary_key='ID',
        ai_summary='hero schema',
        ai_summary_confidence=0.9,
        fields=[
            FieldInfo(name='ID', type='int', description='identifier', confidence=FieldConfidence.CONFIRMED),
            FieldInfo(name='Hero Name', type='str', description='display name', confidence=FieldConfidence.HIGH_AI),
        ],
        last_indexed_at=datetime(2026, 1, 1, 12, 0, 0),
        indexer_model='test-model',
    )


def _write_raw_indexes(project_root: Path, tables=None) -> None:
    raw_indexes_path = get_project_raw_table_indexes_path(project_root)
    raw_indexes_path.parent.mkdir(parents=True, exist_ok=True)
    raw_indexes_path.write_text(
        json.dumps({'version': '1.0', 'tables': tables if tables is not None else [_table_index().model_dump(mode='json')]}, indent=2),
        encoding='utf-8',
    )


def test_rebuild_canonical_tables_rule_only_succeeds_without_llm(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_raw_indexes(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'tables', 'rule_only': True, 'force': False},
        )

    assert response.status_code == 200
    assert response.json() == {
        'success': True,
        'raw_table_index_count': 1,
        'canonical_table_count': 1,
        'written': ['HeroTable.json'],
        'errors': [],
        'warnings': [],
        'next_action': 'build_candidate_from_source',
    }


def test_rebuild_canonical_tables_requires_local_project_directory(monkeypatch):
    workspace = _workspace(_service(None))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'tables', 'rule_only': True, 'force': False},
        )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Local project directory not configured'


def test_rebuild_canonical_tables_rejects_unsupported_scope(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_raw_indexes(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'docs', 'rule_only': True, 'force': False},
        )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Only scope=tables is supported'


def test_rebuild_canonical_tables_rejects_rule_only_false(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_raw_indexes(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'tables', 'rule_only': False, 'force': False},
        )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Only rule_only=true is supported'


def test_rebuild_canonical_tables_returns_explicit_error_when_raw_indexes_are_missing(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True, exist_ok=True)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'tables', 'rule_only': True, 'force': False},
        )

    assert response.status_code == 200
    assert response.json() == {
        'success': False,
        'raw_table_index_count': 0,
        'canonical_table_count': 0,
        'written': [],
        'errors': [
            {
                'raw_index_file': 'table_indexes.json',
                'error': f'Raw table indexes file does not exist: {get_project_raw_table_indexes_path(project_root)}',
                'table_id': None,
            }
        ],
        'warnings': [],
        'next_action': 'build_candidate_from_source',
    }


def test_rebuild_canonical_tables_returns_partial_failure_shape_when_one_entry_is_broken(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    _write_raw_indexes(
        project_root,
        tables=[
            _table_index().model_dump(mode='json'),
            {'table_name': 'BrokenTable'},
        ],
    )
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(canonical_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(workspace, capabilities={'knowledge.build'})) as client:
        response = client.post(
            '/api/game/knowledge/canonical/rebuild',
            json={'scope': 'tables', 'rule_only': True, 'force': False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is False
    assert payload['raw_table_index_count'] == 2
    assert payload['canonical_table_count'] == 1
    assert payload['written'] == ['HeroTable.json']
    assert payload['warnings'] == []
    assert payload['next_action'] == 'build_candidate_from_source'
    assert len(payload['errors']) == 1
    assert payload['errors'][0]['raw_index_file'] == 'BrokenTable.json'
    assert payload['errors'][0]['table_id'] == 'BrokenTable'
    assert 'validation error' in payload['errors'][0]['error'].lower() or 'field required' in payload['errors'][0]['error'].lower()