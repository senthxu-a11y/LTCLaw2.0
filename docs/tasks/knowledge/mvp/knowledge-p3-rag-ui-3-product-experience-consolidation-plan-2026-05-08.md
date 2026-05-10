# Knowledge P3.rag-ui-3 Product Experience Consolidation Plan

Date: 2026-05-08

## Goal

Decide how the current-release RAG MVP product experience should be consolidated after the minimal GameProject entry and the `P3.rag-ui-2a` or `P3.rag-ui-2b` frontend refinements.

This slice is planning only.

This plan does not modify backend code, frontend code, router behavior, request schema, provider selection, or model integration.

## Current MVP Baseline

The current RAG MVP baseline is:

1. The product entry lives inside the existing GameProject surface.
2. The current frontend entry is a narrow `Knowledge Q&A` section rather than a standalone RAG workspace.
3. The current display already surfaces `answer`, `insufficient_context`, and `no_current_release`.
4. The current UX already includes static example questions, recent local history, copy result, and local citation focus.
5. Ask-button `knowledge.read` disablement and handler-side `knowledge.read` guard are already in place.
6. The effective request payload remains `query` only.
7. Router remains thin and does not select provider.
8. `build_rag_answer_with_service_config(...)` remains the live answer handoff entry.
9. Runtime providers remain only `deterministic_mock` and `disabled`.
10. External provider adapter remains skeleton-only and does not connect a real external model.

## Planning Decision

The next product step should be `P3.rag-ui-3a` frontend-only product experience refinement.

It should not be provider credential work, transport work, real external provider work, or backend boundary expansion.

Reasoning:

1. The current user-facing bottleneck is product clarity and next-step guidance, not missing provider controls.
2. The MVP already has a coherent read-only current-release answer loop.
3. The current UX still needs clearer state hierarchy, clearer failure recovery paths, and clearer routing to structured query and numeric workbench.
4. Provider credential or transport work would widen backend and runtime scope before the MVP interaction model is settled.
5. The current adapter and provider layers are intentionally still conservative and should remain unchanged during this product-consolidation step.

## Product Experience Conclusions

### 1. Product Entry Placement

Conclusion:

1. The RAG MVP entry should remain in GameProject for now.
2. Do not split into a standalone Knowledge Q&A page or panel in this slice.
3. Re-evaluate a standalone panel only after the MVP interaction model, status hierarchy, and next-step affordances have stabilized.

Reasoning:

1. The current RAG entry is specifically about current-release game knowledge.
2. The GameProject surface already owns the nearby release and knowledge context needed to understand `no_current_release` and answer grounding status.
3. Splitting now would increase navigation and product-surface complexity before the MVP state model is fully settled.

### 2. Three-State Display Hierarchy

Conclusion:

The display hierarchy should be:

1. `answer` as the primary success state.
2. `insufficient_context` as the primary recoverable failure state.
3. `no_current_release` as the primary setup or release-state blocker.

Planned display hierarchy rules:

1. `answer` should keep answer body, release summary, warnings, and citations visible in one coherent read-only result area.
2. `insufficient_context` should visually interrupt the answer flow more strongly than ordinary warnings and should present next-step guidance before citation detail emphasis.
3. `no_current_release` should be treated as an upstream readiness state and should point users toward release setup or selection context rather than ordinary retry behavior.
4. Ordinary warnings should remain subordinate to the main state and must not visually compete with the main state banner.

### 3. Next-Step Guidance For `insufficient_context`

Conclusion:

The UI should show read-only next-step guidance when `insufficient_context` is returned.

Recommended next-step guidance content:

1. Suggest reframing the question more narrowly around the current release.
2. Suggest using structured query when the question appears to be row-level or value-level.
3. Suggest using numeric workbench when the question is actually a change or edit request.
4. Suggest checking whether the current release contains the expected evidence.

Hard constraint:

1. These next-step affordances are planning-only in this slice.
2. They must not become accept, publish, save, or write actions.

### 4. Precise Numeric Or Row-Level Guidance

Conclusion:

Precise numeric or row-level questions must continue to route toward structured query rather than be treated as authoritative semantic-answer success cases.

Planned product direction:

1. Preserve the current structured-query guardrail copy.
2. Add a future frontend-only affordance concept such as a “Go to structured query” action.
3. Keep that future action read-only and route-like only.
4. Do not implement that action in this docs-only slice.

