import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const consoleRoot = resolve(currentDir, "..", "..");
const mainLayoutSource = readFileSync(
  resolve(consoleRoot, "layouts", "MainLayout", "index.tsx"),
  "utf-8",
);
const sidebarSource = readFileSync(
  resolve(consoleRoot, "layouts", "Sidebar.tsx"),
  "utf-8",
);
const gameIndexSource = readFileSync(resolve(currentDir, "index.ts"), "utf-8");
const projectRouteSource = readFileSync(
  resolve(currentDir, "Project", "index.tsx"),
  "utf-8",
);
const projectCompatSource = readFileSync(resolve(currentDir, "GameProject.tsx"), "utf-8");
const projectPageSource = readFileSync(resolve(currentDir, "ProjectPage.tsx"), "utf-8");

const activeRoutes = [
  {
    path: "/game/project",
    sidebarLabel: "nav.gameProject",
    componentFile: "pages/Game/Project/index.tsx",
    componentExportSource: "../ProjectPage",
  },
  {
    path: "/game/map",
    sidebarLabel: "nav.gameMapEditor",
    componentFile: "pages/Game/MapEditor/index.tsx",
    componentExportSource: "default MapEditorPage",
  },
  {
    path: "/game/knowledge",
    sidebarLabel: "nav.gameKnowledge",
    componentFile: "pages/Game/Knowledge/index.tsx",
    componentExportSource: "default KnowledgePage",
  },
  {
    path: "/numeric-workbench",
    sidebarLabel: "nav.gameWorkbench",
    componentFile: "pages/Game/NumericWorkbench.tsx",
    componentExportSource: "default NumericWorkbench",
  },
  {
    path: "/agent-config",
    sidebarLabel: "nav.agentConfig",
    componentFile: "pages/Agent/Config/index.tsx",
    componentExportSource: "default AgentConfigPage",
  },
];

describe("game route manifest hygiene", () => {
  it("keeps /game/project on the unique Project route entry", () => {
    assert.equal(
      mainLayoutSource.includes('path="/game/project" element={<ProjectPage />}'),
      true,
    );
    assert.equal(projectRouteSource.includes('import CanonicalProjectPage from "../ProjectPage";'), true);
    assert.equal(projectCompatSource.trim(), 'export { default } from "./Project";');
    assert.equal(projectPageSource.includes('defaultValue: "切换工作区"'), true);
    assert.equal(projectPageSource.includes('defaultValue: "Frontend Git Ref"'), true);
    assert.equal(projectPageSource.includes('defaultValue: "Backend Git Ref"'), true);
    assert.equal(projectPageSource.includes('defaultValue: "API Base"'), true);
    assert.equal(projectPageSource.includes('defaultValue: "Backend Static Source"'), true);
    assert.equal(projectPageSource.includes('defaultValue: "Backend Static Dir"'), true);
  });

  it("keeps /game/map on the unique MapEditor page", () => {
    assert.equal(
      mainLayoutSource.includes('path="/game/map" element={<MapEditorPage />}'),
      true,
    );
    assert.equal(existsSync(resolve(currentDir, "MapEditor", "index.tsx")), true);
  });

  it("keeps /numeric-workbench on the standalone NumericWorkbench page", () => {
    assert.equal(
      mainLayoutSource.includes('path="/numeric-workbench" element={<NumericWorkbenchPage />}'),
      true,
    );
    assert.equal(existsSync(resolve(currentDir, "NumericWorkbench.tsx")), true);
  });

  it("keeps /game/workbench as a redirect instead of a separate page", () => {
    assert.equal(
      mainLayoutSource.includes('path="/game/workbench" element={<Navigate to="/numeric-workbench" replace />}'),
      true,
    );
    assert.equal(existsSync(resolve(currentDir, "Workbench.tsx")), false);
    assert.equal(existsSync(resolve(currentDir, "Workbench", "index.tsx")), false);
  });

  it("does not leave a duplicate Project implementation reachable", () => {
    assert.equal(gameIndexSource.includes("export { default as GameProject } from './Project';"), true);
    assert.equal(mainLayoutSource.includes("../../pages/Game/GameProject"), false);
    assert.equal(sidebarSource.includes('path: "/game/project"'), true);
    assert.equal(sidebarSource.includes('path: "/game-project"'), false);
  });

  it("keeps sidebar paths aligned with the route manifest and real files", () => {
    for (const route of activeRoutes) {
      assert.equal(sidebarSource.includes(`label: t("${route.sidebarLabel}`), true);
      assert.equal(sidebarSource.includes(`path: "${route.path}"`), true);
      assert.equal(existsSync(resolve(consoleRoot, route.componentFile)), true);
    }
  });
});