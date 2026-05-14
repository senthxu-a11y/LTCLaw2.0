import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type {
  FormalKnowledgeMapResponse,
  GameStorageSummary,
  KnowledgeReleaseHistoryItem,
} from "../../../api/types/game";
import { buildAdminPanelActions, buildAdminStatusCards } from "./adminPanel";

function createStorageSummary(): GameStorageSummary {
  return {
    working_root: "/workspace",
    game_data_root: "/workspace/game_data",
    workspace_dir: "/workspace/agent",
    user_config_path: "/workspace/user_config.json",
    legacy_user_config_path: "/workspace/legacy_user_config.json",
    svn_root: "/workspace/project",
    project_store_dir: "/workspace/game_data/projects/demo-project",
    project_bundle_root: "/workspace/game_data/projects/demo-project",
    project_source_config_path: "/workspace/game_data/projects/demo-project/project/source_config.yaml",
    project_config_path: "/workspace/game_data/projects/demo-project/project/project_config.json",
    project_index_dir: "/workspace/game_data/projects/demo-project/project/indexes",
    agent_store_dir: "/workspace/agent/store",
    session_store_dir: "/workspace/agent/sessions",
    workbench_dir: "/workspace/agent/workbench",
    chroma_dir: "/workspace/chroma",
    llm_cache_dir: "/workspace/cache/llm",
    svn_cache_dir: "/workspace/cache/svn",
    proposals_dir: "/workspace/proposals",
    code_index_dir: "/workspace/code_index",
    retrieval_dir: "/workspace/retrieval",
    knowledge_base_dir: "/workspace/kb",
    session_name: "current-session",
  };
}

function createRelease(): KnowledgeReleaseHistoryItem {
  return {
    release_id: "release-2026-05-14",
    created_at: "2026-05-14T00:00:00Z",
    label: "current",
    is_current: true,
    indexes: {},
  };
}

function createFormalMap(): FormalKnowledgeMapResponse {
  return {
    mode: "formal_map",
    map: null,
    map_hash: "hash-001",
    updated_at: "2026-05-14T00:00:00Z",
    updated_by: "admin",
  };
}

describe("adminPanel helpers", () => {
  it("maps status payload into read-only admin cards", () => {
    const cards = buildAdminStatusCards({
      storageSummary: createStorageSummary(),
      currentRelease: createRelease(),
      formalMap: createFormalMap(),
      ragStatus: "ready",
    });

    assert.deepEqual(
      cards.map((card) => [card.key, card.value]),
      [
        ["project_bundle_path", "/workspace/game_data/projects/demo-project"],
        ["source_config_path", "/workspace/game_data/projects/demo-project/project/source_config.yaml"],
        ["current_release_id", "release-2026-05-14"],
        ["current_map_hash", "hash-001"],
        ["formal_map_status", "formal_map"],
        ["rag_status", "ready"],
        ["current_knowledge_version", "release-2026-05-14"],
      ],
    );
  });

  it("falls back to project_store_dir when project_bundle_root is absent", () => {
    const storageSummary = createStorageSummary();
    storageSummary.project_bundle_root = null;

    const cards = buildAdminStatusCards({
      storageSummary,
      currentRelease: createRelease(),
      formalMap: createFormalMap(),
      ragStatus: "ready",
    });

    assert.equal(
      cards.find((card) => card.key === "project_bundle_path")?.value,
      "/workspace/game_data/projects/demo-project",
    );
    assert.equal(
      cards.find((card) => card.key === "source_config_path")?.value,
      "/workspace/game_data/projects/demo-project/project/source_config.yaml",
    );
  });

  it("hides admin operations from planner or viewer capability sets", () => {
    assert.deepEqual(buildAdminPanelActions(["knowledge.read", "workbench.read"], true), []);
  });

  it("distinguishes build release from publish and set current", () => {
    const actions = buildAdminPanelActions(["knowledge.build", "knowledge.publish"], true);
    const keys = actions.map((action) => action.key);

    assert.equal(keys.includes("build_release"), true);
    assert.equal(keys.includes("publish_set_current"), true);
    assert.notEqual(
      actions.find((action) => action.key === "build_release")?.label,
      actions.find((action) => action.key === "publish_set_current")?.label,
    );
  });

  it("enables actions only when required capabilities are present", () => {
    const actions = buildAdminPanelActions([
      "knowledge.candidate.read",
      "knowledge.candidate.write",
      "knowledge.map.read",
      "knowledge.map.edit",
      "knowledge.build",
    ], true);

    assert.equal(actions.find((action) => action.key === "candidate_map_review")?.enabled, true);
    assert.equal(actions.find((action) => action.key === "save_formal_map")?.enabled, true);
    assert.equal(actions.find((action) => action.key === "build_release")?.enabled, true);
    assert.equal(actions.find((action) => action.key === "publish_set_current")?.enabled, false);
  });

  it("does not restrict actions when no explicit capability context exists", () => {
    const actions = buildAdminPanelActions(undefined, false);

    assert.equal(actions.length, 4);
    assert.equal(actions.every((action) => action.enabled), true);
  });
});