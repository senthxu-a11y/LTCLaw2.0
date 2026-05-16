# Frontend Route Hygiene Closeout 2026-05-17

## 1. Scope
- branch: foundation/workspace-agent-storage-from-m1
- baseline commit before this slice: ad3e16de2f1c08ad31f4b3d90a4041362eb64606
- scope: frontend route hygiene / stale page cleanup only
- out of scope: main replacement, backend business semantics, cold-start business flow changes, map business flow changes, release business flow changes, RAG business flow changes, txtai, M2 expansion

## 2. Duplicate Pages Found Before Cleanup
- Project route had two page-level files in the same feature area:
  - console/src/pages/Game/Project/index.tsx
  - console/src/pages/Game/GameProject.tsx
- The active route already pointed at console/src/pages/Game/Project/index.tsx, but that file was only a thin wrapper around GameProject.tsx.
- This left the real route entry unclear and made it too easy to keep editing the wrong file.
- Map route did not have a second active /game/map page. The active map entry is console/src/pages/Game/MapEditor/index.tsx. console/src/pages/Game/IndexMap.tsx remains a separate active page on /index-map, not a duplicate /game/map route.
- Workbench did not have a second active page. The active workbench page is console/src/pages/Game/NumericWorkbench.tsx and /game/workbench is now route-only redirect.

## 3. Route Manifest
| route path | sidebar label | actual component file | component export source | active | redirect | legacy | orphan |
| --- | --- | --- | --- | --- | --- | --- | --- |
| /game | none | MainLayout redirect | Navigate -> /game/project | no | yes | yes | no |
| /game-project | none | MainLayout redirect | Navigate -> /game/project | no | yes | yes | no |
| /game/project | 项目配置 | console/src/pages/Game/Project/index.tsx | imports ../ProjectPage | yes | no | no | no |
| /game/knowledge | 知识工作台 | console/src/pages/Game/Knowledge/index.tsx | default KnowledgePage | yes | no | no | no |
| /game/map | 地图编辑器 | console/src/pages/Game/MapEditor/index.tsx | default MapEditorPage | yes | no | no | no |
| /game/workbench | none | MainLayout redirect | Navigate -> /numeric-workbench | no | yes | yes | no |
| /numeric-workbench | 数值工作台 | console/src/pages/Game/NumericWorkbench.tsx | default NumericWorkbench | yes | no | no | no |
| /agent-config | 运行配置 | console/src/pages/Agent/Config/index.tsx | default AgentConfigPage | yes | no | no | no |
| /index-map | 表索引 | console/src/pages/Game/IndexMap.tsx | default IndexMap | yes | no | no | no |
| /doc-library | Legacy 文档库 | console/src/pages/Game/DocLibrary.tsx | default DocLibrary | yes | no | legacy | no |
| /knowledge-base | Legacy 知识库 | console/src/pages/Game/KnowledgeBase.tsx | default KnowledgeBase | yes | no | legacy | no |
| /svn-sync | none | MainLayout redirect | Navigate -> /game/project | no | yes | legacy | no |

## 4. Cleanup Applied
### Re-export / redirect / disconnect
- Added canonical Project UI source file:
  - console/src/pages/Game/ProjectPage.tsx
- Kept the route entry as the only active Project route shell:
  - console/src/pages/Game/Project/index.tsx
- Converted the stale Project file into a compatibility re-export only:
  - console/src/pages/Game/GameProject.tsx -> export { default } from "./Project";
- Updated barrel export so GameProject resolves to the canonical Project route entry instead of a second implementation:
  - console/src/pages/Game/index.ts
- Kept /game/workbench as redirect only:
  - console/src/layouts/MainLayout/index.tsx

### Removed or disconnected old page entry surfaces
- Removed GameProject from patchable dynamic page discovery:
  - console/src/plugins/dynamicModuleRegistry.ts
  - console/src/utils/lazyWithRetry.ts
- This means the stale GameProject path is no longer treated as an independent runtime page entry.

### Dead imports / dead references cleaned
- projectSetupSurface.test now reads the canonical Project UI source instead of the stale GameProject file:
  - console/src/pages/Game/projectSetupSurface.test.ts
- Added route hygiene manifest test:
  - console/src/pages/Game/routeManifest.test.ts

