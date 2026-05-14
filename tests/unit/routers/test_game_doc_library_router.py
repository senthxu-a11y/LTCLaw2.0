from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers import game_doc_library as doc_library_module
from ltclaw_gy_x.app.routers.game_doc_library import router


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _workspace(tmp_path: Path):
    service = SimpleNamespace(
        user_config=SimpleNamespace(svn_local_root=str(tmp_path)),
        project_config=SimpleNamespace(
            svn=SimpleNamespace(root=str(tmp_path)),
            paths=[],
            filters=SimpleNamespace(include_ext=[], exclude_glob=[]),
        ),
    )
    return SimpleNamespace(
        workspace_dir=tmp_path,
        service_manager=SimpleNamespace(services={"game_service": service}),
    )


def test_doc_library_status_marks_sync_and_retrieval_as_legacy(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Docs"
    docs_dir.mkdir()
    (docs_dir / "Combat.md").write_text("# Combat\n", encoding="utf-8")
    workspace = _workspace(tmp_path)

    monkeypatch.setattr(
        doc_library_module,
        "get_retrieval_status",
        lambda *_args, **_kwargs: {"scope": "legacy", "semantic_role": "debug_migration_only"},
    )

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game-doc-library/status")

    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_sync"]["mode"] == "legacy_kb_migration_only"
    assert body["knowledge_sync"]["affects_release"] is False
    assert body["legacy_retrieval"]["scope"] == "legacy"


def test_doc_library_list_returns_legacy_scope_metadata(tmp_path):
    docs_dir = tmp_path / "Docs"
    docs_dir.mkdir()
    (docs_dir / "Combat.md").write_text("# Combat\n", encoding="utf-8")
    workspace = _workspace(tmp_path)

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game-doc-library/documents")

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "legacy_doc_library"
    assert body["knowledge_sync"] == {
        "mode": "legacy_kb_migration_only",
        "affects_release": False,
    }


def test_doc_library_detail_returns_legacy_sync_metadata(tmp_path):
    docs_dir = tmp_path / "Docs"
    docs_dir.mkdir()
    (docs_dir / "Combat.md").write_text("# Combat\n", encoding="utf-8")
    workspace = _workspace(tmp_path)

    with TestClient(_build_app(workspace)) as client:
        response = client.get("/api/game-doc-library/documents/Docs/Combat.md")

    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_sync"] == {
        "mode": "legacy_kb_migration_only",
        "affects_release": False,
    }


def test_doc_library_update_returns_legacy_sync_metadata(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Docs"
    docs_dir.mkdir()
    (docs_dir / "Combat.md").write_text("# Combat\n", encoding="utf-8")
    workspace = _workspace(tmp_path)

    monkeypatch.setattr(doc_library_module, "_sync_document_to_kb", lambda *_args, **_kwargs: "kb-1")

    with TestClient(_build_app(workspace)) as client:
        response = client.patch("/api/game-doc-library/documents/Docs/Combat.md", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["legacy_kb_entry_id"] == "kb-1"
    assert body["knowledge_sync"]["mode"] == "legacy_kb_migration_only"
    assert body["knowledge_sync"]["affects_release"] is False