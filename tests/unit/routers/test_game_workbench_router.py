# -*- coding: utf-8 -*-
"""Unit tests for game workbench preview router."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_workbench import router
from ltclaw_gy_x.game.change_applier import ApplyError
from ltclaw_gy_x.game.change_proposal import ChangeOp


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _ws(service):
    return SimpleNamespace(
        service_manager=SimpleNamespace(services=({"game_service": service} if service else {}))
    )


def test_preview_happy_path():
    async def _dry_run(_proposal):
        return [
            {
                "op": {"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 120},
                "before": 100,
                "after": 120,
                "ok": True,
                "reason": None,
            }
        ]

    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace(dry_run=_dry_run)))
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["ok"] is True
    assert item["old_value"] == 100
    assert item["new_value"] == 120
    assert item["error"] is None


def test_preview_apply_error_returns_failed_items():
    async def _dry_run(_proposal):
        raise ApplyError(
            ChangeOp(op="update_cell", table="Hero", row_id=1, field="HP", new_value=120),
            "row_id not found",
        )

    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace(dry_run=_dry_run)))
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["ok"] is False
    assert item["error"]


def test_preview_missing_game_service_returns_404():
    workspace = _ws(None)
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    assert resp.status_code == 404


def test_preview_missing_change_applier_returns_412():
    workspace = _ws(SimpleNamespace())
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    assert resp.status_code == 412


def test_preview_empty_changes_returns_empty_items():
    async def _dry_run(_proposal):
        return []

    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace(dry_run=_dry_run)))
    with TestClient(_build_app(workspace)) as client:
        resp = client.post("/api/game/workbench/preview", json={"changes": []})
    assert resp.status_code == 200
    assert resp.json() == {"items": []}


def test_preview_per_op_failure_marks_ok_false():
    async def _dry_run(_proposal):
        return [
            {
                "op": {"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 120},
                "before": None,
                "after": None,
                "ok": False,
                "reason": "row_id not found",
            }
        ]

    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace(dry_run=_dry_run)))
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    item = resp.json()["items"][0]
    assert item["ok"] is False
    assert item["error"] == "row_id not found"
