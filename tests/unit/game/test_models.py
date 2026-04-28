"""单元测试: game.models 序列化往返。"""
from datetime import datetime

import pytest

from ltclaw_gy_x.game.models import (
    ChangeSet,
    CommitResult,
    DependencyEdge,
    DependencyGraph,
    DependencySnapshot,
    DocIndex,
    FieldConfidence,
    FieldInfo,
    FieldPatch,
    SystemGroup,
    TableIndex,
    TablePage,
)


def _now():
    return datetime(2026, 1, 1, 12, 0, 0)


def test_field_info_roundtrip():
    f = FieldInfo(
        name="HeroID",
        type="int",
        description="ID",
        confidence=FieldConfidence.CONFIRMED,
        confirmed_by="alice",
        confirmed_at=_now(),
        ai_raw_description="raw",
        references=["Hero"],
        tags=["fk"],
    )
    data = f.model_dump(mode="json")
    back = FieldInfo.model_validate(data)
    assert back.name == "HeroID"
    assert back.confidence == FieldConfidence.CONFIRMED
    assert back.confirmed_at == _now()


def test_table_index_roundtrip():
    t = TableIndex(
        table_name="HeroTable",
        source_path="tables/Hero.xlsx",
        source_hash="sha256:abc",
        svn_revision=42,
        system="combat",
        row_count=100,
        primary_key="ID",
        ai_summary="hero",
        ai_summary_confidence=0.9,
        fields=[],
        last_indexed_at=_now(),
        indexer_model="gpt-4",
    )
    data = t.model_dump(mode="json")
    back = TableIndex.model_validate(data)
    assert back.schema_version == "table-index.v1"
    assert back.svn_revision == 42
    assert back.row_count == 100


def test_doc_index_roundtrip():
    d = DocIndex(
        source_path="docs/sys.md",
        source_hash="sha256:def",
        svn_revision=10,
        doc_type="system",
        title="bag",
        summary="bag sys",
        related_tables=["Item"],
        last_indexed_at=_now(),
    )
    back = DocIndex.model_validate(d.model_dump(mode="json"))
    assert back.title == "bag"
    assert back.related_tables == ["Item"]


def test_dependency_edge_and_graph():
    edge = DependencyEdge(
        from_table="Hero",
        from_field="WeaponID",
        to_table="Weapon",
        to_field="ID",
        confidence=FieldConfidence.HIGH_AI,
        inferred_by="rule",
    )
    g = DependencyGraph(edges=[edge], last_updated=_now())
    back = DependencyGraph.model_validate(g.model_dump(mode="json"))
    assert len(back.edges) == 1
    assert back.edges[0].inferred_by == "rule"


def test_changeset_only_documented_fields():
    cs = ChangeSet(
        from_rev=1,
        to_rev=5,
        added=["a.xlsx"],
        modified=["b.xlsx"],
        deleted=["c.xlsx"],
    )
    data = cs.model_dump(mode="json")
    assert set(data.keys()) == {"from_rev", "to_rev", "added", "modified", "deleted"}


def test_commit_result_optional_fields():
    cr = CommitResult()
    assert cr.revision is None
    assert cr.files_committed == 0
    cr2 = CommitResult.model_validate({"revision": 7, "files_committed": 3})
    assert cr2.revision == 7


def test_field_patch_partial():
    p = FieldPatch(description="d")
    assert p.confidence is None
    assert p.confirmed_by is None
    assert p.description == "d"


def test_system_group_and_pagination():
    sg = SystemGroup(name="combat", tables=["Hero"], source="config")
    back = SystemGroup.model_validate(sg.model_dump(mode="json"))
    assert back.source == "config"

    page = TablePage(total=0, page=1, size=50, items=[])
    back2 = TablePage.model_validate(page.model_dump(mode="json"))
    assert back2.total == 0
    assert back2.items == []


def test_dependency_snapshot_default_empty():
    snap = DependencySnapshot()
    assert snap.upstream == []
    assert snap.downstream == []