# Knowledge P3 Gate Status

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md
3. docs/tasks/knowledge-p2-gate-status-2026-05-07.md
4. docs/tasks/knowledge-p1-gate-status-2026-05-07.md
5. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md

## Scope Snapshot

The current P3 record is narrow and backend-only.

Completed in this gate:

1. P3.1 RAG read boundary review.
2. P3.2 read-only context assembly skeleton.
3. P3.2b read-only debug context endpoint.
4. P3.3 RAG answer-adapter boundary review.
5. P3.4 backend-only minimal answer service skeleton.
6. P3.4b backend-only debug answer endpoint.
7. P3.5 backend-only deterministic map candidate builder.
8. P3.6 read-only map candidate API skeleton.
9. P3.7a formal map read/save boundary review.

Partially landed but not gate-passed:

1. P3.7b backend-only formal map store plus GET/PUT API draft.

This gate does not introduce a real LLM, embedding, vector store, frontend RAG UI, or SVN behavior.

## Completed Scope

### P3.1 Completed Scope

1. RAG read boundary is defined as current-release, release-owned artifacts only.
2. Raw source files, pending files, SVN resources, and external paths are explicitly out of bounds.
3. `candidate_evidence.jsonl` is excluded from default RAG reads.

### P3.2 Completed Scope

1. A bounded current-release context builder now exists as a read-only backend skeleton.
2. It reads only `manifest.json`, `map.json`, `indexes/table_schema.jsonl`, `indexes/doc_knowledge.jsonl`, and `indexes/script_evidence.jsonl` from the current release.
3. It returns bounded `chunks` plus `citations`.
4. It does not generate answers.
5. It does not call an LLM.
6. It does not add embedding or vector-store work.
7. It does not mutate releases or set current release.

### P3.2b Completed Scope

1. The debug endpoint is exposed at `/api/agents/{agentId}/game/knowledge/rag/context`.
2. The endpoint is a thin router over the existing P3.2 context builder.
3. The router resolves workspace, game service, and local project directory, validates request fields, calls the builder, and returns the builder payload.
4. The router does not read artifacts directly.
5. The endpoint remains read-only and context-only.

### P3.3 Completed Scope

1. The answer-adapter boundary is now defined as `query + provided context` only.
2. Any future answer adapter must consume only the P3.2/P3.2b context payload.
3. The adapter must not directly read `manifest.json`, `map.json`, release JSONL artifacts, raw source files, pending JSONL files, or SVN resources.
4. All answer citations must come only from `context.citations`.
5. Unsupported requests must return `insufficient_context` rather than fabricated answers.
6. The next recommended code slice is a minimal backend answer-service skeleton, not frontend UI or vector-store work.

### P3.4 Completed Scope

1. A backend-only minimal answer service skeleton now exists in `knowledge_rag_answer.py`.
2. The service accepts only `query + context`, where `context` is the existing P3.2/P3.2b payload.
3. The service returns `mode`, `answer`, `release_id`, `citations`, and `warnings`.
4. The current implementation is deterministic/no-LLM and does not connect a real model.
5. The service does not directly read release artifacts, raw source files, pending files, or SVN resources.
6. Returned citations are filtered from `context.citations` only; no new citation is generated.
7. Missing or weak support returns `insufficient_context`.
8. No new answer router or endpoint was added in this slice.
9. No frontend change was added in this slice.

### P3.4b Completed Scope

1. A backend-only debug answer endpoint now exists at `/api/agents/{agentId}/game/knowledge/rag/answer`.
2. The request body is `query`, `max_chunks`, and `max_chars`.
3. The response shape is `mode`, `answer`, `release_id`, `citations`, and `warnings`.
4. Blank `query` after trim returns `insufficient_context`.
5. The router is intentionally thin and only chains `context builder -> deterministic answer service`.
6. Artifact reads still occur only inside the existing context builder; the router does not read artifacts directly.
7. The endpoint remains backend-only and debug-oriented, not a frontend or chat UI surface.
8. No real LLM, embedding, vector store, or frontend change was added in this slice.

### P3.5 Completed Scope

1. A backend-only deterministic map candidate builder now exists in `src/ltclaw_gy_x/game/knowledge_map_candidate.py`.
2. Focused coverage now exists in `tests/unit/game/test_knowledge_map_candidate.py`.
3. The builder reads only the current release or an explicit release id through the existing release-store boundary.
4. Default inputs are limited to `manifest.json`, `map.json`, `indexes/table_schema.jsonl`, `indexes/doc_knowledge.jsonl`, and `indexes/script_evidence.jsonl` from the selected release.
5. The builder does not read raw source files, `pending/test_plans.jsonl`, `pending/release_candidates.jsonl`, `indexes/candidate_evidence.jsonl`, or SVN resources.
6. The builder produces a deterministic candidate `KnowledgeMap` containing `tables`, `docs`, `scripts`, `systems`, and `relationships`.
7. Relationships are generated only when release-owned evidence supports them; unsupported links are not guessed.
8. The builder does not save the formal map, mutate release assets, or call `set_current_release`.

