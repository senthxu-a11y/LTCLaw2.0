from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from ltclaw_gy_x.app import agent_context as agent_context_module
from ltclaw_gy_x.game.config import LocalAgentProfile, UserGameConfig


class _DummyManager:
    def __init__(self, workspace):
        self._workspace = workspace

    async def get_agent(self, agent_id: str):
        assert agent_id == 'default'
        return self._workspace


def _request(app: FastAPI) -> Request:
    scope = {
        'type': 'http',
        'headers': [],
        'method': 'GET',
        'path': '/',
        'query_string': b'',
        'app': app,
        'state': {},
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_get_agent_for_request_injects_legacy_mapped_capabilities(monkeypatch):
    app = FastAPI()
    workspace = SimpleNamespace(agent_id='default', workspace_dir='/tmp/default')
    app.state.multi_agent_manager = _DummyManager(workspace)
    request = _request(app)

    config = SimpleNamespace(
        agents=SimpleNamespace(
            active_agent='default',
            profiles={'default': SimpleNamespace(enabled=True, workspace_dir='/tmp/default')},
        )
    )
    monkeypatch.setattr(agent_context_module, 'load_config', lambda: config)
    monkeypatch.setattr(
        agent_context_module,
        'load_agent_config',
        lambda agent_id: SimpleNamespace(name='Default Agent'),
    )
    monkeypatch.setattr(
        agent_context_module,
        'load_user_config',
        lambda: UserGameConfig(my_role='maintainer'),
    )

    resolved = await agent_context_module.get_agent_for_request(request)

    assert resolved is workspace
    assert request.state.capabilities == {'*'}
    assert request.state.agent_profile['role'] == 'admin'
    assert request.state.user['capabilities'] == ['*']


@pytest.mark.asyncio
async def test_get_agent_for_request_prefers_local_agent_profile(monkeypatch):
    app = FastAPI()
    workspace = SimpleNamespace(agent_id='default', workspace_dir='/tmp/default')
    app.state.multi_agent_manager = _DummyManager(workspace)
    request = _request(app)

    config = SimpleNamespace(
        agents=SimpleNamespace(
            active_agent='default',
            profiles={'default': SimpleNamespace(enabled=True, workspace_dir='/tmp/default')},
        )
    )
    monkeypatch.setattr(agent_context_module, 'load_config', lambda: config)
    monkeypatch.setattr(
        agent_context_module,
        'load_agent_config',
        lambda agent_id: SimpleNamespace(name='Default Agent'),
    )
    monkeypatch.setattr(
        agent_context_module,
        'load_user_config',
        lambda: UserGameConfig(
            my_role='consumer',
            agent_profiles={
                'default': LocalAgentProfile(
                    agent_id='default',
                    display_name='Source Writer',
                    role='source_writer',
                    capabilities=[],
                )
            },
        ),
    )

    await agent_context_module.get_agent_for_request(request)

    assert request.state.agent_profile['display_name'] == 'Source Writer'
    assert request.state.agent_profile['role'] == 'source_writer'
    assert 'workbench.source.write' in request.state.capabilities