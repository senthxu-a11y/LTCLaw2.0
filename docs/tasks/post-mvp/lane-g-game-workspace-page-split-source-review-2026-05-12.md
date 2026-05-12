# Lane G Game Workspace Page Split Source Review

Date: 2026-05-12
Status: source review
Scope: freeze frontend page-split boundaries for Game workspace before any route-skeleton implementation

## 1. Final Recommendation

Result: proceed

Reason:

1. Current Game workspace behavior is controlled mainly by `console/src/pages/Game/GameProject.tsx`, `console/src/layouts/MainLayout/index.tsx`, and `console/src/layouts/Sidebar.tsx`.
2. The target split matches the existing Lane G checklist and does not require backend, API, schema, or workflow-semantic changes.
3. NumericWorkbench and SvnSync are already independent route targets, so the main work is route normalization, navigation reshaping, and GameProject block extraction.
4. No blocker was found that would force a backend-first or runtime-first detour.

## 2. Current GameProject Block Inventory

Current `GameProject.tsx` is an overloaded page that mixes at least four responsibilities.

### 2.1 Project-side blocks

1. Project config form
2. Create project agent wizard
3. Save / reset / validate actions
4. Storage summary groups
5. Project and agent binding summary implied by loaded form and storage snapshot

### 2.2 Knowledge runtime blocks

1. Current release summary
2. Release list
3. Build release from current indexes
4. Set current
5. Rollback to previous
6. RAG Ask
7. Example questions
8. Recent questions
9. Structured query side panel
10. RAG answer state panel
11. Citation list
12. Empty doc-context hint when `doc_knowledge` is absent
13. Workbench affordance and citation deep-link entry

### 2.3 Map editor blocks

1. Candidate formal map review
2. Saved formal map review
3. Save as formal map
4. Saved formal map status-only edit
5. Relationship warning display

### 2.4 Cross-page entry blocks already implied in current flow

1. Citation -> NumericWorkbench deep-link
2. RAG warning -> Structured query affordance
3. RAG warning -> Workbench affordance

## 3. Target Page Responsibility Confirmation

### 3.1 Project

Route:

1. `/game/project`

Owns:

1. Project config form
2. Project summary
3. Agent binding summary
4. Storage snapshot
5. Workspace entry cards to Knowledge / Map Editor / NumericWorkbench / Advanced

Must not own:

1. RAG Ask main body
2. Current release main runtime panel
3. Formal map review body
4. SVN main operations

### 3.2 Knowledge

Route:

1. `/game/knowledge`

Owns:

1. Current release summary
2. Release list
3. Build release from current indexes
4. Set current
5. Rollback
6. RAG Ask
7. Citation list
8. Empty doc-context hint
9. Structured query panel
10. Workbench entry affordance

Must not own:

1. Project config form
2. Formal map editor body
3. SVN
4. Provider selector or API key UI

### 3.3 Map Editor

Route:

1. `/game/map`

Owns:

1. Candidate map review
2. Saved formal map review
3. Save as formal map
4. Saved formal map status-only edit
5. Relationship warnings

Must not own:

1. Ordinary RAG Ask
2. Draft table editing
3. Project onboarding config
4. SVN

### 3.4 NumericWorkbench

Routes:

1. `/numeric-workbench`
2. Future normalized alias may be added later only if needed, but current route must keep working in this lane

Owns:

1. Citation target state
2. Dirty edit
3. Save session
4. Export draft dry-run
5. Proposal handoff and proposal/session route state

Must not own:

1. Formal map editing
2. Release publishing
3. SVN write-back

### 3.5 Advanced

Routes:

1. `/game/advanced`
2. `/game/advanced/svn`

Owns:

1. SvnSync entry
2. Low-frequency operator or legacy entry cards
3. Future diagnostics placeholders if needed

Must not own:

1. Daily Knowledge workflow
2. Project onboarding
3. RAG primary path

## 4. Block Migration Table

| Current block | Target page | Move type | Phase note |
| --- | --- | --- | --- |
| Project config form | Project | full move | G.3 |
| Create project agent wizard | Project | full move | G.3 |
| Save / reset / validate | Project | full move | G.3 |
| Storage summary | Project | full move | G.3 |
| Current release summary | Knowledge | full move | G.2 |
| Release list | Knowledge | full move | G.2 |
| Build release modal and trigger | Knowledge | full move | G.2 |
| Set current | Knowledge | full move | G.2 |
| Rollback to previous | Knowledge | full move | G.2 |
| RAG Ask main panel | Knowledge | full move | G.2 |
| Structured query panel | Knowledge | full move | G.2 |
| Citation list | Knowledge | full move | G.2 |
| Empty doc-context hint | Knowledge | full move | G.2 |
| Workbench affordance | Knowledge | entry only, no semantic change | G.2 |
| Candidate map review | Map Editor | full move | G.4 |
| Saved formal map review | Map Editor | full move | G.4 |
| Save as formal map | Map Editor | full move | G.4 |
| Saved formal map status-only edit | Map Editor | full move | G.4 |
| SvnSync page | Advanced | route move + compat redirect | G.5 |
| NumericWorkbench page | NumericWorkbench | no move | unchanged |

