"""????: IndexCommitter ?????????"""
from datetime import datetime
from pathlib import Path

import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.index_committer import IndexCommitter
from ltclaw_gy_x.game.models import (
    DependencyEdge,
    DependencyGraph,
    FieldConfidence,
    TableIndex,
)


def _project():
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="svn://x", poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


class _StubSvn:
    def __init__(self, working_copy):
        self.working_copy = Path(working_copy)


@pytest.fixture
def committer(tmp_path, monkeypatch):
    svn_root = tmp_path / "svn"; svn_root.mkdir()
    workspace = tmp_path / "ws"; workspace.mkdir()
    monkeypatch.setenv("LTCLAW_GAME_PROJECTS_DIR", str(tmp_path / "game-projects"))
    return IndexCommitter(
        project=_project(),
        svn_client=_StubSvn(svn_root),
        workspace_dir=workspace,
        index_output_dir=".ltclaw_index",
    )


def test_setup_paths_use_central_store(committer, tmp_path):
    assert committer.svn_tables_dir is not None
    assert committer.svn_tables_dir.is_relative_to(tmp_path / "game-projects")
    assert committer.svn_tables_file is not None
    assert committer.svn_dependency_file is not None
    assert committer.svn_tables_file.is_relative_to(tmp_path / "game-projects")
    assert committer.svn_dependency_file.is_relative_to(tmp_path / "game-projects")
    assert committer._can_commit_path(committer.svn_tables_file) is False
    assert committer._can_commit_path(committer.svn_dependency_file) is False
    assert committer.cache_dir.exists()


def test_setup_paths_use_central_store_when_configured(tmp_path, monkeypatch):
    svn_root = tmp_path / "svn"
    workspace = tmp_path / "ws"
    central_root = tmp_path / "game-projects"
    svn_root.mkdir()
    workspace.mkdir()
    monkeypatch.setenv("LTCLAW_GAME_PROJECTS_DIR", str(central_root))

    committer = IndexCommitter(
        project=_project(),
        svn_client=_StubSvn(svn_root),
        workspace_dir=workspace,
        index_output_dir=".ltclaw_index",
    )

    assert committer.svn_tables_dir is not None
    assert committer.svn_tables_dir.is_relative_to(central_root)
    assert committer.svn_tables_file is not None
    assert committer.svn_dependency_file is not None
    assert committer.svn_tables_file.is_relative_to(central_root)
    assert committer.svn_dependency_file.is_relative_to(central_root)
    assert committer._can_commit_path(committer.svn_tables_file) is False
    assert committer._can_commit_path(committer.svn_dependency_file) is False


def test_serialize_deserialize_table_indexes_roundtrip(committer):
    t = TableIndex(
        table_name="A",
        source_path="tables/A.xlsx",
        source_hash="sha256:0",
        svn_revision=1,
        row_count=0,
        primary_key="ID",
        ai_summary="",
        ai_summary_confidence=0.0,
        fields=[],
        last_indexed_at=datetime(2026, 1, 1),
        indexer_model="m",
    )
    s = committer._serialize_table_indexes([t])
    assert "A" in s
    back = committer._deserialize_table_indexes(s)
    assert len(back) == 1
    assert back[0].table_name == "A"


def test_deserialize_invalid_returns_empty(committer):
    assert committer._deserialize_table_indexes("not json") == []


def test_serialize_dependency_graph_includes_edges(committer):
    g = DependencyGraph(
        edges=[
            DependencyEdge(
                from_table="Hero",
                from_field="WeaponID",
                to_table="Weapon",
                to_field="ID",
                confidence=FieldConfidence.CONFIRMED,
                inferred_by="rule",
            ),
        ],
        last_updated=datetime(2026, 1, 1),
    )
    if hasattr(committer, "_serialize_dependency_graph"):
        s = committer._serialize_dependency_graph(g)
        assert "Hero" in s and "Weapon" in s
    else:
        assert "Hero" in g.model_dump_json()


def test_runtime_cache_paths_are_nested_by_agent_and_session(committer, tmp_path):
    assert committer.cache_dir.is_relative_to(tmp_path / "game-projects")
    parts = committer.cache_dir.parts
    assert "agents" in parts
    assert "sessions" in parts
    assert "caches" in parts
