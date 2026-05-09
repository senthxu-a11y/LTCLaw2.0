# Knowledge P3.8d Structured Query Destination Discovery

Date: 2026-05-09

## Goal

Determine whether the current console frontend already exposes a concrete structured-query destination that can receive a future `Go to structured query` affordance from the GameProject RAG MVP entry.

This slice is discovery plus boundary review only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

1. `docs/tasks/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md`
2. `docs/tasks/knowledge-p3-8a-routing-affordance-discovery-2026-05-09.md`
3. `docs/tasks/knowledge-p3-8b-workbench-affordance-boundary-review-2026-05-09.md`
4. `docs/tasks/knowledge-p3-8c-go-to-workbench-closeout-2026-05-09.md`
5. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
6. `console/src/pages/Game/GameProject.tsx`
7. `console/src/pages/Game/ragUiHelpers.ts`
8. `console/src/api/modules/game.ts`
9. `console/src/api/modules/gameKnowledgeRelease.ts`
10. `console/src/api/types/game.ts`
11. `console/src/pages/Game/NumericWorkbench.tsx`
12. `console/src/pages/Game/IndexMap.tsx`
13. `console/src/layouts/MainLayout/index.tsx`
14. `console/src/layouts/Sidebar.tsx`

Additional repository discovery used for this review:

1. Search for `structured query`, `precise query`, `query mode`, `gameApi.query`, `table`, `row`, and `field` surfaces across `console/src`.
2. Search for any route, page, tab, or component that currently behaves like a dedicated structured-query destination.

## Baseline Carried Forward

The following boundaries remain fixed during this discovery slice:

1. The current RAG product-facing request payload remains `{ query }` only.
2. No provider, model, provider hint, or service config field is added.
3. No RAG router change is authorized.
4. Router must not select provider and must not call `get_rag_model_client(...)` directly.
5. Structured query remains limited to exact numeric, row-level, field-level, and value-level lookup intent only.
6. Structured query must not absorb change, edit, modify, patch, add, remove, or rewrite intent.
7. Any future `Go to structured query` affordance must be explicit user click only.
8. Any future `Go to structured query` affordance must not auto-submit a query unless a separate destination contract explicitly authorizes it.
9. Any future structured-query affordance must not auto-write test plans, create candidates, build, or publish.
10. No citation artifact endpoint or raw-source reading endpoint is authorized.

## Discovery Findings

### A. No Dedicated Structured-Query Destination Exists Today

The current frontend does not expose a dedicated structured-query page, route, tab, or reusable component.

Confirmed evidence:

1. `GameProject.tsx` still renders only read-only `Structured query path` labels inside the guardrail and warning areas.
2. `ragUiHelpers.ts` contains structured-query warning copy and generic next-step hints only; it contains no navigation or destination behavior.
3. `MainLayout/index.tsx` registers no structured-query route.
4. `Sidebar.tsx` exposes no structured-query navigation item.
5. Repository search found no `StructuredQuery` page, `Query` page, or similar Game-facing destination component in `console/src/pages/Game`.

Conclusion:

1. There is no current frontend destination that can safely receive a `Go to structured query` button.

### B. The Legacy `gameApi.query(...)` Wrapper Is Not A Product Destination

The legacy `gameApi.query(agentId, q, mode = "auto")` wrapper exists in `console/src/api/modules/game.ts`, but discovery found no current frontend page or route that uses it as a user-facing structured-query surface.

Confirmed evidence:

1. Repository search found no `gameApi.query(...)` call site in `console/src`.
2. No current page exposes a query-mode selector, precise-query form, or submit path backed by `/game/index/query`.
3. The current RAG product surface uses `gameKnowledgeReleaseApi.answerRagQuestion(...)`, not `gameApi.query(...)`.

Conclusion:

1. `gameApi.query(...)` is a legacy API wrapper or lower-level capability.
2. By itself it does not define a stable frontend destination.
3. It is therefore insufficient to justify a `Go to structured query` affordance.

### C. Existing Read-Only Nearby Surfaces Do Not Yet Qualify

Two nearby Game surfaces were considered and rejected as first-version structured-query destinations.

#### `NumericWorkbench`

Why it does not qualify:

1. `NumericWorkbench.tsx` is already established as the change or edit surface.
2. Its current route contract is session or table or row or field oriented, but still belongs to workbench flow.
3. Reusing it as the structured-query destination would blur the `P3.8` product boundary between exact lookup and mutation flow.

#### `IndexMap`

Why it does not qualify:

1. `IndexMap.tsx` is an index-browsing and metadata-inspection surface.
2. It lists tables and shows field metadata, references, and dependencies, but it does not execute a user query.
3. It does not provide an explicit exact-value lookup interaction model.
4. It is therefore not a structured-query destination yet.