## 5. Route Change Table

Current controlling route registry is `console/src/layouts/MainLayout/index.tsx`.

| Current route | Planned route | Action | Compatibility requirement |
| --- | --- | --- | --- |
| `/game` | `/game/project` | redirect target changes | must keep a working redirect |
| `/game-project` | `/game/project` | keep as alias or redirect | yes |
| none | `/game/project` | add | new canonical Project route |
| none | `/game/knowledge` | add | new canonical Knowledge route |
| none | `/game/map` | add | new canonical Map Editor route |
| none | `/game/advanced` | add | page shell only is acceptable in G.1 |
| `/svn-sync` | `/game/advanced/svn` | keep old path as redirect or alias | yes |
| `/numeric-workbench` | `/numeric-workbench` | keep | must not break deep-links |

Route notes:

1. `MainLayout` currently maps `/game` -> `/game-project`; G.1 should normalize this to `/game/project`.
2. NumericWorkbench deep-links currently land on `/numeric-workbench` with query params, not on a nested `/game/*` route. That behavior must remain intact in this lane.
3. No route work is needed in `console/src/App.tsx`; the owning route registry is `console/src/layouts/MainLayout/index.tsx`.

## 6. Navigation Change Table

Current controlling navigation is `console/src/layouts/Sidebar.tsx` plus `console/src/layouts/constants.ts`.

Recommended Game section order:

1. Project
2. Knowledge
3. Map Editor
4. NumericWorkbench
5. Advanced

| Current nav item | Current path | Planned nav item | Planned path | Notes |
| --- | --- | --- | --- | --- |
| Game Project | `/game-project` | Project | `/game/project` | reuse current concept, canonical path changes |
| none | none | Knowledge | `/game/knowledge` | new first-class nav item |
| none | none | Map Editor | `/game/map` | new first-class nav item |
| NumericWorkbench | `/numeric-workbench` | NumericWorkbench | `/numeric-workbench` | keep first-class nav item |
| SvnSync | `/svn-sync` | Advanced | `/game/advanced` | SvnSync becomes child entry or card under Advanced |

Navigation notes:

1. G.1 only needs navigation skeleton, not final icons or polished labels.
2. New i18n nav keys will likely be required for Knowledge / Map Editor / Advanced.
3. Legacy entries such as IndexMap / DocLibrary / KnowledgeBase should not be silently deleted without a deliberate compat decision in the implementation lane; in G.1 they can temporarily remain or be folded later, but the new four-page split must become primary.

## 7. Component Split Recommendations

Minimal split recommendation:

### 7.1 Project page components

1. `ProjectPage`
2. `ProjectConfigPanel`
3. `StorageSnapshotPanel`
4. `WorkspaceEntryCards`

### 7.2 Knowledge page components

1. `KnowledgePage`
2. `KnowledgeReleasePanel`
3. `KnowledgeAskPanel`
4. `KnowledgeCitationList`
5. `KnowledgeStatusPanel`

### 7.3 Map Editor page components

1. `MapEditorPage`
2. `MapCandidatePanel`
3. `SavedFormalMapPanel`

### 7.4 Advanced page components

1. `AdvancedPage`
2. `AdvancedEntryCards`
3. `SvnSyncEntryPanel` or direct reuse of existing `SvnSync`

Split rule:

1. Keep API calls and state ownership in page container during initial extraction when possible.
2. First extraction should be presentational and routing-first, not semantic redesign.
3. Reuse `GameProject.module.less` styles in early phases if that is cheaper than immediate style re-architecture.

## 8. Affected Files List

### 8.1 G.1 route skeleton

Expected touched files:

1. `console/src/layouts/MainLayout/index.tsx`
2. `console/src/layouts/Sidebar.tsx`
3. `console/src/layouts/constants.ts`
4. `console/src/pages/Game/index.ts`
5. new Project page container file or files under `console/src/pages/Game/Project/`
6. new Knowledge page container file or files under `console/src/pages/Game/Knowledge/`
7. new Map Editor page container file or files under `console/src/pages/Game/MapEditor/`
8. new Advanced page container file or files under `console/src/pages/Game/Advanced/`
9. locale files under `console/src/locales/` if new nav labels are introduced