### P3.6 Completed Scope

1. A read-only map candidate API skeleton now exists at `/api/agents/{agentId}/game/knowledge/map/candidate`.
2. The semantic implementation files for this slice are `game_knowledge_map.py`, `agent_scoped.py`, and `test_game_knowledge_map_router.py`.
3. The only query parameter is optional `release_id`.
4. When `release_id` is omitted, the endpoint uses the current release.
5. The response shape is `mode`, `release_id`, and `map`, where `map` is the candidate `KnowledgeMap` payload.
6. When no current release exists, the fixed behavior is HTTP 404 with detail `No current knowledge release is set`.
7. The router is intentionally thin and only resolves workspace, game service, project root, and query params before calling the existing P3.5 deterministic builder.
8. The router does not read release artifacts directly and does not construct map content itself.
9. This slice does not save the formal map, does not provide `PUT map`, does not modify release assets, does not call `set_current_release`, and does not add frontend work.
10. During this round, `knowledge_map_candidate.py`, `test_knowledge_map_candidate.py`, and `test_game_knowledge_rag_router.py` required DLP/environment recovery rewrites, but no new product semantics were added in those files.

### P3.7a Completed Scope

1. A formal map read/save boundary review now exists in `docs/tasks/knowledge-p3-7a-formal-map-read-save-boundary-review-2026-05-07.md`.
2. The review defines formal map as app-owned project-level state rather than raw source, pending test-plan state, or release-candidate state.
3. The review concludes that saving formal map must not mutate historical releases, trigger build, set current release, or read/write SVN.
4. The review recommends storing formal map under app-owned `working/` state rather than `releases/<release_id>/map.json` or pending JSONL files.
5. The review recommends explicit `no_formal_map` for future `GET /game/knowledge/map` when no saved formal map exists.
6. The review defines backend validation expectations for schema, relative source paths, status, relationships, and deterministic `map_hash` generation before save.
7. The review concludes that future release build may snapshot saved formal map only during a later safe build, while candidate map remains advisory only.
8. The next recommended implementation step is backend formal map store plus GET/PUT API, not frontend UI.

### P3.7b Backend Store/API Scope

P3.7b backend validation is now complete for the store/API skeleton, but it is still not a shipped product surface.

The current code satisfies the P3.7a save-boundary validation requirement for backend persistence. Safe-build consumption and frontend map-review UX remain separate follow-up work.

Currently landed:

1. A backend-only formal map store draft exists under app-owned project state.
2. The implementation files for this slice are `src/ltclaw_gy_x/game/paths.py`, `src/ltclaw_gy_x/game/local_project_paths.py`, `src/ltclaw_gy_x/game/knowledge_formal_map_store.py`, `src/ltclaw_gy_x/game/knowledge_release_builders.py`, `src/ltclaw_gy_x/app/routers/game_knowledge_map.py`, `src/ltclaw_gy_x/app/routers/agent_scoped.py`, `tests/unit/game/test_knowledge_formal_map_store.py`, and `tests/unit/routers/test_game_knowledge_map_router.py`.
3. The saved formal map path is app-owned project storage at `working/formal_map.json`.
4. `GET /api/agents/{agentId}/game/knowledge/map` now returns `mode=formal_map` plus `map`, `map_hash`, `updated_at`, and `updated_by` when a saved formal map exists.
5. `GET /api/agents/{agentId}/game/knowledge/map` returns HTTP 200 with `mode=no_formal_map` and null `map`, `map_hash`, `updated_at`, and `updated_by` when no saved formal map exists.
6. `PUT /api/agents/{agentId}/game/knowledge/map` accepts `map` plus optional `updated_by`, then returns `mode=formal_map_saved`, `map_hash`, `updated_at`, and `updated_by`.
7. Save-time validation currently covers `KnowledgeMap` schema validation, allowed enum `status` values through model validation, tables/docs/scripts `source_path` guards, relationship endpoint reference validation, relationship `source_hash` prefix validation, deprecated-ref validation, and deterministic `map_hash` generation.
8. The save path remains app-owned only: it does not mutate historical releases, does not auto-build, does not auto-set current release, and does not read or write SVN.
9. The router remains thin and candidate-map read behavior from P3.6 is preserved.
10. This slice added no frontend UI and no new release mutation behavior.

Still missing before this becomes a product workflow:

1. formal map review UX
2. safe-build formal-map consumption rule
3. a decision on whether the formal map API must be role-gated before frontend use

## Endpoint Summary

### Request

`POST /api/agents/{agentId}/game/knowledge/rag/context`

Current request body:

1. `query`
2. `max_chunks`
3. `max_chars`

### Response

Current response payload returns:

1. `mode`
2. `query`
3. `release_id`
4. `built_at`
5. `chunks`
6. `citations`

Current semantics:

1. The endpoint returns context chunks and citations only.
2. The endpoint does not generate a final answer.
3. The endpoint is still a debug/backend surface, not a frontend RAG product UI.

