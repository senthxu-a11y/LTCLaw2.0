# Knowledge P3.8a Routing Affordance Discovery

Date: 2026-05-09

## Goal

Determine whether the current console frontend already exposes reusable entry points for future `Go to structured query` and `Go to workbench` affordances after `P3.8`.

This slice is discovery plus minimal implementation planning only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

1. `docs/tasks/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md`
2. `docs/tasks/knowledge-p3-rag-ui-3a-closeout-2026-05-08.md`
3. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
4. `console/src/pages/Game/GameProject.tsx`
5. `console/src/pages/Game/ragUiHelpers.ts`
6. `console/src/pages/Game/NumericWorkbench.tsx`
7. `console/src/pages/Game/GameProject.module.less`
8. `console/src/api/modules/gameKnowledgeRelease.ts`
9. `console/src/api/types/game.ts`

Additional discovery reads used for entry confirmation:

1. `console/src/layouts/MainLayout/index.tsx`
2. `console/src/layouts/Sidebar.tsx`
3. `console/src/api/modules/game.ts`
4. `console/src/api/modules/gameWorkbench.ts`
5. `console/src/pages/Chat/workbenchCardChannel.ts`

## Boundary Baseline

The following boundaries remain fixed during this discovery slice:

1. RAG answer request payload remains `{ query }` only.
2. No provider, model, provider hint, or service config field is added.
3. No RAG backend router change is authorized.
4. Router must not call `get_rag_model_client(...)` directly.
5. No citation artifact or raw-source endpoint is authorized.
6. No structured-query auto-submit is authorized.
7. No automatic workbench open-and-submit behavior is authorized.
8. No automatic test-plan write, candidate creation, build, or publish is authorized.
9. Ordinary RAG Q&A must not become administrator acceptance.
10. Ask-button and handler-side `knowledge.read` guard must remain intact.
11. Structured-query and workbench permissions must remain separate.

## Current Available Entry List

### A. NumericWorkbench Entry Is Explicit

The current frontend already has an explicit NumericWorkbench entry.

Confirmed evidence:

1. `console/src/layouts/MainLayout/index.tsx` registers `/numeric-workbench` as a real route.
2. `console/src/layouts/Sidebar.tsx` exposes `/numeric-workbench` as a navigation item.
3. `console/src/pages/Game/NumericWorkbench.tsx` consumes `session`, `table`, `row`, and `field` search params through `useSearchParams()`.
4. `NumericWorkbench.tsx` already treats those search params as deep-link or focus state and uses them to restore or focus workbench context.
5. `console/src/pages/Chat/workbenchCardChannel.ts` already defines a deep-link protocol with `href`, including `/numeric-workbench?table=...&row=...` examples.
6. `NumericWorkbench.tsx` already pushes workbench cards and already emits workbench-local navigation targets.
7. `NumericWorkbench.tsx` already enforces separate `workbench.read` and `workbench.test.write` frontend capability checks.
8. `console/src/api/modules/gameWorkbench.ts` already exposes workbench-specific API wrappers, but those wrappers are unrelated to a future affordance click itself and do not need to be called automatically.

Discovery conclusion for workbench:

1. A future `Go to workbench` affordance has a clear frontend landing target.
2. That affordance can remain frontend-only if it performs navigation or local state handoff only.
3. That affordance must still avoid automatic submission or automatic mutation.

### B. Structured Query Entry Is Not Explicit

The current frontend does not expose a dedicated structured-query product entry.

Confirmed evidence:

1. `console/src/pages/Game/GameProject.tsx` currently renders only read-only `Structured query path` labels in guardrail hints and warning descriptions.
2. `console/src/pages/Game/ragUiHelpers.ts` only contains warning text and next-step hints for structured query; it does not expose navigation behavior.
3. No dedicated structured-query page, route, tab, or component was found in `console/src`.
4. No dedicated structured-query API wrapper was found under the current RAG product surface modules.
5. `console/src/api/modules/game.ts` still contains a legacy `query(agentId, q, mode="auto")` wrapper for `/game/index/query`, but discovery found no explicit current frontend route or page that uses it as a structured-query destination.
6. The current `P3.8` boundary review already records that the frontend does not currently implement structured-query opening.