## 5. Active Pages Kept
- console/src/pages/Game/Project/index.tsx
- console/src/pages/Game/ProjectPage.tsx
- console/src/pages/Game/Knowledge/index.tsx
- console/src/pages/Game/MapEditor/index.tsx
- console/src/pages/Game/NumericWorkbench.tsx
- console/src/pages/Game/IndexMap.tsx
- console/src/pages/Game/DocLibrary.tsx
- console/src/pages/Game/KnowledgeBase.tsx
- console/src/pages/Agent/Config/index.tsx

## 6. Legacy Pages Kept Intentionally
- console/src/pages/Game/DocLibrary.tsx
- console/src/pages/Game/KnowledgeBase.tsx
- reason: both still have explicit active routes and sidebar entries labeled as Legacy, so they are not orphan pages in this slice

## 7. Sidebar Path Check
- 项目配置 -> /game/project
- 知识工作台 -> /game/knowledge
- 地图编辑器 -> /game/map
- 数值工作台 -> /numeric-workbench
- 运行配置 -> /agent-config
- No Sidebar item points to /game-project or /game/workbench.
- Sidebar path checks are now covered by source-level test in console/src/pages/Game/routeManifest.test.ts.

## 8. Real Browser Smoke
### Runtime
- backend: http://127.0.0.1:18082
- frontend: http://127.0.0.1:5175
- injected Frontend Build ID: foundation-route-hygiene-ad3e16d
- injected Frontend Git Ref: foundation/workspace-agent-storage-from-m1@ad3e16d

### /game/project
- pass
- visible text confirmed:
  - Frontend Build ID = foundation-route-hygiene-ad3e16d
  - Frontend Git Ref = foundation/workspace-agent-storage-from-m1@ad3e16d
  - Backend Git Ref = foundation/workspace-agent-storage-from-m1@ad3e16d
  - 当前工作区
  - 切换工作区
  - 冷启动状态
- result: user-visible route hits the expected Project page and exposes top-level diagnostics immediately.

### Workspace switcher modal
- pass
- click on 切换工作区 opened Modal titled 打开 / 切换工作区
- visible actions confirmed:
  - 打开已有工作区
  - 新建并切换

### /game/workbench redirect
- pass
- opened /game/workbench
- final URL: http://127.0.0.1:5175/numeric-workbench
- result: redirect remains route-only; no separate stale workbench page is being rendered.

### /numeric-workbench
- pass
- final URL: http://127.0.0.1:5175/numeric-workbench
- page was non-empty and showed 数值工作台

### /game/map
- pass
- final URL: http://127.0.0.1:5175/game/map
- page was non-empty and showed 地图编辑器 / Map Editor

### Sidebar project navigation
- pass
- clicking Sidebar 项目配置 returned to the same /game/project page
- the page again showed 当前工作区 and foundation/workspace-agent-storage-from-m1@ad3e16d

## 9. Automated Validation
- console: pnpm exec tsc --noEmit -> pass
- console: node --test src/pages/Game/routeManifest.test.ts src/pages/Game/projectSetupSurface.test.ts src/pages/Game/components/projectSetupHelpers.test.ts -> pass
- foundation: PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only -> pass
- console: pnpm exec eslint --quiet src/pages/Game/**/*.tsx src/layouts/**/*.tsx src/api/modules/game.ts src/api/types/game.ts src/stores/projectSetupStore.ts -> failed on pre-existing unrelated issues in console/src/pages/Game/IndexMap.tsx and console/src/pages/Game/SvnSync.tsx

## 10. Can Old UI Still Be Hit?
- Active-route answer: not through the active routes covered in this slice.
- /game/project now resolves through one route shell only, and the stale GameProject path is reduced to a compatibility re-export rather than a second maintained implementation.
- /game/workbench now resolves by redirect only.
- Sidebar no longer points to any stale Project or Workbench path.

## 11. Recommendation About Replacing main
- recommendation: do not replace main yet
- reasons:
  - this slice fixed route hygiene and visible route identity, but did not change the earlier rollout decision boundary
  - the requested eslint command still reports pre-existing unrelated failures outside the touched route hygiene files
  - broader write-path human acceptance remains outside this slice and is still a gate for any replacement decision
