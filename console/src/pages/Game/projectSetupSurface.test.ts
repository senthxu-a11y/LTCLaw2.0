import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const consoleRoot = resolve(currentDir, "..", "..");

const pageSource = readFileSync(resolve(currentDir, "GameProject.tsx"), "utf-8");
const apiSource = readFileSync(resolve(consoleRoot, "api", "modules", "game.ts"), "utf-8");

describe("project setup UI surface", () => {
  it("keeps project setup on the existing game project entry page", () => {
    assert.equal(pageSource.includes('title={t("gameProject.projectSetupTitle", { defaultValue: "Project setup" })}'), true);
    assert.equal(pageSource.includes('defaultValue: "工作区 / Workspace"') || pageSource.includes('defaultValue: "Workspace"'), true);
    assert.equal(pageSource.includes('defaultValue: "当前工作区"'), true);
    assert.equal(pageSource.includes('defaultValue: "切换工作区"'), true);
    assert.equal(pageSource.includes('defaultValue: "新建工作区"'), true);
    assert.equal(pageSource.includes('defaultValue: "打开 / 切换工作区"'), true);
    assert.equal(pageSource.includes('defaultValue: "打开已有工作区"'), true);
    assert.equal(pageSource.includes('defaultValue: "新建并切换"'), true);
    assert.equal(pageSource.includes('Project Data / Agent Profiles / Sessions / Cache'), true);
    assert.equal(pageSource.includes('切换 agent 只切换权限和 session'), true);
    assert.equal(pageSource.includes('切换工作区会切换 Project Data / Agent Profiles / Sessions / Cache'), true);
    assert.equal(pageSource.includes('defaultValue: "冷启动状态"'), true);
    assert.equal(pageSource.includes('defaultValue: "当前无冷启动任务"'), true);
    assert.equal(pageSource.includes('defaultValue: "Rule-only 冷启动"'), true);
    assert.equal(pageSource.includes('defaultValue: "Local Project Root"'), true);
    assert.equal(pageSource.includes('defaultValue: "Tables Source"'), true);
    assert.equal(pageSource.includes('defaultValue: "Source Discovery"'), true);
    assert.equal(pageSource.includes('defaultValue: "Build Pipeline Status"'), true);
    assert.equal(pageSource.includes('defaultValue: "Rule-only 冷启动构建"'), true);
  });

  it("uses agent-scoped project setup endpoints instead of top-level game routes", () => {
    assert.equal(apiSource.includes('/agents/${agentId}/game/project/setup-status'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/project/root'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/project/sources/tables'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/project/sources/discover'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/knowledge/map/cold-start-jobs'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/knowledge/map/cold-start-jobs/${encodeURIComponent(jobId)}'), true);
    assert.equal(apiSource.includes('/agents/${agentId}/game/knowledge/map/cold-start-jobs/${encodeURIComponent(jobId)}/cancel'), true);
    assert.equal(apiSource.includes('request<ProjectSetupStatusResponse>(`/game/project/setup-status`)'), false);
  });

  it("surfaces project key, project bundle root, discovery summary, job status, and clipboard diagnostics", () => {
    assert.equal(pageSource.includes('defaultValue: "Project Key"'), true);
    assert.equal(pageSource.includes('defaultValue: "Project Bundle Root"'), true);
    assert.equal(pageSource.includes('defaultValue: "Role / Capability Editor"'), true);
    assert.equal(pageSource.includes('discovered_table_count'), true);
    assert.equal(pageSource.includes('available_table_count'), true);
    assert.equal(pageSource.includes('handleCopyDiagnostics'), true);
    assert.equal(pageSource.includes('defaultValue: "Status"'), true);
    assert.equal(pageSource.includes('defaultValue: "Stage"'), true);
    assert.equal(pageSource.includes('defaultValue: "Current File"'), true);
    assert.equal(pageSource.includes('candidate_refs'), true);
  });

  it("keeps success actions as explicit navigation instead of auto-saving formal map or building release", () => {
    assert.equal(pageSource.includes('defaultValue: "查看 Candidate Map"'), true);
    assert.equal(pageSource.includes('defaultValue: "查看 Diff Review"'), true);
    assert.equal(pageSource.includes('defaultValue: "保存 Formal Map"'), true);
    assert.equal(pageSource.includes('navigate("/game/map")'), true);
    assert.equal(pageSource.includes('saveFormalKnowledgeMap'), false);
    assert.equal(pageSource.includes('buildRelease'), false);
    assert.equal(pageSource.includes('publishCurrentRelease'), false);
  });
});