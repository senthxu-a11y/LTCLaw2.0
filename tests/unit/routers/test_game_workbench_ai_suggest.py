# -*- coding: utf-8 -*-
"""Unit tests for `/game/workbench/ai-suggest` (rule-based AI panel)."""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_workbench import router


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _ws(service):
    return SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )


def _make_table_index(name: str = "HeroTable"):
    field_id = SimpleNamespace(
        name="ID",
        type="int",
        confidence=SimpleNamespace(value="confirmed"),
        description="主键",
    )
    field_hp = SimpleNamespace(
        name="HP",
        type="int",
        confidence=SimpleNamespace(value="confirmed"),
        description="生命值",
    )
    field_unsure = SimpleNamespace(
        name="MysteryField",
        type="string",
        confidence=SimpleNamespace(value="low_ai"),
        description="未知含义",
    )
    rng = SimpleNamespace(
        type="hero",
        start=1000,
        end=1999,
        count=3,
        actual_min=1000,
        actual_max=1002,
    )
    return SimpleNamespace(
        table_name=name,
        primary_key="ID",
        row_count=3,
        fields=[field_id, field_hp, field_unsure],
        id_ranges=[rng],
        description="",
        category="",
        category_confidence=None,
        last_updated="",
    )


def _make_dep_graph(target_table: str):
    edge = SimpleNamespace(
        from_table="SkillTable",
        from_field="HeroId",
        to_table=target_table,
        to_field="ID",
        confidence=SimpleNamespace(value="confirmed"),
        inferred_by="naming",
    )
    return SimpleNamespace(edges=[edge])


def _service_with(rows: list[list], headers: list[str], dep=True):
    tindex = _make_table_index()
    committer = SimpleNamespace(
        load_table_indexes=lambda: [tindex],
        load_dependency_graph=lambda: _make_dep_graph(tindex.table_name) if dep else None,
    )
    applier = SimpleNamespace(
        read_rows=lambda table, offset, limit: {"headers": headers, "rows": rows}
    )
    return SimpleNamespace(index_committer=committer, change_applier=applier)


def test_ai_suggest_returns_available_id_and_dep():
    rows = [
        [1000, 100, "a"],
        [1001, 200, "b"],
        [1002, 300, "c"],
    ]
    svc = _service_with(rows, ["ID", "HP", "MysteryField"])
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get("/api/game/workbench/ai-suggest", params={"table": "HeroTable"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["table"] == "HeroTable"
    assert body["primary_key"] == "ID"
    # 下一个可用 ID 应是 1003
    assert body["available_ids"][0]["next_available"] == 1003
    # 反向依赖
    assert body["reusable_resources"][0]["from_table"] == "SkillTable"
    # 待确认字段
    names = [p["name"] for p in body["pending_confirms"]]
    assert "MysteryField" in names
    assert body["numeric_stats"] is None  # 未指定 field


def test_ai_suggest_numeric_field_returns_quantiles():
    rows = [[1000 + i, i * 10, ""] for i in range(10)]  # HP: 0,10..90
    svc = _service_with(rows, ["ID", "HP", "MysteryField"])
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get(
            "/api/game/workbench/ai-suggest",
            params={"table": "HeroTable", "field": "HP"},
        )
    assert resp.status_code == 200
    body = resp.json()
    stats = body["numeric_stats"]
    assert stats is not None
    assert stats["min"] == 0
    assert stats["max"] == 90
    assert body["suggested_range"] == [stats["p25"], stats["p75"]]
    assert len(body["samples"]) > 0


def test_ai_suggest_unknown_table_404():
    svc = _service_with([], ["ID"])
    with TestClient(_build_app(_ws(svc))) as client:
        resp = client.get("/api/game/workbench/ai-suggest", params={"table": "NoSuch"})
    assert resp.status_code == 404
