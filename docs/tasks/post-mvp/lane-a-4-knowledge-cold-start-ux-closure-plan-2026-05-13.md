# Lane A.4 Knowledge Cold-Start UX Closure Plan

Date: 2026-05-13
Status: planning guidance only.
Classification: post-MVP / MVP-aligned UX closure / pilot blocker hardening

## 1. Background

1. Accepted MVP semantics remain closed and must not be reopened.
2. Lane A is limited to controlled Windows pilot blocker hardening and does not upgrade the product to production rollout or production ready.
3. The current Knowledge page already exposes a Build release action.
4. Backend first-release bootstrap is already available when there is no current release and no saved formal map.
5. The first bootstrap release still requires current table indexes, and the backend now returns the explicit prerequisite detail `Current table indexes are required to build the first knowledge release` when those indexes are missing.
6. The backend already exposes `POST /game/index/rebuild`, and the frontend API client already exposes `rebuildIndex(agentId)`.
7. The current Knowledge page shows the missing-index prerequisite but does not expose an executable rebuild action in that cold-start state.
8. In real pilot terms, this leaves a 0-to-1 UX gap: a maintainer can see why first release build is blocked but cannot complete the initialization loop from the Knowledge page itself.

## 2. Goal

1. Close the Knowledge cold-start UX gap for the first release path without changing accepted MVP semantics.
2. In the cold-start prerequisite state, the Knowledge page must expose an explicit `Rebuild current indexes` action tied to the existing rebuild flow.
3. After rebuild succeeds, the page must refresh release status, candidate map, formal map, and build prerequisites or build candidates so the operator can continue with a normal explicit Build release action.
4. The minimum correct implementation is: rebuild indexes, refresh the page state, and let the user explicitly click Build release.
5. This plan is a post-MVP pilot blocker hardening slice only. It is not a production rollout plan and is not a production-ready claim.

## 3. Non-goals / Forbidden Scope

1. Do not reopen MVP scope or change accepted MVP semantics.
2. Do not change Ask request schema.
3. Do not add provider, model, or api_key UI.
4. Do not change RAG or provider ownership.
5. Do not change Knowledge release governance.
6. Do not change rollback semantics.
7. Do not let RAG, query, or NumericWorkbench write release assets.
8. Do not let NumericWorkbench or query paths initialize releases automatically.
9. Do not touch SVN sync, update, or commit behavior.
10. Do not build a relationship editor.
11. Do not build a graph canvas.
12. Do not redesign broader candidate-map or formal-map governance.
13. Do not introduce a multi-step persisted onboarding system.
14. Do not write this lane as production rollout or production ready.
15. Do not modify the P24 conclusion, recommendation, or operator-startup boundary.
16. Do not continue Lane G.
17. Do not add a one-click auto-initialize flow that rebuilds indexes and builds release in one step.

## 4. Current Capability Inventory

1. Knowledge page currently defines the first-release missing-index detail as `NO_FIRST_RELEASE_INDEXES_DETAIL = "Current table indexes are required to build the first knowledge release"`.
2. Knowledge page already loads and renders these read surfaces:
   - release status
   - candidate map
   - formal map
   - build candidates and build prerequisite errors inside the Build release modal
3. Knowledge page already gates actions and reads through existing frontend capability checks such as `knowledge.build`, `knowledge.candidate.read`, and `knowledge.map.read`.
4. Frontend API client already provides `rebuildIndex(agentId)` in `console/src/api/modules/game.ts` and targets the existing `POST /agents/{agentId}/game/index/rebuild` route.
5. Backend `POST /game/index/rebuild` already exists, requires maintainer role, and must remain the only rebuild entry for this slice.
6. Backend `POST /game/knowledge/releases/build-from-current-indexes` already supports first-release bootstrap when there is no current release and no saved formal map.
7. Backend first-release bootstrap now explicitly fails with `Current table indexes are required to build the first knowledge release` when table indexes are unavailable.
8. Existing candidate-map semantics remain current-release scoped. Bootstrap build does not auto-set current release and does not change that rule.

## 5. UX Closure Scope

1. When the Knowledge page identifies the exact cold-start prerequisite `Current table indexes are required to build the first knowledge release`, it must show an explicit `Rebuild current indexes` action.
2. That action must call the existing rebuild flow only:
   - prefer the existing frontend client `rebuildIndex(agentId)`
   - keep the backend target as the existing `POST /game/index/rebuild`
