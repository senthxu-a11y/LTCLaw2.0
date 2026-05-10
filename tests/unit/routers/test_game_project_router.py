from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_project import router
from ltclaw_gy_x.game.config import UserGameConfig, load_project_config
from ltclaw_gy_x.game.paths import get_project_config_path


class _Service:
    def __init__(self, svn_root: Path):
        self._project_config = None
        self.user_config = UserGameConfig(my_role='maintainer', svn_local_root=str(svn_root))

    @property
    def project_config(self):
        return self._project_config

    async def reload_config(self):
        self._project_config = load_project_config(Path(self.user_config.svn_local_root))


def _workspace(service):
    return SimpleNamespace(service_manager=SimpleNamespace(services={'game_service': service}))


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
