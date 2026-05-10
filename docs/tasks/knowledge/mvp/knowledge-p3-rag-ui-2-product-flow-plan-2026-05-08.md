# Knowledge P3.rag-ui-2 Product Flow Plan

Date: 2026-05-08

## Goal

Plan the next small step after the minimal Block B RAG product-entry UI.

This slice is planning only.

The recommended direction is `P3.rag-ui-2`: pure frontend product-flow enhancement on top of the existing answer endpoint, without touching model or provider plumbing.

Planning authority:

1. This document is the controlling plan for the next RAG UI product-flow implementation slice.
2. Execution agents should implement the plan rather than re-decide the product direction.
3. Any scope expansion beyond this plan requires a new boundary review before code changes.

## Why This Next

`P3.rag-ui-2` should be prioritized before provider credential or transport boundary work.

Reasoning:

1. The current product already has a minimal answer loop on the existing backend endpoint.
2. The current UX still lacks basic usability features such as lightweight recall, example prompts, copy, and citation navigation.
3. These improvements can increase product value without widening provider, router, request-schema, or runtime-provider boundaries.
4. Provider credential or transport work would expand backend and governance surface area, while the current bottleneck is product usability rather than model plumbing.

## Product Decision

The next implementation slice should be `P3.rag-ui-2a`.

`P3.rag-ui-2a` should implement all four frontend-only affordances below, but with strict limits:

1. Static example questions.
2. Recent question history.
3. Copy answer.
4. Citation focus within the displayed returned citation list.

This is intentionally not provider credential work, transport work, chat expansion, or admin-governance work.

The implementation order should be:

1. Static example questions.
2. Recent question history.
3. Copy answer.
4. Citation focus.
5. Final permission and boundary regression pass.

Reasoning:

1. Static examples and recent history improve first-run usability without changing data flow.
2. Copy answer is a local convenience action and has no backend coupling.
3. Citation focus is useful, but must be implemented as local focus or scroll within already-rendered citations, not as file or artifact navigation.
4. Provider credential or transport work should stay deferred until the product surface proves useful with the existing guarded answer endpoint.

## Included Features

The next small-step scope includes only the following UI features:

1. Recent question history.
2. Static example questions.
3. Copy answer action.
4. Citation locate or jump inside the existing returned citation set.

## Allowed Scope Per Feature

### 1. Recent Question History

Allowed:

1. Keep history in local UI state or session-level frontend state only.
2. Store only user-entered question text and lightweight display metadata such as timestamp or last mode.
3. Allow quick re-run by putting the selected history item back into the existing query input.

Forbidden:

1. Do not write history into formal knowledge map.
2. Do not write history into release artifacts.
3. Do not write history into SVN, workbench files, or DLP-sensitive backend paths.
4. Do not turn history into administrator acceptance or release-candidate state.

### 2. Static Example Questions

Allowed:

1. Present a small static list of example questions in the UI.
2. Let the user click an example to populate the existing query input.
3. Keep examples as frontend-only product copy.

Forbidden:

1. Do not treat examples as provider hints.
2. Do not inject examples into prompts unless the user explicitly asks the question.
3. Do not vary examples by provider or model.

### 3. Copy Answer

Allowed:

1. Copy only the currently displayed answer, citations, and warnings.
2. Keep the copy action entirely frontend-local.
3. Optionally support copying either answer-only or answer-plus-citations as display text.

Forbidden:

1. Do not write copied output back into knowledge storage.
2. Do not write copied output into formal map, release notes, or release artifacts.
3. Do not turn copy into a publish, save, or accept action.

### 4. Citation Locate Or Jump

Allowed:

1. Jump only from the displayed citation list returned by the current answer response.
2. Use returned citation fields such as `source_path`, `artifact_path`, `title`, `row`, and `release_id` only for display or local navigation intent.
3. Keep citation navigation read-only.
4. Prefer local focus, highlight, or scroll-to-citation inside the rendered answer panel.

Forbidden:

1. Do not let the frontend read release artifacts directly.
2. Do not let the frontend read raw source files directly.
3. Do not synthesize new citations not returned by the backend.
4. Do not bypass citation grounding by constructing file lookups outside the returned citation payload.
5. Do not add a backend endpoint for citation navigation in this slice.

## Boundary Requirements

The next implementation round must keep all of the following unchanged:

1. No provider or model selection UI.
2. No request body fields for provider, model, provider hint, or service config.
3. The actual minimal request payload remains `query` only.
4. `Ask` remains disabled under explicit capability context when `knowledge.read` is missing.
5. `handleAskRagQuestion(...)` keeps a `knowledge.read` guard before calling the API.
6. No RAG request-schema change.
7. No router provider-selection change.
8. Router must not call `get_rag_model_client(...)` directly.
9. `build_rag_answer_with_service_config(...)` remains the live answer handoff entry.
10. Runtime providers remain only `deterministic_mock` and `disabled`.
11. No external provider registration.
12. No real external provider integration.
13. No `ProviderManager.active_model` integration.
14. No environment-variable provider source.
15. No frontend model or provider settings.
16. Citation validation remains grounded only in `context.citations`.
17. `no_current_release` and `insufficient_context` must still short-circuit before provider selection.
18. Structured-query and workbench-flow guardrail copy must remain visible.
19. RAG UI remains separate from administrator acceptance and release-entry workflows.

