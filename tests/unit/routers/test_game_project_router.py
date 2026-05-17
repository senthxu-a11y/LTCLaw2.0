from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_knowledge_release as release_router_module
from ltclaw_gy_x.app.routers.game_project import router
from ltclaw_gy_x.app.routers.game_knowledge_release import router as release_router
from ltclaw_gy_x.game.config import (
    DEFAULT_TABLES_EXCLUDE_PATTERNS,
    DEFAULT_TABLES_INCLUDE_PATTERNS,
    DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES,
    LocalAgentProfile,
    ProjectTablesSourceConfig,
    UserGameConfig,
    load_project_config,
    save_project_tables_source_config,
    save_workspace_agent_profile,
)
from ltclaw_gy_x.game.models import KnowledgeManifest, KnowledgeSystem
from ltclaw_gy_x.game.paths import (
    get_active_data_workspace_root,
    get_project_bundle_root,
    get_project_config_path,
    get_project_key,
    get_project_tables_source_path,
    get_workspace_agent_profile_path,
    get_workspace_config_path,
    get_workspace_pointer_path,
    load_data_workspace_config,
)


class _Service:
    def __init__(self, svn_root: Path):
        self._project_config = None
        self.user_config = UserGameConfig(my_role='maintainer', svn_local_root=str(svn_root))
        self.reload_calls = 0

    @property
    def project_config(self):
        return self._project_config

    async def reload_config(self):
        self.reload_calls += 1
        svn_local_root = getattr(self.user_config, 'svn_local_root', None)
        if not svn_local_root:
            self._project_config = None
            return
        self._project_config = load_project_config(Path(svn_local_root))


def _workspace(service):
    return SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': service}))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _isolated_working_dir(monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix='/api')
    return app