Boundary note:

1. This plan does not authorize backend request-schema changes.
2. This plan does not authorize direct artifact or raw-source reads from the RAG UI.

### 5. Change Or Edit Intent Guidance

Conclusion:

Change or edit intent must continue to route toward numeric workbench rather than be treated as ordinary RAG Q&A.

Planned product direction:

1. Preserve the current workbench-flow guardrail copy.
2. Add a future frontend-only affordance concept such as a “Go to workbench” action.
3. Keep that future action read-only and route-like only.
4. Do not implement that action in this docs-only slice.

Boundary note:

1. This plan does not turn ordinary RAG Q&A into administrator acceptance or edit workflow.
2. This plan does not allow recent history, copy result, or citation interactions to become workbench writes.

### 6. Citation Display Enhancement

Conclusion:

The next likely citation enhancement should be display grouping only.

Recommended grouping direction for a future frontend-only slice:

1. Group by `source_type` first when useful.
2. Allow secondary display grouping or ordering by `source_path`.
3. Surface `row` more clearly for row-bearing citations.
4. Keep grouping presentation-only and derived only from returned citations.

This plan does not authorize:

1. Artifact reads.
2. Raw-source reads.
3. Synthesizing new citation data.
4. Backend citation-navigation endpoints.

### 7. Citation Reading View

Conclusion:

A citation reading view is not authorized in this plan.

If the product later wants citation-open or reading-view behavior:

1. That requires a separate boundary review.
2. That review must decide whether the view reads release artifacts, rendered snapshots, or another bounded read surface.
3. No reading-view implementation should proceed from this plan alone.

### 8. Recent Question History Scope

Conclusion:

Recent-question history should remain component-local and non-persistent for now.

Default stance:

1. Continue using local component state.
2. Do not persist to storage.
3. Do not promote to backend state.
4. Do not promote to formal knowledge, release artifacts, or admin workflows.

Future possibility:

1. Session-level frontend state may be reviewed later if the MVP proves stable and the product benefit is clear.
2. That is not the recommended next step now.

### 9. Copy Result Scope

Conclusion:

Current copy-result behavior is sufficient for the MVP baseline.

Future planning direction:

1. A later slice may review `copy citation summary` or `copy markdown` as optional frontend-only convenience actions.
2. These are planning-only possibilities and not recommended as the first next slice.
3. They must remain copy-only and must not become save, publish, accept, or formal-knowledge entry paths.

### 10. Minimal Test Strategy

Conclusion:

The next frontend-only refinement slice should adopt a minimal test-strategy plan even if it does not immediately add a full frontend test stack.

Recommended future minimum test strategy:

1. Pure helper unit tests where helper logic is sufficiently stable and isolated.
2. Small component smoke coverage for the three-state display hierarchy when a lightweight test setup exists.
3. Payload-boundary verification that the frontend still sends only `{ query }`.
4. Permission-boundary verification that Ask-button disablement and handler-side `knowledge.read` guard remain intact.
5. Citation-display grouping verification only at the presentation layer if grouping lands later.

Constraint:

1. This plan does not introduce a test framework.
2. This plan records the expected minimum testing direction for `P3.rag-ui-3a` or later slices.

## Recommended Next Slice

Recommended next slice: `P3.rag-ui-3a` frontend-only product experience refinement.

Recommended scope for `P3.rag-ui-3a`:

1. Strengthen display hierarchy across `answer`, `insufficient_context`, and `no_current_release`.
2. Add read-only next-step hints for `insufficient_context`.
3. Plan a frontend entry concept for structured query without implementing backend or route expansion in the slice.
4. Plan a frontend entry concept for numeric workbench without implementing backend or route expansion in the slice.
5. Plan citation display grouping only at the presentation layer.
6. Keep the entry inside GameProject rather than splitting into a separate Knowledge Q&A panel.

This recommendation explicitly rejects the following as the next step:

1. Provider credential work.
2. Provider transport work.
3. Real external provider integration.
4. Provider or model selection UI.
5. Request-schema expansion.

## Parallelism

The future `P3.rag-ui-3a` implementation can be split into the following workstreams.

### Tasks That Can Run In Parallel

