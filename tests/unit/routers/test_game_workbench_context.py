# -*- coding: utf-8 -*-
"""Unit tests for /game/workbench/context and /damage-chain endpoints."""
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
        service_manager=SimpleNamespace(
            services={"game_service": service} if service else {}
        )
    )


async def _async_table_index(name="HeroTable"):
    return SimpleNamespace(
        table_name=name,
        system="Combat",
        primary_key="ID",
        row_count=2,
        fields=[
            SimpleNamespace(name="ID", type="int", description="主键"),
            SimpleNamespace(name="HP", type="int", description="生命值"),
        ],
    )


# ────────── /context ──────────


def test_context_returns_tables_and_records():
    async def get_table(name):
        return await _async_table_index(name)

    def read_rows(name, offset, limit):
        return {
            "headers": ["ID", "HP"],
            "rows": [[1, 100], [2, 200]],
            "total": 2,
        }

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=get_table),
        change_applier=SimpleNamespace(read_rows=read_rows),
    )
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.get("/api/game/workbench/context", params={"tableIds": "HeroTable"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["tables"]) == 1
        t = body["tables"][0]
        assert t["tableName"] == "HeroTable"
        assert t["primaryKey"] == "ID"
        assert {f["key"] for f in t["fields"]} == {"ID", "HP"}
        assert len(t["records"]) == 2
        assert t["records"][0]["id"] == 1
        # field 序列化为 [{key,value}]
        first_record_fields = {f["key"]: f["value"] for f in t["records"][0]["fields"]}
        assert first_record_fields == {"ID": 1, "HP": 100}
        assert body["focusField"] is None


def test_context_focus_field_round_trip():
    async def get_table(name):
        return await _async_table_index(name)

    def read_rows(name, offset, limit):
        return {"headers": ["ID"], "rows": [[1]], "total": 1}

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=get_table),
        change_applier=SimpleNamespace(read_rows=read_rows),
    )
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.get(
            "/api/game/workbench/context",
            params={"tableIds": "HeroTable", "focusTable": "HeroTable", "focusField": "HP"},
        )
        assert resp.status_code == 200
        assert resp.json()["focusField"] == {"table": "HeroTable", "field": "HP"}


def test_context_412_when_no_service():
    with TestClient(_build_app(_ws(None))) as client:
        resp = client.get("/api/game/workbench/context", params={"tableIds": "X"})
        # _service raises 404 when service missing
        assert resp.status_code == 404


def test_context_412_when_no_query_router():
    service = SimpleNamespace(query_router=None, change_applier=object())
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.get("/api/game/workbench/context", params={"tableIds": "X"})
        assert resp.status_code == 412


def test_context_skips_unknown_tables():
    async def get_table(name):
        return None  # always missing

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=get_table),
        change_applier=SimpleNamespace(
            read_rows=lambda *a, **k: {"headers": [], "rows": [], "total": 0}
        ),
    )
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.get("/api/game/workbench/context", params={"tableIds": "Ghost"})
        assert resp.status_code == 200
        assert resp.json()["tables"] == []


# ────────── /damage-chain ──────────


def test_damage_chain_default_no_changes():
    service = SimpleNamespace()
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.post(
            "/api/game/workbench/damage-chain",
            json={"formulaKey": "default", "changes": []},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["formula"] == "ATK * DamageCoeff * (1 - DefenseRatio)"
        assert len(body["variables"]) == 3
        assert all(v["isChanged"] is False for v in body["variables"])
        assert body["deltaPercent"] == 0.0
        assert body["resultBefore"] == body["resultAfter"]


def test_damage_chain_with_atk_change():
    service = SimpleNamespace()
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.post(
            "/api/game/workbench/damage-chain",
            json={
                "formulaKey": "default",
                "changes": [
                    {"table": "HeroTable", "row_id": 1, "field": "ATK", "new_value": 200},
                ],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        atk = next(v for v in body["variables"] if v["name"] == "ATK")
        assert atk["isChanged"] is True
        assert atk["value"] == 200.0
        # before=100*1*(1-0.3)=70, after=200*1*0.7=140, delta=100%
        assert body["resultBefore"] == 70.0
        assert body["resultAfter"] == 140.0
        assert body["deltaPercent"] == 100.0


def test_damage_chain_unsupported_formula_key():
    service = SimpleNamespace()
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.post(
            "/api/game/workbench/damage-chain",
            json={"formulaKey": "complex_skill_v2", "changes": []},
        )
        assert resp.status_code == 422


def test_damage_chain_ignores_non_numeric_changes():
    service = SimpleNamespace()
    with TestClient(_build_app(_ws(service))) as client:
        resp = client.post(
            "/api/game/workbench/damage-chain",
            json={
                "formulaKey": "default",
                "changes": [
                    {"table": "HeroTable", "row_id": 1, "field": "ATK", "new_value": "not_a_number"},
                ],
            },
        )
        assert resp.status_code == 200
        # 改动被忽略, 结果应等于无改动
        body = resp.json()
        assert body["deltaPercent"] == 0.0
