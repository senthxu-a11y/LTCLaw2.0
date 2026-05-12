# Lane G.1 Game Workspace Route Skeleton Receipt

Date: 2026-05-12
Status: receipt
Scope: Game workspace route skeleton and navigation skeleton only
Final result: pass

## 1. Modified Files

Source files changed for G.1:

1. `console/src/layouts/MainLayout/index.tsx`
2. `console/src/layouts/Sidebar.tsx`
3. `console/src/layouts/constants.ts`
4. `console/src/pages/Game/index.ts`
5. `console/src/pages/Game/Project/index.tsx`
6. `console/src/pages/Game/Knowledge/index.tsx`
7. `console/src/pages/Game/MapEditor/index.tsx`
8. `console/src/pages/Game/Advanced/index.tsx`
9. `console/src/pages/Game/AdvancedSvn/index.tsx`
10. `console/src/locales/zh.json`
11. `console/src/locales/en.json`
12. `console/src/locales/ja.json`
13. `console/src/locales/ru.json`

Document added:

1. `docs/tasks/post-mvp/lane-g-1-game-workspace-route-skeleton-receipt-2026-05-12.md`

## 2. New Routes

Added canonical routes:

1. `/game/project`
2. `/game/knowledge`
3. `/game/map`
4. `/game/advanced`
5. `/game/advanced/svn`

## 3. Compatibility Routes

Preserved compatibility routing:

1. `/game` -> `/game/project`
2. `/game-project` -> `/game/project`
3. `/svn-sync` -> `/game/advanced/svn`

Confirmed unchanged route:

1. `/numeric-workbench`

## 4. Sidebar And Navigation Changes

Game navigation skeleton is now normalized to five primary entries:

1. Project
2. Knowledge
3. Map Editor
4. NumericWorkbench
5. Advanced

Implementation details:

1. `game-project` now navigates to `/game/project`.
2. Added `game-knowledge` navigation key for `/game/knowledge`.
3. Added `game-map` navigation key for `/game/map`.
4. Kept `numeric-workbench` unchanged.
5. Added `game-advanced` navigation key for `/game/advanced`.
6. `/game/advanced/svn` and `/svn-sync` both highlight Advanced in sidebar selection.
7. Legacy Game leaf entries were removed from the primary Game sidebar skeleton for this lane.

## 5. Skeleton Containers

Created lightweight route containers only:

1. `ProjectPage` delegates directly to existing `GameProject` as an interim compatibility shell.
2. `KnowledgePage` is a placeholder page with explicit G.1 skeleton copy.
3. `MapEditorPage` is a placeholder page with explicit G.1 skeleton copy.
4. `AdvancedPage` is a placeholder page with an entry to SVN.
5. `AdvancedSvnPage` delegates directly to existing `SvnSync`.

## 6. Explicit Non-Changes

This lane did not migrate or alter the following business logic:

1. RAG main body remains in `GameProject`.
2. Formal map review and save logic remain in `GameProject`.
3. `GameProject` business logic was not modified.
4. `NumericWorkbench` route and behavior were not modified.
5. `SvnSync` behavior was not modified.
6. No backend changes.
7. No API changes.
8. No schema changes.
9. No provider selector or API key UI changes.
10. No SVN command was run.

## 7. Validation Commands And Results

Route source inspection:

1. Verified in `console/src/layouts/MainLayout/index.tsx` that all required canonical and compatibility routes are present.

Validation commands executed:

1. `Set-Location 'e:/LTclaw2.0/console'; .\node_modules\.bin\tsc.cmd -b --noEmit`
2. `Set-Location 'e:/LTclaw2.0/console'; .\node_modules\.bin\eslint.cmd src/layouts/MainLayout/index.tsx src/layouts/Sidebar.tsx src/layouts/constants.ts src/pages/Game/index.ts src/pages/Game/Project/index.tsx src/pages/Game/Knowledge/index.tsx src/pages/Game/MapEditor/index.tsx src/pages/Game/Advanced/index.tsx src/pages/Game/AdvancedSvn/index.tsx`
3. `Set-Location 'e:/LTclaw2.0'; git diff --check`

Results:

1. TypeScript noEmit: pass
2. Targeted ESLint on touched frontend files: pass
3. git diff --check: pass

Runtime note:

1. App was not started for this lane.

## 8. Blocker Review

Blocker status: none

## 9. Outcome Summary

G.1 route skeleton is complete for the approved scope:

1. canonical Game workspace routes now exist
2. compatibility redirects are preserved
3. NumericWorkbench route remains intact
4. sidebar/navigation now reflects the target five-entry skeleton
5. business logic migration is intentionally deferred to G.2 and later lanes
