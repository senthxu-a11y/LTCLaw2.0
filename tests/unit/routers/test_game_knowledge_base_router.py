from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_knowledge_base as kb_router_module
from ltclaw_gy_x.app.routers.game_knowledge_base import router


class _FakeEntry:
    def __init__(self) -> None:
        self.id = "kb-1"
        self.title = "Combat Note"
        self.summary = "legacy kb summary"
        self.category = "design"
        self.source = "manual"
        self.tags = ["combat"]
        self.extra = {"doc_path": "Docs/Combat.md"}

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "source": self.source,
            "tags": self.tags,
            "extra": self.extra,
            "created_at": 0,
        }


class _FakeStore:
    size = 1

    def list_entries(self):
        return [_FakeEntry()]

    def add(self, **_kwargs):
        return _FakeEntry()

    def update(self, _entry_id, **_kwargs):
        return _FakeEntry()

    def delete(self, _entry_id):
        return True

    def search(self, query, *, top_k, category=None):
        assert query == "combat"
        assert top_k == 5
        assert category == "design"
        return [(_FakeEntry(), 0.91)]


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def test_kb_search_is_legacy_only_and_does_not_call_unified_search(monkeypatch):
    workspace = SimpleNamespace(
        workspace_dir="/tmp/workspace",
        service_manager=SimpleNamespace(
            services={"game_service": SimpleNamespace(configured=True)}
        ),
    )

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(kb_router_module, "get_agent_for_request", _get_agent)
    monkeypatch.setattr(kb_router_module, "get_kb_store", lambda _path: _FakeStore())
    monkeypatch.setattr(
        kb_router_module,
        "unified_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call unified_search")),
        raising=False,
    )

    with TestClient(_build_app(workspace)) as client:
        response = client.post(
            "/api/game-knowledge-base/search",
            json={"query": "combat", "top_k": 5, "category": "design"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "legacy_kb_search"
    assert body["scope"] == "legacy"
    assert body["semantic_role"] == "debug_migration_only"
    assert body["affects_release"] is False
    assert body["affects_rag"] is False
    assert body["affects_workbench_suggest"] is False
    assert body["items"][0]["source_type"] == "kb_entry"


def test_kb_list_entries_returns_legacy_metadata(monkeypatch):
    workspace = SimpleNamespace(workspace_dir="/tmp/workspace")

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(kb_router_module, "get_agent_for_request", _get_agent)
    monkeypatch.setattr(kb_router_module, "get_kb_store", lambda _path: _FakeStore())

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game-knowledge-base/entries")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "legacy_kb_entries"
    assert body["scope"] == "legacy"
    assert body["semantic_role"] == "debug_migration_only"
    assert body["affects_release"] is False
    assert body["affects_rag"] is False
    assert body["affects_workbench_suggest"] is False


def test_kb_stats_returns_legacy_metadata(monkeypatch):
    workspace = SimpleNamespace(workspace_dir="/tmp/workspace")

    async def _get_agent(_request):
        return workspace

    monkeypatch.setattr(kb_router_module, "get_agent_for_request", _get_agent)
    monkeypatch.setattr(kb_router_module, "get_kb_store", lambda _path: _FakeStore())

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game-knowledge-base/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "legacy_kb_stats"
    assert body["scope"] == "legacy"
    assert body["semantic_role"] == "debug_migration_only"
    assert body["affects_release"] is False
    assert body["affects_rag"] is False
    assert body["affects_workbench_suggest"] is False