## Verified Items

The current verified summary is:

1. No raw source read: passed.
2. No pending read: passed.
3. No `candidate_evidence` read by default: passed.
4. No SVN read/write: passed.
5. No release mutation: passed.
6. No auto set current: passed.
7. Citations include `release_id` plus artifact or source reference: passed.
8. Output remains context-only and does not generate answers: passed.
9. No LLM integration, embedding, vector store, or frontend change was added in this slice: passed.
10. P3.3 answer-adapter review preserves the single-boundary rule that only the context builder may assemble release-owned evidence: passed.
11. P3.4 answer-service tests: `8 passed`.
12. P3 adjacent regression across answer/context/router/release query/store/service: `46 passed`.
13. RAG router tests: `14 passed`.
14. P3/P1 adjacent regression across context/answer/router/release query/store/service: `53 passed`.
15. Python files touched in this round were rechecked as `NUL=0`.
16. P3.5 focused map-candidate tests: `7 passed`.
17. P3.5 adjacent regression across map candidate, release store/service, and RAG context/answer: `43 passed`.
18. P3.5 touched Python files were rechecked as `NUL=0`.
19. P3.6 minimal adjacent regression across map builder/router plus release store/service and RAG context/answer: `52 passed`.
20. P3.6 touched Python files were rechecked as `NUL=0`.
21. Current formal-map focused collection in this repository is 9 store tests plus 8 router tests.
22. Current targeted formal-map/router focused regression after source-path repair: `17 passed`.
23. Current knowledge-release/plan/candidate/query/RAG/map/workbench adjacent regression after source-path repair: `166 passed`.
24. P3.7b touched Python files were rechecked as `NUL=0`.
25. The partial P3.7b draft added no frontend change, no release mutation, no auto build, no auto set current, and no SVN read/write.

## Current Risks And Notes

1. The current release query path from P1 remains keyword-only and separate from the new context builder.
2. `candidate_evidence.jsonl` remains a build-time evidence artifact and is still excluded from default RAG/context usage.
3. The current endpoint is intentionally narrow and debug-oriented; it should not be treated as a finished answer product surface.
4. P3.3 explicitly forbids future answer code from rereading artifacts or project files outside provided context.
5. During this round, `game_knowledge_rag.py` and `test_game_knowledge_rag_router.py` were rewritten as clean UTF-8 to repair DLP/NUL corruption; router semantics were not changed.
6. During this round, `knowledge_rag_answer.py` and `test_knowledge_rag_answer.py` were also rewritten as clean UTF-8 to repair DLP/NUL corruption; semantics were not changed.
7. The P3.6 route is now available as a read-only backend/debug surface; it should not be treated as a full map review workflow.
8. During P3.6, `knowledge_map_candidate.py`, `test_knowledge_map_candidate.py`, and `test_game_knowledge_rag_router.py` needed environment-recovery rewrites after DLP corruption, but this did not expand product semantics.
9. P3.7a is a documentation-only boundary review; no new runtime behavior was added in this slice.
10. `game_project.py` and `game_svn.py` still have pre-existing dirty worktree changes, but they were not produced by P3.7b and were not touched in the P3.7b slice.

## Still Not Implemented

1. Formal map review UX.
2. Safe-build formal-map consumption boundary and implementation are not yet finalized.
3. Formal map review UX is not implemented.
4. Real LLM integration.
5. Embedding or vector store.
6. Frontend RAG UI.
7. Candidate-evidence RAG usage.

## Recommended Next Step

The recommended next direction after the P3.7b backend validation slice is:

1. Do not start with UI.
2. Treat P3.7b backend validation as landed.
3. Do the safe-build formal-map consumption boundary review or implementation next.
4. Do not add frontend UI until the build-consumption rule is confirmed.
5. The core open question is whether the next safe build should prefer `working/formal_map.json` and how that saved formal map should be snapshotted into `release/map.json`.
6. Keep candidate-map exposure backend-only until formal-map persistence and build consumption are both validated.
7. Keep `candidate_evidence.jsonl` excluded unless a later dedicated review explicitly widens the boundary.

## Gate Decision

The current P3 gate result is:

1. P3.1 is complete.
2. P3.2 is complete.
3. P3.2b is complete.
4. P3.3 is complete as an answer-adapter boundary review.
5. P3.4 is complete as a backend-only minimal answer service skeleton.
6. P3.4b is complete as a backend-only debug answer endpoint.
7. P3.5 is complete as a backend-only deterministic map candidate builder.
8. P3.6 is complete as a read-only map candidate API skeleton.
9. P3.7a is complete as a formal map read/save boundary review.
10. P3.7b backend store/API validation is complete, but frontend exposure remains blocked on formal-map role-gating and safe-build consumption decisions.
11. The current slice is still not a shipped RAG answer or map-review product surface because no formal map review UX, finalized safe-build formal-map consumption rule, real LLM, or frontend UI has been added.
