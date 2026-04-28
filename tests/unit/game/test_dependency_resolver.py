"""单元测试: DependencyResolver (规则层)。"""
from datetime import datetime

import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.dependency_resolver import DependencyResolver
from ltclaw_gy_x.game.models import FieldConfidence, FieldInfo, TableIndex


def _now():
    return datetime(2026, 1, 1)


def _make_project():
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="svn://x", poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


def _table(name, fields, primary_key="ID"):
    return TableIndex(
        table_name=name,
        source_path=f"tables/{name}.xlsx",
        source_hash="sha256:0",
        svn_revision=1,
        row_count=len(fields),
        primary_key=primary_key,
        ai_summary="",
        ai_summary_confidence=0.0,
        fields=fields,
        last_indexed_at=_now(),
        indexer_model="test",
    )


def _field(name, typ="int"):
    return FieldInfo(name=name, type=typ, description="", confidence=FieldConfidence.HIGH_AI)


@pytest.fixture
def resolver():
    return DependencyResolver(project=_make_project(), model_router=None)


def test_extract_table_name_from_field_strips_suffix(resolver):
    assert resolver._extract_table_name_from_field("HeroID") == "Hero"
    assert resolver._extract_table_name_from_field("WeaponRef") == "Weapon"
    assert resolver._extract_table_name_from_field("ID") is None


def test_find_target_table_handles_table_suffix(resolver):
    hero = _table("HeroTable", [_field("ID")])
    target = resolver._find_target_table("Hero", [hero])
    assert target is not None
    assert target.table_name == "HeroTable"


def test_extract_foreign_key_candidates_pattern(resolver):
    weapon = _table("Weapon", [_field("ID")])
    hero = _table("Hero", [_field("ID"), _field("WeaponID")])
    cands = resolver._extract_foreign_key_candidates([hero, weapon])
    weapon_cands = [c for c in cands if c["from_field"] == "WeaponID"]
    assert len(weapon_cands) == 1
    assert weapon_cands[0]["referenced_name"].lower() == "weapon"
    assert weapon_cands[0]["pattern_matched"] is True


def test_resolve_rule_based_dependencies_emits_edge(resolver):
    weapon = _table("Weapon", [_field("ID")])
    hero = _table("Hero", [_field("ID"), _field("WeaponID")])
    edges = resolver._resolve_rule_based_dependencies([hero, weapon])
    fk_edges = [e for e in edges if e.from_field == "WeaponID"]
    assert len(fk_edges) == 1
    assert fk_edges[0].to_table == "Weapon"
    assert fk_edges[0].to_field == "ID"
    assert fk_edges[0].inferred_by == "rule"


def test_types_compatibility_numeric(resolver):
    assert resolver._are_types_compatible("int", "int") is True
    assert resolver._are_types_compatible("int", "float") is True
    assert resolver._are_types_compatible("str", "int") is True


def test_skip_self_primary_key(resolver):
    hero = _table("Hero", [_field("ID")])
    cands = resolver._extract_foreign_key_candidates([hero])
    assert all(c["from_field"] != "ID" for c in cands)