import assert from "node:assert/strict";
import fs from "node:fs";
import { describe, it } from "node:test";

import type { KnowledgeRagCitation } from "../../api/types/game";
import {
  buildCitationWorkbenchTarget,
  normalizeWorkbenchTableName,
  parseCitationRouteContext,
} from "./citationDeepLink";

function createCitation(overrides: Partial<KnowledgeRagCitation> = {}): KnowledgeRagCitation {
  return {
    citation_id: "citation-001",
    release_id: "release-001",
    source_type: "table_schema",
    table: "SkillTable",
    artifact_path: "indexes/table_schema.jsonl",
    source_path: "Tables/SkillTable.xlsx",
    title: "SkillTable",
    row: 12,
    field: "Damage",
    ref: "table:SkillTable",
    ...overrides,
  };
}

describe("citation deep-link helpers", () => {
  it("keeps explicit table and field locators from citation payload", () => {
    const target = buildCitationWorkbenchTarget(
      createCitation({
        source_path: "Docs/Combat.md",
        title: "Combat Overview",
        source_type: "doc_knowledge",
      }),
    );

    assert.deepEqual(target, {
      table: "SkillTable",
      row: "12",
      field: "Damage",
      citationId: "citation-001",
      citationTitle: "Combat Overview",
      citationSource: "Docs/Combat.md",
    });
  });

  it("falls back to source path and title-derived field when explicit locators are absent", () => {
    const target = buildCitationWorkbenchTarget(
      createCitation({
        table: null,
        field: null,
        title: "SkillTable.CritRate",
      }),
    );

    assert.equal(target.table, "SkillTable");
    assert.equal(target.row, "12");
    assert.equal(target.field, "CritRate");
  });

  it("normalizes workbench table names from source paths", () => {
    assert.equal(normalizeWorkbenchTableName("Tables/SkillTable.xlsx?download=1"), "SkillTable");
    assert.equal(normalizeWorkbenchTableName(""), null);
  });

  it("reads citation route context from workbench query params", () => {
    const params = new URLSearchParams({
      from: "rag-citation",
      table: "SkillTable",
      row: "12",
      field: "Damage",
      citationId: "citation-001",
      citationTitle: "SkillTable",
      citationSource: "Tables/SkillTable.xlsx",
    });

    assert.deepEqual(parseCitationRouteContext(params), {
      citationId: "citation-001",
      title: "SkillTable",
      source: "Tables/SkillTable.xlsx",
      table: "SkillTable",
      row: "12",
      field: "Damage",
    });
  });

  it("ignores non citation routes", () => {
    const params = new URLSearchParams({ table: "SkillTable", row: "12", field: "Damage" });

    assert.equal(parseCitationRouteContext(params), null);
  });

  it("keeps NumericWorkbench citation handling read-only and side-effect free", () => {
    const source = fs.readFileSync(new URL("./NumericWorkbench.tsx", import.meta.url), "utf8");
    const deepLinkMatch = source.match(/\/\/ Deep-link[\s\S]*?useEffect\(\(\) => \{[\s\S]*?\}, \[dlTable, dlRow, dlField, tableNames\]\);/);
    const deepLinkBlock = deepLinkMatch?.[0] || "";

    assert.match(deepLinkBlock, /setOpenTables\(/);
    assert.match(deepLinkBlock, /setActiveTab\(/);
    assert.match(deepLinkBlock, /setHighlight\(/);
    assert.doesNotMatch(deepLinkBlock, /setDraftOpen\(/);
    assert.doesNotMatch(deepLinkBlock, /setSourceWriteOpen\(/);
    assert.doesNotMatch(deepLinkBlock, /sourceWrite\(/);
    assert.doesNotMatch(deepLinkBlock, /publish/i);
  });
});
