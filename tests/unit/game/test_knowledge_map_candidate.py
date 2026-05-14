from __future__ import annotations

import json
from datetime import datetime

from ltclaw_gy_x.game import knowledge_map_candidate as candidate_module
from ltclaw_gy_x.game.knowledge_map_candidate import (
    build_map_candidate_from_canonical_facts,
    build_map_candidate_result_from_release,
)
from ltclaw_gy_x.game.models import (
    CanonicalDocFacts,
    CanonicalScriptFacts,
    CanonicalTableSchema,
    KnowledgeDocRef,
    KnowledgeMap,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
)
from ltclaw_gy_x.game.paths import (
    get_project_canonical_docs_dir,
    get_project_canonical_scripts_dir,
    get_project_canonical_tables_dir,
)


def _now():
    return datetime(2026, 1, 1, 12, 0, 0)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _canonical_table_schema(table_id: str = "HeroTable"):
    return CanonicalTableSchema(
        table_id=table_id,
        source_path=f"Tables/{table_id}.xlsx",
        source_hash=f"sha256:{table_id.lower()}",
        primary_key="ID",
        fields=[],
        updated_at=_now(),
    )


def _canonical_doc_facts(doc_id: str = "combat-doc"):
    return CanonicalDocFacts(
        doc_id=doc_id,
        source_path="Docs/Combat.md",
        source_hash="sha256:doc",
        title="Combat Overview",
        summary="combat summary",
        semantic_tags=["design"],
        related_refs=["table:HeroTable"],
        confidence=0.75,
        confirmed=False,
    )


def _canonical_script_facts(script_id: str = "combat-script"):
    return CanonicalScriptFacts(
        script_id=script_id,
        source_path="Scripts/CombatResolver.cs",
        source_hash="sha256:script",
        symbols=["CombatResolver"],
        responsibilities=["resolve combat state"],
        related_refs=["table:HeroTable", "symbol:DamageFormula"],
        confidence=0.75,
        confirmed=False,
    )


def _existing_formal_map() -> KnowledgeMap:
    return KnowledgeMap(
        release_id="formal-map-working",
        systems=[
            KnowledgeSystem(
                system_id="combat",
                title="Combat Formal",
                status="active",
                table_ids=["HeroTable"],
                doc_ids=["combat-doc"],
                script_ids=["combat-script"],
            )
        ],
        tables=[
            KnowledgeTableRef(
                table_id="HeroTable",
                title="Hero Formal",
                source_path="Tables/HeroTable.xlsx",
                source_hash="sha256:formal-hero",
                system_id="combat",
                status="deprecated",
            ),
            KnowledgeTableRef(
                table_id="LegacyTable",
                title="Legacy Table",
                source_path="Tables/LegacyTable.xlsx",
                source_hash="sha256:legacy",
                system_id="legacy",
            ),
        ],
        docs=[
            KnowledgeDocRef(
                doc_id="combat-doc",
                title="Combat Formal Doc",
                source_path="Docs/Combat.md",
                source_hash="sha256:formal-doc",
                system_id="combat",
                status="ignored",
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id="combat-script",
                title="Combat Formal Script",
                source_path="Scripts/CombatResolver.cs",
                source_hash="sha256:formal-script",
                system_id="combat",
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id="rel-formal-doc-table",
                from_ref="doc:combat-doc",
                to_ref="table:HeroTable",
                relation_type="documented_by",
                source_hash="sha256:formal-rel",
            ),
            KnowledgeRelationship(
                relationship_id="rel-formal-legacy-table",
                from_ref="doc:combat-doc",
                to_ref="table:LegacyTable",
                relation_type="documented_by",
                source_hash="sha256:formal-rel-legacy",
            ),
        ],
    )


def test_build_map_candidate_result_from_release_marks_release_snapshot(monkeypatch, tmp_path):
    knowledge_map = KnowledgeMap(release_id="release-001")

    monkeypatch.setattr(candidate_module, "build_map_candidate_from_release", lambda project_root, release_id=None: knowledge_map)

    result = build_map_candidate_result_from_release(tmp_path / "project-root")

    assert result.mode == "candidate_map"
    assert result.candidate_source == "release_snapshot"
    assert result.is_formal_map is False
    assert result.source_release_id == "release-001"
    assert result.map is knowledge_map
    assert "release snapshot" in result.warnings[0]


def test_build_map_candidate_from_canonical_facts_returns_no_canonical_facts_when_empty(monkeypatch, tmp_path):
    working_root = tmp_path / "ltclaw-data"
    project_root = tmp_path / "project-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)

    result = build_map_candidate_from_canonical_facts(project_root)

    assert result.mode == "no_canonical_facts"
    assert result.map is None
    assert result.candidate_source == "source_canonical"
    assert result.source_release_id is None
    assert result.uses_existing_formal_map_as_hint is False
    assert "No canonical facts were available" in result.warnings[0]


def test_build_map_candidate_from_canonical_facts_uses_canonical_inputs_and_formal_hints(monkeypatch, tmp_path):
    working_root = tmp_path / "ltclaw-data"
    project_root = tmp_path / "project-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)

    canonical_table = _canonical_table_schema()
    canonical_doc = _canonical_doc_facts()
    canonical_script = _canonical_script_facts()

    _write_json(
        get_project_canonical_tables_dir(project_root) / "HeroTable.json",
        canonical_table.model_dump(mode="json"),
    )
    _write_json(
        get_project_canonical_docs_dir(project_root) / "combat-doc.json",
        canonical_doc.model_dump(mode="json"),
    )
    _write_json(
        get_project_canonical_scripts_dir(project_root) / "combat-script.json",
        canonical_script.model_dump(mode="json"),
    )

    result = build_map_candidate_from_canonical_facts(project_root, existing_formal_map=_existing_formal_map())

    assert result.mode == "candidate_map"
    assert result.candidate_source == "source_canonical"
    assert result.is_formal_map is False
    assert result.source_release_id is None
    assert result.uses_existing_formal_map_as_hint is True
    assert result.map is not None
    assert result.map.release_id == "candidate-source-canonical"
    assert [table.table_id for table in result.map.tables] == ["HeroTable"]
    assert result.map.tables[0].title == "Hero Formal"
    assert result.map.tables[0].status == "deprecated"
    assert [doc.doc_id for doc in result.map.docs] == ["combat-doc"]
    assert result.map.docs[0].title == "Combat Formal Doc"
    assert [script.script_id for script in result.map.scripts] == ["combat-script"]
    assert result.map.scripts[0].title == "Combat Formal Script"
    relationship_ids = {relationship.relationship_id for relationship in result.map.relationships}
    assert "rel:doc:combat-doc:table:HeroTable:related_table" in relationship_ids
    assert "rel:script:combat-script:table:HeroTable:references_table" in relationship_ids
    assert "rel-formal-doc-table" in relationship_ids
    assert "rel-formal-legacy-table" not in relationship_ids
    assert any("Carried over matching relationships" in warning for warning in result.warnings)
    assert any("Skipped one or more existing formal-map relationships" in warning for warning in result.warnings)