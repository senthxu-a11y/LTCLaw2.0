from datetime import datetime

from ltclaw_gy_x.game.canonical_facts import (
    build_canonical_doc_facts,
    build_canonical_script_facts,
    build_canonical_table_schema,
    infer_canonical_semantic_type,
    map_field_confidence_score,
    normalize_canonical_header,
)
from ltclaw_gy_x.game.models import (
    CodeFileIndex,
    CodeSymbol,
    CodeSymbolReference,
    DocIndex,
    FieldConfidence,
    FieldInfo,
    TableIndex,
)


def _now():
    return datetime(2026, 1, 1, 12, 0, 0)


def test_normalize_canonical_header_is_deterministic():
    assert normalize_canonical_header("Hero ID") == "hero_id"
    assert normalize_canonical_header("HeroID") == "hero_id"
    assert normalize_canonical_header(" hero-id ") == "hero_id"


def test_map_field_confidence_score_is_deterministic():
    assert map_field_confidence_score(FieldConfidence.CONFIRMED) == 1.0
    assert map_field_confidence_score(FieldConfidence.HIGH_AI) == 0.75
    assert map_field_confidence_score(FieldConfidence.LOW_AI) == 0.4


def test_infer_canonical_semantic_type_uses_rule_layer_only():
    assert infer_canonical_semantic_type(
        FieldInfo(name="ID", type="int", description="", confidence=FieldConfidence.CONFIRMED),
        primary_key="ID",
    ) == "id"
    assert infer_canonical_semantic_type(
        FieldInfo(name="WeaponRef", type="int", description="", confidence=FieldConfidence.HIGH_AI),
        primary_key="ID",
    ) == "reference"
    assert infer_canonical_semantic_type(
        FieldInfo(name="Damage", type="float", description="", confidence=FieldConfidence.HIGH_AI),
        primary_key="ID",
    ) == "number"
    assert infer_canonical_semantic_type(
        FieldInfo(name="IsBoss", type="bool", description="", confidence=FieldConfidence.HIGH_AI),
        primary_key="ID",
    ) == "bool"


def test_build_canonical_table_schema_from_table_index():
    table_index = TableIndex(
        table_name="HeroTable",
        source_path="Tables/HeroTable.xlsx",
        source_hash="sha256:table",
        svn_revision=7,
        system="combat",
        row_count=3,
        primary_key="ID",
        ai_summary="hero schema",
        ai_summary_confidence=0.9,
        fields=[
            FieldInfo(name="ID", type="int", description="identifier", confidence=FieldConfidence.CONFIRMED),
            FieldInfo(name="Hero Name", type="str", description="display name", confidence=FieldConfidence.HIGH_AI),
        ],
        last_indexed_at=_now(),
        indexer_model="test-model",
    )

    canonical_schema = build_canonical_table_schema(table_index)

    assert canonical_schema.table_id == "HeroTable"
    assert canonical_schema.source_path == "Tables/HeroTable.xlsx"
    assert canonical_schema.primary_key == "ID"
    assert canonical_schema.updated_at == _now()
    assert canonical_schema.fields[0].raw_header == "ID"
    assert canonical_schema.fields[0].canonical_header == "id"
    assert canonical_schema.fields[0].semantic_type == "id"
    assert canonical_schema.fields[0].confirmed is True
    assert canonical_schema.fields[0].aliases == ["ID", "id"]
    assert canonical_schema.fields[1].canonical_header == "hero_name"
    assert canonical_schema.fields[1].semantic_type == "text"
    assert canonical_schema.fields[1].confirmed is False


def test_build_canonical_doc_and_script_facts_are_serializable():
    doc_index = DocIndex(
        source_path="Docs/Combat.md",
        source_hash="sha256:doc",
        svn_revision=3,
        doc_type="design",
        title="Combat Overview",
        summary="combat loop summary",
        related_tables=["SkillTable", "HeroTable"],
        last_indexed_at=_now(),
    )
    code_index = CodeFileIndex(
        source_path="Scripts/CombatResolver.cs",
        source_hash="sha256:script",
        svn_revision=11,
        namespace="Game.Combat",
        symbols=[
            CodeSymbol(
                name="CombatResolver",
                kind="class",
                summary="resolve combat state",
                references=[
                    CodeSymbolReference(
                        target_kind="table",
                        target_table="SkillTable",
                        line=10,
                        snippet="SkillTable.Get(skillId)",
                        confidence="confirmed",
                    )
                ],
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
        last_indexed_at=_now(),
        indexer_version="regex.v1",
    )

    canonical_doc = build_canonical_doc_facts(doc_index)
    canonical_script = build_canonical_script_facts(code_index)

    assert canonical_doc.model_dump(mode="json")["schema_version"] == "canonical-doc-facts.v1"
    assert canonical_doc.semantic_tags == ["design"]
    assert canonical_doc.related_refs == ["table:HeroTable", "table:SkillTable"]
    assert canonical_doc.confirmed is False

    assert canonical_script.model_dump(mode="json")["schema_version"] == "canonical-script-facts.v1"
    assert canonical_script.symbols == ["CombatResolver"]
    assert canonical_script.responsibilities == ["resolve combat state"]
    assert canonical_script.related_refs == ["symbol:DamageFormula", "table:SkillTable"]
    assert canonical_script.confirmed is False