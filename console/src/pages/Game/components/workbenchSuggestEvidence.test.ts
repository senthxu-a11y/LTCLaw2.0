import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { SuggestChange } from "../../../api/modules/gameWorkbench";
import {
  buildSuggestMessagePresentation,
  buildSuggestionEvidencePresentation,
  dedupeEvidenceRefs,
} from "./workbenchSuggestEvidence";

function createSuggestion(overrides: Partial<SuggestChange> = {}): SuggestChange {
  return {
    table: "ItemConfig",
    row_id: 1001,
    field: "SellPrice",
    new_value: 120,
    reason: "align with current release balance",
    confidence: 0.82,
    uses_draft_overlay: false,
    source_release_id: "release-2026-05-14",
    validation_status: "grounded",
    evidence_refs: ["table:item_config#1001:SellPrice"],
    ...overrides,
  };
}

describe("workbenchSuggestEvidence helpers", () => {
  it("dedupes evidence refs and keeps stable order", () => {
    assert.deepEqual(
      dedupeEvidenceRefs(["table:a", "table:a", "", "table:b", "table:a"]),
      ["table:a", "table:b"],
    );
  });

  it("marks draft overlay without upgrading it to formal evidence", () => {
    const presentation = buildSuggestionEvidencePresentation(
      createSuggestion({ evidence_refs: [], uses_draft_overlay: true }),
      { formal_context_status: "grounded" },
    );

    assert.equal(presentation.usesDraftOverlay, true);
    assert.equal(presentation.evidenceKind, "runtime_only");
    assert.deepEqual(presentation.evidenceRefs, []);
  });

  it("surfaces validation status and source release id", () => {
    const presentation = buildSuggestionEvidencePresentation(createSuggestion(), {
      formal_context_status: "grounded",
    });

    assert.equal(presentation.validationStatus, "grounded");
    assert.equal(presentation.sourceReleaseId, "release-2026-05-14");
    assert.equal(presentation.confidenceText, "82%");
    assert.equal(presentation.formalContextStatus, "grounded");
  });

  it("keeps runtime-only draft suggestions separate from formal release evidence", () => {
    const presentation = buildSuggestionEvidencePresentation(
      createSuggestion({
        evidence_refs: [],
        uses_draft_overlay: true,
        source_release_id: null,
        validation_status: "validated_runtime_only",
      }),
      { formal_context_status: "no_current_release" },
    );

    assert.equal(presentation.evidenceKind, "runtime_only");
    assert.equal(presentation.validationStatus, "validated_runtime_only");
    assert.equal(presentation.sourceReleaseId, null);
    assert.equal(presentation.usesDraftOverlay, true);
    assert.equal(presentation.formalContextStatus, "no_current_release");
  });

  it("keeps runtime-only suggestions distinct in message summary", () => {
    const summary = buildSuggestMessagePresentation(
      [
        createSuggestion(),
        createSuggestion({
          row_id: 1002,
          evidence_refs: [],
          uses_draft_overlay: true,
          source_release_id: null,
        }),
      ],
      {
        evidence_refs: ["table:item_config#1001:SellPrice", "table:item_config#1001:SellPrice"],
        formal_context_status: "grounded",
      },
    );

    assert.deepEqual(summary.evidenceRefs, ["table:item_config#1001:SellPrice"]);
    assert.equal(summary.usesDraftOverlay, true);
    assert.equal(summary.hasFormalEvidence, true);
    assert.equal(summary.hasRuntimeOnlySuggestion, true);
    assert.equal(summary.formalContextStatus, "grounded");
  });
});