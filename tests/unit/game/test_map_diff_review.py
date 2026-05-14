from __future__ import annotations

from ltclaw_gy_x.game.knowledge_map_candidate import build_map_diff_review
from ltclaw_gy_x.game.models import (
    KnowledgeDocRef,
    KnowledgeMap,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
)


def _base_map() -> KnowledgeMap:
    return KnowledgeMap(
        release_id="base-release",
        systems=[KnowledgeSystem(system_id="combat", title="Combat")],
        tables=[
            KnowledgeTableRef(
                table_id="HeroTable",
                title="Hero Table",
                source_path="Tables/HeroTable.xlsx",
                source_hash="sha256:hero",
                system_id="combat",
            )
        ],
        docs=[
            KnowledgeDocRef(
                doc_id="combat-doc",
                title="Combat Doc",
                source_path="Docs/Combat.md",
                source_hash="sha256:doc",
                system_id="combat",
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id="rel-doc-table",
                from_ref="doc:combat-doc",
                to_ref="table:HeroTable",
                relation_type="documented_by",
                source_hash="sha256:rel",
            )
        ],
    )


def _candidate_map() -> KnowledgeMap:
    return KnowledgeMap(
        release_id="candidate-source-canonical",
        systems=[KnowledgeSystem(system_id="combat", title="Combat Updated")],
        tables=[
            KnowledgeTableRef(
                table_id="HeroTable",
                title="Hero Table Updated",
                source_path="Tables/HeroTable.xlsx",
                source_hash="sha256:hero-updated",
                system_id="combat",
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id="combat-script",
                title="Combat Script",
                source_path="Scripts/CombatResolver.cs",
                source_hash="sha256:script",
                system_id="combat",
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id="rel-script-table",
                from_ref="script:combat-script",
                to_ref="table:HeroTable",
                relation_type="references_table",
                source_hash="sha256:rel-script",
            )
        ],
    )


def test_build_map_diff_review_lists_added_removed_changed_and_unchanged_refs():
    review = build_map_diff_review(
        _base_map(),
        _candidate_map(),
        candidate_source="source_canonical",
        base_map_source="formal_map",
        warnings=["review only"],
    )

    assert review.base_map_source == "formal_map"
    assert review.candidate_source == "source_canonical"
    assert review.added_refs == ["relationship:rel-script-table", "script:combat-script"]
    assert review.removed_refs == ["doc:combat-doc", "relationship:rel-doc-table"]
    assert review.changed_refs == ["system:combat", "table:HeroTable"]
    assert review.unchanged_refs == []
    assert review.warnings == ["review only"]