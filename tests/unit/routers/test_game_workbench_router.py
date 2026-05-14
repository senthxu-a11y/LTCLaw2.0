# -*- coding: utf-8 -*-
"""Unit tests for game workbench preview router."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_workbench as workbench_router_module
from ltclaw_gy_x.app.routers.game_workbench import router
from ltclaw_gy_x.game.change_applier import ApplyError
from ltclaw_gy_x.game.change_proposal import ChangeOp
from ltclaw_gy_x.game.workbench_source_write_service import WorkbenchSourceWriteOutcome


_CAPABILITY_UNSET = object()


def _build_app(workspace, capabilities=_CAPABILITY_UNSET):
    app = FastAPI()
    if capabilities is not _CAPABILITY_UNSET:
        app.state.capabilities = capabilities
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _ws(service):
    return SimpleNamespace(
        agent_id="agent-1",
        workspace_dir="/tmp/workspace",
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
    assert resp.json() == {
        "items": [],
        "impacts": [],
        "affected_tables": [],
        "impacts_metadata": {
            "source_type": "dependency_graph",
            "semantic_role": "technical_impact_evidence",
            "is_formal_map_relationship": False,
            "governs_release": False,
            "governs_rag": False,
            "governs_workbench_write": False,
        },
    }


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


def test_preview_includes_reverse_impacts():
    """preview 在 ok 项基础上 BFS 反向依赖图, 给出 affected_tables / impacts。"""

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

    edge = SimpleNamespace(
        from_table="Skill",
        from_field="OwnerHero",
        to_table="Hero",
        to_field="HP",
        confidence=SimpleNamespace(value="high"),
        inferred_by="convention",
    )
    dep = SimpleNamespace(edges=[edge])
    committer = SimpleNamespace(load_dependency_graph=lambda: dep)
    service = SimpleNamespace(
        change_applier=SimpleNamespace(dry_run=_dry_run),
        index_committer=committer,
    )
    workspace = _ws(service)
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    body = resp.json()
    assert resp.status_code == 200
    assert body["affected_tables"] == ["Skill"]
    assert len(body["impacts"]) == 1
    imp = body["impacts"][0]
    assert imp["from_table"] == "Skill"
    assert imp["from_field"] == "OwnerHero"
    assert imp["source_table"] == "Hero"
    assert imp["depth"] == 1
    assert imp["source_type"] == "dependency_graph"
    assert imp["semantic_role"] == "technical_impact_evidence"
    assert imp["is_formal_map_relationship"] is False
    assert body["impacts_metadata"] == {
        "source_type": "dependency_graph",
        "semantic_role": "technical_impact_evidence",
        "is_formal_map_relationship": False,
        "governs_release": False,
        "governs_rag": False,
        "governs_workbench_write": False,
    }


def test_preview_failed_items_have_no_impacts():
    """ok=False 的改动不参与反向影响 BFS。"""

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

    edge = SimpleNamespace(
        from_table="Skill", from_field="OwnerHero",
        to_table="Hero", to_field="HP",
        confidence=SimpleNamespace(value="high"),
        inferred_by="convention",
    )
    committer = SimpleNamespace(
        load_dependency_graph=lambda: SimpleNamespace(edges=[edge])
    )
    service = SimpleNamespace(
        change_applier=SimpleNamespace(dry_run=_dry_run),
        index_committer=committer,
    )
    workspace = _ws(service)
    with TestClient(_build_app(workspace)) as client:
        resp = client.post(
            "/api/game/workbench/preview",
            json={"changes": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}]},
        )
    body = resp.json()
    assert body["affected_tables"] == []
    assert body["impacts"] == []
    assert body["impacts_metadata"]["source_type"] == "dependency_graph"


def test_preview_no_committer_no_impacts():
    """index_committer 缺失时 impacts 为空, 不抛错。"""

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
    body = resp.json()
    assert body["items"][0]["ok"] is True
    assert body["impacts"] == []
    assert body["affected_tables"] == []
    assert body["impacts_metadata"]["source_type"] == "dependency_graph"


def test_source_write_requires_workbench_source_write_capability(monkeypatch):
    called = False

    async def _write(self, *, ops, reason):
        nonlocal called
        called = True
        return WorkbenchSourceWriteOutcome(ok=True, status_code=200, payload={"success": True})

    monkeypatch.setattr(workbench_router_module.WorkbenchSourceWriteService, "write", _write)
    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace()))

    with TestClient(_build_app(workspace, capabilities={"workbench.test.write"})) as client:
        response = client.post(
            "/api/game/workbench/source-write",
            json={
                "ops": [{"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}],
                "reason": "write source",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing capability: workbench.source.write"
    assert called is False


@pytest.mark.parametrize("capabilities", [{"workbench.read"}, {"workbench.read", "workbench.test.write"}])
def test_source_write_viewer_and_planner_capabilities_return_403(monkeypatch, capabilities):
    called = False

    async def _write(self, *, ops, reason):
        nonlocal called
        called = True
        return WorkbenchSourceWriteOutcome(ok=True, status_code=200, payload={"success": True})

    monkeypatch.setattr(workbench_router_module.WorkbenchSourceWriteService, "write", _write)
    workspace = _ws(SimpleNamespace(change_applier=SimpleNamespace()))

    with TestClient(_build_app(workspace, capabilities=capabilities)) as client:
        response = client.post(
            "/api/game/workbench/source-write",
            json={
                "ops": [{"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}],
                "reason": "write source",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing capability: workbench.source.write"
    assert called is False


def test_source_write_uses_injected_capabilities_and_calls_wrapper(monkeypatch):
    captured = {}

    async def _override(request: Request):
        request.state.capabilities = {"workbench.source.write"}
        return _ws(SimpleNamespace(change_applier=SimpleNamespace()))

    async def _write(self, *, ops, reason):
        captured["ops"] = ops
        captured["reason"] = reason
        return WorkbenchSourceWriteOutcome(
            ok=True,
            status_code=200,
            payload={
                "success": True,
                "source_files": ["tables/Hero.csv"],
                "audit_recorded": True,
            },
        )

    monkeypatch.setattr(workbench_router_module.WorkbenchSourceWriteService, "write", _write)
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = _override

    with TestClient(app) as client:
        response = client.post(
            "/api/game/workbench/source-write",
            json={
                "ops": [{"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 120}],
                "reason": "write source",
            },
        )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert captured["reason"] == "write source"
    assert captured["ops"][0].op == "update_cell"


def test_source_write_surfaces_wrapper_failure_and_does_not_trigger_release_calls(monkeypatch):
    async def _write(self, *, ops, reason):
        return WorkbenchSourceWriteOutcome(
            ok=False,
            status_code=400,
            payload={
                "message": "delete_row is blocked in workbench source write",
                "audit_recorded": True,
            },
        )

    monkeypatch.setattr(workbench_router_module.WorkbenchSourceWriteService, "write", _write)
    workspace = _ws(
        SimpleNamespace(
            change_applier=SimpleNamespace(),
            build_release=pytest.fail,
            publish_release=pytest.fail,
        )
    )

    async def _override(request: Request):
        request.state.capabilities = {"workbench.source.write"}
        return workspace

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = _override

    with TestClient(app) as client:
        response = client.post(
            "/api/game/workbench/source-write",
            json={
                "ops": [{"op": "delete_row", "table": "Hero", "row_id": 1}],
                "reason": "forbidden",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "delete_row is blocked in workbench source write"
    assert response.json()["detail"]["audit_recorded"] is True


def test_workbench_suggest_uses_workbench_suggest_model_type(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        workbench_router_module,
        'build_workbench_suggest_formal_context',
        lambda project_root, user_intent: {
            'status': 'grounded',
            'release_id': 'release-001',
            'reason': None,
            'evidence_catalog': [
                {
                    'evidence_ref': 'doc:combat.formula',
                    'title': 'Combat Overview',
                    'chunk_text': 'Combat damage uses release formula.',
                }
            ],
            'allowed_evidence_refs': ['doc:combat.formula'],
        },
    )

    async def _call_model_result(prompt, model_type="default"):
        captured["model_type"] = model_type
        captured['prompt'] = prompt
        return SimpleNamespace(ok=True, text='{"message":"ok","changes":[]}', error_code=None, message=None)

    async def _get_table(name):
        return SimpleNamespace(
            table_name=name,
            primary_key='ID',
            ai_summary='Hero summary.',
            fields=[
                SimpleNamespace(name='ID', type='int', description='primary id'),
                SimpleNamespace(name='HP', type='int', description='health'),
            ],
        )

    def _read_rows(table_name, offset, limit):
        return {
            'headers': ['ID', 'Name', 'HP'],
            'rows': [[1, 'Knight', 100]],
            'total': 1,
        }

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=_get_table, dependencies_of=lambda _name: {'upstream': [], 'downstream': []}),
        change_applier=SimpleNamespace(read_rows=_read_rows),
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )
    workspace = _ws(service)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            "/api/game/workbench/suggest",
            json={
                "user_intent": "把 Hero 表 HP 提高",
                "context_tables": ["Hero"],
                "current_pending": [{"table": "Hero", "row_id": 1, "field": "HP", "new_value": 110}],
                "chat_history": [{"role": "user", "content": "先看 Hero"}],
            },
        )

    assert response.status_code == 200
    assert captured["model_type"] == "workbench_suggest"
    assert 'Formal Knowledge Context' in captured['prompt']
    assert 'doc:combat.formula' in captured['prompt']
    assert 'Draft Overlay' in captured['prompt']


def test_workbench_suggest_surfaces_structured_router_failure(monkeypatch):
    async def _call_model_result(prompt, model_type="default"):
        return SimpleNamespace(ok=False, text="", error_code="no_active_model", message="No active model")

    service = SimpleNamespace(
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )
    workspace = _ws(service)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            "/api/game/workbench/suggest",
            json={"user_intent": "把 Hero 表 HP 提高", "context_tables": [], "current_pending": [], "chat_history": []},
        )

    assert response.status_code == 502
    assert response.json()["detail"]["error_code"] == "no_active_model"


def test_workbench_suggest_invalid_model_output_returns_explicit_error(monkeypatch):
    async def _call_model_result(prompt, model_type="default"):
        return SimpleNamespace(
            ok=True,
            text='not valid json at all',
            error_code=None,
            message=None,
        )

    service = SimpleNamespace(
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )
    workspace = _ws(service)

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            "/api/game/workbench/suggest",
            json={"user_intent": "把 Hero 表 HP 提高", "context_tables": [], "current_pending": [], "chat_history": []},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "error_code": "invalid_model_output",
        "message": "Workbench suggest model returned invalid JSON.",
        "raw": "not valid json at all",
    }


def test_workbench_suggest_no_current_release_keeps_formal_evidence_empty(monkeypatch):
    monkeypatch.setattr(
        workbench_router_module,
        'build_workbench_suggest_formal_context',
        lambda project_root, user_intent: {
            'status': 'no_current_release',
            'release_id': None,
            'reason': 'no_current_release',
            'evidence_catalog': [],
            'allowed_evidence_refs': [],
        },
    )
    captured = {}

    async def _call_model_result(prompt, model_type='default'):
        captured['prompt'] = prompt
        return SimpleNamespace(
            ok=True,
            text='{"message":"runtime only","changes":[{"table":"Hero","row_id":1,"field":"HP","new_value":120,"evidence_refs":["doc:fake"]}]}',
            error_code=None,
            message=None,
        )

    async def _get_table(name):
        return SimpleNamespace(
            table_name=name,
            primary_key='ID',
            ai_summary='Hero summary.',
            fields=[SimpleNamespace(name='ID', type='int', description='id'), SimpleNamespace(name='HP', type='int', description='hp')],
        )

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=_get_table, dependencies_of=lambda _name: {'upstream': [], 'downstream': []}),
        change_applier=SimpleNamespace(read_rows=lambda *_args: {'headers': ['ID', 'HP'], 'rows': [[1, 100]], 'total': 1}),
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )

    with TestClient(_build_app(_ws(service))) as client:
        response = client.post(
            '/api/game/workbench/suggest',
            json={'user_intent': '提高 Hero HP', 'context_tables': ['Hero'], 'current_pending': [], 'chat_history': []},
        )

    body = response.json()
    assert response.status_code == 200
    assert body['formal_context_status'] == 'no_current_release'
    assert body['evidence_refs'] == []
    assert body['changes'][0]['evidence_refs'] == []
    assert 'no_current_release' in captured['prompt']


@pytest.mark.parametrize(
    ('raw_change', 'expected_fragment'),
    [
        ({'table': 'Skill', 'row_id': 1, 'field': 'HP', 'new_value': 120}, 'outside context_tables'),
        ({'table': 'Hero', 'row_id': 1, 'field': 'Cost', 'new_value': 120}, 'is not a valid field'),
        ({'table': 'Hero', 'row_id': 99, 'field': 'HP', 'new_value': 120}, 'is not a valid Hero primary key'),
    ],
)
def test_workbench_suggest_filters_invalid_table_field_or_row(monkeypatch, raw_change, expected_fragment):
    monkeypatch.setattr(
        workbench_router_module,
        'build_workbench_suggest_formal_context',
        lambda project_root, user_intent: {
            'status': 'grounded',
            'release_id': 'release-001',
            'reason': None,
            'evidence_catalog': [],
            'allowed_evidence_refs': [],
        },
    )

    async def _call_model_result(prompt, model_type='default'):
        return SimpleNamespace(
            ok=True,
            text=f'{{"message":"candidate","changes":[{raw_change!r}]}}'.replace("'", '"'),
            error_code=None,
            message=None,
        )

    async def _get_table(name):
        return SimpleNamespace(
            table_name=name,
            primary_key='ID',
            ai_summary='Hero summary.',
            fields=[SimpleNamespace(name='ID', type='int', description='id'), SimpleNamespace(name='HP', type='int', description='hp')],
        )

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=_get_table, dependencies_of=lambda _name: {'upstream': [], 'downstream': []}),
        change_applier=SimpleNamespace(read_rows=lambda *_args: {'headers': ['ID', 'HP'], 'rows': [[1, 100]], 'total': 1}),
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )

    with TestClient(_build_app(_ws(service))) as client:
        response = client.post(
            '/api/game/workbench/suggest',
            json={'user_intent': '提高 Hero HP', 'context_tables': ['Hero'], 'current_pending': [], 'chat_history': []},
        )

    body = response.json()
    assert response.status_code == 200
    assert body['changes'] == []
    assert expected_fragment in body['message']


def test_workbench_suggest_returns_validated_change_metadata(monkeypatch):
    monkeypatch.setattr(
        workbench_router_module,
        'build_workbench_suggest_formal_context',
        lambda project_root, user_intent: {
            'status': 'grounded',
            'release_id': 'release-001',
            'reason': None,
            'evidence_catalog': [
                {'evidence_ref': 'doc:combat.formula', 'title': 'Combat Overview', 'chunk_text': 'Combat damage uses release formula.'}
            ],
            'allowed_evidence_refs': ['doc:combat.formula'],
        },
    )

    async def _call_model_result(prompt, model_type='default'):
        return SimpleNamespace(
            ok=True,
            text='{"message":"adjusted","changes":[{"table":"Hero","row_id":1,"field":"HP","new_value":125,"reason":"Keep hero competitive.","confidence":0.88,"uses_draft_overlay":true,"evidence_refs":["doc:combat.formula","doc:fake"]}]}',
            error_code=None,
            message=None,
        )

    async def _get_table(name):
        return SimpleNamespace(
            table_name=name,
            primary_key='ID',
            ai_summary='Hero summary.',
            fields=[SimpleNamespace(name='ID', type='int', description='id'), SimpleNamespace(name='HP', type='int', description='hp')],
        )

    service = SimpleNamespace(
        query_router=SimpleNamespace(get_table=_get_table, dependencies_of=lambda _name: {'upstream': [], 'downstream': []}),
        change_applier=SimpleNamespace(read_rows=lambda *_args: {'headers': ['ID', 'Name', 'HP'], 'rows': [[1, 'Knight', 100]], 'total': 1}),
        _model_router=lambda: SimpleNamespace(call_model_result=_call_model_result),
    )

    with TestClient(_build_app(_ws(service))) as client:
        response = client.post(
            '/api/game/workbench/suggest',
            json={
                'user_intent': '提高 Hero HP',
                'context_tables': ['Hero'],
                'current_pending': [{'table': 'Hero', 'row_id': 1, 'field': 'HP', 'new_value': 110}],
                'chat_history': [{'role': 'assistant', 'content': '之前建议先看 combat formula'}],
            },
        )

    body = response.json()
    assert response.status_code == 200
    assert body['evidence_refs'] == ['doc:combat.formula']
    assert body['formal_context_status'] == 'grounded'
    assert len(body['changes']) == 1
    change = body['changes'][0]
    assert change['confidence'] == 0.88
    assert change['uses_draft_overlay'] is True
    assert change['source_release_id'] == 'release-001'
    assert change['validation_status'] == 'validated'
    assert change['evidence_refs'] == ['doc:combat.formula']
