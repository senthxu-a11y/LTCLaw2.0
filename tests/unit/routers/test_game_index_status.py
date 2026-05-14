from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_index as game_index_module
from ltclaw_gy_x.app.routers.game_index import router


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def test_index_status_marks_retrieval_as_legacy(monkeypatch):
    workspace = SimpleNamespace(
        service_manager=SimpleNamespace(
            services={
                "game_service": SimpleNamespace(
                    configured=True,
                    query_router=object(),
                )
            }
        )
    )
    monkeypatch.setattr(
        game_index_module,
        "get_retrieval_status",
        lambda *_args, **_kwargs: {"scope": "legacy", "semantic_role": "debug_migration_only"},
    )

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game/index/status")

    assert response.status_code == 200
    body = response.json()
    assert body["formal_knowledge"]["source"] == "current_release"
    assert body["formal_knowledge"]["legacy_retrieval_included"] is False
    assert body["legacy_retrieval"]["scope"] == "legacy"
