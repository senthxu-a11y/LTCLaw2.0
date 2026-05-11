# Lane E.2 NumericWorkbench Citation Entry Closeout

Date: 2026-05-11
Status: frontend slice completed
Scope: add a citation-scoped GameProject to NumericWorkbench entry and reinforce draft-only, dry-run, and not-publish wording without changing backend API schema, provider transport, or no-write semantics

## 1. Actual Modified Files

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/NumericWorkbench.tsx`
3. `docs/tasks/post-mvp/lane-e-2-numeric-workbench-citation-entry-closeout-2026-05-11.md`

## 2. Backend Change

1. backend changed: no
2. backend router changed: no
3. release, formal map, and no-write semantics changed: no

## 3. API Schema Change

1. RAG request schema changed: no
2. RAG response schema changed: no
3. new endpoint added: no
4. existing backend contract expanded: no

## 4. Provider Or LLM Change

1. provider selection changed: no
2. provider transport changed: no
3. LLM contract changed: no
4. API key handling changed: no

## 5. Citation To Workbench UX Change

Implemented behavior:

1. each RAG citation row in GameProject now exposes a citation-scoped `Open in workbench` action when enough location context is available
2. the action reuses the existing NumericWorkbench deep-link route and passes `table` plus `row` and `field` when they can be inferred
3. the action does not create any draft automatically
4. the action does not call a new backend endpoint
5. when the citation does not contain enough table context, the action stays disabled and explains why instead of sending the user to a broken route

Implementation note:

1. the target is inferred from existing citation metadata such as `artifact_path`, `source_path`, `title`, and `row`
2. the workbench still owns the actual session creation and landing behavior

## 6. Draft-Only And Dry-Run Wording Change

Implemented wording changes:

1. NumericWorkbench session entry view now states that the flow is for draft and dry-run use only
2. NumericWorkbench active workspace now shows a compact boundary notice stating that it does not publish automatically or write formal knowledge release
3. NumericWorkbench draft export modal now states that export creates a draft proposal only and does not publish automatically

Effect:

1. the workbench remains positioned as a safe planning workspace
2. the UI now makes the no-publish boundary easier to understand at first glance

## 7. Validation Result

Validation performed:

1. TypeScript: passed
2. targeted ESLint on `GameProject.tsx` and `NumericWorkbench.tsx`: no errors; existing `react-hooks/exhaustive-deps` warnings remain in `NumericWorkbench.tsx`
3. related frontend tests: none found for GameProject or NumericWorkbench
4. `git diff --check`: passed
5. touched-file NUL check: passed

Manual smoke:

1. executed against a running local LTClaw Console instance at `http://127.0.0.1:8092`
2. GameProject route used: `http://127.0.0.1:8092/game-project`
3. sample question `How does combat damage work in the current release?` returned manifest and map citations only; after the targeting fix, both `Open in workbench` buttons were disabled and showed `workbench target: -`
4. sample question `Where is equipment enhancement described?` returned a table citation for `元素表` with `source path: 元素表.xlsx`, `row: 2`, and an enabled `Open in workbench` button
5. clicking that citation-scoped action navigated to `http://127.0.0.1:8092/numeric-workbench?table=%E5%85%83%E7%B4%A0%E8%A1%A8&row=2` and the workbench then normalized the route to include `session`, `tableId`, and `rowId`
6. NumericWorkbench showed the boundary copy in all three intended places:
7. session entry view: `仅用于 draft 和 dry-run，不会自动发布，也不会写入 formal knowledge release。`
8. active workspace notice: `Draft-only dry-run workspace. It does not publish automatically or write formal knowledge release.`
9. draft export modal: `This exports a draft proposal only. It does not publish automatically or write formal knowledge release.`
10. no draft was created automatically from the GameProject citation click
11. a temporary local dirty cell edit was created only to open the export modal and was reverted before closeout
12. no publish or formal-knowledge write action was triggered during the smoke

## 8. Remaining UX Gaps

Remaining gaps after this slice:

1. insufficient-context warning copy is still too implementation-oriented for planner-facing workflows
2. citation targeting still depends on heuristics from current citation metadata and does not yet guarantee field-level precision for every citation shape
3. session and draft state are clearer than before but still spread across several UI regions
4. there is still no richer table preview or cited-field summary inside the GameProject answer area

## 9. Explicit Non-Goals Preserved

This slice did not do any of the following:

1. provider selector
2. API key UI
3. production rollout
4. production ready claim
5. automatic publish
6. Ask schema provider, model, or api_key fields
7. ordinary RAG writes release
8. ordinary RAG writes formal map
9. ordinary RAG writes test plan
10. ordinary RAG writes workbench draft