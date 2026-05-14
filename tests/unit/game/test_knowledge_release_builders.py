from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_release_builders import (
    DEFAULT_RELEASE_INDEXES,
    build_minimal_manifest,
    build_minimal_map,
    build_source_snapshot_entries,
    compute_source_snapshot_hash,
    export_doc_knowledge_jsonl,
    export_script_evidence_jsonl,
    export_table_schema_jsonl,
    validate_knowledge_manifest,
    validate_knowledge_map,
    validate_release_id,
)
from ltclaw_gy_x.game.models import (
    CodeFileIndex,
    CodeSymbol,
    CodeSymbolReference,
    DocIndex,
    FieldConfidence,
    FieldInfo,
    KnowledgeDocRef,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
    TableIndex,
)


def _write_source(project_root: Path, relative_path: str, content: str) -> None:
    target = project_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _table_index(
    name: str = "SkillTable",
    source_path: str = "Tables/SkillTable.xlsx",
    revision: int = 42,
    row_count: int = 7,
    fields: list[FieldInfo] | None = None,
) -> TableIndex:
    return TableIndex(
        table_name=name,
        source_path=source_path,
        source_hash="sha256:table",
        svn_revision=revision,
        system="combat",
        row_count=row_count,
        primary_key="ID",
        ai_summary="skill schema",
        ai_summary_confidence=0.9,
        fields=fields or [],
        last_indexed_at=datetime(2026, 1, 1, 12, 0, 0),
        indexer_model="test-model",
    )


def _code_file_index(
    source_path: str,
    source_hash: str,
    revision: int = 0,
    symbol_name: str = "CombatResolver",
    summary: str = "combat logic",
) -> CodeFileIndex:
    return CodeFileIndex(
        source_path=source_path,
        source_hash=source_hash,
        svn_revision=revision,
        namespace="Game.Combat",
        symbols=[
            CodeSymbol(
                name=symbol_name,
                kind="class",
                signature=f"class {symbol_name}",
                line_start=10,
                line_end=40,
                references=[
                    CodeSymbolReference(
                        target_kind="table",
                        target_table="SkillTable",
                        line=12,
                        snippet="SkillTable.Get(skillId)",
                        confidence="confirmed",
                    )
                ],
                summary=summary,
            )
        ],
        references=[
            CodeSymbolReference(
                target_kind="symbol",
                target_symbol="DamageFormula",
                line=18,
                snippet="DamageFormula.Calculate()",
                confidence="inferred",
            )
        ],
        indexer_version="regex.v1",
    )


def test_build_minimal_manifest_uses_stable_snapshot_hash_and_explicit_indexes(tmp_path):
    project_root = tmp_path / "project-root"
    _write_source(project_root, "Tables/SkillTable.xlsx", "value=1\n")
    _write_source(project_root, "Docs/combat.md", "# combat\n")

    knowledge_map = build_minimal_map(
        "release-001",
        systems=[KnowledgeSystem(system_id="combat", title="Combat")],
        tables=[
            KnowledgeTableRef(
                table_id="SkillTable",
                title="SkillTable",
                source_path="Tables/SkillTable.xlsx",
                source_hash="sha256:table",
                system_id="combat",
            )
        ],
        docs=[
            KnowledgeDocRef(
                doc_id="combat-doc",
                title="Combat Doc",
                source_path="Docs/combat.md",
                source_hash="sha256:doc",
                system_id="combat",
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id="rel-1",
                from_ref="system:combat",
                to_ref="table:SkillTable",
                relation_type="contains",
                source_hash="sha256:relationship",
            )
        ],
    )

    manifest_one = build_minimal_manifest(
        project_root,
        "release-001",
        knowledge_map,
        source_paths=["Docs/combat.md", "Tables/SkillTable.xlsx"],
        created_by="admin",
        index_entries={"table_schema": {"hash": "sha256:table-schema", "count": 1}},
    )
    manifest_two = build_minimal_manifest(
        project_root,
        "release-001",
        knowledge_map,
        source_paths=["Tables/SkillTable.xlsx", "Docs/combat.md"],
        created_by="admin",
        index_entries={"table_schema": {"hash": "sha256:table-schema", "count": 1}},
    )

    validate_knowledge_manifest(manifest_one)
    assert manifest_one.source_snapshot_hash == manifest_two.source_snapshot_hash
    assert manifest_one.project_root_hash.startswith("sha256:")
    assert manifest_one.map_hash.startswith("sha256:")
    assert set(manifest_one.indexes.keys()) == set(DEFAULT_RELEASE_INDEXES.keys())
    assert manifest_one.indexes["table_schema"].path == "indexes/table_schema.jsonl"
    assert manifest_one.indexes["table_schema"].hash == "sha256:table-schema"
    assert manifest_one.indexes["doc_knowledge"].hash is None
    assert manifest_one.build_mode == "strict"
    assert manifest_one.status == "ready"
    assert manifest_one.map_source == "provided"
    assert manifest_one.warnings == []


