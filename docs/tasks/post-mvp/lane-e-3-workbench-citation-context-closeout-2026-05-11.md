# Lane E.3 Workbench Citation Context Closeout

Date: 2026-05-11
Status: frontend-only closeout
Scope: preserve the Lane E.2 citation deep-link behavior, add a lightweight workbench citation-context hint, and keep all backend, schema, and no-write boundaries unchanged

## 1. Actual Modified Files

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/NumericWorkbench.tsx`
3. `docs/tasks/post-mvp/lane-e-3-workbench-citation-context-closeout-2026-05-11.md`

## 2. Citation Context Parameters

GameProject citation deep-link continues to preserve the existing workbench targeting parameters:

1. `table`
2. `row`
3. `field`

Lane E.3 adds lightweight context parameters for display only:

1. `from=rag-citation`
2. `citationId`
3. `citationTitle`
4. `citationSource`

Boundary:

1. these parameters are frontend-only route context
2. they do not change any backend contract
3. they do not create drafts automatically
4. they do not trigger publish or formal-knowledge writes

## 3. NumericWorkbench Hint Placement And Copy Boundary

Hint placement:

1. NumericWorkbench shows the citation-context hint near the top of the active workbench view, below the existing draft-only boundary notice and above the main workbench shell

Hint behavior:

1. the hint appears only when the route is explicitly opened from `from=rag-citation`
2. the hint also requires an active deep-link target such as `table`, `row`, or `field`
3. this avoids leaking the citation hint into unrelated session-only workbench navigation

Hint copy boundary:

1. `Opened from a RAG citation`
2. citation tags summarize `table`, `row`, `field`, and `citationId` when present
3. a secondary line shows citation title or source details when available
4. the boundary line states that the hint is for inspection context only
5. the boundary line states that changes remain draft-only dry-run work
6. the boundary line states that the flow does not publish automatically

## 4. Backend And Schema Changes

1. backend changed: no
2. API schema changed: no
3. provider changed: no
4. Ask schema changed: no
5. release build changed: no
6. formal map save changed: no

## 5. Write Or Publish Side Effects

1. citation click does not create a draft automatically
2. citation click does not trigger publish
3. citation click does not write formal knowledge release
4. citation click does not trigger backend write operations by itself

## 6. Real Test Data Path Validation Note

Requested real test data path:

1. `/Users/Admin/Documents/中小型游戏设计框架`

Validation note:

1. a local LTClaw app on port `8092` was available for smoke testing
2. the running app was not configured to the requested real test data path during this turn
3. the visible current local project directory in the running app remained a different path, so a real-path smoke against `/Users/Admin/Documents/中小型游戏设计框架` was not executed in this turn
4. no result was fabricated for that real-path scenario

## 7. Validation Result

Validation performed:

1. TypeScript: passed
2. targeted ESLint on `GameProject.tsx` and `NumericWorkbench.tsx`: no errors; existing `react-hooks/exhaustive-deps` warnings remain in `NumericWorkbench.tsx`
3. `git diff --check`: passed
4. touched-file NUL check: passed

Manual smoke status:

1. executed against a running local LTClaw app at `http://127.0.0.1:8092`
2. GameProject route used: `http://127.0.0.1:8092/game-project`
3. the running app was still configured to a different local project directory, so the smoke did not use `/Users/Admin/Documents/中小型游戏设计框架`
4. the sample question `Where is equipment enhancement described?` returned a table citation for `元素表` with `source path: 元素表.xlsx` and `row: 2`
5. clicking `Open in workbench` first navigated to `http://127.0.0.1:8092/numeric-workbench?table=%E5%85%83%E7%B4%A0%E8%A1%A8&from=rag-citation&citationId=citation-001&citationTitle=%E5%85%83%E7%B4%A0%E8%A1%A8&citationSource=%E5%85%83%E7%B4%A0%E8%A1%A8.xlsx&row=2`
6. NumericWorkbench then normalized the route while preserving citation context, resulting in a URL that still included `from=rag-citation`, `citationId`, `citationTitle`, `citationSource`, `table`, and `row`
7. NumericWorkbench showed the top-of-page citation context hint with:
8. `Opened from a RAG citation`
9. tags for `table: 元素表`, `row: 2`, and `citation-001`
10. `Citation: 元素表 (元素表.xlsx)`
11. `Use this as inspection context only. Any changes remain draft-only dry-run work and do not publish automatically.`
12. the workbench still showed `当前 0 项待保存`, so citation click did not create a draft automatically
13. no publish action and no formal-knowledge write action was triggered during the smoke

## 8. Remaining Risks

1. citation targeting still depends on existing frontend inference from citation metadata
2. field-level precision still depends on the citation title and source-type shape returned by the current answer path
3. real-path smoke for `/Users/Admin/Documents/中小型游戏设计框架` still remains to be executed under a correctly configured local app
4. the workbench hint is intentionally lightweight and does not yet provide richer cited-row preview content