Conclusion:

1. The current console has related read-only browsing surfaces, but none is the dedicated structured-query destination required for a future button.

## Boundary Judgment

### 1. Does A Dedicated Structured-Query Page Or Route Or Tab Or Component Exist?

Decision: no.

Reasoning:

1. No route exists.
2. No sidebar entry exists.
3. No dedicated page exists.
4. No explicit GameProject in-page structured-query panel exists.
5. No reusable structured-query component was found.

### 2. Is Legacy `gameApi.query(agentId, q, mode)` Sufficient As A Product Entry?

Decision: no.

Reasoning:

1. It is not wired to any visible frontend destination.
2. It does not provide product-level affordance semantics by itself.
3. It does not define permission UX, disabled copy, empty state, or prefill behavior.
4. It does not define whether `mode` is user-visible or purely internal.

### 3. If The Product Later Adds `Go to structured query`, Where Should The First Version Go?

Decision: the first version should go to a newly introduced minimal structured-query panel inside the existing GameProject surface, not to NumericWorkbench and not directly to the legacy query API.

Recommended target shape:

1. A small dedicated structured-query panel or tab inside GameProject.
2. The panel may prefill the raw query text locally.
3. The panel must require explicit user submission.
4. The panel must remain read-only lookup only.

Why this is the recommended first destination:

1. It keeps the user in the same product area where the warning already appears.
2. It avoids inventing a new global route before the interaction model is stable.
3. It keeps structured query separate from workbench mutation flow.
4. It creates an explicit destination contract before any button wiring happens.

### 4. Should The Product Add A Minimal Structured-Query Panel First, Or Keep The Read-Only Label?

Decision: keep the current read-only label for now.

Recommendation for the next implementation-capable slice:

1. First define a minimal structured-query panel contract.
2. Only after that contract exists should a frontend affordance implementation be considered.

This means:

1. `P3.8d` does not recommend immediate frontend button implementation.
2. The current label remains the correct product state until a destination exists.

## Frozen First-Version Boundary For Future Structured Query

If a later slice creates the minimal structured-query panel, the first-version boundary should be:

1. The destination is exact numeric, row-level, field-level, and value-level lookup only.
2. The destination must not accept change, edit, modify, patch, add, remove, or rewrite intent.
3. Entry must be explicit user click only.
4. The entry must not auto-submit.
5. Prefill may use local frontend state only.
6. The destination must not auto-write a test plan.
7. The destination must not create a release candidate.
8. The destination must not build or publish.
9. Destination-entry permission must be evaluated separately from `knowledge.read`.
10. The first version must not require `knowledge.build` or `knowledge.publish`.
11. The RAG answer request must still send only `{ query }`.
12. No provider, model, provider hint, or service config field may be introduced.
13. No RAG router change, provider-selection change, or real LLM integration is authorized.
14. No citation artifact or raw-source reading endpoint is authorized.

Implementation note for future permission naming:

1. The product should use a dedicated structured-query read capability rather than collapsing destination-entry permission into `knowledge.read`.
2. This review does not require finalizing the exact token name yet.

## Why Combined Routing Should Still Not Start

Combined `Go to structured query` plus `Go to workbench` routing should still not start.

Reasoning:

1. Workbench already has an explicit destination.
2. Structured query still does not.
3. Shipping only one half as explicit and leaving the other half conceptual would distort the product promise.
4. Routing both through one shared surface would break the exact-lookup versus mutation boundary established in `P3.8`.

## Recommendation

Recommendation for this round:

1. Keep this slice docs-only.
2. Do not implement a `Go to structured query` button yet.
3. Keep the current read-only structured-query label in GameProject.
4. Treat the next slice as a minimal structured-query panel contract review inside GameProject.

## Acceptance

This discovery and boundary review is acceptable only if all of the following remain true:

1. The review confirms that no dedicated structured-query destination currently exists in the frontend.
2. The review confirms that legacy `gameApi.query(...)` is insufficient as a product destination by itself.
3. The review rejects NumericWorkbench as the structured-query destination.
4. The review rejects IndexMap as the current structured-query destination.
5. The review recommends a new minimal structured-query panel before any affordance implementation.
6. The review keeps structured query limited to exact lookup only and keeps mutation intent out.
7. The review keeps future entry explicit and non-submitting by default.
8. The review preserves the `{ query }` request boundary and existing provider, router, and citation boundaries.
9. The review adds no backend code, no frontend code, and no new API.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/`.
4. This slice does not modify `console/src`.
5. Post-edit validation for this slice is limited to documentation error checking.