def test_build_minimal_manifest_marks_bootstrap_warnings(tmp_path):
    project_root = tmp_path / "project-root"
    _write_source(project_root, "Tables/SkillTable.xlsx", "value=1\n")

    knowledge_map = build_minimal_map(
        "release-bootstrap-001",
        tables=[
            KnowledgeTableRef(
                table_id="SkillTable",
                title="SkillTable",
                source_path="Tables/SkillTable.xlsx",
                source_hash="sha256:table",
                system_id="combat",
            )
        ],
    )

    manifest = build_minimal_manifest(
        project_root,
        "release-bootstrap-001",
        knowledge_map,
        source_paths=["Tables/SkillTable.xlsx"],
        build_mode="bootstrap",
        map_source="bootstrap_current_indexes",
        warnings=["Bootstrap release used current indexes."],
    )

    validate_knowledge_manifest(manifest)
    assert manifest.build_mode == "bootstrap"
    assert manifest.status == "bootstrap_warning"
    assert manifest.map_source == "bootstrap_current_indexes"
    assert manifest.warnings == ["Bootstrap release used current indexes."]


def test_source_snapshot_entries_are_stably_sorted(tmp_path):
    project_root = tmp_path / "project-root"
    _write_source(project_root, "Tables/ZSkill.xlsx", "z\n")
    _write_source(project_root, "Docs/ASkill.md", "a\n")

    entries = build_source_snapshot_entries(project_root, ["Tables/ZSkill.xlsx", "Docs/ASkill.md"])
    hash_one = compute_source_snapshot_hash(project_root, ["Tables/ZSkill.xlsx", "Docs/ASkill.md"])
    hash_two = compute_source_snapshot_hash(project_root, ["Docs/ASkill.md", "Tables/ZSkill.xlsx"])

    assert [entry["path"] for entry in entries] == ["Docs/ASkill.md", "Tables/ZSkill.xlsx"]
    assert hash_one == hash_two


def test_build_minimal_map_supports_statuses_and_relationships():
    knowledge_map = build_minimal_map(
        "release-001",
        systems=[KnowledgeSystem(system_id="combat", title="Combat", status="active")],
        tables=[
            KnowledgeTableRef(
                table_id="SkillTable",
                title="SkillTable",
                source_path="Tables/SkillTable.xlsx",
                source_hash="sha256:table",
                system_id="combat",
                status="deprecated",
            )
        ],
        docs=[
            KnowledgeDocRef(
                doc_id="combat-doc",
                title="Combat Doc",
                source_path="Docs/combat.md",
                source_hash="sha256:doc",
                system_id="combat",
                status="ignored",
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id="combat-script",
                title="Combat Script",
                source_path="Scripts/combat.cs",
                source_hash="sha256:script",
                system_id="combat",
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id="system-table",
                from_ref="system:combat",
                to_ref="table:SkillTable",
                relation_type="contains",
                source_hash="sha256:relationship-1",
            ),
            KnowledgeRelationship(
                relationship_id="doc-table",
                from_ref="doc:combat-doc",
                to_ref="table:SkillTable",
                relation_type="documents",
                source_hash="sha256:relationship-2",
            ),
            KnowledgeRelationship(
                relationship_id="table-script",
                from_ref="table:SkillTable",
                to_ref="script:combat-script",
                relation_type="implemented_by",
                source_hash="sha256:relationship-3",
            ),
        ],
        deprecated=["table:SkillTable"],
    )

    validate_knowledge_map(knowledge_map)
    assert knowledge_map.tables[0].status == "deprecated"
    assert knowledge_map.docs[0].status == "ignored"
    assert knowledge_map.deprecated == ["table:SkillTable"]
    assert len(knowledge_map.relationships) == 3


def test_export_table_schema_jsonl_single_table_and_fields():
    payload, artifact = export_table_schema_jsonl(
        [
            _table_index(
                fields=[
                    FieldInfo(name="ID", type="int", description="identifier", confidence=FieldConfidence.CONFIRMED),
                    FieldInfo(name="Damage", type="int", description="damage value", confidence=FieldConfidence.HIGH_AI),
                ]
            )
        ]
    )

    lines = payload.splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["table_name"] == "SkillTable"
    assert record["source_path"] == "Tables/SkillTable.xlsx"
    assert record["source_hash"] == "sha256:table"
    assert record["primary_key"] == "ID"
    assert record["row_count"] == 7
    assert record["source_revision"] == 42
    assert record["fields"] == [
        {"confidence": "confirmed", "description": "identifier", "name": "ID", "type": "int"},
        {"confidence": "high_ai", "description": "damage value", "name": "Damage", "type": "int"},
    ]
    assert artifact.path == "indexes/table_schema.jsonl"
    assert artifact.count == 1
    assert artifact.hash.startswith("sha256:")


def test_export_table_schema_jsonl_hash_is_deterministic_for_same_tables():
    left = _table_index(name="BTable", source_path="Tables/BTable.xlsx")
    right = _table_index(name="ATable", source_path="Tables/ATable.xlsx")

    payload_one, artifact_one = export_table_schema_jsonl([left, right])
    payload_two, artifact_two = export_table_schema_jsonl([right, left])

    assert payload_one == payload_two
    assert artifact_one.hash == artifact_two.hash
    assert artifact_one.count == artifact_two.count == 2