@pytest.fixture
def client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.mark.asyncio
async def test_project_config_api_persists_external_provider_config_and_omits_secret_values(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    svn_root = tmp_path / 'svn-root'
    svn_root.mkdir()
    service = _Service(svn_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    payload = {
        'schema_version': 'project-config.v1',
        'project': {'name': 'Test Game', 'engine': 'Unity', 'language': 'zh-CN'},
        'svn': {'root': str(svn_root), 'poll_interval_seconds': 300, 'jitter_seconds': 30},
        'paths': [],
        'filters': {'include_ext': ['.xlsx'], 'exclude_glob': []},
        'table_convention': {
            'header_row': 1,
            'comment_row': None,
            'primary_key_field': 'ID',
            'per_table_primary_keys': {},
            'auto_detect_primary_key': True,
            'id_ranges': [],
        },
        'doc_templates': {},
        'models': {},
        'external_provider_config': {
            'enabled': True,
            'transport_enabled': True,
            'provider_name': 'future_external',
            'model_name': 'backend-model',
            'allowed_providers': ['future_external'],
            'allowed_models': ['backend-model'],
            'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
            'timeout_seconds': 15.0,
            'max_output_tokens': 256,
            'max_prompt_chars': 12000,
            'max_output_chars': 2000,
            'api_key': 'REQUEST_SECRET_SHOULD_NOT_BE_SAVED',
            'env': {
                'api_key_env_var': 'QWENPAW_RAG_API_KEY',
                'api_key': 'NESTED_REQUEST_SECRET_SHOULD_NOT_BE_SAVED',
            },
        },
    }

    async with client:
        put_response = await client.put('/api/game/project/config', json=payload)
        get_response = await client.get('/api/game/project/config')

    assert put_response.status_code == 200
    assert get_response.status_code == 200
    response_payload = get_response.json()
    external_provider_config = response_payload['external_provider_config']
    assert external_provider_config == {
        'enabled': True,
        'transport_enabled': True,
        'provider_name': 'future_external',
        'model_name': 'backend-model',
        'allowed_providers': ['future_external'],
        'allowed_models': ['backend-model'],
        'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
        'timeout_seconds': 15.0,
        'max_output_tokens': 256,
        'max_prompt_chars': 12000,
        'max_output_chars': 2000,
        'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
    }
    assert 'api_key' not in external_provider_config
    assert 'api_key' not in external_provider_config['env']

    config_path = get_project_config_path(svn_root)
    saved_text = config_path.read_text(encoding='utf-8')
    assert 'REQUEST_SECRET_SHOULD_NOT_BE_SAVED' not in saved_text
    assert 'NESTED_REQUEST_SECRET_SHOULD_NOT_BE_SAVED' not in saved_text


@pytest.mark.asyncio
async def test_setup_status_returns_defaults_before_project_root_is_configured(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    service = _Service(tmp_path / 'missing-root')
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['project_root'] is None
    assert payload['project_root_exists'] is False
    assert payload['project_bundle_root'] is None
    assert payload['project_key'] is None
    assert payload['project_root_source'] is None
    assert payload['user_config_svn_local_root'] is None
    assert payload['project_config_svn_root'] is None
    assert payload['tables_config'] == {
        'roots': [],
        'include': DEFAULT_TABLES_INCLUDE_PATTERNS,
        'exclude': DEFAULT_TABLES_EXCLUDE_PATTERNS,
        'header_row': 1,
        'primary_key_candidates': DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES,
    }
    assert payload['discovery'] == {
        'status': 'not_scanned',
        'discovered_table_count': 0,
        'available_table_count': 0,
        'unsupported_table_count': 0,
        'excluded_table_count': 0,
        'error_count': 0,
    }
    assert payload['build_readiness'] == {
        'blocking_reason': 'project_root_not_configured',
        'next_action': 'set_project_root',
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('project_root', 'detail_fragment'),
    [
        ('', 'must not be empty'),
        ('svn://repo/path', 'local filesystem path'),
        ('http://example.com/project', 'local filesystem path'),
        ('https://example.com/project', 'local filesystem path'),
        ('/definitely/not/there', 'does not exist'),
    ],
)
async def test_put_project_root_rejects_invalid_values(app, client, monkeypatch, tmp_path, project_root, detail_fragment):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    service = _Service(tmp_path / 'unused-root')
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.put('/api/game/project/root', json={'project_root': project_root})

    assert response.status_code == 400
    assert detail_fragment in response.json()['detail']


@pytest.mark.asyncio
async def test_put_project_root_saves_and_returns_setup_status(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.put('/api/game/project/root', json={'project_root': str(project_root)})
        readback = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['project_key'] == get_project_key(project_root)
    assert payload['project_bundle_root'] == str(get_project_bundle_root(project_root))
    assert payload['setup_status']['project_root'] == str(project_root)
    assert payload['setup_status']['project_root_source'] == 'user_config_svn_local_root'
    assert payload['setup_status']['project_root_exists'] is True
    assert payload['setup_status']['build_readiness'] == {
        'blocking_reason': 'no_table_sources_found',
        'next_action': 'configure_tables_source',
    }
    assert readback.status_code == 200
    assert readback.json()['project_root'] == str(project_root)


@pytest.mark.asyncio
async def test_put_project_root_reloads_other_loaded_game_services(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    default_service = _Service(project_root)
    default_service.user_config.svn_local_root = None
    qa_service = _Service(project_root)
    qa_service.user_config.svn_local_root = None
    default_workspace = SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': default_service}))
    qa_workspace = SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': qa_service}))
    app.dependency_overrides[get_agent_for_request] = lambda: default_workspace
    manager = SimpleNamespace(agents={'default': default_workspace, 'qa-agent': qa_workspace})
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_manager', lambda: manager)

    async with client:
        response = await client.put('/api/game/project/root', json={'project_root': str(project_root)})

    assert response.status_code == 200
    assert default_service.reload_calls == 1
    assert qa_service.reload_calls == 1


@pytest.mark.asyncio
async def test_put_project_root_normalizes_backslashes_and_supports_spaces_and_chinese(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / '中文 项目' / 'Example Root'
    project_root.mkdir(parents=True)
    service = _Service(project_root)
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    backslash_path = str(project_root).replace('/', '\\')

    async with client:
        response = await client.put('/api/game/project/root', json={'project_root': backslash_path})
        readback = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    assert response.json()['setup_status']['project_root'] == str(project_root)
    assert readback.status_code == 200
    assert readback.json()['project_root'] == str(project_root)


@pytest.mark.asyncio
async def test_capability_status_reflects_legacy_maintainer_role(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.agent_profiles = {}
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.get('/api/game/project/capability-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['role'] == 'admin'
    assert payload['capability_source'] == 'game_user_config.my_role'
    assert payload['is_legacy_role_fallback'] is True
    assert payload['required_for_cold_start']['knowledge.candidate.write'] is True
    assert payload['required_for_formal_map']['knowledge.map.edit'] is True
    assert payload['required_for_release']['knowledge.publish'] is True


@pytest.mark.asyncio
async def test_workspace_root_api_creates_pointer_and_updates_setup_status(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    workspace_root = tmp_path / 'LTClawWorkspace'

    async with client:
        response = await client.put(
            '/api/game/project/workspace-root',
            json={'workspace_root': str(workspace_root), 'workspace_name': 'LTClaw Workspace', 'create_if_missing': True},
        )
        setup = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['active_workspace_root'] == str(workspace_root)
    assert get_active_data_workspace_root() == workspace_root
    assert get_workspace_pointer_path().exists()
    assert get_workspace_config_path(workspace_root).exists()
    assert get_workspace_agent_profile_path('default', workspace_root).exists()
    workspace_config = load_data_workspace_config(workspace_root)
    assert workspace_config['active_project_root'] == str(project_root)
    default_profile = LocalAgentProfile.model_validate(
        yaml.safe_load(get_workspace_agent_profile_path('default', workspace_root).read_text(encoding='utf-8'))
    )
    assert default_profile.role == 'admin'
    assert setup.status_code == 200
    setup_payload = setup.json()
    assert setup_payload['active_workspace_root'] == str(workspace_root)
    assert setup_payload['active_workspace_project_root'] == str(project_root)
    assert setup_payload['project_bundle_root'] == str(get_project_bundle_root(project_root))
    assert str(get_project_bundle_root(project_root)).startswith(str(workspace_root / 'projects'))


@pytest.mark.asyncio
async def test_setup_status_prefers_workspace_active_project_root_over_agent_local_root(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    workspace_root = tmp_path / 'LTClawWorkspace'
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(tmp_path / 'agent-local-missing')
    service.user_config = UserGameConfig(my_role='consumer', svn_local_root=None)
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'qa-workspace'),
        agent_id='qa-agent',
    )
    (tmp_path / 'qa-workspace').mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_data_workspace_root', lambda: workspace_root)
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_workspace_project_root', lambda: project_root)
    monkeypatch.setattr('ltclaw_gy_x.game.paths.get_active_data_workspace_root', lambda: workspace_root)

    async with client:
        response = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['project_root'] == str(project_root)
    assert payload['project_root_source'] == 'workspace_active_project_root'
    assert payload['active_workspace_project_root'] == str(project_root)


@pytest.mark.asyncio
async def test_capability_status_prefers_workspace_agent_profile(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    workspace_root = tmp_path / 'LTClawWorkspace'
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config = UserGameConfig(my_role='maintainer', svn_local_root=str(project_root))
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'qa-workspace'),
        agent_id='qa-agent',
    )
    (tmp_path / 'qa-workspace').mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_data_workspace_root', lambda: workspace_root)
    monkeypatch.setattr('ltclaw_gy_x.game.config.get_active_data_workspace_root', lambda: workspace_root)
    monkeypatch.setattr('ltclaw_gy_x.game.paths.get_active_data_workspace_root', lambda: workspace_root)
    save_workspace_agent_profile(
        LocalAgentProfile(agent_id='qa-agent', display_name='QA Agent', role='viewer', capabilities=[]),
        workspace_root=workspace_root,
    )

    async with client:
        response = await client.get('/api/game/project/capability-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['agent_id'] == 'qa-agent'
    assert payload['role'] == 'viewer'
    assert payload['capability_source'] == 'workspace.agents'
    assert payload['is_legacy_role_fallback'] is False
    assert 'knowledge.build' in payload['missing_required_capabilities']


@pytest.mark.asyncio
async def test_workspace_agent_profile_api_persists_role_and_capabilities(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    workspace_root = tmp_path / 'LTClawWorkspace'
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config = UserGameConfig(my_role='consumer', svn_local_root=str(project_root))
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'qa-workspace'),
        agent_id='qa-agent',
    )
    (tmp_path / 'qa-workspace').mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_data_workspace_root', lambda: workspace_root)
    monkeypatch.setattr('ltclaw_gy_x.game.config.get_active_data_workspace_root', lambda: workspace_root)
    monkeypatch.setattr('ltclaw_gy_x.game.paths.get_active_data_workspace_root', lambda: workspace_root)

    async with client:
        response = await client.put(
            '/api/game/project/agent-profile',
            json={
                'display_name': 'QA Agent',
                'role': 'planner',
                'capabilities': ['workbench.test.write', 'knowledge.read', 'invalid.capability'],
            },
        )
        readback = await client.get('/api/game/project/agent-profile')

    assert response.status_code == 200
    payload = response.json()
    assert payload['profile'] == {
        'agent_id': 'qa-agent',
        'display_name': 'QA Agent',
        'role': 'planner',
        'capabilities': ['workbench.test.write', 'knowledge.read'],
    }
    assert payload['capability_status']['role'] == 'planner'
    assert payload['capability_status']['capability_source'] == 'workspace.agents'
    assert readback.status_code == 200
    assert readback.json() == payload['profile']


def test_project_root_path_normalizes_windows_style_backslashes():
    from ltclaw_gy_x.app.routers.game_project import _project_root_path

    assert _project_root_path(r'E:\test_project') == Path('E:/test_project')


@pytest.mark.asyncio
async def test_put_tables_source_requires_project_root(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    service = _Service(tmp_path / 'unused-root')
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.put(
            '/api/game/project/sources/tables',
            json={'roots': ['Tables'], 'header_row': 1},
        )

    assert response.status_code == 400
    assert 'project_root must be configured' in response.json()['detail']


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('payload', 'detail_fragment'),
    [
        ({'roots': [], 'header_row': 1}, 'roots must not be empty'),
        ({'roots': ['Tables'], 'header_row': 0}, 'header_row must be greater than or equal to 1'),
    ],
)
async def test_put_tables_source_rejects_invalid_config(app, client, monkeypatch, tmp_path, payload, detail_fragment):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.put('/api/game/project/sources/tables', json=payload)

    assert response.status_code == 400
    assert detail_fragment in response.json()['detail']


@pytest.mark.asyncio
async def test_put_tables_source_persists_config_and_setup_status_reads_it_back(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    payload = {
        'roots': ['Tables', 'Excel'],
        'include': ['**/*.csv', '**/*.xlsx'],
        'exclude': ['**/~$*', '**/.backup/**', '**/ignored/**'],
        'header_row': 2,
        'primary_key_candidates': ['ID', 'HeroID'],
    }

    async with client:
        response = await client.put('/api/game/project/sources/tables', json=payload)
        readback = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    response_payload = response.json()
    assert response_payload['effective_config'] == payload
    assert response_payload['setup_status']['tables_config'] == payload
    assert response_payload['setup_status']['build_readiness'] == {
        'blocking_reason': None,
        'next_action': 'ready_for_discovery',
    }
    tables_config_path = get_project_tables_source_path(project_root)
    assert response_payload['config_path'] == str(tables_config_path)
    assert tables_config_path.exists()
    saved_text = tables_config_path.read_text(encoding='utf-8')
    assert 'Tables' in saved_text
    assert 'HeroID' in saved_text
    assert readback.status_code == 200
    assert readback.json()['tables_config'] == payload


@pytest.mark.asyncio
async def test_put_tables_source_reloads_other_loaded_game_services(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    default_service = _Service(project_root)
    qa_service = _Service(project_root)
    default_workspace = SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': default_service}))
    qa_workspace = SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': qa_service}))
    app.dependency_overrides[get_agent_for_request] = lambda: default_workspace
    manager = SimpleNamespace(agents={'default': default_workspace, 'qa-agent': qa_workspace})
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_manager', lambda: manager)

    async with client:
        response = await client.put(
            '/api/game/project/sources/tables',
            json={'roots': ['Tables'], 'header_row': 1},
        )

    assert response.status_code == 200
    assert default_service.reload_calls == 1
    assert qa_service.reload_calls == 1


@pytest.mark.asyncio
async def test_source_discovery_finds_minimal_project_sample(app, client):
    project_root = _repo_root() / 'examples' / 'minimal_project'
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['project_root'] == str(project_root)
    assert payload['table_files'] == [
        {
            'source_path': 'Tables/HeroTable.csv',
            'format': 'csv',
            'status': 'available',
            'reason': 'matched_supported_format',
            'cold_start_supported': True,
            'cold_start_reason': 'rule_only_supported_csv',
        }
    ]


@pytest.mark.asyncio
async def test_setup_status_default_table_include_does_not_include_txt(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    service = _Service(tmp_path / 'missing-root')
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['tables_config']['include'] == ['**/*.csv', '**/*.xlsx']
    assert '**/*.txt' not in payload['tables_config']['include']


@pytest.mark.asyncio
async def test_source_discovery_accepts_txt_when_explicitly_included(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'txt-project'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.txt').write_text('ID\tName\n1\tHeroA\n', encoding='utf-8')

    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.txt']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['discovered_table_count'] == 1
    assert payload['summary']['available_table_count'] == 0
    assert payload['table_files'] == [
        {
            'source_path': 'Tables/HeroTable.txt',
            'format': 'txt',
            'status': 'recognized',
            'reason': 'matched_recognized_format',
            'cold_start_supported': False,
            'cold_start_reason': 'rule_only_cold_start_not_supported_for_txt',
        }
    ]
    assert payload['excluded_files'] == []
    assert payload['unsupported_files'] == []
    assert payload['errors'] == []
    assert payload['summary'] == {
        'discovered_table_count': 1,
        'available_table_count': 0,
        'excluded_table_count': 0,
        'unsupported_table_count': 0,
        'error_count': 0,
    }
    assert payload['next_action'] == 'configure_tables_source'


@pytest.mark.asyncio
async def test_source_discovery_marks_temp_excel_excluded_and_xls_unsupported(app, client, tmp_path):
    project_root = tmp_path / 'demo-project'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    (tables_dir / '~$Temp.xlsx').write_text('placeholder', encoding='utf-8')
    (tables_dir / 'OldTable.xls').write_text('legacy', encoding='utf-8')
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['summary'] == {
        'discovered_table_count': 2,
        'available_table_count': 1,
        'excluded_table_count': 1,
        'unsupported_table_count': 1,
        'error_count': 0,
    }
    assert payload['next_action'] == 'run_raw_index'
    assert {
        'source_path': 'Tables/~$Temp.xlsx',
        'format': 'xlsx',
        'status': 'excluded',
        'reason': 'matched_exclude_pattern',
        'cold_start_supported': False,
        'cold_start_reason': 'rule_only_cold_start_not_supported_for_xlsx',
    } in payload['excluded_files']
    unsupported_entry = {
        'source_path': 'Tables/OldTable.xls',
        'format': 'xls',
        'status': 'unsupported',
        'reason': 'xls_format_not_supported',
        'cold_start_supported': False,
        'cold_start_reason': 'rule_only_cold_start_not_supported_for_xls',
    }
    assert unsupported_entry in payload['unsupported_files']
    assert unsupported_entry in payload['table_files']


@pytest.mark.asyncio
async def test_source_discovery_returns_configure_action_when_include_misses(app, client, tmp_path):
    project_root = tmp_path / 'demo-project'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.json']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['table_files'] == []
    assert payload['summary']['discovered_table_count'] == 0
    assert payload['summary']['available_table_count'] == 0
    assert payload['next_action'] == 'configure_tables_source'


@pytest.mark.asyncio
async def test_source_discovery_scans_chinese_paths(app, client, tmp_path):
    project_root = tmp_path / '中文项目'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / '英雄表.csv').write_text('ID,Name\n1,英雄A\n', encoding='utf-8')
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['table_files'][0]['source_path'] == 'Tables/英雄表.csv'
    assert payload['next_action'] == 'run_raw_index'


@pytest.mark.asyncio
async def test_source_discovery_matches_uppercase_csv_extension_and_backslash_root(app, client, tmp_path):
    project_root = tmp_path / 'demo project'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.CSV').write_text('ID,Name\n1,HeroA\n', encoding='utf-8')
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables\\'], include=['**/*.csv']),
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['table_files'] == [
        {
            'source_path': 'Tables/HeroTable.CSV',
            'format': 'csv',
            'status': 'available',
            'reason': 'matched_supported_format',
            'cold_start_supported': True,
            'cold_start_reason': 'rule_only_supported_csv',
        }
    ]


@pytest.mark.asyncio
async def test_source_discovery_handles_missing_project_root_without_unhandled_exception(app, client, tmp_path):
    service = _Service(tmp_path / 'missing-root')
    service.user_config.svn_local_root = None
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is False
    assert payload['project_root'] is None
    assert payload['table_files'] == []
    assert payload['errors'] == [{'reason': 'project_root_not_configured'}]
    assert payload['summary']['error_count'] == 1
    assert payload['next_action'] == 'configure_tables_source'


@pytest.mark.asyncio
async def test_source_discovery_handles_missing_table_roots_without_unhandled_exception(app, client, tmp_path):
    project_root = tmp_path / 'demo-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.svn_local_root = str(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.post('/api/game/project/sources/discover')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is False
    assert payload['project_root'] == str(project_root)
    assert payload['errors'] == [{'reason': 'tables_roots_not_configured'}]
    assert payload['summary']['error_count'] == 1
    assert payload['next_action'] == 'configure_tables_source'


def test_file_backed_external_provider_config_keeps_project_and_release_routes_healthy(monkeypatch, tmp_path):
    svn_root = tmp_path / 'svn-root'
    svn_root.mkdir()
    service = _Service(svn_root)
    app = FastAPI()
    app.include_router(router, prefix='/api')
    app.include_router(release_router, prefix='/api')
    workspace = _workspace(service)
    app.dependency_overrides[get_agent_for_request] = lambda: workspace

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(release_router_module, 'get_agent_for_request', _get_agent)

    config_path = get_project_config_path(svn_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
schema_version: project-config.v1
project:
    name: Test Game
    engine: Unity
    language: zh-CN
svn:
    root: {svn_root}
    poll_interval_seconds: 300
    jitter_seconds: 30
paths: []
filters:
    include_ext:
    - .xlsx
    exclude_glob: []
table_convention:
    header_row: 1
    comment_row: null
    primary_key_field: ID
    per_table_primary_keys: {{}}
    auto_detect_primary_key: true
    id_ranges: []
doc_templates: {{}}
models: {{}}
external_provider_config:
    enabled: true
    transport_enabled: true
    provider_name: future_external
    model_name: backend-model
    allowed_providers:
    - future_external
    allowed_models:
    - backend-model
    base_url: http://127.0.0.1:8765/v1/chat/completions
    timeout_seconds: 15.0
    max_output_tokens: 256
    max_prompt_chars: 12000
    max_output_chars: 2000
    api_key: REQUEST_SECRET_SHOULD_BE_STRIPPED
    env:
        api_key_env_var: QWENPAW_RAG_API_KEY
        api_key: NESTED_REQUEST_SECRET_SHOULD_BE_STRIPPED
""".format(svn_root=svn_root.as_posix()).strip() + "\n",
        encoding='utf-8',
    )
    service._project_config = load_project_config(svn_root)

    manifest = KnowledgeManifest(
            release_id='release-001',
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source_snapshot_hash='sha256:snapshot',
            map_hash='sha256:map',
            systems=[KnowledgeSystem(system_id='combat', title='Combat')],
    )
    monkeypatch.setattr(release_router_module, 'list_releases', lambda project_root: [manifest])
    monkeypatch.setattr(release_router_module, 'get_current_release', lambda project_root: manifest)

    with TestClient(app) as client:
        project_response = client.get('/api/game/project/config')
        release_response = client.get('/api/game/knowledge/releases/status')

    assert project_response.status_code == 200
    assert project_response.json()['external_provider_config'] == {
        'enabled': True,
        'transport_enabled': True,
        'provider_name': 'future_external',
        'model_name': 'backend-model',
        'allowed_providers': ['future_external'],
        'allowed_models': ['backend-model'],
        'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
        'timeout_seconds': 15.0,
        'max_output_tokens': 256,
        'max_prompt_chars': 12000,
        'max_output_chars': 2000,
        'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
    }
    assert release_response.status_code == 200
    assert release_response.json()['current']['release_id'] == 'release-001'


@pytest.mark.asyncio
async def test_project_config_commit_returns_frozen_without_touching_svn(app, client, tmp_path):
    svn_root = tmp_path / 'svn-root'
    svn_root.mkdir()
    service = _Service(svn_root)
    service.svn = SimpleNamespace(add=pytest.fail, commit=pytest.fail)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    config_path = get_project_config_path(svn_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('schema_version: project-config.v1\n', encoding='utf-8')

    async with client:
        response = await client.post('/api/game/project/config/commit', json={'message': 'should not commit'})

    assert response.status_code == 409
    body = response.json()
    assert body['detail']['disabled'] is True
    assert body['detail']['config_exists'] is True


@pytest.mark.asyncio
async def test_setup_status_returns_maprag_and_agent_binding(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.maprag_bundle_root = str(tmp_path / 'bundle')
    service.user_config.bound_agent_id = 'bound-agent'
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'current-workspace'),
        agent_id='current-agent',
    )

    async with client:
        response = await client.get('/api/game/project/setup-status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['maprag_bundle_root'] == str(tmp_path / 'bundle')
    assert payload['bound_agent_id'] == 'bound-agent'
    assert payload['current_agent_id'] == 'current-agent'
    assert payload['agent_binding']['matches'] is False
    assert payload['agent_binding']['warning'] == '当前 Agent 与项目绑定不一致，可能造成记忆污染'


@pytest.mark.asyncio
async def test_put_maprag_bundle_saves_existing_directory(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    bundle_root = tmp_path / 'maprag-bundle'
    project_root.mkdir()
    bundle_root.mkdir()
    service = _Service(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)

    async with client:
        response = await client.put('/api/game/project/maprag-bundle', json={'maprag_bundle_root': str(bundle_root)})

    assert response.status_code == 200
    assert service.user_config.maprag_bundle_root == str(bundle_root)
    assert response.json()['maprag_bundle_root'] == str(bundle_root)
    assert service.reload_calls == 1


@pytest.mark.asyncio
async def test_put_agent_binding_defaults_to_current_agent(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'qa-workspace'),
        agent_id='qa-agent',
    )
    config = SimpleNamespace(agents=SimpleNamespace(profiles={'qa-agent': object()}, active_agent='default'))
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.load_config', lambda: config)

    async with client:
        response = await client.put('/api/game/project/agent-binding', json={'agent_id': ''})

    assert response.status_code == 200
    assert service.user_config.bound_agent_id == 'qa-agent'
    assert response.json()['agent_binding']['matches'] is True


@pytest.mark.asyncio
async def test_apply_agent_binding_sets_active_agent(app, client, monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    project_root = tmp_path / 'minimal-project'
    project_root.mkdir()
    service = _Service(project_root)
    service.user_config.bound_agent_id = 'qa-agent'
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={'game_service': service}),
        workspace_dir=str(tmp_path / 'default-workspace'),
        agent_id='default',
    )
    config = SimpleNamespace(agents=SimpleNamespace(profiles={'default': object(), 'qa-agent': object()}, active_agent='default'))
    saved = {}
    manager = SimpleNamespace(get_agent=lambda agent_id: SimpleNamespace(agent_id=agent_id))

    async def fake_get_agent(agent_id):
        return SimpleNamespace(agent_id=agent_id)

    manager.get_agent = fake_get_agent
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.load_config', lambda: config)
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.save_config', lambda cfg: saved.setdefault('active_agent', cfg.agents.active_agent))
    monkeypatch.setattr('ltclaw_gy_x.app.routers.game_project.get_active_manager', lambda: manager)

    async with client:
        response = await client.post('/api/game/project/agent-binding/apply')

    assert response.status_code == 200
    assert config.agents.active_agent == 'qa-agent'
    assert saved['active_agent'] == 'qa-agent'
    assert response.json()['applied_agent_id'] == 'qa-agent'
    assert response.json()['reload_required'] is True
