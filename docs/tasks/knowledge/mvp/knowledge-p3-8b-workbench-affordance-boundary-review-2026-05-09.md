# Knowledge P3.8b Workbench Affordance Boundary Review

Date: 2026-05-09

## Goal

Define the product boundary for a future minimal `Go to workbench` affordance from the current RAG MVP entry.

This slice is boundary review only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

1. `docs/tasks/knowledge/mvp/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md`
2. `docs/tasks/knowledge/mvp/knowledge-p3-8a-routing-affordance-discovery-2026-05-09.md`
3. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`
5. `console/src/pages/Game/GameProject.tsx`
6. `console/src/pages/Game/ragUiHelpers.ts`
7. `console/src/pages/Game/NumericWorkbench.tsx`
8. `console/src/layouts/MainLayout/index.tsx`
9. `console/src/layouts/Sidebar.tsx`

Implementation-path correction for current repository reality:

1. The current NumericWorkbench page lives at `console/src/pages/Game/NumericWorkbench.tsx`.
2. The current sidebar component lives at `console/src/layouts/Sidebar.tsx`.

## Current Baseline

The current baseline is:

1. RAG already shows read-only workbench guardrail copy in the GameProject entry.
2. RAG already shows generic `insufficient_context` next-step hints that include a workbench hint string.
3. NumericWorkbench already exists as a real frontend destination at `/numeric-workbench`.
4. NumericWorkbench currently has explicit route-param support for `session`, `table`, `row`, and `field`.
5. NumericWorkbench does not currently define a dedicated freeform RAG-query handoff surface.
6. The current RAG request payload remains `{ query }` only.
7. Router behavior, provider selection, and citation boundaries remain unchanged.

## Boundary Decision

The future minimal `Go to workbench` affordance should be treated as a narrow workbench-only routing slice.

This boundary review does not authorize a combined structured-query plus workbench implementation.

Reasoning:

1. Workbench destination is explicit in the current frontend.
2. Structured-query destination is still not explicit in the current frontend.
3. A narrow workbench-only affordance can be reasoned about safely without widening the unresolved structured-query destination problem.

## Where The Workbench Affordance May Appear

### Allowed First-Version Surface

The first-version `Go to workbench` affordance should appear only when the RAG surface already exposes explicit workbench or change-intent guardrail context.

Allowed first-version placement:

1. In the existing workbench guardrail block shown above the result area.
2. In warning rows whose warning text is the existing workbench-flow warning.

### Not Allowed In First Version

The first-version affordance should not appear from generic `insufficient_context` next-step hints alone.

Why:

1. The current `insufficient_context` hints are generic and static.
2. They are not currently specific to proven change or edit intent.
3. Showing a workbench button there would over-broaden routing and could misdirect ordinary explanatory failures into an edit surface.
4. `insufficient_context` is a recoverable evidence-state, not a mutation-intent classifier.

Future possibility:

1. If a later slice introduces explicit query-intent classification for `insufficient_context` hints, that later slice may revisit whether a workbench affordance can appear there.
2. That is not authorized by this review.

## Interaction Boundary

Any future `Go to workbench` affordance must remain an explicit user-driven action.

Required behavior:

1. No automatic redirect.
2. No automatic route change on warning render.
3. No automatic route change on `insufficient_context` render.
4. No automatic route change on recent-question click.
5. No automatic route change on copy result.
6. No automatic route change on citation focus or citation review.
7. Only an explicit user click may trigger navigation.

## Navigation Boundary

The first version should navigate only to the existing NumericWorkbench route.

Allowed first-version behavior:

1. Navigate to `/numeric-workbench`.
2. Optionally preserve ordinary browser navigation semantics only.

Not allowed in first version:

1. Automatic workbench chat submission.
2. Automatic workbench change submission.
3. Automatic creation of dirty cells.
4. Automatic test-plan creation.
5. Automatic release-candidate creation.
6. Automatic build.
7. Automatic publish.

## Query And Context Handoff Boundary

The first version should not carry freeform RAG query text into NumericWorkbench.

Recommended first-version rule:

1. Navigate only to `/numeric-workbench` with no freeform-query payload handoff.

Why the current review does not recommend freeform-query handoff:

1. NumericWorkbench currently documents and consumes explicit route params only for `session`, `table`, `row`, and `field`.
2. The current route-param contract does not define a `query` or `prompt` handoff shape.
3. The current workbench page is table-centric and session-centric, not freeform-RAG-query-centric.
4. Adding freeform-query handoff too early would create an implicit product contract without a reviewed destination state model.
5. This review is intentionally limited to a minimal affordance and should not invent a new local-state protocol.

Implication:

1. A later slice may separately review transient local-state handoff if the product wants a prefilled workbench assistant input.
2. That later review must still keep the action non-submitting and non-writing by default.

## Permission Boundary

The permission boundary for the future workbench affordance is:

1. Viewing or entering the workbench destination requires `workbench.read`.
2. Any later write inside NumericWorkbench remains controlled by `workbench.test.write`.
3. The affordance must not require `knowledge.build`.
4. The affordance must not require `knowledge.publish`.
5. The affordance must not repurpose `knowledge.read` as the workbench-entry permission.

UI implication for a later implementation:

1. If explicit capability context exists and `workbench.read` is missing, the affordance should render disabled.
2. Disabled copy should use fixed permission messaging, not build or publish or administrator-acceptance copy.

## RAG And Router Boundary Confirmation

The following remain unchanged:

1. RAG request payload remains `{ query }` only.
2. No provider, model, provider hint, or service config field is added.
3. RAG router is not modified.
4. Provider selection is not modified.
5. No real LLM integration is added.
6. No new citation artifact endpoint is added.
7. No new raw-source reading endpoint is added.
8. Ordinary RAG Q&A does not become administrator acceptance.
9. Structured query remains outside this slice and stays a separate destination-boundary problem.

## Recommendation

Recommendation: do not start a combined `P3.8b` implementation.

Instead:

1. Treat this review as a workbench-only affordance boundary definition.
2. If implementation is later approved, implement only a minimal workbench-only button.
3. Keep structured query out of that implementation until a dedicated structured-query destination boundary exists.

## Minimum Future UI Behavior If Later Approved

If a later frontend-only workbench affordance implementation is approved, the minimum UI behavior should be:

1. Show the button only after the workbench guardrail block or the explicit workbench warning.
2. Do not show the button from generic `insufficient_context` hints alone.
3. Require explicit user click.
4. Navigate only to `/numeric-workbench`.
5. Do not pass freeform query in the first version.
6. Do not auto-submit anything.
7. Do not auto-create test plans.
8. Do not auto-create candidates.
9. Do not build or publish.
10. If `workbench.read` is missing, render disabled with fixed permission copy.

## Acceptance

This boundary review is acceptable only if all of the following remain true:

1. The review defines `Go to workbench` as a workbench-only destination review rather than a combined routing implementation.
2. The review limits the first-version affordance to explicit workbench or change-intent guardrail surfaces.
3. The review rejects generic `insufficient_context` next-step hints as a first-version trigger.
4. The review keeps navigation explicit and user-triggered only.
5. The review limits the first version to plain navigation to `/numeric-workbench`.
6. The review explains why freeform-query handoff is not recommended yet.
7. The review keeps `workbench.read` as the destination-entry permission and `workbench.test.write` as the later write permission.
8. The review does not require `knowledge.build` or `knowledge.publish`.
9. The review preserves the `{ query }` RAG payload boundary and all existing provider, router, and citation boundaries.
10. The review adds no backend code, no frontend code, and no API expansion.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/`.
4. This slice does not modify `console/src`.
5. Post-edit validation for this slice is limited to documentation error checking.
