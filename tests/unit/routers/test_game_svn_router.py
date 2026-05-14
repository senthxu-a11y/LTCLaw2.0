from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_svn import router
from ltclaw_gy_x.game.models import ChangeSet
def _workspace(service):
    return SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )


def _make_service(
    *,
    configured: bool = True,
    role: str = "maintainer",
    watcher=None,
    recent_changes=None,
    index_committer=None,
    svn_info=None,
):
    return SimpleNamespace(
        configured=configured,
        user_config=SimpleNamespace(my_role=role),
        svn_watcher=watcher,
        svn=SimpleNamespace(info=AsyncMock(return_value=svn_info or {})) if svn_info is not None else None,
        _recent_changes_buffer=list(recent_changes or []),
        index_committer=index_committer,
    )


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_status_unconfigured(app, client):
    service = _make_service(configured=False, role="consumer")
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    assert body["my_role"] == "consumer"


@pytest.mark.asyncio
async def test_status_returns_frozen_shape_when_configured(app, client):
    service = _make_service(watcher=SimpleNamespace())
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["disabled"] is True
    assert body["running"] is False
    assert body["current_rev"] is None


@pytest.mark.asyncio
async def test_sync_returns_frozen_error_for_consumer(app, client):
    service = _make_service(role="consumer")
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.post("/api/game/svn/sync")
    assert resp.status_code == 409
    assert resp.json()["detail"]["disabled"] is True


@pytest.mark.asyncio
async def test_sync_returns_frozen_error_for_unconfigured(app, client):
    service = _make_service(configured=False)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.post("/api/game/svn/sync")
    assert resp.status_code == 409
    assert resp.json()["detail"]["disabled"] is True


@pytest.mark.asyncio
async def test_sync_does_not_trigger_watcher(app, client):
    watcher = SimpleNamespace(trigger_now=AsyncMock())
    service = _make_service(watcher=watcher)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.post("/api/game/svn/sync")
    assert resp.status_code == 409
    watcher.trigger_now.assert_not_called()


@pytest.mark.asyncio
async def test_log_recent_returns_buffer(app, client):
    service = _make_service()
    service._log_bus_buffer = [{"msg": "a"}, {"msg": "b"}, {"msg": "c"}]
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/log/recent?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["logs"] == [{"msg": "b"}, {"msg": "c"}]


@pytest.mark.asyncio
async def test_changes_recent_from_buffer(app, client):
    entries = [
        {"revision": 5, "modified": ["a.csv"]},
        {"revision": 4, "modified": ["b.csv"]},
        {"revision": 3, "modified": ["c.csv"]},
    ]
    service = _make_service(recent_changes=entries)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/changes/recent?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "buffer"
    assert body["count"] == 2
    assert [c["revision"] for c in body["changes"]] == [5, 4]


@pytest.mark.asyncio
async def test_changes_recent_fallback_to_persisted(app, client):
    cs = ChangeSet(from_rev=1, to_rev=9, added=["x.csv"], modified=[], deleted=[])
    committer = SimpleNamespace(load_changeset=lambda: cs)
    service = _make_service(recent_changes=[], index_committer=committer)
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/changes/recent")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "persisted"
    assert body["count"] == 1
    assert body["changes"][0]["revision"] == 9


@pytest.mark.asyncio
async def test_changes_recent_empty(app, client):
    service = _make_service(recent_changes=[])
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/changes/recent")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "empty"
    assert body["count"] == 0


@pytest.mark.asyncio
async def test_stream_logs_returns_disabled_event(app, client):
    service = _make_service()
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service)
    async with client:
        resp = await client.get("/api/game/svn/log/stream")
    assert resp.status_code == 200
    assert "disabled" in resp.text
