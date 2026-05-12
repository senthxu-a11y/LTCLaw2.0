# Lane E.5 NumericWorkbench First-Screen UX Review

Date: 2026-05-11
Status: source review only
Scope: freeze the minimum E.5 UI slice for NumericWorkbench first-screen usability after citation entry

## 1. Review Baseline

- repository status: clean working tree on main
- reviewed HEAD: 0bf5b6d23982229ca583fab268ed008824c60f9e
- origin/main after fetch: 0bf5b6d23982229ca583fab268ed008824c60f9e
- sync result: local main already matched origin/main, so no source sync change was needed
- local run-condition note: `.venv\Scripts\ltclaw.exe` exists, `console/node_modules` exists, `website/node_modules` exists, `pnpm` is not currently on PATH on this Windows machine
- review mode note: no app startup was required for this slice, and no assumption was made about port 8093 or a real-data path

## 2. Source Review Inputs

Primary files reviewed:

1. `console/src/pages/Game/NumericWorkbench.tsx`
2. `console/src/pages/Game/NumericWorkbench.module.less`
3. `console/src/pages/Game/GameProject.tsx`
4. `docs/tasks/post-mvp/lane-e-3-workbench-citation-context-closeout-2026-05-11.md`
5. `docs/tasks/post-mvp/lane-e-4-real-data-workbench-citation-smoke-receipt-2026-05-11.md`

Relevant current behavior confirmed from source:

1. `Open in workbench` builds a frontend-only deep-link with `table`, optional `row`, optional `field`, plus citation display context such as `from=rag-citation`, `citationId`, `citationTitle`, and `citationSource`.
2. NumericWorkbench shows a draft-only / dry-run notice as a separate top-level Alert Card.
3. NumericWorkbench shows citation context as another separate top-level Alert Card.
4. NumericWorkbench shows pending-save state in at least three places: page-header tag, toolbar tag, and right-side DirtyList.
5. Deep-link row highlight is transient and field highlight is column-level only.
6. Missing table, missing row, missing field, or failed row load do not currently surface an explicit first-screen failure message.

## 3. Current Observations

### 3.1 Citation context hint placement and screen usage

Observed:

1. The citation context hint is rendered above the main workbench shell as its own full-width Alert inside its own Card.
2. The hint currently uses a title, a tag row, a secondary citation-source line, and a secondary boundary line.
3. This is clear, but it consumes too much first-screen vertical space before the user reaches the main editable table area.

Assessment:

1. The information itself is useful and should stay.
2. The current container hierarchy is too tall for a first-screen entry state.
3. The current presentation feels like a separate informational block, not a compact entry-state indicator.

### 3.2 Draft-only / dry-run notice placement

Observed:

1. The draft-only / dry-run boundary is rendered as another separate full-width Alert Card above the workbench shell.
2. The page header subtitle already repeats the same high-level boundary.
3. The draft export modal also repeats the same non-publish boundary later in the flow.

Assessment:

1. The boundary must remain visible.
2. The current placement duplicates message weight at the most expensive vertical location.
3. This is a strong candidate to merge into a compact status strip closer to the main action area.

### 3.3 Dirty count and pending-save status placement

Observed:

1. Pending-save state appears in the page header as a green or volcano Tag.
2. Dirty count appears again in the top toolbar as `当前 X 项待保存`.
3. Dirty count appears again in the right-side DirtyList section header.
4. Save action also appears in the page header and in DirtyList.

Assessment:

1. The user can tell that drafts are unsaved, but the signal is fragmented.
2. The header and toolbar repeat nearly the same status before the user reaches the table.
3. For citation-entry first screen, one compact status area near the main action region would be clearer than repeated badges.

### 3.4 Row / field highlight behavior

Observed:

1. Deep-link opens the target table only if `dlTable` exists in the loaded table-name list.
2. If `dlRow` exists, the table search box is prefilled with the row value.
3. Row highlight is based on primary-key equality and lasts about 1.8 seconds.
4. Field highlight is column-header and column-cell styling only; there is no explicit success message that says the requested target was found.
5. Row filtering is substring search across all cells, not an exact row-id locator.

Assessment:

1. Successful positioning is visible, but subtle and short-lived.
2. The first screen does not explicitly tell the user whether the requested row and field were actually found.
3. When the row id is missing, the search prefill can degrade into a generic filter result rather than a precise target-state message.

### 3.5 Deep-link row missing behavior

Observed:

1. If the row does not exist in the currently loaded table data, no explicit warning is shown.
2. The search box is still prefilled with the row string.
3. The user may see zero hits, unrelated partial hits, or simply no highlight.

Assessment:

1. This is the main usability gap for citation-entry first screen.
2. The system currently fails soft, but too silently.
3. A lightweight first-screen notice is enough; no new backend behavior is needed.

### 3.6 Table open failure or missing-table behavior

Observed:

1. If the deep-link table is not present in `tableNames`, the deep-link effect returns early without user-facing feedback.
2. If row loading fails, the code falls back to empty headers and empty rows without a visible error banner in the main content area.
3. The empty table view copy is generic and does not explain whether the citation target table could not be found or failed to load.

Assessment:

