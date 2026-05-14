import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProjectSetupStatusResponse, ProjectTableSourceDiscoveryResponse } from "../../../api/types/game.ts";
import {
  buildProjectSetupDiagnosticsText,
  getProjectSetupDiscoverySummary,
  isProjectSetupBuildBlocked,
  joinProjectSetupLines,
  splitProjectSetupLines,
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
      exclude: ["**/.backup/**"],
      header_row: 1,
      primary_key_candidates: ["ID"],
    },
    discovery: {
      discovered_table_count: 0,
      available_table_count: 0,
      excluded_table_count: 0,
      unsupported_table_count: 0,
      error_count: 0,
    },
    build_readiness: {
      blocking_reason: "no_table_sources_found",
      next_action: "configure_tables_source",
    },
  };
}

function createDiscovery(): ProjectTableSourceDiscoveryResponse {
  return {
    success: true,
    project_root: "/workspace/project",
    table_files: [
      {
        source_path: "Tables/HeroTable.csv",
        format: "csv",
        status: "available",
        reason: "matched_supported_format",
      },
    ],
    excluded_files: [],
    unsupported_files: [],
    errors: [],
    summary: {
      discovered_table_count: 1,
      available_table_count: 1,
      excluded_table_count: 0,
      unsupported_table_count: 0,
      error_count: 0,
    },
    next_action: "run_raw_index",
  };
}

describe("projectSetupHelpers", () => {
  it("splits and joins multiline config fields", () => {
    assert.deepEqual(splitProjectSetupLines("Tables\n\n Configs \n"), ["Tables", "Configs"]);
    assert.equal(joinProjectSetupLines(["Tables", "Configs"]), "Tables\nConfigs");
  });

  it("prefers live discovery summary when available", () => {
    assert.deepEqual(getProjectSetupDiscoverySummary(createSetupStatus(), createDiscovery()), createDiscovery().summary);
  });

  it("blocks downstream build steps when discovered or available counts are zero", () => {
    assert.equal(isProjectSetupBuildBlocked(createSetupStatus(), null), true);
    assert.equal(isProjectSetupBuildBlocked(createSetupStatus(), createDiscovery()), false);
  });

  it("serializes copyable diagnostics with setup status and discovery payloads", () => {
    const text = buildProjectSetupDiagnosticsText({
      setupStatus: createSetupStatus(),
      discovery: createDiscovery(),
    });

    assert.match(text, /demo-project/);
    assert.match(text, /Tables\/HeroTable\.csv/);
    assert.match(text, /matched_supported_format/);
  });
});