### 8.2 G.2 move Knowledge runtime blocks

Expected touched files:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. `console/src/pages/Game/Knowledge/KnowledgePage.tsx`
4. `console/src/pages/Game/Knowledge/KnowledgePage.module.less`
5. `console/src/pages/Game/Knowledge/components/KnowledgeReleasePanel.tsx`
6. `console/src/pages/Game/Knowledge/components/KnowledgeAskPanel.tsx`
7. `console/src/pages/Game/Knowledge/components/KnowledgeCitationList.tsx`
8. possibly `console/src/pages/Game/ragUiHelpers.ts`

### 8.3 G.3 shrink Project page

Expected touched files:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. `console/src/pages/Game/Project/ProjectPage.tsx`
4. `console/src/pages/Game/Project/ProjectPage.module.less`
5. `console/src/pages/Game/Project/components/ProjectConfigPanel.tsx`
6. `console/src/pages/Game/Project/components/StorageSnapshotPanel.tsx`
7. `console/src/pages/Game/Project/components/WorkspaceEntryCards.tsx`

### 8.4 G.4 move Formal Map body to Map Editor

Expected touched files:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. `console/src/pages/Game/MapEditor/MapEditorPage.tsx`
4. `console/src/pages/Game/MapEditor/MapEditorPage.module.less`
5. `console/src/pages/Game/MapEditor/components/MapCandidatePanel.tsx`
6. `console/src/pages/Game/MapEditor/components/SavedFormalMapPanel.tsx`

### 8.5 G.5 move SVN to Advanced

Expected touched files:

1. `console/src/layouts/MainLayout/index.tsx`
2. `console/src/layouts/Sidebar.tsx`
3. `console/src/layouts/constants.ts`
4. `console/src/pages/Game/SvnSync.tsx` or wrapper usage from Advanced
5. `console/src/pages/Game/SvnSync.module.less` if reused directly
6. `console/src/pages/Game/Advanced/AdvancedPage.tsx`
7. `console/src/pages/Game/Advanced/AdvancedPage.module.less`

## 9. Deep-Link and Compatibility Requirements

Must not break:

1. Citation -> NumericWorkbench deep-link assembled from `GameProject.tsx` via `navigate(`/numeric-workbench?${params.toString()}`)`.
2. NumericWorkbench query-param parsing for `table`, `row`, `field`, `from=rag-citation`, `citationId`, `citationTitle`, `citationSource`.
3. Proposal or draft session state handled inside `NumericWorkbench.tsx` by search params and session store.
4. Current release / RAG behavior currently hosted in `GameProject.tsx`.
5. Old `/game-project` route.
6. Old `/svn-sync` route.

## 10. Minimal Implementation Order

### G.1 route skeleton

Goal:

1. Add canonical routes and navigation entries without moving logic yet.

Acceptance:

1. `/game/project`, `/game/knowledge`, `/game/map`, `/game/advanced` all resolve.
2. `/game` redirects to `/game/project`.
3. `/game-project` still resolves through alias or redirect.
4. `/numeric-workbench` remains unchanged.
5. No backend or semantic changes.

### G.2 move Knowledge runtime blocks

Goal:

1. Move current release, build/set-current/rollback, RAG Ask, citations, doc-context hint, and workbench entry to Knowledge page.

Acceptance:

1. Knowledge page contains the full existing runtime behavior.
2. Citation -> NumericWorkbench still works.
3. Empty doc-context hint still appears only in the same conditions.
4. Build / set-current / rollback semantics remain unchanged.

### G.3 shrink Project page

Goal:

1. Reduce GameProject into pure Project scope or replace it with Project page implementation.

Acceptance:

1. Project page contains config, storage, and entry cards only.
2. No RAG or map editor body remains on Project page.
3. Save / reset / validate behavior is unchanged.

### G.4 move Formal Map body to Map Editor

Goal:

1. Move candidate/saved formal map body and save controls to Map Editor page.

Acceptance:

1. Candidate map review renders exactly as before.
2. Save as formal map behavior is unchanged.
3. Saved formal map status-only edit behavior is unchanged.
4. Relationship warnings still render.

### G.5 move SVN to Advanced

Goal:

1. Make Advanced the low-frequency entry point for SvnSync.

Acceptance:

1. Advanced page exposes SVN entry.
2. `/svn-sync` still resolves through redirect or alias.
3. No SVN runtime semantics change.

### G.6 runtime build and smoke

Goal:

1. Validate frontend build and targeted runtime flows after route split.

Acceptance:

1. Frontend build passes.
2. Route navigation smoke passes.
3. Citation -> NumericWorkbench smoke passes.
4. Current release / RAG smoke passes.
5. Formal map save smoke passes.

