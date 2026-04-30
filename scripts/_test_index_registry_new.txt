"""单元测试: registry.json 序列化与持久化。"""
import asyncio
import json
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
    ChangeSet,
    DependencyEdge,
    DependencyGraph,
    FieldConfidence,
    TableIndex,
)


def _project():
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="x", poll_interval_seconds=300, jitter_seconds=30),
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
def committer(tmp_path):
    src_root = tmp_path / "src"; src_root.mkdir()
    workspace = tmp_path / "ws"; workspace.mkdir()
    return IndexCommitter(
        project=_project(),
        svn_client=_StubSvn(src_root),
        workspace_dir=workspace,
        index_output_dir=".ltclaw_index",
    )


def _make_table(name, source="t.xlsx"):
    return TableIndex(
        table_name=name,
        source_path=source,
        source_hash="sha256:abc",
        svn_revision=10,
        row_count=42,
        primary_key="ID",
        ai_summary="x",
        ai_summary_confidence=0.8,
        fields=[],
        last_indexed_at=datetime(2026, 1, 1),
        indexer_model="m",
    )


def _make_graph():
    return DependencyGraph(
        edges=[
            DependencyEdge(
                from_table="A", from_field="X", to_table="B", to_field="ID",
                confidence=FieldConfidence.CONFIRMED, inferred_by="rule",
            ),
        ],
        last_updated=datetime(2026, 1, 1),
    )


def test_registry_serialization_shape(committer):
    s = committer._serialize_registry([_make_table("Hero")], _make_graph())
    data = json.loads(s)
    assert data["schema_version"] == "registry.v1"
    assert data["dependencies_count"] == 1
    assert len(data["tables"]) == 1
    entry = data["tables"][0]
    assert entry["name"] == "Hero"
    assert entry["row_count"] == 42
    assert "table_indexes_sha256" in data["integrity"]
    assert "dependency_graph_sha256" in data["integrity"]
    assert "generated_at" in data


def test_registry_integrity_hash_matches_payload(committer):
    import hashlib
    tables = [_make_table("A")]
    g = _make_graph()
    s = committer._serialize_registry(tables, g)
    data = json.loads(s)
    expected_t = hashlib.sha256(committer._serialize_table_indexes(tables).encode("utf-8")).hexdigest()
    expected_g = hashlib.sha256(committer._serialize_dependency_graph(g).encode("utf-8")).hexdigest()
    assert data["integrity"]["table_indexes_sha256"] == expected_t
    assert data["integrity"]["dependency_graph_sha256"] == expected_g


def test_save_all_writes_registry_to_cache_and_svn(committer):
    cs = ChangeSet(from_rev=0, to_rev=1, added=[], modified=[], deleted=[])
    asyncio.run(committer.save_all([_make_table("A")], _make_graph(), cs))
    assert committer.registry_file.exists()
    cache = json.loads(committer.registry_file.read_text(encoding="utf-8"))
    assert cache["schema_version"] == "registry.v1"
    assert committer.svn_registry_file is not None
    assert committer.svn_registry_file.exists()
    out = json.loads(committer.svn_registry_file.read_text(encoding="utf-8"))
    assert out["dependencies_count"] == 1


def test_load_registry_roundtrip(committer):
    cs = ChangeSet(from_rev=0, to_rev=1, added=[], modified=[], deleted=[])
    asyncio.run(committer.save_all([_make_table("Hero")], _make_graph(), cs))
    loaded = committer.load_registry()
    assert loaded is not None
    assert loaded["tables"][0]["name"] == "Hero"