1. The current empty states are acceptable for generic workbench usage.
2. They are not specific enough for citation-entry troubleshooting.
3. A compact citation-target warning would cover both missing-row and missing-field cases, and a table-not-found warning should be distinct.

### 3.7 First-screen vertical pressure

Observed:

1. The first screen can stack: page header, permission card, draft-only card, citation-context card, toolbar, table card title, then actual table content.
2. On smaller desktop heights, the actual editable table area is pushed lower than needed.
3. Right-side DirtyList and ImpactPanel also create strong visual weight, but they are secondary to the top-of-screen stacking problem.

Assessment:

1. The current issue is not lack of information.
2. The current issue is information packaging.
3. This can be improved with a small UI slice rather than a layout rewrite.

## 4. Final Recommendation

Freeze E.5 as a small first-screen compression slice, not a workbench redesign.

Recommended direction:

1. Compress citation entry context into a one-line or two-line status bar near the top of the editor area.
2. Merge draft-only / dry-run and pending-save state into the same compact status area, close to the main actions.
3. Add explicit, lightweight target-state copy for `found` versus `not found` outcomes.
4. Keep all routing, data structures, write semantics, and API contracts unchanged.

In short:

1. keep the current data and navigation model
2. keep the current workbench shell
3. reduce first-screen stack height
4. make citation targeting success or failure explicit

## 5. Recommended Minimum Implementation Slice

### 5.1 Compact citation status bar

Replace the current tall citation Alert Card with a compact status bar that keeps:

1. entry source: `Opened from RAG citation`
2. target summary: `table`, `row`, `field`
3. citation summary: `citationId` or `title`

Preferred behavior:

1. one line on wide screens
2. two lines on narrower screens
3. no separate multi-line explanatory block unless the user expands or needs an error state

### 5.2 Compact workbench state bar near main actions

Merge these into one compact status bar placed beside or directly under the toolbar:

1. draft-only / dry-run
2. no auto-publish behavior
3. current dirty count
4. pending-save state

Rationale:

1. this keeps the most important safety and progress state near the controls the user will use next
2. it removes duplicated header-level badges and top-level cards from the first screen

### 5.3 Explicit target-found copy

When row and field targeting succeed, make the status copy explicit, for example:

1. `Focused citation target in current table`
2. `Table: X, row: Y, field: Z`

The current visual highlight can remain, but the text state should confirm success so the user does not have to infer it from a short pulse.

### 5.4 Explicit lightweight target-not-found copy

When row or field cannot be located in the currently opened table, show a lightweight warning near the same status area, for example:

1. `Citation target not found in current table`
2. `Opened table X, but row Y or field Z could not be matched`

This should cover at least:

1. row missing
2. field missing
3. deep-link table present but row data not matched

### 5.5 Distinct table-not-found copy

If the citation target table itself cannot be opened, the warning should be distinct from row/field mismatch, for example:

1. `Citation table could not be opened`
2. `Requested table X is not available in this workbench`

This remains frontend-only state and does not require any backend recovery flow.

## 6. What Should Not Be Recommended

Do not recommend the following for E.5:

1. large-scale workbench layout refactor
2. moving side panel architecture around
3. new backend endpoint
4. new API schema or route schema
5. provider selector changes
6. API key UI
7. automatic draft creation
8. automatic save
9. any auto-publish behavior
10. any formal-release persistence step
11. any release-writing path from ordinary RAG flow
12. publish-flow expansion
13. release, test-plan, or formal-map workflow additions

## 7. Boundaries That Must Be Preserved

Keep these boundaries unchanged in E.5 implementation:

1. frontend-only UI slice
2. no backend change
3. no API schema change
4. no provider or LLM change
5. no Ask schema change
6. no publish action
7. no formal-release persistence
8. no automatic draft creation
9. no auto-publish path
10. no write-semantics change for current draft-only workbench flow
11. no broad layout rewrite of NumericWorkbench

## 8. Suggested Validation Method

Because this review freezes a small UI slice, validation can stay lightweight.

Recommended validation after E.5 implementation:

1. source-level check that the old tall citation Card and standalone boundary Card are replaced by a compact first-screen status treatment
2. manual UI check from a citation entry with target fully available
3. manual UI check from a citation entry where table exists but row does not match
4. manual UI check from a citation entry where table exists but field does not match
5. manual UI check from a citation entry where table cannot be opened
6. confirm dirty count and pending-save state are still visible without repeating in multiple tall blocks
7. confirm all wording still preserves `draft-only`, `dry-run`, and `does not publish automatically`
8. confirm no route, API, save, export, publish, or formal-release behavior changed

## 9. Can E.5 Move Directly To Implementation?

Yes.

Reason:

1. the main first-screen UX problem is clear from source alone
2. the minimum fix surface is small and local to NumericWorkbench UI composition
3. the recommendation does not depend on real-data availability, 8093 availability, or a new backend contract
4. the slice boundary is narrow enough to implement without reopening architecture questions

Implementation gate recommendation:

1. proceed to E.5 implementation as a docs-aligned, frontend-only, minimal UI compression slice
2. keep the success and failure messaging explicit
3. do not widen scope beyond first-screen usability