3. Rebuild success must not auto-build a release.
4. Rebuild success must refresh the current page state so the operator can review the updated readiness and then explicitly click Build release.
5. Projects that already have current table indexes should continue using the existing first-release bootstrap path with no additional required steps.
6. Projects that already have a current knowledge release must remain behaviorally unchanged.
7. This closure belongs to the Knowledge page because the missing step occurs inside release initialization, not inside general project setup or map review.

## 6. Page Responsibility Boundary

1. Project page responsibility: local project directory configuration and base readiness state for the current local project.
2. Knowledge page responsibility: knowledge release lifecycle and cold-start release initialization orchestration, including the missing-index rebuild affordance needed to continue first-release bootstrap.
3. Map page responsibility: candidate map and formal map review, plus save-as-formal-map actions.
4. This lane must not collapse those page boundaries into a cross-page onboarding wizard.
5. The rebuild affordance belongs on Knowledge because the trigger condition is a release-build prerequisite surfaced from the Knowledge page itself.

## 7. Implementation Checklist

1. Reconfirm the existing Knowledge page state branches before implementation:
   - `NO_FIRST_RELEASE_INDEXES_DETAIL`
   - `buildCandidatesError`
   - release status loading
   - candidate map loading
   - formal map loading
   - `canBuildRelease` and related permission gating
2. Reuse the existing rebuild API wiring:
   - prefer `console/src/api/modules/game.ts` `rebuildIndex(agentId)`
   - do not add any new backend endpoint
3. Add only the minimal new frontend state needed for the rebuild action:
   - `isRebuildingIndexes`
   - `rebuildIndexesError`
   - `rebuildIndexesSuccess` or an equivalent recoverable success message
4. Show the `Rebuild current indexes` entry only in the cold-start prerequisite scenario where the page is surfacing `Current table indexes are required to build the first knowledge release`.
5. Keep permission handling aligned with existing semantics:
   - backend rebuild remains maintainer-only
   - non-maintainer and HTTP 403 responses must surface as recoverable rebuild errors
   - do not change `knowledge.build`, `knowledge.map.read`, or `knowledge.map.edit` semantics
6. On rebuild success, refresh all affected Knowledge page state from existing fetch paths:
   - release status
   - candidate map
   - formal map
   - build candidates and prerequisites
7. Adjust Build release modal wording so it clearly distinguishes:
   - indexes ready
   - indexes missing
   - no current release but first bootstrap still possible
8. Distinguish candidate-map empty and info states for these cases:
   - no current release plus indexes missing
   - no current release plus indexes ready
   - existing current release
9. Keep the post-rebuild operator flow explicit:
   - rebuild completes
   - page refreshes
   - operator manually clicks Build release
10. Preserve existing no-auto-publish and no-auto-set-current behavior.
11. Preserve existing rollback, query, RAG, and NumericWorkbench boundaries.
12. Reserve a dedicated implementation closeout document for the future execution slice:
   - `docs/tasks/post-mvp/lane-a-4-knowledge-cold-start-ux-closure-closeout-2026-05-13.md`

## 8. Validation Checklist

1. Run `git status --short --branch`.
2. Run console TypeScript validation:

```powershell
cd console
.\node_modules\.bin\tsc.cmd --noEmit -p tsconfig.json
```

3. Run backend Knowledge regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_knowledge_release_router.py tests\unit\routers\test_game_knowledge_map_router.py tests\unit\routers\test_game_knowledge_rag_router.py
```

4. Run index rebuild router tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_index*.py
```

5. If a lightweight frontend test surface already exists for the Knowledge page, add or run the smallest cold-start UI test that covers the rebuild affordance. If no suitable frontend test surface exists, do not add a large framework; use TypeScript validation plus manual smoke and record that boundary in closeout.
6. Run manual smoke for these scenarios:
   - Scenario A: no current release, no formal map, current table indexes already exist, and Build release succeeds.
   - Scenario B: no current release, no formal map, current table indexes are missing, the page prompts rebuild, user triggers rebuild, rebuild succeeds, and Build release then succeeds.
   - Scenario C: rebuild fails or returns 403, and the page shows a recoverable rebuild error without mislabeling it as a release-build failure.
   - Scenario D: an existing current-release project keeps normal build, rollback, query, and RAG behavior.
