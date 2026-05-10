# Knowledge P3.8 RAG Routing Boundary Review

Date: 2026-05-09

## Goal

Define the product and router boundary between ordinary current-release RAG Q&A, precise structured query, and workbench flow after `P3.rag-ui-3a`.

This slice is boundary planning only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

Product and implementation anchors reviewed for this boundary:

1. `docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-3a-closeout-2026-05-08.md`
2. `docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-3-product-experience-consolidation-plan-2026-05-08.md`
3. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`
5. `console/src/pages/Game/GameProject.tsx`
6. `console/src/pages/Game/ragUiHelpers.ts`
7. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
8. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`

## Current Baseline

The current baseline after `P3.rag-ui-3a` is:

1. The RAG MVP entry remains inside GameProject.
2. The UI already shows read-only structured-query and workbench path labels only.
3. The current product entry still sends only `{ query }`.
4. The current frontend does not implement route navigation, deep linking, workbench opening, or structured-query opening.
5. The backend router remains thin and calls `build_current_release_context(...)` plus `build_rag_answer_with_service_config(...)` only.
6. The router does not select provider and does not call `get_rag_model_client(...)` directly.
7. The answer service still emits guardrail warnings for exact numeric or row-level fact requests and for change or edit intent.
8. Citation grouping and citation focus in the UI are still derived only from returned citations.

## Product Boundary Decision

The product boundary between the three surfaces is:

1. Ordinary RAG Q&A is a read-only explanatory surface for current-release knowledge.
2. Structured query is the precise lookup surface for exact numeric, row-level, field-level, or value-level facts.
3. Workbench flow is the explicit change or edit surface for modification intent.

This means:

1. Ordinary RAG Q&A may summarize grounded current-release evidence but must not become the authoritative path for exact row-level or value-level answers.
2. Structured query routing is appropriate only when the user is asking for exact numeric, row-level, field-level, or value-level lookup behavior.
3. Workbench routing is appropriate only when the user intent is to change, edit, modify, rewrite, patch, remove, add, or otherwise mutate project data.
4. Ordinary explanatory questions remain in the RAG Q&A surface even if warnings or next-step hints are shown.

## Ordinary RAG Q&A Boundary

Ordinary RAG Q&A remains strictly read-only.

Allowed product role:

1. Ask a question about the current release.
2. Show one of `answer`, `insufficient_context`, or `no_current_release`.
3. Show warnings, next-step hints, returned citations, copy result, recent questions, and local citation focus.

Not allowed in ordinary RAG Q&A:

1. Creating or editing test plans.
2. Creating or editing release candidates.
3. Creating or editing formal map.
4. Building or publishing a release.
5. Administrator acceptance.
6. Automatic transition into structured query or workbench flow.

Administrator acceptance remains outside ordinary RAG Q&A.

Specifically, administrator acceptance does not participate in:

1. Ordinary Q&A answers.
2. Recent-question history.
3. Copy result.
4. Citation viewing or local citation focus.
5. Structured-query routing hints.
6. Workbench routing hints.

## Structured Query Boundary

Structured query routing is limited to precise fact retrieval.

Allowed routing rationale:

1. Exact numeric facts.
2. Row-level facts.
3. Field-level facts.
4. Value-level facts.
5. Questions that are effectively lookup requests against a specific table, row, id, field, or value.

Not allowed under the structured-query routing boundary:

1. Freeform explanatory RAG Q&A.
2. Change or edit intent.
3. Automatic creation of workbench artifacts.
4. Automatic build or publish behavior.

## Workbench Boundary

Workbench routing is limited to change or edit intent.

Allowed routing rationale:

1. Change intent.
2. Edit intent.
3. Modify intent.
4. Patch, rewrite, remove, add, or set intent that implies project mutation.

Not allowed under the workbench routing boundary:

1. Ordinary explanatory RAG Q&A.
2. Exact fact lookup that should stay structured-query only.
3. Automatic write actions without explicit user choice.
4. Automatic test-plan creation.
5. Automatic release-candidate creation.

## Future `Go to structured query` / `Go to workbench` Boundary

If the product later adds an explicit `Go to structured query` or `Go to workbench` action, that future work must keep all of the following constraints:

1. The action must be an explicit frontend user action.
2. The action must not be triggered automatically from warnings, hints, answer content, recent questions, copy result, or citations.
3. The action must not auto-submit a structured query.
4. The action must not auto-submit a workbench change.
5. The action must not auto-write a test plan.
6. The action must not auto-create a release candidate.
7. The action must not auto-build or auto-publish a release.
8. The action must not bypass permission checks.
9. Structured-query permission checks and workbench permission checks must remain separate and explicit.
10. Any future deep link or route handoff still requires its own boundary review before implementation.

## Request And Router Boundary

The request and router boundary remains unchanged.

Current and required boundary:

1. The product-facing query payload remains `{ query }` only.
2. Request body must not accept provider name.
3. Request body must not accept model name.
4. Request body must not accept provider hint.
5. Request body must not accept service config.
6. No routing-planning work in this slice authorizes request-schema expansion.
7. Router remains thin and must not select provider.
8. Router must not call `get_rag_model_client(...)` directly.
9. `build_rag_answer_with_service_config(...)` remains the existing answer handoff path.
10. This slice does not add any new routing endpoint or public API.

Implementation note for current code reality:

1. The current GameProject caller still sends only `{ query }`.
2. This planning slice does not authorize any frontend use of provider or model hints.
3. This planning slice does not authorize any new product payload field even if bounded debug fields exist elsewhere.

## Citation Boundary

Citation behavior also remains unchanged.

1. Citation grouping remains presentation-only.
2. Citation grouping and citation focus remain derived only from returned citations.
3. No new citation data may be synthesized for routing.
4. No new citation artifact endpoint is authorized.
5. No new raw-source reading endpoint is authorized.
6. Routing hints must not depend on raw artifact reads.
7. Citation interactions remain read-only and do not become administrator acceptance or write actions.

## Not Authorized By P3.8

This planning slice does not authorize any of the following:

1. Route navigation implementation.
2. Deep-link implementation.
3. Structured-query auto-submit.
4. Workbench auto-submit.
5. Test-plan auto-creation.
6. Candidate auto-creation.
7. Release build or publish coupling.
8. Backend API expansion.
9. Router provider selection.
10. Real provider integration.
11. Provider or model UI controls.
12. Request-schema expansion beyond `{ query }` for the product surface.
13. Artifact-reading or raw-source-reading citation endpoints.

## Acceptance

`P3.8` boundary planning is acceptable only if all of the following remain true:

1. The document clearly separates ordinary RAG Q&A, structured query, and workbench flow by product role.
2. Structured query is limited to exact numeric, row-level, field-level, and value-level lookup intent.
3. Workbench is limited to change or edit intent.
4. Ordinary RAG Q&A remains read-only and does not create test plans, candidates, formal map, or releases.
5. Administrator acceptance remains outside ordinary RAG Q&A, recent questions, copy result, citation review, and routing hints.
6. Any future `Go to structured query` or `Go to workbench` action is explicitly defined as user-initiated only and non-writing by default.
7. The product-facing query payload remains `{ query }` only.
8. Request body does not gain provider, model, provider hint, or service-config fields.
9. Router does not select provider and does not call `get_rag_model_client(...)` directly.
10. Citation grouping or focus remains based only on returned citations.
11. No new citation artifact or raw-source reading endpoint is authorized.
12. This slice remains docs-only and adds no new API.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/` or `console/src/`.
4. Post-edit validation for this slice is limited to documentation error checking.
