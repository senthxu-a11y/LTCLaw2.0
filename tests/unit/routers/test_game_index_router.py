from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_index import router
from ltclaw_gy_x.game.change_applier import ChangeApplier
from ltclaw_gy_x.game.config import (
    FilterConfig,
    PathRule,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.models import TableIndex
from ltclaw_gy_x.game.paths import get_project_raw_table_index_path
from ltclaw_gy_x.game.query_router import QueryRouter


def _build_app(workspace):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_agent_for_request] = lambda: workspace
    return app


def _project_config(project_root):
    return ProjectConfig(
        project=ProjectMeta(name="Test Game", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root=str(project_root), poll_interval_seconds=300, jitter_seconds=30),
        paths=[PathRule(path="Tables/*", semantic="table", system="core")],
        filters=FilterConfig(include_ext=[".csv"], exclude_glob=[]),
        table_convention=TableConvention(header_row=1, primary_key_field="ID"),
        doc_templates={},
        models={},
    )


def _workspace(service):
    return SimpleNamespace(service_manager=SimpleNamespace(services={"game_service": service}))


def _write_minimal_raw_only_project(project_root):
    table_dir = project_root / "Tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    (table_dir / "HeroTable.csv").write_text(
        "ID,Name,HP,Attack\n1,HeroA,100,20\n",
        encoding="utf-8",
    )

    raw_index_path = get_project_raw_table_index_path(project_root, "HeroTable")
    raw_index_path.parent.mkdir(parents=True, exist_ok=True)
    raw_index_path.write_text(
        TableIndex(
            table_name="HeroTable",
            source_path="Tables/HeroTable.csv",
            source_hash="sha256:hero",
            svn_revision=1,
            system="core",
            row_count=1,
            header_row=1,
            primary_key="ID",
            ai_summary="Hero table",
            ai_summary_confidence=0.1,
            fields=[],
            id_ranges=[],
            last_indexed_at="2026-05-15T00:00:00Z",
            indexer_model="rule_only",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )


def test_index_routes_fall_back_to_project_raw_indexes(tmp_path):
    project_root = tmp_path / "project-root"
    _write_minimal_raw_only_project(project_root)
    project_config = _project_config(project_root)
    service = SimpleNamespace(
        configured=True,
        project_config=project_config,
        user_config=SimpleNamespace(my_role="maintainer", svn_local_root=str(project_root)),
        _runtime_svn_root=lambda: project_root,
    )
    service.query_router = QueryRouter(service)
    service.change_applier = ChangeApplier(project_config, project_root)

    with TestClient(_build_app(_workspace(service))) as client:
        tables_response = client.get("/api/game/index/tables", params={"page": 1, "size": 20})
        rows_response = client.get("/api/game/index/tables/HeroTable/rows", params={"offset": 0, "limit": 20})

    assert tables_response.status_code == 200
    assert tables_response.json()["items"] == [
        {
            "schema_version": "table-index.v1",
            "table_name": "HeroTable",
            "source_path": "Tables/HeroTable.csv",
            "source_hash": "sha256:hero",
            "svn_revision": 1,
            "system": "core",
            "row_count": 1,
            "header_row": 1,
            "primary_key": "ID",
            "ai_summary": "Hero table",
            "ai_summary_confidence": 0.1,
            "fields": [],
            "id_ranges": [],
            "last_indexed_at": "2026-05-15T00:00:00Z",
            "indexer_model": "rule_only",
        }
    ]

    assert rows_response.status_code == 200
    assert rows_response.json()["headers"] == ["ID", "Name", "HP", "Attack"]
    assert rows_response.json()["rows"] == [["1", "HeroA", "100", "20"]]


def test_viewer_still_cannot_rebuild_index(tmp_path):
    project_root = tmp_path / "project-root"
    project_root.mkdir(parents=True, exist_ok=True)
    service = SimpleNamespace(
        query_router=SimpleNamespace(),
        change_applier=None,
        project_config=object(),
        user_config=SimpleNamespace(my_role="viewer"),
    )

    with TestClient(_build_app(_workspace(service))) as client:
        response = client.post("/api/game/index/rebuild")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only maintainers can rebuild index"