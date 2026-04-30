# -*- coding: utf-8 -*-
"""Unit tests for `/game/index/impact` reverse-impact endpoint."""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_index import router


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _ws(service):
    return SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )


def _edge(ft, ff, tt, tf, conf="confirmed", by="rule"):
    return SimpleNamespace(
        from_table=ft,
        from_field=ff,
        to_table=tt,
        to_field=tf,
        confidence=SimpleNamespace(value=conf),
        inferred_by=by,
    )


def _service_with_graph(edges):
    committer = SimpleNamespace(
        load_dependency_graph=lambda: SimpleNamespace(edges=edges),
    )
    return SimpleNamespace(
        index_committer=committer,
        query_router=SimpleNamespace(),  # 占位
    )


def _patch_get(monkeypatch, svc):
    """绕过 _get 的 query_router 检查。"""
    from ltclaw_gy_x.app.routers import game_index

    monkeypatch.setattr(game_index, "_get", lambda ws: (svc, svc.query_router))


def test_impact_single_hop(monkeypatch):
    edges = [
        _edge("SkillTable", "HeroId", "HeroTable", "ID"),
        _edge("EquipTable", "OwnerHeroId", "HeroTable", "ID"),
        _edge("BuffTable", "TargetSkillId", "SkillTable", "ID"),
    ]
    svc = _service_with_graph(edges)
    _patch_get(monkeypatch, svc)
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get("/api/game/index/impact", params={"table": "HeroTable", "max_depth": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert sorted(body["tables"]) == ["EquipTable", "SkillTable"]


def test_impact_transitive(monkeypatch):
    edges = [
        _edge("SkillTable", "HeroId", "HeroTable", "ID"),
        _edge("BuffTable", "TargetSkillId", "SkillTable", "ID"),
    ]
    svc = _service_with_graph(edges)
    _patch_get(monkeypatch, svc)
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get("/api/game/index/impact", params={"table": "HeroTable", "max_depth": 3})
    body = resp.json()
    # Should follow SkillTable → BuffTable
    tables = body["tables"]
    assert "SkillTable" in tables
    assert "BuffTable" in tables
    depths = {i["from_table"]: i["depth"] for i in body["impacts"]}
    assert depths["SkillTable"] == 1
    assert depths["BuffTable"] == 2


def test_impact_field_filter(monkeypatch):
    edges = [
        _edge("SkillTable", "HeroId", "HeroTable", "ID"),
        _edge("LogTable", "HeroName", "HeroTable", "Name"),
    ]
    svc = _service_with_graph(edges)
    _patch_get(monkeypatch, svc)
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get(
            "/api/game/index/impact",
            params={"table": "HeroTable", "field": "ID", "max_depth": 2},
        )
    body = resp.json()
    assert body["tables"] == ["SkillTable"]


def test_impact_no_graph(monkeypatch):
    svc = SimpleNamespace(
        index_committer=SimpleNamespace(load_dependency_graph=lambda: None),
        query_router=SimpleNamespace(),
    )
    _patch_get(monkeypatch, svc)
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get("/api/game/index/impact", params={"table": "X"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