### G.7 closeout

Goal:

1. Produce closeout doc confirming no semantic drift.

Acceptance:

1. Closeout explicitly states no backend/API/schema change.
2. Closeout explicitly states no NumericWorkbench semantic change.
3. Closeout explicitly states no SVN semantic change.

## 11. Hard-No Scope

Do not do any of the following in Lane G:

1. Change backend API
2. Change API schema
3. Change ordinary RAG no-write behavior
4. Change release build semantics
5. Change set-current semantics
6. Change rollback semantics
7. Change formal map save semantics
8. Change NumericWorkbench draft-only semantics
9. Change proposal or export semantics
10. Add provider selector UI
11. Add API key UI
12. Change provider or model ownership in Game pages
13. Change SVN sync, update, commit, or proposal behavior
14. Add automatic formal map writes from chat
15. Add automatic NumericWorkbench draft creation from chat

## 12. Blockers Review

Blocker status: none found

Observed risks, but not blockers:

1. `GameProject.tsx` currently owns a very large amount of local state, so extraction order matters.
2. `GameProject.module.less` contains mixed style concerns for release, RAG, and map review blocks; early phases should prefer reuse over premature restyling.
3. Sidebar still exposes legacy Game entries such as IndexMap / DocLibrary / KnowledgeBase; G.1 should decide whether they remain temporarily visible or become secondary to the new split.

## 13. G.1 Suggested Construction Scope

Only do this in G.1:

1. Add route containers for Project / Knowledge / Map Editor / Advanced.
2. Add canonical route mappings and redirects.
3. Update Sidebar and route-key constants.
4. Add minimal page shells or placeholder entry cards.
5. Keep existing GameProject, NumericWorkbench, and SvnSync behavior intact.

Do not do this yet in G.1:

1. Move RAG body
2. Move formal map body
3. Refactor NumericWorkbench
4. Change any API call ownership beyond route container composition

## 14. Exact Prompt For Next G.1 Route Skeleton Agent

```text
你是 Lane G.1 route skeleton implementation agent。只做 Game workspace 拆页第一步：新增 canonical routes、导航骨架、兼容 redirect，不搬大块运行逻辑，不改 backend，不改 API schema，不运行 SVN，不执行 commit。

仓库：e:/LTclaw2.0

必须先阅读：
1. docs/tasks/post-mvp/lane-g-game-workspace-page-split-checklist-2026-05-12.md
2. docs/tasks/post-mvp/lane-g-game-workspace-page-split-source-review-2026-05-12.md
3. console/src/layouts/MainLayout/index.tsx
4. console/src/layouts/Sidebar.tsx
5. console/src/layouts/constants.ts
6. console/src/pages/Game/index.ts
7. console/src/pages/Game/GameProject.tsx
8. console/src/pages/Game/SvnSync.tsx
9. console/src/pages/Game/NumericWorkbench.tsx

目标：
1. 新增 canonical routes:
   - /game/project
   - /game/knowledge
   - /game/map
   - /game/advanced
2. 兼容旧路由：
   - /game -> /game/project
   - /game-project -> /game/project
   - /svn-sync -> /game/advanced/svn 或等价兼容入口
3. Sidebar 新增一级导航：
   - Project
   - Knowledge
   - Map Editor
   - NumericWorkbench
   - Advanced
4. NumericWorkbench 继续保留 /numeric-workbench，绝对不能破坏 citation deep-link。
5. G.1 只搭骨架：
   - 可以新增 ProjectPage / KnowledgePage / MapEditorPage / AdvancedPage
   - 可以先让其中部分页面复用现有页面或显示 placeholder/entry cards
   - 不搬 RAG 主体
   - 不搬 formal map 主体
   - 不改 NumericWorkbench 语义
   - 不改 SVN 语义

实施边界：
1. 不改 backend/API/schema
2. 不加 provider selector/API key UI
3. 不改 release build / set-current / rollback semantics
4. 不改 formal map save semantics
5. 不改 NumericWorkbench draft-only semantics
6. 不改 proposal/export semantics

期望输出：
1. 完成路由骨架实现
2. 只做最小必要代码变更
3. 运行最小前端校验
4. 新增 closeout 文档：
   docs/tasks/post-mvp/lane-g-game-workspace-route-skeleton-implementation-2026-05-12.md

收尾必须汇报：
1. 改动文件列表
2. 新路由列表
3. 旧路由兼容情况
4. 导航改动
5. 运行了什么校验
6. 是否发现 blocker
7. git diff --check 结果
```

## 15. This G.0 Step Output Summary

1. This step should add only one docs file.
2. This step should not modify source code.
3. Expected `git diff --check` result is clean.
