import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type {
  FormalKnowledgeMapResponse,
  KnowledgeMap,
  KnowledgeMapCandidateResponse,
  MapDiffReview,
} from "../../../api/types/game";
import {
  buildDiffReviewSections,
  buildMapBuildArtifactStates,
  canSaveReviewedCandidateAsFormalMap,
  summarizeKnowledgeMap,
} from "./mapBuildReview";

function createMap(): KnowledgeMap {
  return {
    release_id: "r1",
    systems: [{ system_id: "combat", title: "Combat", status: "active", table_ids: ["damage"], doc_ids: [], script_ids: [] }],
    tables: [{ table_id: "damage", title: "Damage", source_path: "Tables/Damage.xlsx", source_hash: "hash-1", status: "active" }],
    docs: [{ doc_id: "damage-doc", title: "Damage Notes", source_path: "Docs/damage.md", source_hash: "hash-2", status: "active" }],
    scripts: [{ script_id: "damage-calc", title: "Damage Calc", source_path: "Scripts/damage.cs", source_hash: "hash-3", status: "active" }],
    relationships: [{ relationship_id: "rel-1", from_ref: "table:damage", to_ref: "doc:damage-doc", relation_type: "described_by", source_hash: "hash-rel" }],
    deprecated: [],
  };
}

function createCandidate(overrides: Partial<KnowledgeMapCandidateResponse> = {}): KnowledgeMapCandidateResponse {
  return {
    mode: "candidate_map",
    map: createMap(),
    release_id: null,
    candidate_source: "source_canonical",
    is_formal_map: false,
    source_release_id: null,
    uses_existing_formal_map_as_hint: true,
    warnings: [],
    diff_review: null,
    ...overrides,
  };
}

function createFormalMap(overrides: Partial<FormalKnowledgeMapResponse> = {}): FormalKnowledgeMapResponse {
  return {
    mode: "formal_map",
    map: createMap(),
    map_hash: "hash-formal",
    updated_at: "2026-05-14T00:00:00Z",
    updated_by: "tester",
    ...overrides,
  };
}

describe("mapBuildReview helpers", () => {
  it("summarizes knowledge map counts", () => {
    assert.deepEqual(summarizeKnowledgeMap(createMap()), {
      systems: 1,
      tables: 1,
      docs: 1,
      scripts: 1,
      relationships: 1,
    });
  });

  it("distinguishes candidate, formal, and release artifact states", () => {
    const states = buildMapBuildArtifactStates({
      sourceCandidate: createCandidate(),
      formalMap: createFormalMap(),
      releaseSnapshot: createCandidate({ candidate_source: "release_snapshot", release_id: "release-2026-05-14" }),
    });

    assert.deepEqual(states.map((item) => [item.key, item.source, item.status]), [
      ["candidate", "source_canonical", "available"],
      ["formal", "formal_map", "available"],
      ["release", "release_snapshot", "available"],
    ]);
  });

  it("only allows saving a reviewed candidate when admin save conditions are met", () => {
    assert.equal(
      canSaveReviewedCandidateAsFormalMap({
        agentId: "agent-1",
        sourceCandidate: createCandidate(),
        hasExplicitCapabilityContext: true,
        canReadMap: true,
        canEditMap: true,
      }),
      true,
    );

    assert.equal(
      canSaveReviewedCandidateAsFormalMap({
        agentId: "agent-1",
        sourceCandidate: createCandidate(),
        hasExplicitCapabilityContext: true,
        canReadMap: true,
        canEditMap: false,
      }),
      false,
    );
  });

  it("returns diff review sections in the review order used by the UI", () => {
    const review: MapDiffReview = {
      base_map_source: "formal_map",
      candidate_source: "source_canonical",
      added_refs: ["table:damage"],
      removed_refs: ["doc:legacy"],
      changed_refs: ["system:combat"],
      unchanged_refs: ["script:damage-calc"],
      warnings: ["relationship carryover skipped for doc:legacy"],
    };

    assert.deepEqual(buildDiffReviewSections(review), [
      { key: "added_refs", refs: ["table:damage"] },
      { key: "removed_refs", refs: ["doc:legacy"] },
      { key: "changed_refs", refs: ["system:combat"] },
      { key: "unchanged_refs", refs: ["script:damage-calc"] },
    ]);
  });
});