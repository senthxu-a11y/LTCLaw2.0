from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.routers import game_knowledge_map as map_router_module
from ltclaw_gy_x.app.routers.game_knowledge_map import router
from ltclaw_gy_x.game.knowledge_release_store import CurrentKnowledgeReleaseNotSetError
from ltclaw_gy_x.game.models import CanonicalField, CanonicalTableSchema, KnowledgeMap, KnowledgeMapCandidateResult, KnowledgeRelationship, KnowledgeTableRef, MapDiffReview
from ltclaw_gy_x.game.paths import (
    get_project_bundle_root,
    get_project_canonical_table_schema_path,
    get_project_canonical_tables_dir,
    get_project_raw_table_indexes_path,
    get_project_tables_source_path,
)


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


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def _write_tables_config(project_root: Path) -> None:
    path = get_project_tables_source_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'roots:\n  - Tables\ninclude:\n  - "**/*.csv"\nexclude: []\nheader_row: 1\nprimary_key_candidates:\n  - ID\n',
        encoding='utf-8',
    )


def _write_raw_indexes(project_root: Path, tables: list[dict]) -> None:
    _write_json(get_project_raw_table_indexes_path(project_root), {'version': '1.0', 'tables': tables})


def _write_canonical_table(project_root: Path, table_id: str = 'HeroTable') -> None:
    schema = CanonicalTableSchema(
        table_id=table_id,
        source_path=f'Tables/{table_id}.csv',
        source_hash=f'sha256:{table_id}',
        primary_key='ID',
        fields=[
            CanonicalField(
                raw_header='ID',
                canonical_header='id',
                aliases=['ID', 'id'],
                semantic_type='id',
                description='identifier',
                confidence=1.0,
                confirmed=True,
                source='raw_index_rule',
                raw_type='int',
            )
        ],
        updated_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    _write_json(get_project_canonical_table_schema_path(project_root, table_id), schema.model_dump(mode='json'))


def test_candidate_map_router_forwards_project_root(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_candidate(project_root, release_id=None):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return KnowledgeMapCandidateResult(
            mode='candidate_map',
            map=_map(),
            release_id='release-001',
            candidate_source='release_snapshot',
            is_formal_map=False,
            source_release_id='release-001',
            uses_existing_formal_map_as_hint=False,
            warnings=['compat review'],
        )

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_result_from_release', _build_candidate)

    with TestClient(_build_app()) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 200
    assert response.json()['mode'] == 'candidate_map'
    assert response.json()['map']['release_id'] == 'release-001'
    assert response.json()['candidate_source'] == 'release_snapshot'
    assert response.json()['is_formal_map'] is False
    assert response.json()['source_release_id'] == 'release-001'
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': None}


def test_candidate_map_router_returns_no_current_release_detail(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    def _build_candidate(_project_root, release_id=None):
        raise CurrentKnowledgeReleaseNotSetError('No current knowledge release is set')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_result_from_release', _build_candidate)

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


def test_candidate_map_router_requires_knowledge_candidate_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _build_candidate(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('candidate map read should be blocked before builder call')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_result_from_release', _build_candidate)

    with TestClient(_build_app(capabilities=set())) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.candidate.read'
    assert called is False


def test_candidate_map_router_allows_knowledge_candidate_read_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}

    async def _get_agent(_request):
        return workspace

    def _build_candidate(project_root, release_id=None):
        captured['project_root'] = project_root
        captured['release_id'] = release_id
        return KnowledgeMapCandidateResult(
            mode='candidate_map',
            map=_map(),
            release_id='release-001',
            candidate_source='release_snapshot',
            is_formal_map=False,
            source_release_id='release-001',
            uses_existing_formal_map_as_hint=False,
            warnings=[],
        )

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_result_from_release', _build_candidate)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/candidate')

    assert response.status_code == 200
    assert captured == {'project_root': tmp_path / 'project-root', 'release_id': None}


def test_build_readiness_returns_project_root_missing_when_unconfigured(monkeypatch):
    workspace = _workspace(_service(None))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    assert response.json()['blocking_reason'] == 'project_root_missing'


def test_build_readiness_returns_tables_source_missing_when_config_missing(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True, exist_ok=True)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    payload = response.json()
    assert payload['tables_config_exists'] is False
    assert payload['blocking_reason'] == 'tables_source_missing'


def test_build_readiness_returns_no_raw_indexes_when_sources_exist(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    (project_root / 'Tables').mkdir(parents=True, exist_ok=True)
    (project_root / 'Tables' / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    _write_tables_config(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    payload = response.json()
    assert payload['discovered_table_count'] == 1
    assert payload['raw_table_index_count'] == 0
    assert payload['blocking_reason'] == 'no_raw_indexes'


def test_build_readiness_returns_no_canonical_facts_when_raw_exists(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    (project_root / 'Tables').mkdir(parents=True, exist_ok=True)
    (project_root / 'Tables' / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    _write_tables_config(project_root)
    _write_raw_indexes(project_root, [{'table_name': 'HeroTable'}])
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    payload = response.json()
    assert payload['raw_table_index_count'] == 1
    assert payload['canonical_table_count'] == 0
    assert payload['blocking_reason'] == 'no_canonical_facts'


def test_build_readiness_returns_candidate_ready_when_canonical_exists(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    (project_root / 'Tables').mkdir(parents=True, exist_ok=True)
    (project_root / 'Tables' / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    _write_tables_config(project_root)
    _write_raw_indexes(project_root, [{'table_name': 'HeroTable'}])
    _write_canonical_table(project_root)
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    payload = response.json()
    assert payload['canonical_table_count'] == 1
    assert payload['blocking_reason'] == 'candidate_ready'
    assert payload['next_action'] == 'build_candidate_from_source'


def test_build_readiness_returns_path_mismatch_when_candidate_read_dir_outside_bundle(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True, exist_ok=True)
    _write_tables_config(project_root)
    workspace = _workspace(_service(project_root))
    outside_dir = tmp_path / 'outside-candidate-dir'

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, '_candidate_read_dir', lambda _project_root: outside_dir)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.get('/api/game/knowledge/map/build-readiness')

    assert response.status_code == 200
    payload = response.json()
    assert payload['same_project_bundle'] is False
    assert payload['project_bundle_root'] == str(get_project_bundle_root(project_root))
    assert payload['candidate_read_dir'] == str(outside_dir)
    assert payload['blocking_reason'] == 'path_mismatch'


def test_source_candidate_router_returns_diagnostics_when_canonical_is_missing(monkeypatch, tmp_path):
    project_root = tmp_path / 'project-root'
    (project_root / 'Tables').mkdir(parents=True, exist_ok=True)
    (project_root / 'Tables' / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    _write_tables_config(project_root)
    _write_raw_indexes(project_root, [{'table_name': 'HeroTable'}])
    workspace = _workspace(_service(project_root))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)

    with TestClient(_build_app(capabilities={'knowledge.candidate.write'})) as client:
        response = client.post('/api/game/knowledge/map/candidate/from-source', json={'use_existing_formal_map_as_hint': True})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_canonical_facts'
    assert response.json()['diagnostics'] == {
        'raw_table_index_count': 1,
        'canonical_table_count': 0,
        'canonical_tables_dir': str(get_project_canonical_tables_dir(project_root)),
        'blocking_reason': 'no_canonical_facts',
        'next_action': 'run_canonical_rebuild',
    }


def test_source_candidate_router_returns_candidate_count_and_refs_on_success(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', lambda _root: None)
    monkeypatch.setattr(
        map_router_module,
        'build_map_candidate_from_canonical_facts',
        lambda project_root, existing_formal_map=None: KnowledgeMapCandidateResult(
            mode='candidate_map',
            map=KnowledgeMap(
                release_id='candidate-source-canonical',
                tables=[
                    KnowledgeTableRef(
                        table_id='HeroTable',
                        title='HeroTable',
                        source_path='Tables/HeroTable.csv',
                        source_hash='sha256:hero',
                        system_id=None,
                    )
                ],
            ),
            release_id=None,
            candidate_source='source_canonical',
            is_formal_map=False,
            source_release_id=None,
            uses_existing_formal_map_as_hint=False,
            warnings=[],
        ),
    )
    monkeypatch.setattr(map_router_module, 'resolve_map_diff_base', lambda project_root, existing_formal_map=None: (None, 'none'))
    monkeypatch.setattr(
        map_router_module,
        'build_map_diff_review',
        lambda base_map, candidate_map, *, candidate_source, base_map_source, warnings=(): MapDiffReview(
            base_map_source='none',
            candidate_source='source_canonical',
            added_refs=['table:HeroTable'],
            removed_refs=[],
            changed_refs=[],
            unchanged_refs=[],
            warnings=[],
        ),
    )

    with TestClient(_build_app(capabilities={'knowledge.candidate.write'})) as client:
        response = client.post('/api/game/knowledge/map/candidate/from-source', json={'use_existing_formal_map_as_hint': False})

    assert response.status_code == 200
    payload = response.json()
    assert payload['candidate_table_count'] == 1
    assert payload['candidate_refs'] == ['table:HeroTable']
    assert payload['map']['tables'][0]['table_id'] == 'HeroTable'


def test_source_candidate_router_builds_from_source_and_attaches_diff(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    formal_map = _map('formal-map-working')

    async def _get_agent(_request):
        return workspace

    def _load_formal(_root):
        return SimpleNamespace(knowledge_map=formal_map)

    def _build_candidate(project_root, existing_formal_map=None):
        captured['project_root'] = project_root
        captured['existing_formal_map'] = existing_formal_map
        return KnowledgeMapCandidateResult(
            mode='candidate_map',
            map=_map('candidate-source-canonical'),
            release_id=None,
            candidate_source='source_canonical',
            is_formal_map=False,
            source_release_id=None,
            uses_existing_formal_map_as_hint=True,
            warnings=['hint only'],
        )

    def _resolve_diff_base(project_root, existing_formal_map=None):
        captured['diff_base_project_root'] = project_root
        captured['diff_base_existing_formal_map'] = existing_formal_map
        return formal_map, 'formal_map'

    def _build_diff(base_map, candidate_map, *, candidate_source, base_map_source, warnings=()):
        captured['base_map'] = base_map
        captured['candidate_map'] = candidate_map
        captured['candidate_source'] = candidate_source
        captured['base_map_source'] = base_map_source
        captured['warnings'] = list(warnings)
        return MapDiffReview(
            base_map_source='formal_map',
            candidate_source='source_canonical',
            added_refs=['table:NewTable'],
            removed_refs=[],
            changed_refs=['table:Table_Player'],
            unchanged_refs=['system:combat'],
            warnings=['review diff'],
        )

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', _load_formal)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_canonical_facts', _build_candidate)
    monkeypatch.setattr(map_router_module, 'resolve_map_diff_base', _resolve_diff_base)
    monkeypatch.setattr(map_router_module, 'build_map_diff_review', _build_diff)

    with TestClient(_build_app(capabilities={'knowledge.candidate.write'})) as client:
        response = client.post('/api/game/knowledge/map/candidate/from-source', json={'use_existing_formal_map_as_hint': True})

    assert response.status_code == 200
    assert response.json()['candidate_source'] == 'source_canonical'
    assert response.json()['uses_existing_formal_map_as_hint'] is True
    assert response.json()['diff_review']['base_map_source'] == 'formal_map'
    assert response.json()['diff_review']['candidate_source'] == 'source_canonical'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['existing_formal_map'] == formal_map
    assert captured['candidate_source'] == 'source_canonical'
    assert captured['base_map_source'] == 'formal_map'
    assert captured['warnings'] == ['hint only']


def test_source_candidate_router_returns_no_canonical_facts_without_fallback(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'load_formal_knowledge_map', lambda _root: None)
    monkeypatch.setattr(
        map_router_module,
        'build_map_candidate_from_canonical_facts',
        lambda project_root, existing_formal_map=None: KnowledgeMapCandidateResult(
            mode='no_canonical_facts',
            map=None,
            release_id=None,
            candidate_source='source_canonical',
            is_formal_map=False,
            source_release_id=None,
            uses_existing_formal_map_as_hint=False,
            warnings=['No canonical facts were available'],
        ),
    )

    with TestClient(_build_app(capabilities={'knowledge.candidate.write'})) as client:
        response = client.post('/api/game/knowledge/map/candidate/from-source', json={'use_existing_formal_map_as_hint': True})

    assert response.status_code == 200
    assert response.json()['mode'] == 'no_canonical_facts'
    assert response.json()['candidate_source'] == 'source_canonical'
    assert response.json()['source_release_id'] is None
    assert response.json()['map'] is None
    assert response.json()['diff_review'] is None


def test_source_candidate_router_requires_knowledge_candidate_write_when_capabilities_present(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(_request):
        return workspace

    def _build_candidate(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('source candidate build should be blocked before builder call')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'build_map_candidate_from_canonical_facts', _build_candidate)

    with TestClient(_build_app(capabilities={'knowledge.candidate.read'})) as client:
        response = client.post('/api/game/knowledge/map/candidate/from-source', json={'use_existing_formal_map_as_hint': True})

    assert response.status_code == 403
    assert response.json()['detail'] == 'Missing capability: knowledge.candidate.write'
    assert called is False


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


def test_save_formal_map_router_requires_injected_viewer_capabilities(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    called = False

    async def _get_agent(request):
        request.state.capabilities = {'knowledge.map.read'}
        return workspace

    def _save(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('formal map save should be blocked by injected viewer capabilities')

    monkeypatch.setattr(map_router_module, 'get_agent_for_request', _get_agent)
    monkeypatch.setattr(map_router_module, 'save_formal_knowledge_map', _save)

    with TestClient(_build_app()) as client:
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


def test_save_formal_map_router_allows_injected_admin_capabilities(monkeypatch, tmp_path):
    workspace = _workspace(_service(tmp_path / 'project-root'))
    captured = {}
    record = SimpleNamespace(
        knowledge_map=_map(),
        map_hash='sha256:admin-saved',
        updated_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        updated_by='admin',
    )

    async def _get_agent(request):
        request.state.capabilities = {'*'}
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
            json={'map': _map().model_dump(mode='json'), 'updated_by': 'admin'},
        )

    assert response.status_code == 200
    assert response.json()['map_hash'] == 'sha256:admin-saved'
    assert captured['project_root'] == tmp_path / 'project-root'
    assert captured['updated_by'] == 'admin'
