import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ColdStartJobState, ProjectSetupStatusResponse, ProjectTableSourceDiscoveryResponse } from "../../../api/types/game.ts";
import {
  canStartRuleOnlyColdStartBuild,
  clearColdStartActiveJobId,
  getColdStartActiveJobStorageKey,
  loadColdStartActiveJobId,
  saveColdStartActiveJobId,
  toColdStartProgressView,
} from "./projectSetupHelpers.ts";

function createSetupStatus(): ProjectSetupStatusResponse {
  return {
    project_root: "/workspace/project",
    project_root_exists: true,
    project_bundle_root: "/workspace/game_data/projects/demo",
    project_key: "demo-project",
    tables_config: {
      roots: ["Tables"],
      include: ["**/*.csv"],
      exclude: [],
      header_row: 1,
      primary_key_candidates: ["ID"],
    },
    discovery: {
      status: "not_scanned",
      discovered_table_count: 1,
      available_table_count: 1,
      excluded_table_count: 0,
      unsupported_table_count: 0,
      error_count: 0,
    },
    build_readiness: {
      blocking_reason: null,
      next_action: "review_candidate_map",
    },
  };
}

function createDiscovery(available = 1): ProjectTableSourceDiscoveryResponse {
  return {
    success: true,
    project_root: "/workspace/project",
    table_files: available
      ? [{ source_path: "Tables/HeroTable.csv", format: "csv", status: "available", reason: "matched_supported_format", cold_start_supported: true, cold_start_reason: "rule_only_supported_csv" }]
      : [],
    excluded_files: [],
    unsupported_files: [],
    errors: [],
    summary: {
      discovered_table_count: available,
      available_table_count: available,
      excluded_table_count: 0,
      unsupported_table_count: 0,
      error_count: 0,
    },
    next_action: available ? "run_raw_index" : "configure_tables_source",
  };
}

function createJob(status: string): ColdStartJobState {
  return {
    job_id: "job-1",
    project_key: "demo-project",
    project_root: "/workspace/project",
    status,
    stage: status === "succeeded" ? "done" : "building_candidate_map",
    progress: status === "succeeded" ? 100 : 80,
    message: "Running",
    current_file: "Tables/HeroTable.csv",
    counts: {
      discovered_table_count: 1,
      raw_table_index_count: 1,
      canonical_table_count: 1,
      candidate_table_count: status === "succeeded" ? 1 : 0,
    },
    warnings: [],
    errors: [],
    next_action: status === "succeeded" ? "review_candidate_map" : "build_candidate_from_source",
    partial_outputs: {},
    timeout_seconds: 300,
    timed_out: false,
    candidate_refs: status === "succeeded" ? ["table:HeroTable"] : [],
    created_at: "2026-05-14T00:00:00Z",
    updated_at: "2026-05-14T00:00:00Z",
    started_at: "2026-05-14T00:00:00Z",
    finished_at: status === "succeeded" ? "2026-05-14T00:01:00Z" : null,
  };
}

describe("coldStartJob helpers", () => {
  it("maps job status to progress view model", () => {
    const running = toColdStartProgressView(createJob("running"));
    const success = toColdStartProgressView(createJob("succeeded"));

    assert.equal(running.isRunning, true);
    assert.equal(running.canCancel, true);
    assert.equal(success.isTerminal, true);
    assert.equal(success.candidateTableCount, 1);
  });

  it("persists active job id per agent", () => {
    const storage = new Map<string, string>();
    Object.defineProperty(globalThis, "localStorage", {
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
      },
      configurable: true,
    });

    saveColdStartActiveJobId("agent-1", "job-123");
    assert.equal(loadColdStartActiveJobId("agent-1"), "job-123");
    clearColdStartActiveJobId("agent-1");
    assert.equal(loadColdStartActiveJobId("agent-1"), "");
    assert.equal(getColdStartActiveJobStorageKey("agent-1"), "ltclaw_cold_start_active_job:agent-1");
  });

  it("disables one-click build when available tables are zero", () => {
    assert.equal(canStartRuleOnlyColdStartBuild(createSetupStatus(), createDiscovery(0)), false);
    assert.equal(canStartRuleOnlyColdStartBuild(createSetupStatus(), createDiscovery(1)), true);
  });

  it("keeps candidate refs visible only after success", () => {
    assert.deepEqual(toColdStartProgressView(createJob("succeeded")).candidateTableCount, 1);
    assert.deepEqual(createJob("succeeded").candidate_refs, ["table:HeroTable"]);
  });
});