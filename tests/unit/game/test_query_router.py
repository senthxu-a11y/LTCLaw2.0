from __future__ import annotations

from types import SimpleNamespace

import pytest

from ltclaw_gy_x.game.models import TableIndex
from ltclaw_gy_x.game.paths import get_project_raw_table_index_path
from ltclaw_gy_x.game.query_router import QueryRouter


def _service(project_root, *, configured=True):
    return SimpleNamespace(
        configured=configured,
        project_config=SimpleNamespace(svn=SimpleNamespace(root=str(project_root))),
        user_config=SimpleNamespace(svn_local_root=str(project_root)),
        _runtime_svn_root=lambda: project_root,
    )


def _write_raw_table_index(project_root, table_name: str, *, source_path: str, system: str = "core"):
    index_path = get_project_raw_table_index_path(project_root, table_name)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        TableIndex(
            table_name=table_name,
            source_path=source_path,
            source_hash="sha256:test",
            svn_revision=1,
            system=system,
            row_count=1,
            header_row=1,
            primary_key="ID",
            ai_summary=f"{table_name} summary",
            ai_summary_confidence=0.1,
            fields=[],
            id_ranges=[],
            last_indexed_at="2026-05-15T00:00:00Z",
            indexer_model="rule_only",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_list_tables_falls_back_to_project_raw_indexes(tmp_path):
    project_root = tmp_path / "project-root"
    _write_raw_table_index(project_root, "HeroTable", source_path="Tables/HeroTable.csv")

    router = QueryRouter(_service(project_root))

    payload = await router.list_tables(page=1, size=20)

    assert payload["total"] == 1
    assert payload["items"][0]["table_name"] == "HeroTable"
    assert payload["items"][0]["source_path"] == "Tables/HeroTable.csv"


@pytest.mark.asyncio
async def test_get_table_falls_back_to_project_raw_index(tmp_path):
    project_root = tmp_path / "project-root"
    _write_raw_table_index(project_root, "HeroTable", source_path="Tables/HeroTable.csv")

    router = QueryRouter(_service(project_root))

    table = await router.get_table("HeroTable")

    assert table is not None
    assert table.table_name == "HeroTable"
    assert table.source_path == "Tables/HeroTable.csv"


@pytest.mark.asyncio
async def test_list_tables_uses_runtime_root_even_when_service_not_configured(tmp_path):
    project_root = tmp_path / "project-root"
    _write_raw_table_index(project_root, "HeroTable", source_path="Tables/HeroTable.csv")

    router = QueryRouter(_service(project_root, configured=False))

    payload = await router.list_tables(page=1, size=20)

    assert payload["total"] == 1
    assert payload["items"][0]["table_name"] == "HeroTable"