def test_export_table_schema_jsonl_empty_result():
    payload, artifact = export_table_schema_jsonl([])

    assert payload == ""
    assert artifact.path == "indexes/table_schema.jsonl"
    assert artifact.count == 0
    assert artifact.hash == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_export_doc_knowledge_jsonl_from_doc_indexes_and_approved_docs():
    payload, artifact = export_doc_knowledge_jsonl(
        doc_indexes=[
            DocIndex(
                source_path="Docs/Combat.md",
                source_hash="sha256:doc-index",
                svn_revision=18,
                doc_type="design",
                title="Combat Overview",
                summary="combat loop summary",
                related_tables=["SkillTable", "HeroTable"],
                last_indexed_at=datetime(2026, 1, 1, 12, 0, 0),
            )
        ],
        knowledge_docs=[
            KnowledgeDocRef(
                doc_id="kb-combat-approved",
                title="Approved Combat KB",
                source_path="KB/CombatApproved.md",
                source_hash="sha256:approved",
                system_id="combat",
                status="active",
            ),
            KnowledgeDocRef(
                doc_id="kb-combat-ignored",
                title="Ignored Combat KB",
                source_path="KB/CombatIgnored.md",
                source_hash="sha256:ignored",
                system_id="combat",
                status="ignored",
            ),
        ],
    )

    lines = payload.splitlines()
    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    by_title = {record["title"]: record for record in records}

    approved = by_title["Approved Combat KB"]
    assert approved["summary"] is None
    assert approved["category"] == "approved_doc"
    assert approved["tags"] == ["combat"]
    assert approved["source_path"] == "KB/CombatApproved.md"
    assert approved["related_tables"] == []
    assert approved["source_hash"] == "sha256:approved"

    overview = by_title["Combat Overview"]
    assert overview["summary"] == "combat loop summary"
    assert overview["category"] == "design"
    assert overview["tags"] == []
    assert overview["source_path"] == "Docs/Combat.md"
    assert overview["related_tables"] == ["HeroTable", "SkillTable"]
    assert overview["source_hash"] == "sha256:doc-index"
    assert overview["source_revision"] == 18

    assert artifact.path == "indexes/doc_knowledge.jsonl"
    assert artifact.count == 2
    assert artifact.hash.startswith("sha256:")


def test_export_doc_knowledge_jsonl_empty_result():
    payload, artifact = export_doc_knowledge_jsonl()

    assert payload == ""
    assert artifact.path == "indexes/doc_knowledge.jsonl"
    assert artifact.count == 0
    assert artifact.hash == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_export_script_evidence_jsonl_uses_stable_sorting_and_fields():
    left = _code_file_index(
        source_path="Scripts/ZCombatResolver.cs",
        source_hash="sha256:z-script",
        revision=31,
        symbol_name="ZCombatResolver",
        summary="z combat logic",
    )
    right = _code_file_index(
        source_path="Scripts/ACombatResolver.cs",
        source_hash="sha256:a-script",
        revision=12,
        symbol_name="ACombatResolver",
        summary="a combat logic",
    )

    payload_one, artifact_one = export_script_evidence_jsonl([left, right])
    payload_two, artifact_two = export_script_evidence_jsonl([right, left])

    assert payload_one == payload_two
    assert artifact_one.hash == artifact_two.hash
    assert artifact_one.path == "indexes/script_evidence.jsonl"
    assert artifact_one.count == 2

    lines = payload_one.splitlines()
    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["source_path"] == "Scripts/ACombatResolver.cs"
    assert first["source_hash"] == "sha256:a-script"
    assert first["language"] == "csharp"
    assert first["kind"] == "code_index"
    assert first["summary"] == "a combat logic"
    assert first["source_revision"] == 12
    assert first["symbols"][0]["name"] == "ACombatResolver"
    assert first["references"][0]["target_symbol"] == "DamageFormula"
    assert second["source_path"] == "Scripts/ZCombatResolver.cs"


def test_export_script_evidence_jsonl_empty_result():
    payload, artifact = export_script_evidence_jsonl([])

    assert payload == ""
    assert artifact.path == "indexes/script_evidence.jsonl"
    assert artifact.count == 0
    assert artifact.hash == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest.mark.parametrize("release_id", ["", "   ", "../bad", "bad/name", ".", ".hidden", "/absolute"])
def test_validate_release_id_boundaries(release_id):
    with pytest.raises(ValueError, match="Invalid release id"):
        validate_release_id(release_id)


@pytest.mark.parametrize('source_path', ['../Secrets.xlsx', '..\\Secrets.xlsx', 'C:/abs/path.xlsx', '/abs/path.xlsx'])
def test_validate_knowledge_map_rejects_source_path_escape(source_path):
    knowledge_map = build_minimal_map(
        'release-001',
        tables=[
            KnowledgeTableRef(
                table_id='SkillTable',
                title='SkillTable',
                source_path=source_path,
                source_hash='sha256:table',
                system_id='combat',
            )
        ],
    )

    with pytest.raises(ValueError, match='Invalid local project relative path'):
        validate_knowledge_map(knowledge_map)
