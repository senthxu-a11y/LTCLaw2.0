import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProjectSetupStatusResponse, ProjectTableSourceDiscoveryResponse } from "../../../api/types/game.ts";
import {
  buildProjectSetupDiagnosticsText,
  clearProjectSetupCachedDiscovery,
  clearColdStartActiveJobId,
  getEffectiveProjectSetupBuildReadiness,
  getAvailableColdStartTables,
  getColdStartActiveJobStorageKey,
  getProjectSetupDiscoveryCacheKey,
  getProjectSetupDiscoverySummary,
  isProjectSetupProjectRootDirty,
  isProjectSetupBuildBlocked,
  joinProjectSetupLines,
  loadProjectSetupCachedDiscovery,
  loadColdStartActiveJobId,
  saveProjectSetupCachedDiscovery,
  saveColdStartActiveJobId,
  splitProjectSetupLines,
} from "./projectSetupHelpers.ts";

function createStorage() {
  const store = new Map<string, string>();
  return {
    getItem(key: string) {
      return store.has(key) ? store.get(key)! : null;
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
    removeItem(key: string) {
      store.delete(key);
    },
    clear() {
      store.clear();
    },
  };
}

const localStorageMock = createStorage();
Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  configurable: true,
});

function createSetupStatus(): ProjectSetupStatusResponse {
  return {
    active_workspace_root: "/workspace-a",
    active_workspace_project_root: "/workspace/project",
    active_workspace_project_key: "demo-project",
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
      status: "not_scanned",
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
    roots: [
      {
        configured_root: "Tables",
        resolved_root: "/workspace/project/Tables",
        exists: true,
        is_directory: true,
      },
    ],
    table_files: [
      {
        source_path: "Tables/HeroTable.csv",
        format: "csv",
        status: "available",
        reason: "matched_supported_format",
        cold_start_supported: true,
        cold_start_reason: "rule_only_supported_csv",
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
  it("builds a stable discovery cache key from workspace and project identity", () => {
    assert.equal(
      getProjectSetupDiscoveryCacheKey(createSetupStatus()),
      "ltclaw_project_setup_discovery:/workspace-a::demo-project",
    );
  });

  it("caches and restores discovery results for the same workspace/project", () => {
    localStorage.clear();
    const setupStatus = createSetupStatus();
    const discovery = createDiscovery();

    saveProjectSetupCachedDiscovery(setupStatus, discovery);

    assert.deepEqual(loadProjectSetupCachedDiscovery(setupStatus), discovery);
  });

  it("persists active cold-start job id by project identity", () => {
    localStorage.clear();
    const setupStatus = createSetupStatus();

    saveColdStartActiveJobId(setupStatus, "job-001");

    assert.equal(getColdStartActiveJobStorageKey(setupStatus), "ltclaw.game.projectSetup.activeJob.demo-project");
    assert.equal(loadColdStartActiveJobId(setupStatus), "job-001");
  });

  it("isolates active cold-start job id across project keys and clears it", () => {
    localStorage.clear();
    const setupStatus = createSetupStatus();
    const otherProject = { ...createSetupStatus(), project_key: "other-project" };

    saveColdStartActiveJobId(setupStatus, "job-001");
    saveColdStartActiveJobId(otherProject, "job-002");

    assert.equal(loadColdStartActiveJobId(setupStatus), "job-001");
    assert.equal(loadColdStartActiveJobId(otherProject), "job-002");

    clearColdStartActiveJobId(setupStatus);
    assert.equal(loadColdStartActiveJobId(setupStatus), "");
    assert.equal(loadColdStartActiveJobId(otherProject), "job-002");
  });

  it("does not leak cached discovery across workspaces and can clear it", () => {
    localStorage.clear();
    const setupStatus = createSetupStatus();
    const otherWorkspaceStatus = {
      ...createSetupStatus(),
      active_workspace_root: "/workspace-b",
    };

    saveProjectSetupCachedDiscovery(setupStatus, createDiscovery());

    assert.equal(loadProjectSetupCachedDiscovery(otherWorkspaceStatus), null);

    clearProjectSetupCachedDiscovery(setupStatus);
    assert.equal(loadProjectSetupCachedDiscovery(setupStatus), null);
  });

  it("splits and joins multiline config fields", () => {
    assert.deepEqual(splitProjectSetupLines("Tables\n\n Configs \n"), ["Tables", "Configs"]);
    assert.equal(joinProjectSetupLines(["Tables", "Configs"]), "Tables\nConfigs");
  });

  it("prefers live discovery summary when available", () => {
    assert.deepEqual(getProjectSetupDiscoverySummary(createSetupStatus(), createDiscovery()), {
      status: "scanned",
      ...createDiscovery().summary,
    });
  });

  it("blocks downstream build steps when discovered or available counts are zero", () => {
    assert.equal(isProjectSetupBuildBlocked(createSetupStatus(), null), true);
    assert.equal(isProjectSetupBuildBlocked(createSetupStatus(), createDiscovery()), false);
  });

  it("prefers discovery readiness when csv tables are available", () => {
    assert.deepEqual(getEffectiveProjectSetupBuildReadiness(createSetupStatus(), createDiscovery()), {
      blocking_reason: null,
      next_action: "ready_for_rule_only_cold_start",
      source: "discovery",
    });
  });

  it("flags project root input when it differs from backend effective value", () => {
    assert.equal(isProjectSetupProjectRootDirty("/workspace/project-next", createSetupStatus()), true);
    assert.equal(isProjectSetupProjectRootDirty("/workspace/project", createSetupStatus()), false);
  });

  it("keeps setup-status discovery in not_scanned state until discovery runs", () => {
    const summary = getProjectSetupDiscoverySummary(createSetupStatus(), null);

    assert.equal(summary.status, "not_scanned");
    assert.equal(summary.available_table_count, 0);
  });

  it("filters available cold-start tables by explicit support flag", () => {
    const discovery = createDiscovery();
    discovery.table_files.push({
      source_path: "Tables/HeroTable.xlsx",
      format: "xlsx",
      status: "recognized",
      reason: "matched_recognized_format",
      cold_start_supported: false,
      cold_start_reason: "rule_only_cold_start_not_supported_for_xlsx",
    });

    assert.deepEqual(getAvailableColdStartTables(discovery).map((item) => item.source_path), ["Tables/HeroTable.csv"]);
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