## Parallelism

The future implementation work can be split as follows:

### Sequential Foundation

1. Review current GameProject RAG section and choose the smallest UX layout extension.
2. Confirm whether local-only UI state is sufficient for recent-question history, or whether existing frontend session store patterns should be reused.

### Parallel Frontend Tasks

1. Static example questions can be implemented in parallel with copy-answer UX.
2. Recent-question history can be implemented in parallel with citation-focus UX if both remain frontend-local.
3. Copy-answer formatting and history display formatting can be implemented in parallel.

### Sequential Integration Tasks

1. Final button-state and permission review must happen after all new UI affordances are wired.
2. Final regression pass must confirm the Ask button and handler still keep `knowledge.read` guard.
3. Final UX review must confirm ordinary RAG Q&A is not presented as administrator acceptance, release publishing, or formal knowledge entry.

## Likely Files For A Future Implementation Round

If `P3.rag-ui-2` is implemented later, the expected file set should remain small:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. Optionally `console/src/api/types/game.ts` only if the display layer needs a local helper type and not a backend contract change.
4. Optionally a nearby frontend utility or small local component only if it reduces duplication without changing product semantics.

## Files That Should Not Change In The Next Small Step

Unless a later review discovers a concrete blocker, `P3.rag-ui-2` should not modify:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
4. Provider-selection modules.
5. External provider adapter modules.
6. Backend request or response schema files.
7. Formal-map, release-build, publish, candidate, or workbench backend flow files.

## Testing And Checks For A Future Implementation Round

### Frontend Checks

1. TypeScript no-emit build for `console`.
2. Editor diagnostics on touched frontend files.
3. If the repo later has targeted frontend tests for GameProject, add small UI tests around history rendering, example-question fill, copy action visibility, citation jump visibility, and permission-disabled Ask behavior.

### Backend Regression Checks

Even if the next round remains frontend-only, rerun focused backend regression to confirm boundaries were not accidentally widened:

1. `tests/unit/game/test_knowledge_rag_answer.py`
2. `tests/unit/game/test_knowledge_rag_model_client.py`
3. `tests/unit/game/test_knowledge_rag_model_registry.py`
4. `tests/unit/game/test_knowledge_rag_provider_selection.py`
5. `tests/unit/game/test_knowledge_rag_external_model_client.py`
6. `tests/unit/routers/test_game_knowledge_rag_router.py`

## Acceptance Criteria

`P3.rag-ui-2` should be accepted only if all of the following remain true:

1. The product improves usability without changing model or provider semantics.
2. The Ask button remains protected by `knowledge.read` in both button state and handler guard.
3. The request payload remains effectively `query` only.
4. No frontend provider or model control appears.
5. Citation navigation, if added, uses only returned citations and does not read artifacts or raw source.
6. History, if added, remains local or session-scoped and does not enter formal knowledge or release assets.
7. Example questions, if added, remain static UI suggestions only.
8. Copy answer, if added, remains a frontend-only convenience action.
9. Structured-query and workbench-flow guardrail text remains visible.
10. The implemented feature set matches `P3.rag-ui-2a`: static examples, recent history, copy answer, and local citation focus.
11. No new backend endpoint is added for this slice.
12. No result, history item, copied text, or citation focus action can save, accept, publish, or enter formal knowledge.

## Non-Negotiable Product Line Checks

Before accepting the future implementation, reviewers must explicitly verify:

1. Product line remains `RAG read-only Q&A over current release`, not admin acceptance.
2. Numeric precision remains routed by guardrail toward structured query, not answered as authoritative table facts from semantic chunks.
3. Change intent remains routed by guardrail toward workbench flow, not treated as a RAG answer edit.
4. Recent history remains user-interface memory only and does not become a knowledge artifact.
5. Citation focus remains a view affordance over returned citations only and does not become source-file browsing.
6. Provider/model selection remains invisible and unavailable from this UI.

## Rollback Conditions

The future implementation should be rolled back or reduced if any of the following occurs:

1. A proposed UX change requires backend schema change.
2. A proposed UX change requires provider or model controls.
3. Citation jump requires direct file or artifact reads outside returned citations.
4. History persistence starts touching backend-owned knowledge assets or admin workflows.
5. The Ask permission guard is weakened or removed.
6. The UX starts mixing ordinary RAG Q&A with administrator acceptance or release-entry decisions.

## Validation Note For This Planning Pass

1. This round is docs-only.
2. This round does not run pytest.
3. This round does not run TypeScript build.
4. Post-edit validation for this planning pass should be limited to `git diff --check`.