7. Run `git diff --check`.
8. Run touched-doc NUL check for the new plan and the updated indexes.
9. Run keyword boundary review for:
   - `production ready`
   - `production rollout`
   - `provider/model/api_key`
   - `Ask schema`
   - `RAG provider ownership`
   - `SVN sync/update/commit`
   - `P24`
   - `Lane G`

## 9. Risk Controls

1. Keep all behavior behind existing endpoints and capability boundaries.
2. Do not add any backend route, data model, or release-governance mutation for this slice.
3. Treat rebuild failure as a local recoverable UX state, not as a release-build result.
4. Keep rebuild and build as two separate user actions so the operator can see prerequisites and intent clearly.
5. Refresh state after rebuild using the current Knowledge page fetch functions instead of introducing a new workflow engine.
6. Do not expand the scope into Project-page readiness redesign or Map-page review redesign.
7. Keep wording explicit that this is pilot blocker hardening only and does not change product maturity status.

## 10. Acceptance Criteria

1. The plan explicitly states that this is not a production rollout plan and not a production-ready claim.
2. The plan explicitly states that this is a post-MVP pilot blocker hardening slice.
3. The plan explicitly states that the minimum correct implementation is `rebuild indexes, refresh state, then let the user explicitly click Build release`, not one-click automatic initialization.
4. The plan preserves the page responsibility boundary:
   - Project handles local project directory configuration and readiness baseline.
   - Knowledge handles release lifecycle and cold-start release initialization orchestration.
   - Map handles candidate-map or formal-map review and save-as-formal-map.
5. The plan explicitly keeps existing projects with a current release unaffected.
6. The plan explicitly keeps accepted MVP semantics, Ask schema, RAG ownership, rollback semantics, and SVN boundaries unchanged.
7. The plan includes a concrete next-agent implementation prompt for the future execution slice.

## 11. Recommended Next-Agent Prompt

```text
接手当前仓库 E:\LTclaw2.0，只执行 Lane A.4: Knowledge Cold-Start UX Closure 的实现，不做额外功能扩展。

先阅读：
1. docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md
2. docs/tasks/post-mvp/lane-a-controlled-windows-pilot-hardening-2026-05-10.md
3. docs/tasks/post-mvp/lane-a-4-knowledge-cold-start-ux-closure-plan-2026-05-13.md
4. docs/tasks/post-mvp/knowledge-first-release-bootstrap-bugfix-closeout-2026-05-13.md
5. console/src/pages/Game/Knowledge/index.tsx
6. console/src/api/modules/game.ts
7. src/ltclaw_gy_x/app/routers/game_index.py
8. src/ltclaw_gy_x/app/routers/game_knowledge_release.py

实现目标：
1. 在 Knowledge 页识别到 `Current table indexes are required to build the first knowledge release` 时，显示显式 `Rebuild current indexes` 入口。
2. 复用现有 `rebuildIndex(agentId)`，不要新增后端 endpoint。
3. rebuild 成功后刷新 release status、candidate map、formal map、build candidates 和 prerequisites。
4. 不自动 Build release；rebuild 成功后仍由用户明确点击 Build release。
5. 非 maintainer 或 403 时显示可恢复 rebuild 错误，不要误报为 release build 失败。
6. 保持已有 current release 项目行为不变。

禁止事项：
1. 不重开 MVP scope，不改 accepted MVP semantics。
2. 不改 Ask schema。
3. 不加 provider/model/api_key UI。
4. 不改 RAG/provider ownership。
5. 不改 release governance、rollback 语义、SVN sync/update/commit。
6. 不继续 Lane G，不写 production rollout 或 production ready。

完成后至少执行：
1. git status --short --branch
2. cd console ; .\node_modules\.bin\tsc.cmd --noEmit -p tsconfig.json
3. .\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_knowledge_release_router.py tests\unit\routers\test_game_knowledge_map_router.py tests\unit\routers\test_game_knowledge_rag_router.py
4. .\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_index*.py
5. git diff --check

如果没有合适的前端测试基建，不要新建大框架；用 tsc + manual smoke，并在 closeout 明确说明。
closeout 写入：docs/tasks/post-mvp/lane-a-4-knowledge-cold-start-ux-closure-closeout-2026-05-13.md
```