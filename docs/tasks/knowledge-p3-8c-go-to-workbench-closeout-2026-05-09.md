# Knowledge P3.8c Go To Workbench Closeout

Date: 2026-05-09

## Goal

Record that `P3.8c` is complete as a frontend-only minimal `Go to workbench` affordance slice on top of the existing GameProject RAG MVP entry.

## Scope

This slice intentionally stays inside the existing GameProject RAG entry and the existing NumericWorkbench destination.

Implemented in this round:

1. Added a minimal `Go to workbench` button only in explicit workbench guardrail contexts.
2. Kept navigation user-triggered only.
3. Kept the first version limited to navigation to `/numeric-workbench` only.
4. Added explicit `workbench.read` disabled behavior when capability context exists.

## Implemented Files

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. `docs/tasks/knowledge-p3-8c-go-to-workbench-closeout-2026-05-09.md`
4. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
5. `docs/tasks/knowledge-p3-gate-status-2026-05-07.md`
6. `docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md`

## Landed UI Behavior

1. The static workbench guardrail block in GameProject now shows a `Go to workbench` button.
2. A returned warning row with the existing workbench warning now also shows a `Go to workbench` button.
3. Generic `insufficient_context` next-step hints do not show the button.
4. Clicking the button navigates only to `/numeric-workbench`.
5. The first version does not pass freeform query text.
6. The first version does not auto-submit anything inside NumericWorkbench.
7. The first version does not create a test plan, candidate, build, publish, or SVN action.

## Permission Behavior

1. If capability context is absent, local trusted fallback remains intact and the button stays enabled.
2. If capability context exists and `workbench.read` is missing, the button is disabled.
3. Disabled tooltip copy is fixed to `Requires workbench.read permission.`.
4. Entering the button path does not require `knowledge.build` or `knowledge.publish`.
5. `workbench.test.write` still governs later workbench write behavior only and does not gate the entry button.

## Boundary Confirmation

The following boundaries remain unchanged:

1. `answerRagQuestion(...)` still sends only `{ query }`.
2. No provider, model, provider hint, or service config field was added.
3. No RAG request-schema change was added.
4. No backend router change was added.
5. No router provider-selection change was added.
6. No real LLM integration was added.
7. No structured-query affordance was added.
8. No combined structured-query plus workbench implementation was added.
9. No citation artifact or raw-source endpoint was added.
10. Ordinary RAG Q&A still does not become administrator acceptance.

## Validation

Validation completed for this round:

1. Frontend TypeScript no-emit validation ran with no output.
2. Targeted ESLint for `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/ragUiHelpers.ts` ran with no output.
3. `git diff --check` ran with no output.
4. Editor diagnostics reported no errors in `GameProject.tsx`, `ragUiHelpers.ts`, or `GameProject.module.less`.
5. No existing GameProject or RAG UI frontend test suite was found for this slice, so no frontend component test was run.
6. No backend pytest was run because this slice did not touch backend code.

## Result

1. `P3.8c` is complete.
2. The current GameProject RAG MVP entry now has a minimal workbench-only affordance without widening request, router, provider, or citation boundaries.
3. Structured query remains deferred as a separate destination problem.
