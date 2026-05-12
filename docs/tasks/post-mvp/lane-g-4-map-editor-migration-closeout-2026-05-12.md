# Lane G.4 Map Editor Migration Closeout

Date: 2026-05-12
Status: implementation complete, awaiting user decision on commit/push
Scope: migrate formal map review/save/status-edit ownership from Project to Map Editor without changing backend or API semantics

## 1. Actual Modified Files

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/MapEditor/index.tsx`
3. `console/src/pages/Game/components/FormalMapWorkspace.tsx`
4. `docs/tasks/post-mvp/lane-g-4-map-editor-migration-closeout-2026-05-12.md`

## 2. Backend / API / Schema Change Check

1. Backend changed: no
2. API schema changed: no
3. Formal map save endpoint changed: no
4. Provider / LLM / Ask schema changed: no
5. Knowledge release build / publish flow changed: no
6. NumericWorkbench draft semantics changed: no

## 3. `/game/map` Now Owns

1. Candidate map review panel
2. Saved formal map review panel
3. Save as formal map primary action
4. Saved formal map status-only edit controls
5. Save status changes action
6. Relationship warning display
7. Candidate and saved map count display
8. Safe unavailable states for missing local project directory or missing current release

Implementation note:
1. Existing route `/game/map` already pointed to `MapEditor/index.tsx`, so this lane reused that route and replaced the prior placeholder body.
2. Existing table index / dependency browser in `IndexMap.tsx` was not the target of this lane and remains separate from Map Editor ownership.

## 4. Project Removed vs Retained

Project removed:
1. Candidate map full list
2. Saved formal map full list
3. Save as formal map action
4. Status select controls
5. Save status changes action
6. Full relationship warning panel

Project retained:
1. Project config form
2. Storage snapshot
3. Save / validate / reset actions
4. Create-agent wizard
5. Workspace entry cards
6. Compact candidate map summary
7. Compact saved formal map summary with map hash safe state
8. Open Map Editor button
9. Refresh button for compact summary

## 5. Formal Map Semantics Check

1. Save as formal map still saves the current candidate map through the existing `saveFormalMap` API.
2. Status-only edits still operate on a local draft of the saved formal map.
3. Save status changes still persists through the same `saveFormalMap` API with unchanged semantics.
4. No release build or publish action was added to Map Editor.
5. No automatic formal map writes from RAG or chat were added.

## 6. Validation

1. `./node_modules/.bin/tsc --noEmit`: pass
2. `./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/MapEditor/index.tsx src/pages/Game/components/FormalMapWorkspace.tsx`: pass
3. `git diff --check`: pending at time of writing, rerun after closeout write
4. NUL check on touched files: pending at time of writing, rerun after closeout write
5. Keyword boundary review: pending at time of writing, rerun after closeout write

## 7. Manual Smoke

Smoke URL:
1. `http://127.0.0.1:8097/game/project`
2. `http://127.0.0.1:8097/game/map`

`/game/project`:
1. Project config form visible: pass
2. Storage snapshot visible: pass
3. Save / validate / reset visible: pass
4. Compact formal map summary visible: pass
5. Open Map Editor visible: pass
6. Full formal map editor body absent from Project main body: pass

`/game/map`:
1. Map Editor page visible with correct primary title: pass
2. Candidate map panel visible: pass
3. Saved formal map panel visible: pass
4. Save as formal map button present: pass
5. Save as formal map disabled in unavailable state: pass
6. Save status changes button present: pass
7. Status edit path remains non-primary when no saved formal map is available: pass via disabled safe state
8. No release build or publish action shown on Map Editor: pass
9. No automatic formal map write behavior introduced in smoke: pass

Observed smoke state:
1. Temporary smoke workspace had no configured local project directory.
2. Candidate and saved formal map panels therefore surfaced safe unavailable states with `Local project directory not configured`.
3. This matches the lane boundary and was not treated as a G.4 blocker.

## 8. Remaining Caveat

1. This lane moved formal map ownership to `/game/map`, but did not merge or redesign the separate table index / dependency browser route.
2. `IndexMap.tsx` remains outside the Map Editor primary flow and should be treated as a secondary surface until a later lane explicitly addresses that UX relationship.
3. Smoke covered route ownership and safe-state behavior, not a live configured project with writable formal map data.

## 9. Commit / Push Recommendation

1. Recommend commit: yes
2. Recommend push after final diff/NUL/keyword checks pass: yes
3. Do not include `.vite/` or other runtime cache artifacts in any commit.