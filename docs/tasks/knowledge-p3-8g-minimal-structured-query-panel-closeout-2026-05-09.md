# Knowledge P3.8g Minimal Structured-Query Panel Closeout

Date: 2026-05-09

## Goal

Record that `P3.8g` is complete as a frontend-only minimal structured-query panel slice on top of the existing GameProject RAG MVP entry.

## Scope

This slice intentionally stays inside the existing GameProject RAG surface and reuses the existing `/game/index/query` backend endpoint without backend changes.

Implemented in this round:

1. Added a minimal in-page structured-query panel only in explicit structured-query guardrail contexts.
2. Added a frontend typed wrapper and normalization layer over the existing `/game/index/query` response.
3. Kept panel opening and submit user-triggered only.
4. Kept the first version read-only and limited to exact table-result and field-result display.
5. Added explicit `knowledge.read` disabled behavior only when capability context exists.

## Implemented Files

1. `console/src/api/modules/gameStructuredQuery.ts`
2. `console/src/api/types/game.ts`
3. `console/src/pages/Game/GameProject.tsx`
4. `console/src/pages/Game/GameProject.module.less`
5. `docs/tasks/knowledge-p3-8g-minimal-structured-query-panel-closeout-2026-05-09.md`
6. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
7. `docs/tasks/knowledge-p3-gate-status-2026-05-07.md`
8. `docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md`

## Landed UI Behavior

1. The static structured-query guardrail block in GameProject now shows an `Open structured query` button.
2. A returned warning row with the existing structured-query warning now also shows an `Open structured query` button.
3. Clicking the button opens a local in-page panel and may prefill the current RAG query if the panel draft is still empty.
4. Opening the panel does not auto-submit.
5. Submit is enabled only when a `selectedAgent` exists.
6. Submit sends only the local panel `query` and always fixes request mode to `auto`.
7. Returned results are normalized into read-only table items or field items only.
8. Source-like display remains limited to already returned `source_path`, `references`, and `tags` fields.
9. The first version does not navigate away from GameProject and does not create a test plan, candidate, build, publish, or SVN action.

## Permission Behavior

1. If no `selectedAgent` exists, panel submit stays disabled.
2. If capability context is absent and a `selectedAgent` exists, local trusted fallback remains intact and open plus submit stay enabled.
3. If capability context exists and `knowledge.read` is missing, both `Open structured query` and panel submit are disabled.
4. Disabled tooltip copy is fixed to `Requires knowledge.read permission.`.
5. This slice does not require `knowledge.build`.
6. This slice does not require `knowledge.publish`.

## Boundary Confirmation

The following boundaries remain unchanged:

1. `answerRagQuestion(...)` still sends only `{ query }`.
2. No provider, model, provider hint, or service config field was added.
3. No RAG router change was added.
4. No provider-selection change was added.
5. No backend API was added.
6. No backend `src` file was changed.
7. No real LLM integration was added.
8. No test-plan, candidate, build, publish, or mutation path was added.
9. `P3.8c` workbench affordance behavior was not changed.

## Validation

Validation completed for this round:

1. Editor diagnostics reported no errors in the touched frontend files.
2. Frontend TypeScript no-emit validation ran with no output.
3. Targeted ESLint for `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/ragUiHelpers.ts`, and `console/src/api/modules/gameStructuredQuery.ts` ran with no output.
4. `git diff --check` ran with no output.
5. No existing GameProject or RAG UI frontend test suite was found for this slice, so no frontend component test was run.
6. No backend pytest was run because this slice did not touch backend code.

## Result

1. `P3.8g` is complete.
2. The current GameProject RAG MVP entry now has a minimal structured-query panel with explicit open, optional prefill, explicit submit, and read-only normalized result display.
3. Ordinary RAG Q&A, structured query, and workbench flow remain product-distinct.