Discovery conclusion for structured query:

1. There is no explicit reusable structured-query destination in the current frontend.
2. The old `gameApi.query(...)` wrapper is insufficient by itself to justify a `Go to structured query` affordance.
3. A combined `Go to structured query` and `Go to workbench` implementation should not proceed until the structured-query target is defined more concretely.

## Gap List

The current frontend gaps are:

1. No dedicated structured-query page.
2. No dedicated structured-query route.
3. No dedicated structured-query tab or in-page panel.
4. No explicit structured-query API wrapper attached to the current GameProject RAG surface.
5. No explicit structured-query permission entry point or fixed disabled copy tied to a concrete destination.
6. No current RAG-side button wiring that navigates to NumericWorkbench.
7. No current RAG-side transient local-state handoff for carrying raw query text into NumericWorkbench without auto-submit.
8. NumericWorkbench deep-link support is table or row or field oriented today, not freeform-query oriented.

## Implementation Feasibility Judgment

### `Go to workbench`

Judgment: feasible as a future frontend-only slice.

Reasoning:

1. The frontend already has a real NumericWorkbench route.
2. The frontend already has separate workbench permissions.
3. The workbench already supports navigation or focus state through route params and session state.
4. A future affordance can remain non-writing if it only navigates or seeds local state.

Constraint still required:

1. The affordance must not auto-submit a workbench chat or change.
2. The affordance must not create a test plan.
3. The affordance must not create a release candidate.
4. The affordance must not build or publish.

### `Go to structured query`

Judgment: not yet ready for frontend-only implementation.

Reasoning:

1. The destination surface is not explicit.
2. The current console does not expose a clear structured-query route, tab, or page.
3. The old `gameApi.query(...)` wrapper does not by itself define a user-facing frontend target.
4. The permission model for a structured-query destination is not explicit in the currently discovered frontend surface.

## Recommendation

Recommendation: do not enter a combined `P3.8b frontend-only implementation` yet.

Reasoning:

1. NumericWorkbench entry is explicit and reusable.
2. Structured-query entry is still undefined in the current frontend.
3. Shipping only one button while the other remains conceptual would create an uneven product promise unless the next slice is explicitly narrowed.
4. The safer next step is either:
   1. a docs-only structured-query destination definition slice, or
   2. a clearly renamed workbench-only affordance implementation slice.

## Minimum Future UI Behavior If Later Approved

If a later frontend-only affordance slice is approved, the minimum behavior should be:

1. Show affordance buttons only after warnings or next-step hints, not as part of the default ask form.
2. Require explicit user click.
3. Carry only raw query text or other transient local frontend state.
4. Do not auto-submit anything.
5. When permission is missing, keep the button disabled and use fixed permission copy.

### For Future `Go to workbench`

Minimum future behavior:

1. Only show the button after the workbench warning or relevant next-step hint.
2. Clicking the button may navigate to `/numeric-workbench` only.
3. The navigation may carry raw query text as transient local state, or may prefill local frontend state only.
4. The click must not submit workbench chat.
5. The click must not create dirty cells automatically.
6. The click must not export or save any draft.
7. Missing `workbench.read` should keep the button disabled with fixed permission copy.

### For Future `Go to structured query`

Minimum future behavior, only after a destination exists:

1. Only show the button after the structured-query warning or relevant next-step hint.
2. Clicking the button may navigate only to a clearly defined structured-query destination.
3. The navigation may carry raw query text or prefill local frontend state only.
4. The click must not auto-submit a structured query.
5. Missing structured-query permission should keep the button disabled with fixed permission copy.

## Final Decision For This Round

This round should remain docs-only.

Why not implement now:

1. Workbench destination is clear, but structured-query destination is not.
2. The requested paired discovery result is asymmetric.
3. Implementing only half of the planned routing pair now would blur the `P3.8` product contract.
4. A small additional planning slice is cheaper than creating an affordance that has no stable structured-query landing surface.

## Validation Note

1. This slice is discovery/docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/`.
4. This slice does not modify `console/src`.
5. Post-edit validation for this slice is limited to documentation error checking.