1. Display-hierarchy copy and layout planning for the three main states.
2. `insufficient_context` next-step guidance copy refinement.
3. Structured-query entry affordance design, as planning-only frontend UX.
4. Numeric-workbench entry affordance design, as planning-only frontend UX.
5. Citation grouping presentation planning.
6. Minimal frontend test-strategy planning.

### Tasks That Should Stay Serial Within The Slice

1. Final product-line review of ordinary RAG Q&A versus admin acceptance boundaries.
2. Final payload-boundary confirmation that the effective request remains `{ query }` only.
3. Final permission-boundary confirmation for Ask-button and handler-side `knowledge.read` guard.
4. Final citation-boundary confirmation that no artifact or raw-source read has been introduced.

## Serial Review Requirements

The following reviews must remain serial and blocking before any later implementation is accepted:

1. Product-line review that ordinary RAG Q&A still does not become administrator acceptance.
2. Boundary review if any future slice wants citation-open or reading-view behavior.
3. Boundary review if any future slice wants session persistence for recent-question history.
4. Boundary review if any future slice wants request-schema expansion, provider controls, or model controls.
5. Boundary review if any future slice wants any route or deep-link behavior that could imply backend capability expansion.

## Acceptance Criteria

`P3.rag-ui-3` planning is acceptable only if all of the following are true:

1. The plan keeps the RAG MVP entry inside GameProject for now.
2. The plan clearly defines the three main display-state hierarchy.
3. The plan defines read-only next-step guidance for `insufficient_context`.
4. The plan keeps precise numeric or row-level guidance pointed at structured query.
5. The plan keeps change or edit intent pointed at numeric workbench.
6. The plan limits citation enhancement to display grouping only.
7. The plan does not authorize citation reading view implementation without a new boundary review.
8. The plan keeps recent-question history component-local and non-persistent by default.
9. The plan treats expanded copy affordances as optional future planning only.
10. The plan recommends `P3.rag-ui-3a` as the next implementation slice.
11. The plan explicitly recommends frontend-only product refinement before provider credential or transport work.
12. The plan keeps provider, model, router, request-schema, retrieval, and citation-validation boundaries unchanged.

## Rollback Conditions

A future implementation based on this plan should be rolled back or reduced if any of the following occurs:

1. The slice expands request payload beyond `{ query }`.
2. The slice adds provider or model controls.
3. The slice changes router provider-selection behavior.
4. The slice introduces direct artifact or raw-source citation reads.
5. The slice weakens Ask-button or handler-side `knowledge.read` protection.
6. The slice turns ordinary RAG Q&A into administrator acceptance, publish, save, or formal-knowledge entry.
7. The slice treats structured query or numeric workbench links as write actions rather than read-only routing affordances.
8. The slice attempts to implement citation reading view without a dedicated boundary review.

## Hard Boundary Confirmation

This plan keeps all of the following unchanged:

1. No code changes.
2. No `src/` changes.
3. No `console/src/` changes.
4. No provider or model selection.
5. No request body fields for provider, model, provider hint, or service config.
6. The effective answer payload remains `{ query }` only.
7. No RAG request-schema change.
8. No router provider selection.
9. Router must not call `get_rag_model_client(...)` directly.
10. `build_rag_answer_with_service_config(...)` remains the live answer handoff entry.
11. Runtime providers remain only `deterministic_mock` and `disabled`.
12. No external provider registration.
13. No real external model integration.
14. No `ProviderManager.active_model` integration.
15. No environment-variable RAG provider source.
16. Citation validation remains limited to `context.citations`.
17. `no_current_release` and `insufficient_context` remain pre-provider-selection states.
18. Structured-query and workbench-flow guardrail copy must remain present.
19. Ask-button and handler-side `knowledge.read` guard must remain present.
20. Ordinary RAG Q&A must not become administrator acceptance.
21. Administrator acceptance remains limited to formal knowledge admission decisions and not ordinary Q&A, recent history, copy result, citation review, structured-query routing, or workbench routing.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not run TypeScript checks.
4. Post-edit validation for this planning pass should be limited to `git diff --check`.

## Plan Result

1. `P3.rag-ui-3` is complete as a docs-only product experience consolidation plan.
2. The recommended next slice is `P3.rag-ui-3a` frontend-only product experience refinement.
3. Provider credential, transport, and real external model work remain intentionally deferred.
4. GameProject remains the current MVP entry until the product experience stabilizes further.
5. Any future citation reading view requires a separate boundary review before implementation.
