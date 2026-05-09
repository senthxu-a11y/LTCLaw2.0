# Knowledge P3.8e Structured Query Panel Contract

Date: 2026-05-09

## Goal

Freeze the minimal product and technical contract for a future structured-query panel so that a later frontend-only implementation has a bounded destination inside the existing GameProject surface.

This slice is contract review only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

1. `docs/tasks/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md`
2. `docs/tasks/knowledge-p3-8a-routing-affordance-discovery-2026-05-09.md`
3. `docs/tasks/knowledge-p3-8d-structured-query-destination-discovery-2026-05-09.md`
4. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
5. `console/src/pages/Game/GameProject.tsx`
6. `console/src/pages/Game/ragUiHelpers.ts`
7. `console/src/api/modules/game.ts`
8. `console/src/api/types/game.ts`
9. `src/ltclaw_gy_x/app/routers/game_index.py`
10. `src/ltclaw_gy_x/app/routers/game_knowledge_query.py`

## Baseline Carried Forward

The following boundaries remain fixed during this contract review:

1. The RAG MVP entry remains inside GameProject.
2. Ordinary RAG Q&A remains read-only and continues to send only `{ query }`.
3. Structured query remains limited to exact numeric, row-level, field-level, and value-level lookup intent only.
4. Workbench remains the change or edit destination and is unchanged by this review.
5. Any future structured-query entry must be explicit user action only.
6. Any future structured-query entry must not auto-submit.
7. No provider, model, provider hint, or service config field is added.
8. No RAG router change, provider-selection change, or real LLM integration is authorized.
9. No citation artifact endpoint or raw-source reading endpoint is authorized.
10. `P3.8c` workbench affordance remains unchanged.

## Product Decision

The first-version structured-query destination should be a minimal panel inside the existing GameProject surface.

It should not be introduced first as a new global route.

Reasoning:

1. The warning already appears inside GameProject.
2. The destination can stay adjacent to the current RAG ask surface without inventing a new navigation model.
3. This keeps exact lookup separate from NumericWorkbench mutation flow.
4. This minimizes scope for a future frontend-only implementation.

## First-Version Panel Scope

The first-version structured-query panel is a read-only lookup surface only.

Allowed first-version request intent:

1. Exact numeric lookup.
2. Row-level lookup.
3. Field-level lookup.
4. Value-level lookup.
5. Questions that are effectively asking for a specific table or row or id or field or scalar value.

Not allowed in the first-version panel:

1. Change intent.
2. Edit intent.
3. Modify intent.
4. Patch, add, remove, set, rewrite, or migration intent.
5. Test-plan creation.
6. Release-candidate creation.
7. Build or publish.

All mutation-oriented requests remain routed to workbench.

## Entry Contract

### Opening The Panel

The panel may open only from explicit frontend user action.

Allowed entry behavior:

1. A future `Open structured query` button may appear in the static structured-query guardrail area inside GameProject.
2. A future `Open structured query` button may also appear in returned warning rows when the warning is the existing structured-query warning.

Not allowed:

1. Automatic panel open on render.
2. Automatic panel open when `insufficient_context` appears.
3. Automatic panel open from generic next-step hints alone.
4. Automatic panel open from recent-question click, copy result, or citation interaction.

### Prefill Behavior

Prefill is allowed in the first version.

Allowed first-version prefill:

1. The current RAG input text may be copied into the structured-query input box when the user explicitly clicks `Open structured query`.
2. The panel may also keep its own local draft after it is opened.

Not allowed:

1. Prefill must not auto-submit.
2. Prefill must not trigger validation side effects beyond local input state.
3. Prefill must not trigger test-plan, candidate, build, publish, or any write action.

## Panel State Contract

The first-version panel should be treated as a small in-page destination with local UI state only.

Recommended minimal state shape:

1. `closed`
2. `open-idle`
3. `submitting`
4. `result`
5. `empty`
6. `error`

Recommended first-version local inputs:

1. Raw query text.
2. Submission state.
3. Last read-only result payload.
4. Last error message.

The first version should not introduce route state, deep-link state, or cross-page handoff.

## Submission Contract

### Decision

This review does not authorize the future implementation to bind panel submission directly to the existing `gameApi.query(agentId, q, mode)` wrapper without one more narrow API contract review.

### Why The Current Wrapper Is Not Yet Sufficient As A Product Contract

The current wrapper is close to a transport hook but not yet a stable product-facing contract.

Confirmed gaps:

1. `console/src/api/modules/game.ts` exposes `query(agentId, q, mode = "auto")`, but `console/src/api/types/game.ts` does not define typed request or response models for it.
2. The current frontend has no documented result shape for read-only structured-query rendering.
3. The `mode` field is an untyped string with no product-level allowed-value contract in the current frontend.
4. The wrapper is not currently used by any visible structured-query surface in `console/src`.
5. The permission behavior for this endpoint is not yet frozen at the panel product level.

### Consequence

The next implementation-capable slice should assume:

1. The future panel submit path may likely reuse `/game/index/query`.
2. But first it needs a narrow contract review or typing slice that freezes:
   1. allowed request fields,
   2. allowed `mode` value for first-version structured lookup,
   3. read-only response shape used by the panel,
   4. empty-state and error-state behavior.

This is intentionally smaller than a backend redesign.

It is a product-facing contract clarification only.

## Result Display Contract

The first-version structured-query panel should display read-only results only.

Allowed first-version output behavior:

1. Show the submitted query text.
2. Show read-only result rows or result blocks.
3. Show an empty-state message when no exact or structured result is found.
4. Show a non-writing error state when lookup fails.

Not allowed:

1. No test-plan creation.
2. No candidate creation.
3. No build.
4. No publish.
5. No write-back or patch action.
6. No mutation shortcut into NumericWorkbench.

## Permission Boundary

The first-version panel must not require `knowledge.build` or `knowledge.publish`.

Current boundary decision:

1. The panel should not be gated by build or publish permissions.
2. The panel requires a read capability.
3. Long term, that read capability should be a dedicated structured-query read capability.

Temporary product recommendation:

1. This review does not force the exact token name yet.
2. If a future implementation needs an interim fallback before a finer token exists, that fallback requires its own small permission review.
3. This review does not authorize silently collapsing the destination-entry permission into `knowledge.read` as a permanent product contract.

## RAG Boundary Confirmation

The following remain unchanged:

1. RAG answer request still sends only `{ query }`.
2. No provider, model, provider hint, or service config field is added.
3. No RAG router change is added.
4. No provider selection change is added.
5. No real LLM integration is added.
6. No citation artifact endpoint is added.
7. No raw-source reading endpoint is added.
8. `P3.8c` workbench affordance remains unchanged.

## Minimum Future UI Behavior If Later Approved

If a later frontend-only slice implements the panel, the minimum allowed behavior should be:

1. Keep the panel inside the existing GameProject page.
2. Open it only after explicit user click.
3. Optionally prefill the current RAG query into the panel input.
4. Never auto-submit on open.
5. Keep results read-only.
6. Keep all test-plan, candidate, build, publish, and mutation actions out of the first version.

## Recommendation

Recommendation for this round:

1. Keep this slice docs-only.
2. Freeze the destination as an in-page GameProject panel.
3. Allow future explicit `Open structured query` affordance only in explicit structured-query warning contexts.
4. Allow future prefill only as local input seeding with no auto-submit.
5. Do not enter frontend implementation until the narrow panel submit contract is reviewed.

## Acceptance

This contract review is acceptable only if all of the following remain true:

1. The first-version structured-query destination is defined as an in-page GameProject panel rather than a new global route.
2. The panel is limited to exact numeric, row-level, field-level, and value-level lookup only.
3. The panel explicitly rejects change or edit or modify intent and keeps those requests in workbench.
4. Entry remains explicit user click only.
5. Any future `Open structured query` button may only open the panel and must not auto-submit.
6. Prefill is allowed only as local input state and must not auto-submit.
7. The review records why the current `gameApi.query(...)` wrapper is not yet a sufficient product contract by itself.
8. The panel remains read-only and non-writing in the first version.
9. The permission boundary excludes `knowledge.build` and `knowledge.publish`.
10. The review preserves the `{ query }` RAG payload boundary and all existing provider, router, and citation boundaries.
11. The review does not change the existing `P3.8c` workbench affordance.
12. This slice adds no backend code, no frontend code, and no new API.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/`.
4. This slice does not modify `console/src`.
5. Post-edit validation for this slice is limited to documentation error checking.
