# Knowledge P3 Gate Status

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md
3. docs/tasks/knowledge-p2-gate-status-2026-05-07.md
4. docs/tasks/knowledge-p1-gate-status-2026-05-07.md
5. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
6. docs/tasks/knowledge-permission-boundary-review-2026-05-08.md

## Scope Snapshot

The current P3 record remains narrow.

It now includes backend slices plus limited frontend review and governance surfaces inside the existing GameProject UI.

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
10. P3.7b+ safe-build formal-map consumption boundary and backend implementation.
11. Knowledge capability or permission boundary review.
12. P3.permission-3 backend read capability checks plus regression repair.
13. `P3.provider-credential-boundary-review` docs-only safety boundary review.
14. `P3.external-provider-1` docs closeout for the backend external provider adapter skeleton.
15. `P3.external-provider-2` backend credential/config skeleton implementation closeout.
16. `P3.external-provider-3` backend service config wiring skeleton implementation.
17. `P3.external-provider-4` runtime allowlist boundary review.
18. `P3.external-provider-5` runtime allowlist implementation plan.
19. `P3.external-provider-6` backend-only minimal runtime allowlist implementation.
20. `P3.external-provider-7` real provider rollout boundary review.
21. `P3.external-provider-8a` mocked HTTP client skeleton implementation plan.
22. `P3.external-provider-8b` mocked HTTP client skeleton implementation.
23. `P3.external-provider-9` real transport design review.

This gate does not introduce a real LLM, embedding, vector store, frontend RAG UI, or SVN behavior.

It also still does not introduce real external provider credentials, transport, provider rollout, or frontend provider selection.

Later post-MVP target-machine execution updates now also exist for the accepted MVP state:

1. the Mac operator-side validation closeout is recorded in `docs/tasks/knowledge-post-mvp-operator-side-pilot-validation-2026-05-10.md`
2. the Windows operator-side validation closeout is recorded in `docs/tasks/knowledge-post-mvp-windows-operator-side-pilot-validation-2026-05-10.md`
3. the Windows round reused the same accepted MVP/operator path, validated a real Chinese-path local project directory and real `18`-table dataset, and preserved the same non-production and deferred-scope boundaries
4. the Windows round also records two environment-specific operational differences rather than product-scope changes: `.\.venv\Scripts\ltclaw.exe` instead of `python -m ltclaw`, and Python/urllib UTF-8 JSON instead of direct PowerShell JSON for Chinese path payloads
5. the Windows round did not reopen P0-P3, did not add code changes, and did not change the governing MVP conclusion

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
2. a decision on whether the formal map API must be role-gated before frontend use

### P3.7b+ Safe-Build Formal-Map Consumption Scope

P3.7b+ is complete as a backend-only safe-build consumption slice.

Currently landed:

1. The implementation files for this slice are `src/ltclaw_gy_x/game/knowledge_release_service.py` and `tests/unit/game/test_knowledge_release_service.py`.
2. Safe build now prefers `working/formal_map.json` when it exists and validates successfully.
3. When `working/formal_map.json` exists and is valid, safe build may proceed without depending on the current release map.
4. The saved formal map is reloaded and revalidated at build time before snapshotting into the new release.
5. The build-time in-memory copy rewrites `map.release_id` to the new `release_id` before release creation.
6. The final `release/map.json` is the build-time snapshot, and `manifest.map_hash` is required to match that final `release/map.json`.
7. When `working/formal_map.json` is absent, safe build falls back to the current release map and preserves the prior behavior.
8. When `working/formal_map.json` is absent and no current release exists, safe build fails clearly.
9. When `working/formal_map.json` is invalid, safe build fails clearly, does not create a partial release, and does not set current release.
10. Saving formal map itself still does not build, does not set current release, and does not read or write SVN.
11. Candidate inclusion remains build-time evidence output only and does not rewrite the formal map.
12. No frontend change, API expansion, router behavior change, SVN hot-path file touch, or P3.7c UI work was added in this slice.

### P3.permission-0 Capability Or Permission Boundary Review

The capability or permission boundary review is complete as a documentation-only governance slice.

Currently landed:

1. The review is recorded in `docs/tasks/knowledge-permission-boundary-review-2026-05-08.md`.
2. The review states that frontend button hiding is not a permission boundary.
3. The review keeps ordinary workbench fast-test flows separate from administrator-governed knowledge release actions.
4. The review defines the capability set `knowledge.read`, `knowledge.build`, `knowledge.publish`, `knowledge.map.read`, `knowledge.map.edit`, `knowledge.candidate.read`, `knowledge.candidate.write`, `workbench.read`, `workbench.test.write`, and `workbench.test.export`.
5. The review maps release read, build, publish, map read, map edit, candidate, and test-plan endpoints to explicit future backend capability checks.
6. The review recommends `knowledge.map.read` for candidate-map and saved-formal-map reads, rather than relying on broad `knowledge.read`.
7. The review recommends `workbench.read` for test-plan listing rather than requiring mutation permission.
8. The review recommends treating legacy full-payload build as internal or test-only, or disabling it outside dev or test.
9. The review recommends `P3.permission-1` backend capability helper plus route checks before any formal map UI work.

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
26. P3.7b+ `tests/unit/game/test_knowledge_release_service.py`: `15 passed`.
27. later post-MVP Mac operator-side target-machine validation is recorded as complete for the accepted MVP state.
28. later post-MVP Windows operator-side target-machine validation is recorded as complete for the accepted MVP state.
29. the Windows closeout records successful rebuild, formal map save, build-from-current-indexes, set current, rollback, current-release query/RAG, structured query, NumericWorkbench draft dry-run, and draft test-plan create/list on the Windows target machine.
30. the Windows closeout also records that frontend TypeScript no-emit and targeted ESLint reran on that machine, while focused backend pytest was explicitly waived there because the configured venv did not include `pytest`.
27. Post-MVP data-backed final regression receipt later reran focused backend regression at `179 passed`, reran frontend validation successfully, and reconfirmed real data-backed rebuild, release, rollback, query, RAG, structured query, and draft export on the real local project directory.
28. The resulting pilot disposition remains `Data-backed pilot readiness pass.` and not production ready.
29. Post-MVP Final Handoff / Delivery Packaging is now complete in `docs/tasks/knowledge-post-mvp-final-handoff-delivery-packaging-2026-05-10.md`.
30. That handoff keeps the official state as MVP complete, `Data-backed pilot readiness pass.`, pilot usable, and not production ready.
31. That handoff explicitly keeps SVN integration deferred, keeps SVN Phase 0/1 deferred to a separate slice, and keeps `P20` deferred.
32. Post-MVP operator-side pilot validation is now complete in `docs/tasks/knowledge-post-mvp-operator-side-pilot-validation-2026-05-10.md`.
33. That target-machine validation records `Operator-side pilot pass with known limitations.` while preserving the same accepted MVP disposition: `Data-backed pilot readiness pass.`, pilot usable, and not production ready.
34. That validation confirms live operator success for rebuild, formal map save, reversible status edit, build-from-current-indexes, set current, rollback, current-release query, current-release RAG, structured query, NumericWorkbench draft proposal dry-run, and draft test-plan create/list on the target runtime.
35. The next recommended action after operator-side validation is controlled pilot usage on the validated target machine, followed only by an optional separately scoped slice such as SVN Phase 0/1 review or another post-MVP production-hardening scope decision.
36. Post-MVP Windows operator-side pilot validation final hygiene receipt is now recorded in `docs/tasks/knowledge-post-mvp-windows-operator-side-pilot-validation-2026-05-10.md`.
37. That Windows receipt keeps the Windows-side status as `Windows operator-side pilot pass with known limitations.`, pilot usable on Windows target machine, and not production ready.
38. That Windows receipt records touched-doc NUL check `all touched docs NUL=0` and keyword boundary review `clean in meaning`.
39. That Windows receipt keeps backend pytest waived on Windows because `pytest` is missing from that venv, not because tests failed.
40. The next recommended Windows-side action remains controlled pilot usage first, with SVN Phase 0/1 or production-hardening only as a later separately scoped slice.
27. P3.7b+ focused formal-map/release/router set: `35 passed`.
28. P3.7b+ wider `tests/unit/game` + `tests/unit/routers`: `328 passed`.
29. P3.7b+ `git diff --check`: passed.
30. P3.7b+ touched Python files were rechecked as `NUL=0`.
31. P3.7b+ code review: passed.
32. A local reviewer attempted pytest, but local Windows temp permission blocked `tmp_path` setup; the agent-side `328 passed` result remains accepted.
33. P3.7b+ added no frontend change, no API expansion, no router behavior change, no SVN hot-path file touch, and no P3.7c UI work.
34. Knowledge capability or permission boundary review: recorded.
35. This review adds no frontend change, no API expansion, no router behavior change, and no SVN behavior.
36. P3.permission-1 capability helper unit tests: `10 passed`.
37. P3.permission-1 router `403` and allow-path tests: `26 passed`.
38. P3.permission-1 release/map/query/rag adjacent regression: `67 passed`.
39. P3.permission-1 `git diff --check`: passed.
40. P3.permission-1 touched Python files were rechecked as `NUL=0`.
41. P3.permission-1 added no frontend change, no UI work, no RAG expansion, no LLM integration, and no SVN hot-path file touch.
42. P3.permission-2 test-plan/candidate/router capability regression across `test_game_knowledge_test_plans_router.py`, `test_game_knowledge_release_candidates_router.py`, `test_capabilities.py`, `test_game_knowledge_release_router.py`, and `test_game_knowledge_map_router.py`: `48 passed`.
43. P3.permission-2 `git diff --check`: passed.
44. P3.permission-2 touched Python files were rechecked as `NUL=0`.
45. P3.permission-2 code review: passed.
46. P3.permission-2 added no frontend change, no UI work, no new API, no RAG expansion, no LLM integration, and no SVN hot-path file touch.
47. Frontend permission-aware UI boundary review: recorded.
48. This frontend permission review adds no frontend implementation, no API expansion, no backend behavior change, and no SVN behavior.
49. P3.permission-ui-1 frontend capability plumbing is complete in `console/src/pages/Game/GameProject.tsx`, `console/src/api/types/permissions.ts`, `console/src/utils/permissions.ts`, and `console/src/api/types/agents.ts`.
50. `AgentSummary` and `AgentProfileConfig` now include optional `capabilities` so explicit frontend capability context can be consumed without a new API.
51. The GameProject release panel now applies permission-aware disabled behavior for build and set-current, and the build modal stops requesting the candidate list when `knowledge.candidate.read` is missing.
52. Local trusted fallback remains unchanged: missing capability context still allows the control path until backend enforcement decides otherwise.
53. Frontend governance `403` handling continues to collapse to `You do not have permission to perform this action.`.
54. P3.permission-ui-1 TypeScript validation: `npm exec tsc -- -p tsconfig.app.json --noEmit --incremental false` passed.
55. P3.permission-ui-1 added no backend `src` change, no new API, no formal map review UX, no RAG UI, no real LLM integration, and no SVN behavior change.
56. Frontend permission copy review is recorded in `docs/tasks/knowledge-frontend-permission-copy-review-2026-05-08.md`.
57. The copy review fixes recommended permission strings for build, publish, candidate-read, map-edit, workbench-read, and workbench-test-write cases.
58. The copy review explicitly forbids describing permission failures as SVN problems, local-project-directory problems, feature absence, or administrator-approval requirements for ordinary fast tests.
59. The copy review is docs-only and adds no frontend implementation, no backend behavior change, no API change, and no SVN behavior.
60. P3.permission-ui-2 broader frontend permission coverage is complete as a narrow existing-entry-point slice in `console/src/pages/Game/NumericWorkbench.tsx` and `console/src/pages/Game/components/DirtyList.tsx`.
61. NumericWorkbench now reuses the shared capability helper for `workbench.read` and `workbench.test.write` using the same fixed copy rules from the permission copy review.
62. Existing workbench read paths now avoid loading table, row, and AI panel data when explicit capability context is present and `workbench.read` is missing.
63. Existing workbench chat send and draft export flows now collapse frontend permission failures to `You do not have permission to perform this action.`.
64. No separate frontend caller for `/game/knowledge/test-plans` was found, so this slice did not add a dedicated test-plan page permission layer.
65. No current frontend formal-map review or candidate-map review entry point was found, so formal-map permission UI remains unimplemented.
66. P3.permission-ui-2 TypeScript validation: `npm exec --prefix .\\console tsc -- -p .\\console\\tsconfig.app.json --noEmit --incremental false` passed.
67. P3.permission-ui-2 added no backend `src` change, no new API, no formal map review UX, no RAG UI, no real LLM integration, and no SVN behavior change.
68. Broader read capability checks boundary review is recorded in `docs/tasks/knowledge-read-permission-boundary-review-2026-05-08.md`.
69. The review recommends `knowledge.read` for general release read and query or RAG read routes, and `knowledge.map.read` for candidate-map and saved-formal-map reads.
70. The review keeps `GET /game/knowledge/release-candidates` under `knowledge.candidate.read` and `GET /game/knowledge/test-plans` under `workbench.read`.
71. The review recommends preserving local trusted fallback only when explicit capability context is absent, and otherwise enforcing read checks strictly.
72. The review recommends `P3.permission-3` backend read capability checks before broader map-review or query-read UI work.
73. This read-permission review is docs-only and adds no backend change, no frontend change, no new API, no RAG expansion, and no SVN behavior.
74. P3.permission-3 backend read capability checks are now implemented for `GET /game/knowledge/releases`, `GET /game/knowledge/releases/current`, and `GET /game/knowledge/releases/{release_id}/manifest` under `knowledge.read`.
75. P3.permission-3 backend read capability checks are now implemented for `POST /game/knowledge/query`, `POST /game/knowledge/rag/context`, and `POST /game/knowledge/rag/answer` under `knowledge.read`.
76. P3.permission-3 backend read capability checks are now implemented for `GET /game/knowledge/map/candidate` and `GET /game/knowledge/map` under `knowledge.map.read`.
77. Local trusted fallback remains unchanged: the helper still permits requests when explicit capability context is absent.
78. Query and RAG read boundaries remain unchanged and still do not widen to raw source, pending state, or `candidate_evidence.jsonl`.
79. `P3.permission-1` write gates remain in place for release build, build-from-current-indexes, set current release, and `PUT /game/knowledge/map`.
80. `P3.permission-2` candidate and test-plan route checks remain in place and unchanged.
81. The initial P3.permission-3 read-check slice briefly regressed by overwriting `P3.permission-1` write gates on release/map routes, and that regression was subsequently repaired.
82. Post-repair focused permission tests: `77 passed`.
83. Post-repair release/map router repair slice: `27 passed`.
84. Post-repair `git diff --check`: passed except for the existing `console/src/pages/Game/GameProject.tsx` CRLF/LF warning.
85. Post-repair touched Python files were rechecked as `NUL=0`.
86. Post-repair code review: passed.
87. Formal map review UX boundary review is recorded in `docs/tasks/knowledge-p3-7c-formal-map-review-ux-boundary-2026-05-08.md`.
88. The review confirms the current backend is already sufficient for a minimal frontend formal map review surface using only `GET /game/knowledge/map/candidate`, `GET /game/knowledge/map`, and `PUT /game/knowledge/map`.
89. The review recommends placing the first formal map review UX inside the existing GameProject release or knowledge surface rather than creating a new page.
90. The review selects `P3.7c-1` as the first implementation slice: read-only review plus `Save as formal map`, with no field-level edit.
91. The review explicitly defers relationship editing and graph canvas work.
92. This boundary review is docs-only and adds no frontend implementation, no backend change, no new API, no RAG expansion, and no SVN behavior.
93. P3.7c-1 minimal frontend formal map review is now implemented in `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/GameProject.module.less`, `console/src/api/modules/gameKnowledgeRelease.ts`, and `console/src/api/types/game.ts`.
94. The frontend reuses or adds only `getMapCandidate`, `getFormalMap`, and `saveFormalMap` over the existing map APIs.
95. The UI is placed inside the existing GameProject `Knowledge Release Status` or governance surface.
96. The first slice loads candidate map and saved formal map, shows `no saved formal map`, and shows `No current knowledge release is set` as a separate candidate-map state.
97. `Save as formal map` saves candidate map only and does not build or set current.
98. `knowledge.map.read` controls reads, `knowledge.map.edit` controls save, and backend `403` still uses `You do not have permission to perform this action.`.
99. TypeScript validation passed for the console slice: `npm exec --prefix console tsc -- -p tsconfig.app.json --noEmit --incremental false`.
100. There are no existing GameProject or formal-map frontend tests in this repository to run for this slice.
101. `git diff --check` reports only CRLF/LF warnings in the current worktree and no patch-format errors.
102. Formal map status edit boundary review is recorded in `docs/tasks/knowledge-p3-7c-2-formal-map-status-edit-boundary-2026-05-08.md`.
103. The review recommends `P3.7c-2` as a minimal status-only edit slice over saved formal map.
104. The review limits the editable objects to `systems`, `tables`, `docs`, and `scripts`.
105. The review limits the editable values to `active`, `deprecated`, and `ignored`.
106. The review explicitly defers relationship editing and graph canvas work.
107. The review keeps save on the existing `PUT /game/knowledge/map` boundary and does not introduce PATCH API.
108. This boundary review is docs-only and adds no frontend implementation, no backend change, no new API, and no SVN behavior.
109. P3.7c-2 minimal frontend formal map status edit is now implemented in `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/GameProject.module.less`.
110. Candidate map remains read-only in this slice.
111. Saved formal map is the only editable object in this slice.
112. The editable surface is limited to `systems`, `tables`, `docs`, and `scripts` status values.
113. The allowed status values are limited to `active`, `deprecated`, and `ignored`.
114. This slice does not expose editing for ids, titles, `source_path`, `source_hash`, `relationships`, `deprecated`, `release_id`, or `schema_version`.
115. Save continues to use the existing `saveFormalMap` wrapper over `PUT /game/knowledge/map` and no PATCH API was added.
116. Save still does not build a release, does not set current release, does not modify release history, and does not read or write SVN.
117. Relationship handling is warning-only in this slice: deprecated or ignored items may still be referenced, but the frontend does not auto-clean or auto-rewrite relationships.
118. `knowledge.map.read` remains the review permission, `knowledge.map.edit` remains the edit or save permission, and backend `403` still uses `You do not have permission to perform this action.` as the final boundary.
119. TypeScript validation passed for this slice in the console workspace: `npm exec tsc -- -p tsconfig.app.json --noEmit --incremental false`.
120. `git diff --check` reported no patch-format errors and only CRLF/LF warnings.
121. There are still no existing GameProject or formal-map frontend tests in this repository to run for this slice.
122. Code review for the slice is complete.
123. This slice adds no backend `src` changes, no new API, no graph canvas, no relationship editor, no field-level edit, no LLM, no frontend RAG UI, no build or publish auto-coupling, and no SVN behavior changes.
124. `P3.7c-3-alpha` relationship edit boundary decision is recorded in `docs/tasks/knowledge-p3-7c-3-relationship-edit-boundary-2026-05-08.md`.
125. That decision explicitly defers relationship editor from the conservative P3.7 closeout.
126. Any future relationship edit slice is limited to saved-formal-map-only, simple form-based add or remove using existing refs, and still uses complete `PUT /game/knowledge/map` save.
127. The decision explicitly rejects graph canvas, drag-and-drop relationship editor, LLM relationship generation, automatic relationship cleanup, and candidate-to-map auto merge for that first future slice.
128. Conservative P3.7 closeout is recorded in `docs/tasks/knowledge-p3-7-conservative-closeout-2026-05-08.md`.
129. P3.7 formal map MVP is now treated as a usable closed loop: candidate review -> save formal map -> status edit -> safe build snapshot.
130. Relationship editor, graph canvas, and LLM map generation are not treated as blockers for P3.7 conservative completion.
131. P3.7 is now treated as conservatively complete.
132. The recommended next direction is broader P3 gate consolidation or the P3 RAG or model-client boundary, not more P3.7 UI expansion.
133. P3.10 release rollback UX or API is complete and keeps rollback limited to current-pointer switch rather than rebuild or publish.
134. P3.11 permissions hardening is now complete for the current MVP slice.
135. The final MVP capability vocabulary is `knowledge.read`, `knowledge.build`, `knowledge.publish`, `knowledge.map.read`, `knowledge.map.edit`, `knowledge.candidate.read`, `knowledge.candidate.write`, `workbench.read`, `workbench.test.write`, and `workbench.test.export`.
136. `knowledge.map.read` is retained rather than collapsed into `knowledge.read` because map review remains a narrower governance-oriented read surface.
137. `knowledge.candidate.read` and `knowledge.candidate.write` are retained rather than replaced by `workbench.candidate.mark` because the current backend already distinguishes candidate read from candidate write and collapsing them would change semantics.
138. `workbench.candidate.mark` is therefore not adopted in the current MVP capability set.
139. Existing workbench draft export or proposal-create path is now explicitly gated by `workbench.test.export` on `POST /game/change/proposals`.
140. Existing build and publish boundaries remain unchanged: build still requires `knowledge.build`, and set-current or rollback still requires `knowledge.publish`.
141. Existing release, query, and RAG reads remain under `knowledge.read`; map review reads remain under `knowledge.map.read`; test-plan reads remain under `workbench.read`.
142. Existing release-candidate routes remain under `knowledge.candidate.read` and `knowledge.candidate.write`.
143. Existing workbench fast-test write remains separately grantable under `workbench.test.write` and still does not require `knowledge.publish`.
144. Local trusted fallback remains unchanged and still allows requests when explicit capability context is absent.
145. Focused backend validation for the new export gate passed in `7 passed in 2.05s` on `tests/unit/routers/test_game_change_router.py`.
146. The next recommended step after P3.11 is now P3.12 P3 Review Gate rather than external-provider P20.
147. P3.12 P3 Review Gate is now passed for the current P0-P3 MVP slice.
148. The gate confirms that the current conservative map UX is sufficient for MVP closeout because saved formal map can be saved and status-edited through GameProject, while candidate-map editing and relationship editor remain explicitly deferred.
149. The gate confirms that RAG and keyword query remain current-release-only and continue to follow the restored release after rollback.
150. The gate confirms that precise numeric or row-level lookup remains routed to structured query rather than to the ordinary RAG entry.
151. The gate confirms that rollback remains limited to current-pointer switch and does not rebuild, publish, or mutate formal-map or pending state.
152. The gate confirms that the final MVP permission split remains enforced across release, map, candidate, workbench read or write, and workbench export surfaces.
153. The only blocker found in the review round was stale P3.11 closeout wording, corrected as documentation drift only.
154. No new product functionality was added in the P3.12 review-gate round.
155. Post-MVP scope decision review is now complete as a docs-only slice after final handover.
156. That review confirms that external-provider remains frozen at `P3.external-provider-19` and that `P20` real HTTP transport must not continue by default.
157. The review evaluates `P20`, `P3.9 table_facts.sqlite`, relationship-editor or graph-governance UX, release packaging or final QA, provider admin/config boundary, and structured-query hardening as the main post-MVP candidates.
158. The review recommends `release packaging / final QA / handoff hardening` as the next mainline because it most directly improves delivery quality without reopening secret, credential, real-HTTP, or provider-rollout risk.
159. The review keeps `structured query hardening` as the strongest implementation-oriented alternative and keeps provider admin/config boundary plus optional `P3.9 table_facts.sqlite` planning as secondary follow-on routes.
160. The review keeps `P20` resume, relationship editor, graph canvas, and real provider rollout deferred unless a later dedicated slice explicitly reopens them.
161. Post-MVP pilot readiness checklist or final QA plan is now complete as a docs-only planning slice.
162. That checklist confirms that the current phase is pilot readiness rather than new feature development and that the current goal is to decide whether the MVP can enter real-user pilot.
163. The checklist defines pilot readiness around startup, release build, current-release query or RAG, structured query, conservative formal-map flow, NumericWorkbench fast-test flow, export draft proposal, rollback, permission clarity, and recovery clarity.
164. The checklist records that external-provider remains frozen at `P3.external-provider-19`, that `P20` real HTTP transport remains deferred, and that `P3.9 table_facts.sqlite`, relationship editor, graph canvas, and real provider rollout are not pilot blockers.
165. The checklist freezes the critical QA paths, pilot pass criteria, known limitations, and recommended validation commands for the next execution round without changing source, tests, Ask schema, or provider boundaries.
166. The checklist recommends `Post-MVP Pilot QA Execution / Handoff Hardening` as the next slice and does not recommend implicit continuation of `P20`.
167. Post-MVP pilot QA execution or handoff hardening is now complete as an execution closeout slice.
168. That round ran focused backend regression, frontend TypeScript no-emit, targeted ESLint, production bundle build, isolated `ltclaw` startup, and browser smoke for GameProject plus NumericWorkbench.
169. The execution round found no source-code pilot blocker; backend regression passed in `113 passed in 2.47s`, TypeScript passed, targeted ESLint had warnings only, and the latest `console/dist` bundle built successfully.
170. The isolated smoke confirmed that GameProject and NumericWorkbench load, that structured query remains explicit-open plus explicit-submit, that workbench export remains draft-only, and that missing `local project directory` degrades with clear recoverable errors rather than a crash.
171. The closeout therefore keeps `P20`, real provider rollout, relationship editor, graph canvas, and SVN integration deferred, and shifts the next practical step to real pilot-environment configuration rather than new implementation.
172. Post-MVP data-backed pilot validation is now complete as a real-environment execution slice.
173. The round configured `/Users/Admin/CodeBuddy/20260501110222/test-data` as a real local project directory and generated current indexes from 8 real `.xlsx` files.
174. The stricter round found one configured-runtime crash in `src/ltclaw_gy_x/game/retrieval.py`, where `GET /game/index/status` raised `NameError: svn_root`, and that blocker is now fixed.
175. The stricter round also found one current-index persistence mismatch in `src/ltclaw_gy_x/game/index_committer.py`, where rebuild artifacts were not being written to the project-level current-index path required by `build-from-current-indexes`, and that blocker is now fixed.
176. After those fixes, real formal-map save, real release build, set-current, rollback, current-release query, structured query, current-release RAG, and NumericWorkbench draft export all succeeded against the same real data path.
177. The data-backed closeout records real releases `pilot-real-data-r1-direct` and `pilot-real-data-r2-api`, with `table_schema` count `8` and `doc_knowledge` or `script_evidence` count `0` for this table-only validation environment.
178. The closeout therefore upgrades the pilot evidence from isolated degraded smoke to a real data-backed path while still keeping `P20`, real provider rollout, graph canvas, relationship editor, and SVN integration deferred.
179. Post-MVP Final Handoff / Delivery Packaging is now complete as a docs-only delivery closeout.
180. That handoff records the delivered MVP surface, pilot environment, startup/config confirmation standards, operator flow, rollback/recovery rules, permission matrix, SVN position, external-provider position, known limitations, QA receipt summary, operator checklist, and next-agent handoff guidance.
181. That handoff keeps the current status as `Data-backed pilot readiness pass.`, pilot usable, and not production ready.
182. Post-MVP operator-side pilot validation is now complete as the target-machine execution closeout.
183. That closeout records macOS target-environment facts, live startup/config state, real rebuild/query/RAG/workbench evidence, backend `179 passed`, frontend TypeScript pass, targeted ESLint `0 errors / 10 warnings`, and production build pass on the target machine.
184. That closeout explicitly records SVN CLI absence on the target machine as non-blocking because full rescan fallback still succeeded, and also records the pre-existing NumericWorkbench `Select model` control as a non-blocking boundary note rather than GameProject provider rollout.
185. The next recommended action after operator-side validation is controlled pilot usage on the validated target machine rather than implicit `P20` continuation or immediate SVN implementation.

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
11. P3.7b+ is limited to safe-build map selection and validation in the backend service layer; it does not widen the saved-formal-map API surface.
12. The current governance gap is no longer initial build/publish/map-edit/test-plan/candidate enforcement; it is now the broader read-surface hardening recommended by the new read-permission review and the later permission-aware UI decisions.
13. The broader backend read-surface hardening recommended by the read-permission review is now implemented; the remaining gap is later frontend permission-aware coverage and post-P3.7c-1 map editing UX.
14. The current worktree still contains historical temporary recovery scripts under `tmp/`, including `tmp/strip_nulls_p2_1.ps1`; these remain as existing workspace notes only and were not modified in this documentation slice.
15. Frontend permission-aware coverage is still intentionally partial: it now covers GameProject release governance plus existing NumericWorkbench read or export entry points, but not proposal/SVN actions.
16. The fixed copy baseline is now used by the implemented frontend permission slices, but any later surfaces still need to adopt it.
17. Provider credential and transport rollout remain documentation-only; no real external provider, no credential store, no request-body provider hint, and no frontend provider/model UI are implemented.

## Still Not Implemented

1. Relationship editor.
2. Graph canvas.
3. Broader frontend permission coverage beyond the current GameProject and NumericWorkbench slices if later product review still needs it.
4. Real LLM integration.
5. Embedding or vector store.
6. Frontend RAG UI.
7. Candidate-evidence RAG usage.
8. Broader map governance UX if later needed.

## Recommended Next Step

The recommended next direction after P3.read-permission-boundary-review is:

1. Do not start with UI.
2. Treat P3.7b, P3.7b+, P3.permission-0, P3.permission-1, P3.permission-2, P3.permission-ui-0, P3.permission-ui-1, P3.permission-ui-copy-review, P3.permission-ui-2, and P3.read-permission-boundary-review as landed.
3. Treat broader backend read checks as landed rather than optional for multi-user or non-trusted operation.
4. Keep legacy full-payload build under the existing `knowledge.build` route check until a later slice decides whether to narrow it further to internal or test-only handling.
5. The next recommended direction should be broader P3 gate consolidation followed by the P3 RAG or model-client boundary rather than more P3.7 UI expansion.
6. Keep candidate map read-only in the frontend review surface; editing remains limited to saved formal map.
7. Keep `candidate_evidence.jsonl` excluded unless a later dedicated review explicitly widens the boundary.
8. `P3.rag-model-1` backend model-client protocol plus deterministic or mock adapter is now complete.
9. `P3.rag-model-2` backend provider registry or provider selection boundary review is now complete as a docs-only slice.
10. `P3.rag-model-2a` backend provider registry skeleton is now complete after a DLP/NUL clean repair and revalidation pass.
11. `P3.rag-model-2b` service-layer provider selection skeleton is now complete.
12. `P3.rag-ui-3a` frontend-only product experience refinement is now complete, and provider credential, transport, or real external model integration remains deferred.
13. `P3.provider-credential-boundary-review` is now complete as a docs-only boundary freeze for backend-owned credentials, backend-only provider selection, conservative timeout/retry/cost policy, safe logging/privacy rules, and citation-grounded failure behavior before any real external provider rollout.
14. `P3.external-provider-2` is now complete as a backend-only credential/config skeleton implementation with disabled-by-default config, backend-owned provider/model selection, allowlist-before-credential/transport interception, and safe degradation for disabled, missing-credential, and allowlist-failure cases.
15. `P3.external-provider-3` is now complete as a backend service config wiring skeleton implementation that keeps backend-owned live handoff through the existing answer-service entry, keeps router thin, keeps request-like provider fields ignored, keeps `ProviderManager.active_model` out of scope, and keeps runtime rollout blocked.

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
10. P3.7b backend store/API validation is complete.
11. P3.7b+ safe-build formal-map consumption is complete.
12. Knowledge capability or permission boundary review is complete.
13. P3.permission-1 backend capability helper and initial route checks for build, publish, and formal-map edit are complete.
14. P3.permission-2 backend capability checks for test-plan and release-candidate routes are complete.
15. Frontend permission-aware UI boundary review is complete as a docs-only slice.
16. P3.permission-ui-1 frontend capability plumbing is complete as a narrow GameProject release-governance slice.
17. P3.permission-ui-copy-review is complete as a docs-only permission-copy baseline.
18. P3.permission-ui-2 broader frontend permission coverage is complete as a narrow NumericWorkbench existing-entry-point slice.
19. P3.read-permission-boundary-review is complete as a docs-only broader read-boundary decision slice.
20. P3.permission-3 backend read capability checks are complete, and the associated write-gate regression has been repaired.
21. P3.7c-alpha formal map review UX boundary review is complete as a docs-only slice.
22. P3.7c-1 minimal frontend formal map review is complete inside the existing GameProject surface.
23. P3.7c-2 status edit boundary review is complete as a docs-only slice.
24. P3.7c-2 minimal frontend formal map status edit is complete inside the existing GameProject surface.
25. P3.7c-3-alpha relationship edit boundary decision is complete as a docs-only slice and explicitly defers relationship editor.
26. P3.7 formal map MVP is conservatively complete.
27. The next recommended direction is broader P3 gate consolidation followed by the P3 RAG or model-client boundary.
28. Candidate map is now exposed as a read-only frontend review surface, while editing remains limited to saved formal map.
29. The current slice is still not a shipped RAG product or full map-governance product surface because no real LLM, live backend app/service config injection into the RAG answer path, embedding flow, frontend RAG UI, relationship editor, or graph canvas has been added.
30. `P3.rag-model-1` backend model-client protocol plus deterministic or mock adapter is complete.
31. The implementation files for `P3.rag-model-1` are `knowledge_rag_model_client.py` and `knowledge_rag_answer.py`, and the focused test files are `test_knowledge_rag_model_client.py` and `test_knowledge_rag_answer.py`.
32. `P3.rag-model-1` keeps router behavior unchanged, keeps artifact reads inside the existing context builder boundary, validates returned citation ids against `context.citations`, and degrades to `insufficient_context` when model output is not grounded.
33. `P3.rag-model-1` focused pytest: `15 passed`.
34. `P3.rag-model-1` touched Python files were rechecked as `NUL=0`.
35. `P3.rag-model-1` `git diff --check` reported no patch-format errors and only existing CRLF or LF warnings.
36. `P3.rag-model-2` backend provider registry or provider selection boundary review is complete as a docs-only slice.
37. `P3.rag-model-2` records that provider registry may select only model-client implementations and must not widen retrieval, context-builder, router, citation-validation, permission, or frontend boundaries.
38. `P3.rag-model-2` recommends provider types `deterministic_mock`, `disabled`, and documentation-only `future_external`, with backend-controlled selection order and allowlist enforcement.
39. `P3.rag-model-2` recommends `deterministic_mock` as the default provider and `disabled` as the fallback when provider initialization fails.
40. `P3.rag-model-2a` backend provider registry skeleton is now complete.
41. The implementation files for `P3.rag-model-2a` are `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` and `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`, with `src/ltclaw_gy_x/game/knowledge_rag_answer.py` compatibility-checked only.
42. The focused test files for `P3.rag-model-2a` are `tests/unit/game/test_knowledge_rag_model_client.py`, `tests/unit/game/test_knowledge_rag_model_registry.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
43. `P3.rag-model-2a` adds `get_rag_model_client(provider_name=None, *, factories=None)` and `ResolvedRagModelClient(provider_name, client, warnings)` as backend registry API shape.
44. `P3.rag-model-2a` runtime providers are limited to `deterministic_mock` and `disabled`, and `future_external` remains documentation-only rather than runtime.
45. `P3.rag-model-2a` keeps `deterministic_mock` as the default provider, fails unknown providers clearly with `ValueError`, and falls back to `disabled` only when factory initialization fails.
46. `DisabledRagModelClient` returns empty `answer`, empty `citation_ids`, and `Model provider is disabled.` warning.
47. `P3.rag-model-2a` does not read files, does not read environment variables, does not modify router behavior, does not modify frontend, and does not add public API.
48. `P3.rag-model-2a` does not widen retrieval, context assembly, or citation-validation boundaries and does not connect any real external model.
49. This slice hit DLP/NUL corruption during editing and then received a clean repair before final validation.
50. Post-repair NUL checks for `knowledge_rag_model_client.py`, `knowledge_rag_answer.py`, `knowledge_rag_model_registry.py`, `test_knowledge_rag_model_client.py`, `test_knowledge_rag_model_registry.py`, and `test_knowledge_rag_answer.py` all reported `NUL=0`.
51. `P3.rag-model-2a` focused pytest: `27 passed`.
52. Local pytest may emit `.pytest_cache` permission warnings, but they do not affect the passing result.
53. `P3.rag-model-2a` `git diff --check` reported no patch-format or whitespace errors and only existing CRLF/LF warnings.
54. `P3.rag-model-2b` service-layer provider selection skeleton is now complete.
55. The implementation files for `P3.rag-model-2b` are `src/ltclaw_gy_x/game/knowledge_rag_answer.py` and `tests/unit/game/test_knowledge_rag_answer.py`.
56. `P3.rag-model-2b` keeps provider selection limited to `get_rag_model_client(...)` and does not read provider from request body.
57. `P3.rag-model-2b` keeps router behavior thin, adds no new API, and does not let frontend choose arbitrary provider names.
58. `P3.rag-model-2b` keeps `deterministic_mock` as the effective default path and degrades conservatively to `disabled` when fallback is needed.
59. `P3.rag-model-2b` keeps citation validation in the existing answer path and still accepts citations only from `context.citations`.
60. `P3.rag-model-2b` preserves the early-return rule that `no_current_release` and `insufficient_context` must not call provider selection or model client.
61. `P3.rag-model-2b` reported Python NUL scan `ALL_PY_NUL=0`, RAG model focused tests `32 passed`, TypeScript passed, and `git diff --check` clean.
62. Local router pytest on one Windows machine hit `tmp_path` permission issues during this round; this is recorded as an environment issue rather than an assertion failure.
63. `P3.rag-model-2b` adds no real LLM, no embedding/vector store, no frontend RAG UI, and no SVN logic.
64. `P3.rag-model-2c` app/service config injection boundary review is now complete as a docs-only slice.
65. `P3.rag-model-2c` reviews `src/ltclaw_gy_x/game/config.py`, `src/ltclaw_gy_x/game/service.py`, `src/ltclaw_gy_x/providers/provider_manager.py`, `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`, `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, and `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` as the relevant current baseline.
66. `P3.rag-model-2c` records that provider configuration should enter through backend dependency injection first, then server-side app or service config, rather than request body, frontend control, or router logic.
67. `P3.rag-model-2c` records that `ProjectConfig.models`, `UserGameConfig`, and `ProviderManager.active_model` are not adopted as the source of truth in this slice.
68. `P3.rag-model-2c` keeps environment-variable-driven provider selection out of scope in this slice.
69. `P3.rag-model-2c` keeps provider selection bounded to `get_rag_model_client(...)`, preserves the current allowlist, requires unknown providers to clear-fail, and allows fallback only to `disabled` when provider initialization fails.
70. `P3.rag-model-2c` keeps warning merge, early-return, retrieval, context, and citation-validation boundaries unchanged.
71. `P3.rag-model-2c` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
72. `P3.rag-model-2d` minimal app/service config injection implementation is now complete.
73. The implementation files for `P3.rag-model-2d` are `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, `tests/unit/game/test_knowledge_rag_provider_selection.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
74. `P3.rag-model-2d` adds a narrow service-layer resolver helper that resolves provider name only from explicit backend-passed object or mapping fields.
75. The helper does not perform I/O, does not read environment variables, and does not access `ProviderManager`.
76. The helper currently supports direct or nested `config`-style resolution for `rag_model_provider` and `knowledge_rag_model_provider` only.
77. `P3.rag-model-2d` keeps `build_rag_answer_with_provider(...)` as the service-layer entry point and `get_rag_model_client(...)` as the only registry entry point.
78. `P3.rag-model-2d` keeps router behavior unchanged, request body unchanged, frontend unchanged, and runtime providers limited to `deterministic_mock` and `disabled` only.
79. `P3.rag-model-2d` keeps unknown provider as clear-fail, provider factory initialization failure as fallback-to-disabled only, and `no_current_release` or `insufficient_context` as no-resolver and no-registry early-return paths.
80. `P3.rag-model-2d` keeps citation validation restricted to `context.citations` and does not widen retrieval or context boundaries.
81. Focused pytest for the implementation round: `38 passed`.
82. `P3.rag-model-2d` `git diff --check`: clean.
83. The current closeout pass is docs-only and did not rerun pytest.
84. `P3.rag-model-2d` is not real LLM integration and does not allow request-level provider hint, frontend provider control, or `ProviderManager.active_model` integration.
85. The next recommended step is `P3.rag-model-3` external provider adapter boundary review rather than direct external model integration.
86. `P3.rag-model-2e` live backend app/service config injection boundary review is now complete as a docs-only slice.
87. `P3.rag-model-2e` records that live config injection should happen only through explicit server-side handoff of app or service config into the existing backend answer path rather than through request body, frontend control, router selection, environment variables, `ProjectConfig.models`, `UserGameConfig`, or `ProviderManager.active_model`.
88. `P3.rag-model-2e` keeps `build_rag_answer_with_provider(...)` as the service-layer entry point and `get_rag_model_client(...)` as the only registry entry point for provider resolution.
89. `P3.rag-model-2e` keeps runtime providers limited to `deterministic_mock` and `disabled`, keeps unknown provider as clear-fail, and keeps provider factory initialization failure as fallback-to-disabled only.
90. `P3.rag-model-2e` keeps `no_current_release` and `insufficient_context` ahead of provider resolution and provider lookup, and keeps retrieval, context, and citation-validation boundaries unchanged.
91. `P3.rag-model-2e` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
92. `P3.rag-model-2e` does not authorize real external provider integration, request-level provider hint, or frontend provider control.
93. `P3.rag-model-2f` minimal live config handoff implementation plan is now complete as a docs-only slice.
94. `P3.rag-model-2f` plans the next code round to hand backend-owned app or service config explicitly into the existing RAG answer path while keeping `build_rag_answer_with_provider(...)` as the service-layer entry point and `get_rag_model_client(...)` as the only registry entry point.
95. `P3.rag-model-2f` recommends a very small service-layer helper such as `build_rag_answer_with_service_config(...)` in `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, or a narrowly scoped resolver helper extension in `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, with preference for the answer-layer wrapper because it keeps router logic thinner.
96. `P3.rag-model-2f` allows a minimal `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` touch only if needed to hand off backend-owned service config and explicitly forbids router provider selection logic and direct `get_rag_model_client(...)` calls from router code.
97. `P3.rag-model-2f` keeps request-body provider hint, frontend provider control, environment variables, `ProjectConfig.models`, `UserGameConfig`, and `ProviderManager.active_model` out of scope.
98. `P3.rag-model-2f` keeps runtime providers limited to `deterministic_mock` and `disabled`, keeps unknown provider as clear-fail, and keeps provider factory initialization failure as fallback-to-disabled only.
99. `P3.rag-model-2f` keeps `no_current_release` and `insufficient_context` ahead of provider resolution and provider lookup, keeps citation validation restricted to `context.citations`, and does not widen retrieval or context boundaries.
100. `P3.rag-model-2f` defines the next allowed file touch set as `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, `tests/unit/game/test_knowledge_rag_answer.py`, `tests/unit/game/test_knowledge_rag_provider_selection.py`, and optionally `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` only for backend-owned config handoff.
101. `P3.rag-model-2f` defines focused tests for no-config default behavior, disabled provider handoff, unknown-provider clear fail, init-failure fallback warning, early-return no-call behavior, router no-provider-choice behavior, citation degradation, and unchanged runtime-provider list.
102. `P3.rag-model-2f` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
103. `P3.rag-model-2g` minimal live config handoff implementation is now complete.
104. The implementation files for `P3.rag-model-2g` are `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`, `tests/unit/game/test_knowledge_rag_answer.py`, and `tests/unit/routers/test_game_knowledge_rag_router.py`.
105. `P3.rag-model-2g` adds a very small answer-layer wrapper that hands backend-owned service config into the existing RAG answer path.
106. Router now passes `game_service` as a backend-owned object into that wrapper and remains a handoff surface only.
107. Router does not choose provider, does not read request-body provider fields, and does not call `get_rag_model_client(...)` directly.
108. Frontend and request schema remain unchanged.
109. Provider resolution still flows through the existing resolver and `get_rag_model_client(...)`.
110. Runtime providers remain limited to `deterministic_mock` and `disabled` only.
111. Unknown provider remains clear-fail.
112. Provider factory initialization failure still falls back only to `disabled` with warning.
113. `no_current_release` and `insufficient_context` still return before provider selection.
114. Citation validation still trusts only `context.citations`.
115. Retrieval and context boundaries remain unchanged and do not widen.
116. `P3.rag-model-2g` is not real LLM integration and does not authorize request-level provider hint or frontend provider control.
117. Focused pytest for the implementation round: 59 passed.
118. `P3.rag-model-2g` `git diff --check`: clean.
119. The current closeout pass is docs-only and did not rerun pytest.
120. `P3.rag-model-3` external provider adapter boundary review is now complete as a docs-only slice.
121. `P3.rag-model-3` records that any future external provider adapter must sit behind the existing registry and RagModelClient protocol boundaries.
122. `P3.rag-model-3` records that any future external provider adapter must accept only bounded prompt payload and must not read release artifacts, raw source, pending state, or SVN directly.
123. `P3.rag-model-3` does not authorize request-body provider hint, frontend provider control, environment-variable-driven live source selection, ProviderManager reuse by default, new runtime provider names, candidate_evidence RAG usage, or embedding or vector-store widening.
124. `P3.rag-model-3` keeps unknown provider clear-fail, keeps external-provider initialization failure constrained to fallback-to-disabled or explicit clear-fail, and forbids silent provider switching.
125. `P3.rag-model-3` records that model outputs must still be citation-validated against `context.citations`, and that missing citations or out-of-context citations must degrade to `insufficient_context`.
126. `P3.rag-model-3` keeps the structured-query boundary for exact numeric facts and the workbench-flow boundary for modification intent unchanged.
127. `P3.rag-model-3` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
128. `P3.rag-model-3a` external provider adapter implementation plan is now complete as a docs-only slice.
129. `P3.rag-model-3a` defines the future adapter skeleton file surface as a small new adapter module such as `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py` or a more conservative `src/ltclaw_gy_x/game/knowledge_rag_provider_adapters.py`, plus focused tests and only the minimum registry touch if a later slice explicitly chooses to wire a skeleton behind an allowlist.
130. `P3.rag-model-3a` requires any future adapter class to implement `RagModelClient`, accept only `RagAnswerPromptPayload`, and return only `RagModelClientResponse`.
131. `P3.rag-model-3a` keeps network I/O out of the future skeleton slice and limits that slice to contract shape, injected secret or config placeholders, timeout or retry or cost or token-limit config shape, and tests.
132. `P3.rag-model-3a` does not authorize environment-variable reads, request-body or frontend provider control, router changes, request-schema changes, ProviderManager integration, candidate_evidence RAG usage, embedding, or vector-store work.
133. `P3.rag-model-3a` requires future tests to mock the adapter, verify no artifact or raw-source or pending-state or SVN reads, verify citation out-of-bounds degradation, verify empty-answer or no-citation degradation, verify structured-query and workbench warnings remain, and verify router or request or frontend still do not participate in provider selection.
134. `P3.rag-model-3a` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
135. `P3.rag-model-3b`, now also recorded as `P3.external-provider-1`, backend external provider adapter skeleton implementation is complete.
136. The backend skeleton module is `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`.
137. The focused pytest coverage for this slice is `tests/unit/game/test_knowledge_rag_external_model_client.py`, `tests/unit/game/test_knowledge_rag_model_registry.py`, `tests/unit/game/test_knowledge_rag_model_client.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
138. `P3.external-provider-1` implements only a backend adapter skeleton behind the existing client and answer-service boundaries.
139. The skeleton does not connect a real LLM, does not perform real HTTP, does not read real credential material, and does not read environment variables.
140. Runtime providers remain limited to `deterministic_mock` and `disabled`, and there is still no runtime external-provider rollout.
141. Router remains unchanged as a backend-owned config handoff surface only, request schema remains unchanged, and frontend remains unchanged.
142. Provider read authority remains bounded: the client still does not read raw source, pending state, SVN, `candidate_evidence`, or release artifacts directly.
143. Citation validation remains restricted to `context.citations` in the answer service, and retrieval or context boundaries were not widened.
144. `P3.external-provider-1` is adapter skeleton only and is not real external provider integration.
145. Recorded implementation validation for this slice: focused pytest `57 passed in 0.55s`.
146. Recorded implementation validation for this slice: NUL checks are `0` for `knowledge_rag_external_model_client.py`, `test_knowledge_rag_external_model_client.py`, `test_knowledge_rag_answer.py`, and `test_knowledge_rag_model_client.py`.
147. Recorded implementation validation for this slice: `git diff --check` reported no whitespace error, with only pre-existing unrelated line-ending warnings.
148. `P3.external-provider-2` backend credential/config skeleton implementation is now complete.
149. The implementation remains skeleton only and is not real external provider integration.
150. The implementation adds backend-owned config shape only, including `enabled`, `provider_name`, optional `model_name`, `timeout_seconds`, optional `base_url`, optional `proxy`, optional `max_output_tokens`, `allowed_providers`, `allowed_models`, and optional env entry shape.
151. `enabled` defaults to false, so external behavior remains disabled-by-default.
152. Runtime providers still remain only `deterministic_mock` and `disabled`, and there is still no runtime provider rollout.
153. Allowlist validation now runs before credential resolver and transport, so allowlist failure degrades safely without entering the external call path.
154. Missing credential, disabled state, and allowlist failure all return safe non-answer behavior and do not generate a fake answer.
155. Request-like `provider_name`, `model_name`, and `api_key` fields still do not participate in provider selection.
156. `no_current_release` and `insufficient_context` still do not trigger provider/config/credential path execution.
157. The slice does not add frontend provider/model UI, does not change the RAG request schema, does not add API, and does not connect a real LLM.
158. Recorded implementation validation for this slice: focused pytest `59 passed in 1.04s`.
159. Recorded implementation validation for this slice: NUL checks are `0` for the touched Python files.
160. Recorded implementation validation for this slice: `git diff --check` reported no whitespace error for this slice, with only pre-existing unrelated CRLF/LF warnings.
161. The next recommended step is backend service config handoff or assembly-point boundary review rather than direct runtime rollout.
162. `P3.external-provider-3` backend service config wiring boundary review is now complete as a docs-only slice.
163. The approved live handoff entry remains `build_rag_answer_with_service_config(...)`.
164. The preferred live handoff anchor remains a backend-owned injected service object, currently `game_service`, or a backend-owned config object derived from it.
165. Router may obtain backend-owned service/app objects only to hand off an existing backend-owned object and remains forbidden from direct `get_rag_model_client(...)` calls, provider/model resolution, request-hint parsing, resolver creation, and transport creation.
166. The answer service remains the only approved service-config interpretation point and the only approved warning-merge point.
167. `no_current_release` and `insufficient_context` must still return before any service-config or provider resolution.
168. `ProviderManager.active_model` remains out of scope.
169. Env reads remain unimplemented and still cannot become request-time provider selection.
170. Runtime providers still remain only `deterministic_mock` and `disabled`, and external provider still cannot enter runtime allowlist without a later dedicated rollout review.
171. `P3.external-provider-3` backend service config wiring skeleton implementation is now complete.
    - `build_rag_answer_with_service_config(...)` remains the only live handoff entry.
    - Backend-owned `external_provider_config` is interpreted by the answer/provider-selection layer, not by router, request body, or UI.
    - Request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields still do not participate in provider selection.
    - Router behavior is not widened: Ask still only passes `query`, and the router still does not call the provider registry directly.
    - `future_external` still is not a runtime supported provider and cannot be directly selected at runtime.
    - Runtime providers still remain only `deterministic_mock` and `disabled`.
    - The slice adds no real LLM, no real HTTP, no real credential, no new API, no frontend change, and no Ask request schema change.
    - NUL repair for related test files was validation recovery only, not logic expansion.
    - Recorded implementation validation for this slice: focused pytest `84 passed in 11.05s`.
    - Recorded implementation validation for this slice: 9 related files checked as `NUL=0`, and slice-related `git diff --check` had empty output.
    - The next recommended step is runtime allowlist boundary review rather than direct real-provider connection.

`P3.external-provider-4` runtime allowlist boundary review is now complete as a docs-only slice.

Recorded review result:

1. This slice does not change runtime allowlist membership.
2. `future_external` still remains outside `SUPPORTED_RAG_MODEL_PROVIDERS`.
3. Runtime providers still remain only `deterministic_mock` and `disabled`.
4. The future runtime entry decision must remain backend-owned through config interpretation and registry decision, not through router, request body, frontend UI, or `ProviderManager.active_model`.
5. Future runtime entry requires disabled-by-default explicit enablement, credential presence, provider allowlist, model allowlist, and explicit timeout/cost/privacy policy together.
6. Unknown provider must clear-fail rather than silently switch.
7. Provider init failure may only clear-fail or fall back to `disabled`, never to another real provider.
8. `no_current_release` and `insufficient_context` still must bypass provider, credential, and transport work.
9. Citation grounding still remains answer-service-owned and limited to `context.citations`, and `candidate_evidence` still does not automatically enter RAG.
10. The review adds no real LLM, no real HTTP, no real credential, no new API, no frontend change, and no Ask request-schema change.
11. The next recommended step is a runtime allowlist implementation plan rather than direct real-provider connection.

`P3.external-provider-5` runtime allowlist implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. This plan defines the minimum future backend code surface as `knowledge_rag_model_registry.py`, `knowledge_rag_answer.py`, `knowledge_rag_provider_selection.py`, `knowledge_rag_external_model_client.py`, and the existing focused test files for registry, answer, provider selection, external client, and router.
2. This plan keeps current runtime allowlist membership unchanged.
3. `future_external` still remains outside `SUPPORTED_RAG_MODEL_PROVIDERS` in the current code.
4. The plan requires future tests to prove unknown-provider clear-fail, `disabled`-only fallback on init failure, request-field ignore behavior, early-return preservation, transport suppression on allowlist or credential failure, and citation-boundary preservation.
5. The plan explicitly forbids real provider connection, real LLM execution, real HTTP, real credential integration, Ask request-schema changes, frontend provider control, router-side provider selection, and any second real-provider widening.
6. The plan explicitly records rollback triggers for router drift, request-owned selection, early-return regression, fake-answer regression, citation-boundary regression, and accidental real-provider rollout.
7. The next recommended step is backend-only minimal runtime allowlist implementation rather than real-provider connection.

`P3.external-provider-6` backend-only minimal runtime allowlist implementation is now complete.

Recorded implementation result:

1. `future_external` now exists in the backend runtime provider allowlist.
2. Runtime path entry for `future_external` still requires backend-owned `external_provider_config` and still remains backend-owned.
3. Registry ownership now controls runtime support for `future_external`, and the prior answer-layer external-provider bypass no longer owns runtime allowlist behavior.
4. Router remains thin and still does not choose provider or call `get_rag_model_client(...)` directly.
5. Request-body provider/model/api_key fields still do not participate in provider selection.
6. `ProviderManager.active_model` still remains out of scope.
7. Missing or invalid external config for `future_external` now clear-fails rather than silently switching provider.
8. The implementation still adds no real LLM, no real HTTP, no real credential integration, no API, no frontend change, and no Ask request-schema change.
9. Focused validation for this slice: pytest `86 passed in 1.44s`.
10. The next recommended step is a later dedicated rollout review rather than direct real-provider connection in this slice.

`P3.external-provider-7` real provider rollout boundary review is now complete as a docs-only slice.

Recorded review result:

1. Real provider rollout remains unimplemented.
2. Current backend runtime allowlist support for `future_external` is not sufficient by itself to authorize real rollout.
3. Any future rollout must remain backend-owned across provider selection, credential resolution, transport creation, and disable-switch control.
4. Router, request body, frontend UI, and `ProviderManager.active_model` still do not own provider selection for this path.
5. Ask request schema still remains unchanged.
6. The review keeps real HTTP, real credential integration, API expansion, frontend changes, and request-schema changes out of scope.
7. The review freezes credential, allowlist, runtime, HTTP-client, logging, DLP, API, router, frontend, testing, and rollback gates before any later rollout slice.
8. The next recommended step is a real provider rollout implementation plan or a mocked HTTP client skeleton plan rather than direct rollout.

`P3.external-provider-8a` mocked HTTP client skeleton implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. This plan is based on source code review rather than documentation assumptions alone.
2. The plan confirms that current RAG path still has no real HTTP client and no real credential resolver.
3. The plan explicitly records that `game/service.py` contains `SimpleModelRouter` real-provider bridge logic outside the current RAG path and treats that as a source-based risk rather than as a completed RAG capability.
4. The plan defines the minimum next-round code surface as external client, narrow provider-selection or registry guards if needed, and the existing focused backend test files.
5. The plan freezes mocked transport seam rules, credential-source rules, allowlist constraints, feature-flag and rollback-switch rules, logging and DLP rules, and router or frontend boundaries before implementation.
6. This round remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.
7. The next recommended step is mocked HTTP client skeleton implementation rather than production rollout.

`P3.external-provider-8b` mocked HTTP client skeleton implementation is now complete.

Recorded implementation result:

1. `ExternalRagModelClientConfig` now has an explicit backend-owned `transport_enabled` gate in addition to adapter `enabled`.
2. `enabled=True` alone no longer authorizes credential resolution or transport invocation.
3. when `transport_enabled=False`, the external client now returns `transport is not connected` before credential resolution.
4. when `transport_enabled=False`, neither credential resolver nor injected transport is called.
5. backend-owned `external_provider_config` coercion preserves `transport_enabled` when explicitly configured.
6. focused validation for this slice passed in `60 passed in 0.05s` across external client, answer, and provider-selection tests.
7. This slice remains mocked transport only and still does not authorize real provider rollout.

`P3.external-provider-9` real transport design review is now complete as a docs-only slice.

Recorded review result:

1. This review is based on current source code and current focused tests rather than on prior documentation assumptions alone.
2. The review confirms that the current 8b gate remains valid: `enabled=False` blocks resolver and transport, and `transport_enabled=False` returns not connected before resolver or transport runs.
3. The review confirms that current RAG path still has no real HTTP client and no real credential resolver, and that mocked transport still enters only through injected transport or responder seams.
4. The review records that backend-owned `external_provider_config` coercion already preserves `transport_enabled`, and that router still has no provider/model/api_key fields and still does not call `get_rag_model_client(...)` directly.
5. The review records that `SimpleModelRouter` still contains a real-provider bridge outside the current RAG path and freezes that as a source-level risk rather than as an approved integration path.
6. The review records that current allowlist logic still permits mocked transport when `allowed_providers` or `allowed_models` is absent, and freezes allowlist hardening as a required future step before any real transport slice.
7. This round remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.

`P3.external-provider-10` allowlist hardening implementation is now complete.

Recorded implementation result:

1. `transport_enabled=True` now requires non-empty backend-owned `allowed_providers` and non-empty backend-owned `allowed_models` before credential resolution or injected transport can run.
2. blank or missing `provider_name` now returns `External provider adapter skeleton provider is not allowed.` before credential resolution and transport.
3. blank or missing `model_name` now returns `External provider adapter skeleton model is not allowed.` before credential resolution and transport.
4. `enabled=False` and `transport_enabled=False` still short-circuit exactly as before and do not require allowlists.
5. request-like provider, model, api_key, and service_config fields remain ignored by the current router and prompt-normalization path.
6. focused validation for this slice passed in `95 passed in 2.02s` across external client, answer, provider-selection, model-registry, and router tests.
7. this slice remains mocked transport only and still does not authorize real provider rollout.

`P3.external-provider-11` gate-order hardening implementation is now complete.

Recorded implementation result:

1. `enabled=False` now returns the disabled warning before `_normalize_prompt_payload(...)` runs.
2. `transport_enabled=False` now returns the not-connected warning before `_normalize_prompt_payload(...)` runs.
3. malformed direct payload input in disabled and not-connected branches no longer raises payload shape errors.
4. disabled and not-connected branches still do not call credential resolver or injected transport.
5. only `enabled=True` plus `transport_enabled=True` still performs payload normalization and still raises the existing payload validation errors for malformed input.
6. P10 allowlist hardening remains unchanged and still blocks resolver and transport before either can run.
7. this slice remains mocked transport only and still does not authorize real provider rollout.

`P3.external-provider-12` real transport skeleton implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. This plan is based on current source code and current focused tests rather than on prior documentation assumptions alone.
2. The plan confirms that P10 allowlist hardening and P11 gate-order hardening are already completed preconditions for any next-round transport skeleton work.
3. The plan keeps the next-round implementation surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, model-registry, or answer-layer follow-ups if strictly necessary.
4. The plan keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
5. The plan keeps credential resolution unimplemented beyond the current injected seam and still forbids env-value reads, secret-store reads, and production transport.
6. The plan defines transport contract, error mapping, redaction, DLP, and focused test-matrix requirements for the next round.
7. This round remains docs-only, does not change runtime behavior, and does not authorize real provider rollout.

`P3.external-provider-13` real transport skeleton implementation is now complete as a backend-only slice.

Recorded implementation result:

1. A named backend-only non-network transport skeleton now exists as `ExternalRagModelHttpTransportSkeleton`.
2. The skeleton builds only a redacted request preview and removes query strings from previewed URL-like values.
3. The skeleton does not perform real HTTP, does not open sockets, does not read files, does not read `os.environ`, and does not read a secret store.
4. Default skeleton invocation now fails safely and is mapped to `External provider adapter skeleton request failed.` without leaking secret-like text.
5. P10 allowlist hardening remains preserved and still blocks resolver and transport when provider or model allowlists are missing, empty, blank, or disallowed.
6. P11 gate-order hardening remains preserved and still keeps disabled and not-connected gates ahead of payload normalization.
7. Credential resolver behavior remains injected-only and still is not implemented as a real resolver.
8. Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` remain unchanged.
9. Focused validation for this slice passed in `104 passed in 1.91s` across external client, answer, provider-selection, model-registry, and router tests.
10. This slice remains non-production and does not authorize real provider rollout.

`P3.external-provider-14` credential resolver boundary and implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. This plan is based on current source code and current focused tests rather than on prior documentation assumptions alone.
2. The plan confirms that P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton are already completed preconditions for any next-round credential resolver skeleton work.
3. The plan confirms that current RAG external-provider path still uses injected credential resolver only and still has no secret-store integration, no env value reads, and no provider-manager credential loading.
4. The plan keeps the next-round implementation surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, model-registry, or answer-layer follow-ups if strictly necessary.
5. The plan freezes credential resolver contract, secret-source policy, redaction, DLP, and logging rules without authorizing any real secret source integration.
6. The plan keeps Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
7. This round remains docs-only, does not change runtime behavior, and does not authorize credential rollout or real provider rollout.

`P3.external-provider-15` credential resolver skeleton implementation is now complete as a backend-only slice.

Recorded implementation result:

1. A named default resolver skeleton now exists as `ExternalRagModelCredentialResolverSkeleton`.
2. Default client construction now uses that resolver skeleton when no injected resolver seam is supplied.
3. The resolver skeleton validates only backend-owned metadata shape and returns `None` by default.
4. The resolver skeleton does not read env values, does not access secret store, does not read config-file secret values, does not access `ProviderManager`, and does not access `SimpleModelRouter`.
5. Resolver exceptions now map to the existing safe not-configured warning rather than surfacing raw exception text.
6. P10 allowlist hardening remains preserved and still blocks resolver and transport on disallowed provider or model selection.
7. P11 gate-order hardening remains preserved and still keeps disabled and not-connected gates ahead of payload normalization.
8. P13 transport skeleton remains non-network and still safe-fails without real HTTP.
9. Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` remain unchanged.
10. Focused validation for this slice passed in `106 passed in 1.93s` across external client, answer, provider-selection, model-registry, and router tests.
11. This slice remains backend-only and does not authorize production credential rollout or real provider rollout.

`P3.external-provider-16` credential source governance boundary review is now complete as a docs-only slice.

Recorded review result:

1. The review confirms that after P15 the runtime still has only a resolver skeleton and still has zero real credential sources.
2. The review confirms that `transport_enabled=True` still does not authorize any real secret source.
3. The review confirms that current RAG path still has no env value reads, no secret-store integration, no config-file secret-value reads, no provider-manager credential loading, and no `SimpleModelRouter` integration.
4. The review freezes credential-source ownership as backend-only and explicitly forbids request body, frontend, router, map, formal map, snapshot, export, docs, tasks, and ordinary fast-test input as credential sources.
5. The review separates runtime credential governance from formal-knowledge acceptance and states that administrator acceptance must not be reused as credential approval or runtime provider approval.
6. The review records future candidate source categories, source-precedence draft, DLP and redaction rules, rollback and kill-switch requirements, and a future implementation test matrix without authorizing any real source integration.
7. Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` remain unchanged.
8. This round remains docs-only, does not change runtime behavior, and does not authorize production credential rollout or real provider rollout.

`P3.external-provider-17` backend env-var credential source implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. The plan confirms that after P16 the runtime still has zero real credential sources and that P17 itself does not implement env value reads.
2. The plan selects backend env-var credential source as the minimal P18 candidate because `ExternalRagModelEnvConfig.api_key_env_var` already exists as backend-owned metadata and this path does not require router, frontend, admin UI, secret store, `ProviderManager`, or `SimpleModelRouter` integration.
3. The plan keeps P18 implementation local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
4. The plan freezes env-read ordering so that any future env value read can occur only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
5. The plan keeps request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of credential ownership for the next round.
6. The plan keeps formal-knowledge acceptance separate from runtime credential governance and states that administrator acceptance must not be reused as credential approval or provider rollout approval.
7. Ask request schema, router authority, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` remain unchanged.
8. This round remains docs-only, does not change runtime behavior, and does not authorize production credential rollout or real provider rollout.

`P3.external-provider-18` backend env-var credential source implementation is now complete as a backend-only slice.

Recorded implementation result:

1. The runtime now has a named backend-only default env-aware resolver, `ExternalRagModelEnvCredentialResolver`, in `knowledge_rag_external_model_client.py`.
2. The default resolver reads only `env.api_key_env_var` from backend-owned config and only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
3. Missing env config, blank env-var name, missing env value, blank env value, and env read exceptions all safely degrade to `External provider adapter skeleton is not configured.`
4. Injected resolver seams and responder seams still override the default env source unchanged.
5. P10 allowlist hardening, P11 gate-order hardening, and the P13 non-network transport skeleton remain preserved.
6. Ask request schema, router authority, frontend, `ProviderManager.active_model`, `SimpleModelRouter`, and `secret_store` remain unchanged.
7. Focused validation for this slice passed in `119 passed in 2.03s` across external client, answer, provider-selection, model-registry, and router tests.
8. This slice remains backend-only, does not add real HTTP, and does not authorize production credential rollout or real provider rollout.

`P3.external-provider-19` backend-only real HTTP transport governance and implementation plan is now complete as a docs-only slice.

Recorded plan result:

1. The plan confirms that after P18 the current Ask RAG runtime has a backend-owned env-var credential source but still has zero real HTTP transports and zero real provider rollouts.
2. The plan confirms that current env reads still occur only through `ExternalRagModelEnvConfig.api_key_env_var` and only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
3. The plan keeps P20 local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
4. The plan defines the future P20 transport contract, warning mapping, DLP or redaction, rollback or kill-switch requirements, and focused five-file test matrix without authorizing implementation in P19.
5. The plan keeps Ask request schema, router authority, frontend, `ProviderManager`, `SimpleModelRouter`, and `secret_store` unchanged and out of scope for P20.
6. The plan records the unreachable trailing `return None` in `ExternalRagModelEnvCredentialResolver` as future code cleanup only and does not authorize source change in this slice.
7. The plan keeps formal-knowledge acceptance separate from runtime credential approval and provider rollout approval.
8. This round remains docs-only, does not change runtime behavior, and does not authorize production HTTP transport or real provider rollout.

`P3.10` release rollback UX/API is now complete for the MVP slice.

Recorded implementation result:

1. Backend now exposes `GET /game/knowledge/releases/status` on the existing release router and returns structured `current`, `previous`, and `history` state.
2. Release history is derived from the existing release store and is sorted by `(created_at, release_id)` descending.
3. History items now carry backend current marker state through `is_current`, and `previous` is derived as the first older available release after current in that history order.
4. Rollback still reuses the existing `POST /game/knowledge/releases/{release_id}/current` endpoint and the existing `set_current_release(...)` store path.
5. Rollback still only changes the current pointer and does not rebuild, publish, mutate release artifacts, mutate pending test plans, or mutate working formal map.
6. GameProject now reads structured release status, displays current plus previous release explicitly, and adds an explicit `Rollback to previous` action with confirmation.
7. Rollback remains gated by `knowledge.publish`, while read status remains gated by `knowledge.read` under explicit capability context.
8. Focused backend validation for this slice passed in `50 passed in 1.90s` across release store, release router, current-release query router, and RAG context tests.
9. Frontend TypeScript no-emit and targeted ESLint both passed through local `node_modules/.bin` binaries after the workspace `pnpm` wrapper path was blocked by `approve-builds` enforcement.
10. External-provider remains frozen at `P3.external-provider-19` docs-only, and this slice does not continue P20.

`P3.12` P3 Review Gate is now complete and passed for the current P0-P3 MVP mainline.

Recorded closeout result:

1. The closeout is recorded in `docs/tasks/knowledge-p3-12-review-gate-closeout-2026-05-10.md`.
2. All five gate items passed: map editable through conservative saved-formal-map UX, RAG reads current release only, precise values go through structured query, release rollback works, and permission split is enforced.
3. Focused review-gate regression passed in `68 passed in 1.98s` across release, map, current-release RAG, test plan, release candidate, and workbench export gate tests.
4. The final MVP capability matrix remains `knowledge.read`, `knowledge.build`, `knowledge.publish`, `knowledge.map.read`, `knowledge.map.edit`, `knowledge.candidate.read`, `knowledge.candidate.write`, `workbench.read`, `workbench.test.write`, and `workbench.test.export`.
5. Candidate-map editing, relationship editor, graph canvas, `P3.9 table_facts.sqlite`, real HTTP transport, and production provider rollout remain optional or deferred and are not blockers for P0-P3 MVP acceptance.
6. P0-P3 final handover is recorded in `docs/tasks/knowledge-p0-p3-mvp-final-handover-2026-05-10.md`.
7. External-provider remains frozen at `P3.external-provider-19`; `P20` is deferred until a new explicit scoped slice is opened.

172. `P3.rag-ui-1` minimal product-entry UI on the existing answer endpoint is now complete.
173. The implementation files for `P3.rag-ui-1` are `console/src/api/types/game.ts`, `console/src/api/modules/gameKnowledgeRelease.ts`, `console/src/pages/Game/GameProject.tsx`, and `console/src/pages/Game/GameProject.module.less`.
174. `P3.rag-ui-1` adds the smallest GameProject knowledge Q&A surface that calls the existing `POST /api/agents/{agentId}/game/knowledge/rag/answer` endpoint.
175. The frontend request remains limited to `query` and does not expose provider or model control.
176. `P3.rag-ui-1` renders backend-returned `mode`, `answer`, `release_id`, `citations`, and `warnings`, and explicitly surfaces `no_current_release` and `insufficient_context` states.
177. `P3.rag-ui-1` keeps structured-query and workbench-flow guardrail messaging explicit in the UI.
178. The minimal Ask entry is disabled under explicit capability context when the member lacks `knowledge.read`, and the handler also blocks the API call on the same condition.
179. `P3.rag-ui-1` adds no backend code, no router contract changes, no request-schema changes, no provider registry changes, and no real external provider integration.
180. VS Code Problems check on touched frontend files reported no errors.
181. Console TypeScript no-emit validation passed through the local binary: `./node_modules/.bin/tsc -b --noEmit`.
182. Focused backend RAG regression passed: `70 passed`.
183. `pnpm build` could not run in the current environment because `pnpm` is unavailable.
184. `npm run build` could not run in the current environment because `npm` is unavailable.
185. `P3.rag-ui-1` `git diff --check`: clean.
186. `P3.rag-ui-2` product-flow UX enhancement planning is now complete as a docs-only slice.
187. The planning file for `P3.rag-ui-2` is `docs/tasks/knowledge-p3-rag-ui-2-product-flow-plan-2026-05-08.md`.
188. `P3.rag-ui-2` recommends prioritizing pure frontend UX enhancement on the existing answer endpoint before provider credential or transport boundary work.
189. The planned candidate features are recent-question history, static example questions, copy answer, and citation locate or jump.
190. The plan requires recent-question history to remain local UI state or session-level frontend state only and not enter formal knowledge, release artifacts, or SVN-adjacent flows.
191. The plan requires example questions to remain static UI suggestions only and not act as provider hints or prompt injection.
192. The plan requires copy-answer behavior to remain a frontend-only convenience action and not write back into knowledge storage.
193. The plan requires citation locate or jump to stay limited to citations already returned by the backend and forbids frontend artifact or raw-source reads.
194. The plan keeps Ask-button `knowledge.read` disablement and handler-side `knowledge.read` guard unchanged.
195. The plan keeps the effective minimal request payload at `query` only and does not authorize provider, model, provider-hint, or service-config request fields.
196. The plan keeps router/provider boundaries unchanged: no request-schema change, no router call to `get_rag_model_client(...)`, no change to `build_rag_answer_with_service_config(...)` as the live handoff entry, and no runtime-provider expansion beyond `deterministic_mock` and `disabled`.
197. The plan keeps real external provider integration, `ProviderManager.active_model`, environment-variable provider sources, and frontend provider/model settings out of scope.
198. The plan keeps structured-query and workbench-flow guardrail copy required in the UI and keeps ordinary RAG Q&A separate from administrator acceptance workflows.
199. `P3.rag-ui-2` is docs-only and does not modify `src/` or `console/src/` files.
200. This docs-only planning pass does not rerun pytest.
201. `P3.rag-ui-2a` frontend UX enhancement implementation is now complete.
202. The implementation files for `P3.rag-ui-2a` are `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/GameProject.module.less`.
203. `P3.rag-ui-2a` adds all four planned UX features: static example questions, recent question history, copy result, and local citation focus.
204. Example questions only populate the existing query input and do not auto-submit.
205. Recent-question history remains component-local only, stores only query plus mode plus timestamp, is capped at 5 items, deduplicates by query, and is not persisted.
206. Copy-result uses the browser clipboard API only and does not write files, knowledge artifacts, formal map, release notes, or release assets.
207. Citation focus is local scroll or highlight over the returned citation list only and does not read artifacts, raw source, or any new backend endpoint.
208. The effective frontend request payload remains limited to `query` and does not expose provider or model control.
209. Ask-button `knowledge.read` disablement and handler-side `knowledge.read` guard remain in place.
210. `P3.rag-ui-2a` adds no backend code, no request-schema changes, no router provider-selection changes, no runtime-provider expansion, and no real external provider integration.
211. VS Code Problems check on touched frontend files reported no errors.
212. Focused backend RAG regression passed: `70 passed`.
213. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
214. `P3.rag-ui-2a` `git diff --check`: clean.
215. Optional `./node_modules/.bin/vite build` could not complete because Rollup's native optional dependency failed to load with a macOS code-signature or optional-dependency error.
216. `P3.rag-ui-2b` frontend hardening and helper extraction is now complete.
217. The implementation files for `P3.rag-ui-2b` are `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/GameProject.module.less`, and `console/src/pages/Game/ragUiHelpers.ts`.
218. `P3.rag-ui-2b` extracts pure helper logic for recent-question history shaping, copy-result text assembly, citation-value formatting, and guardrail-warning classification.
219. `P3.rag-ui-2b` adds only minimal narrow-screen polish for example buttons, result actions, and citation metadata wrapping.
220. The effective frontend request payload remains limited to `query`, and Ask-button `knowledge.read` disablement plus handler-side guard remain unchanged.
221. `P3.rag-ui-2b` keeps recent history, copied output, and citation focus frontend-local only and does not add save, accept, publish, or formal-knowledge writes.
222. `P3.rag-ui-2b` adds no backend code, no request-schema changes, no router provider-selection changes, no runtime-provider expansion, and no real external provider integration.
223. No frontend test framework was added in `P3.rag-ui-2b` because the console workspace does not already define one.
224. Targeted frontend ESLint passed for `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/ragUiHelpers.ts`.
225. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
226. Focused backend RAG regression passed: `70 passed`.
227. `P3.rag-ui-2b` `git diff --check`: clean.
228. `P3.rag-ui-3` product experience consolidation planning is now complete as a docs-only slice.
229. The planning file for `P3.rag-ui-3` is `docs/tasks/knowledge-p3-rag-ui-3-product-experience-consolidation-plan-2026-05-08.md`.
230. `P3.rag-ui-3` records that the current RAG MVP entry should remain inside GameProject rather than splitting into a standalone Knowledge Q&A surface at this stage.
231. `P3.rag-ui-3` defines `answer` as the primary success state, `insufficient_context` as the primary recoverable failure state, and `no_current_release` as the primary readiness blocker state.
232. `P3.rag-ui-3` records that `insufficient_context` should gain read-only next-step guidance before any provider credential or transport work is considered.
233. `P3.rag-ui-3` keeps precise numeric or row-level questions routed toward structured query and keeps change or edit intent routed toward numeric workbench.
234. `P3.rag-ui-3` recommends future citation enhancement as display grouping only and does not authorize artifact or raw-source reading behavior.
235. `P3.rag-ui-3` records that any future citation reading view requires a separate boundary review before implementation.
236. `P3.rag-ui-3` keeps recent-question history component-local and non-persistent by default.
237. `P3.rag-ui-3` treats expanded copy affordances such as citation summary or markdown copy as future planning only and not the immediate next slice.
238. `P3.rag-ui-3` records a minimum future frontend test-strategy direction including helper tests, component smoke coverage when lightweight infrastructure exists, and payload-boundary checks, but does not introduce a new test framework in this slice.
239. `P3.rag-ui-3` explicitly recommends `P3.rag-ui-3a` as the next implementation slice.
240. `P3.rag-ui-3a` is recommended to remain frontend-only and to focus on three-state display hierarchy refinement, read-only next-step guidance, structured-query and workbench entry affordance planning, and citation display grouping planning.
241. `P3.rag-ui-3` explicitly recommends frontend-only product experience refinement before provider credential or transport work.
242. `P3.rag-ui-3` keeps provider or model control closed, keeps the effective request payload limited to `query`, keeps router provider selection unchanged, and keeps runtime providers limited to `deterministic_mock` and `disabled`.
243. `P3.rag-ui-3` keeps ordinary RAG Q&A separate from administrator acceptance and does not allow recent history, copy result, citation review, structured-query routing, or workbench routing to become acceptance or formal-knowledge entry paths.
244. `P3.rag-ui-3` is docs-only, does not rerun pytest, does not rerun TypeScript checks, and limits post-edit validation to `git diff --check`.
245. `P3.rag-ui-3a` frontend-only product experience refinement is now complete.
246. The implementation files for `P3.rag-ui-3a` are `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/GameProject.module.less`, and `console/src/pages/Game/ragUiHelpers.ts`.
247. `P3.rag-ui-3a` keeps the RAG MVP entry inside the existing GameProject surface and does not create a standalone Knowledge Q&A page.
248. `P3.rag-ui-3a` refines the three-state hierarchy so `answer` remains the primary success content, `insufficient_context` is a recoverable failure state, and `no_current_release` is a readiness blocker state.
249. `P3.rag-ui-3a` keeps answer body primary, while release metadata, warnings, and citations remain auxiliary information.
250. `P3.rag-ui-3a` adds read-only next-step hints for `insufficient_context` and does not auto-retry or fabricate an answer.
251. `P3.rag-ui-3a` keeps structured-query and workbench guardrail copy in place and adds read-only compact path labels only.
252. `P3.rag-ui-3a` does not navigate routes, does not write URLs, and does not trigger a workbench session.
253. `P3.rag-ui-3a` groups citations by `source_type` for display only and derives that grouping only from returned `ragAnswer.citations`.
254. `P3.rag-ui-3a` does not synthesize citations, does not read artifact or raw source content, and does not add a new backend endpoint.
255. `P3.rag-ui-3a` keeps existing example questions, recent-question history, copy result, and local citation focus in place.
256. The effective frontend request payload remains limited to `query`, and `answerRagQuestion(...)` still sends only `{ query }`.
257. Ask-button `knowledge.read` disablement and handler-side `knowledge.read` guard remain unchanged in `P3.rag-ui-3a`.
258. `P3.rag-ui-3a` adds no backend code, no request-schema changes, no router provider-selection changes, no runtime-provider expansion, and no real external provider integration.
259. Targeted frontend ESLint passed for `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/ragUiHelpers.ts`.
260. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
261. Focused backend RAG regression passed: `70 passed`.
262. `P3.rag-ui-3a` `git diff --check`: clean.
263. `P3.8` RAG router or structured-query or workbench routing boundary planning is now complete as a docs-only slice.
264. The planning file for `P3.8` is `docs/tasks/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md`.
265. `P3.8` keeps ordinary current-release RAG Q&A as a read-only explanatory surface and does not allow ordinary Q&A to create test plans, release candidates, formal map, release build, or release publish actions.
266. `P3.8` keeps structured-query routing limited to exact numeric, row-level, field-level, and value-level lookup intent only.
267. `P3.8` keeps workbench routing limited to change or edit intent only.
268. `P3.8` keeps administrator acceptance outside ordinary RAG Q&A, recent-question history, copy result, citation review, and routing hints.
269. `P3.8` records that any future `Go to structured query` or `Go to workbench` action must be an explicit frontend user action and must not auto-submit, auto-write a test plan, auto-create a candidate, auto-build, or auto-publish.
270. `P3.8` keeps the product-facing query payload limited to `{ query }` only and does not authorize provider name, model name, provider hint, or service config in request body.
271. `P3.8` keeps router provider selection forbidden and reconfirms that router code must not call `get_rag_model_client(...)` directly.
272. `P3.8` keeps citation grouping and local citation focus derived only from returned citations and authorizes no new citation artifact or raw-source reading endpoint.
273. `P3.8` adds no `src/` change, no `console/src/` change, no new API, no real provider, and no RAG request-schema change.
274. `P3.8` is docs-only and does not rerun pytest.
275. `P3.8b` workbench affordance boundary review is now complete as a docs-only slice.
276. The review file for `P3.8b` is `docs/tasks/knowledge-p3-8b-workbench-affordance-boundary-review-2026-05-09.md`.
277. `P3.8b` keeps the future `Go to workbench` affordance as a workbench-only routing review and does not authorize a combined structured-query plus workbench implementation.
278. `P3.8b` keeps the first-version workbench affordance limited to explicit workbench or change-intent guardrail surfaces only.
279. `P3.8b` explicitly rejects generic `insufficient_context` next-step hints as a first-version trigger for the workbench affordance.
280. `P3.8b` keeps any future affordance user-triggered only and forbids automatic redirect, auto-submit, automatic test-plan creation, automatic candidate creation, automatic build, and automatic publish.
281. `P3.8b` keeps the recommended first version limited to plain navigation to `/numeric-workbench` only.
282. `P3.8b` does not recommend freeform-query handoff because current NumericWorkbench deep-link support is explicit only for `session`, `table`, `row`, and `field`.
283. `P3.8b` keeps `workbench.read` as the destination-entry permission and keeps `workbench.test.write` as the later mutation permission without requiring `knowledge.build` or `knowledge.publish`.
284. `P3.8b` keeps structured query outside this slice as a separate destination-boundary problem.
285. `P3.8b` adds no `src/` change, no `console/src/` change, no new API, no real provider, and no request-schema change.
286. `P3.8b` is docs-only and does not rerun pytest.
287. `P3.8c` frontend-only `Go to workbench` affordance implementation is now complete.
288. The closeout file for `P3.8c` is `docs/tasks/knowledge-p3-8c-go-to-workbench-closeout-2026-05-09.md`.
289. `P3.8c` adds the workbench affordance only in the static workbench guardrail block and in warning rows using the existing workbench warning.
290. `P3.8c` does not add the affordance to generic `insufficient_context` next-step hints.
291. `P3.8c` keeps navigation explicit user click only and navigates only to `/numeric-workbench`.
292. `P3.8c` does not pass freeform query text, does not auto-submit workbench chat or changes, and does not auto-create test plans or candidates.
293. `P3.8c` does not build, publish, or trigger SVN behavior.
294. `P3.8c` preserves local trusted fallback when capability context is absent.
295. `P3.8c` disables the button only when capability context exists and `workbench.read` is missing, with fixed copy `Requires workbench.read permission.`.
296. `P3.8c` does not require `knowledge.build` or `knowledge.publish`, and `workbench.test.write` continues to govern later workbench write behavior only.
297. `P3.8c` adds no backend code, no new API, no request-schema change, no provider or model control, no structured-query affordance, and no real LLM integration.
298. Frontend TypeScript no-emit validation ran with no output.
299. Targeted ESLint for `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/ragUiHelpers.ts` ran with no output.
300. `git diff --check` ran with no output.
301. Editor diagnostics reported no errors in `GameProject.tsx`, `ragUiHelpers.ts`, or `GameProject.module.less`.
302. No GameProject or RAG UI frontend test suite was found for this slice, so no frontend component test was run.
303. No backend pytest was run because this slice did not touch backend code.
304. `P3.8d` structured-query destination discovery and boundary review is now complete as a docs-only slice.
305. The review file for `P3.8d` is `docs/tasks/knowledge-p3-8d-structured-query-destination-discovery-2026-05-09.md`.
306. `P3.8d` reconfirms that the current frontend has no dedicated structured-query page, route, tab, or reusable component.
307. `P3.8d` reconfirms that `GameProject.tsx` and `ragUiHelpers.ts` still expose only read-only structured-query labels and warning copy.
308. `P3.8d` confirms that legacy `gameApi.query(...)` has no visible call site in `console/src` and is not a sufficient structured-query product destination by itself.
309. `P3.8d` rejects NumericWorkbench as the structured-query destination because NumericWorkbench remains the change or edit surface.
310. `P3.8d` rejects IndexMap as the structured-query destination because IndexMap is an index-browsing surface rather than a query-execution surface.
311. `P3.8d` recommends a new minimal structured-query panel inside the existing GameProject surface as the first explicit destination contract.
312. `P3.8d` keeps the current read-only structured-query label in place and does not recommend immediate frontend button implementation.
313. `P3.8d` keeps any future structured-query entry explicit-click only, non-submitting by default, non-writing by default, and separate from `knowledge.read`, `knowledge.build`, and `knowledge.publish` gating.
314. `P3.8d` preserves the `{ query }` request boundary, adds no backend `src` change, no `console/src` change, no new API, no provider or model control, and no real LLM integration.
315. `P3.8d` is docs-only and does not rerun pytest.
316. `P3.8e` minimal structured-query panel contract review is now complete as a docs-only slice.
317. The contract file for `P3.8e` is `docs/tasks/knowledge-p3-8e-structured-query-panel-contract-2026-05-09.md`.
318. `P3.8e` freezes the first-version structured-query destination as a minimal panel inside the existing GameProject surface rather than a new global route.
319. `P3.8e` limits the panel to exact numeric, row-level, field-level, and value-level lookup only and keeps change or edit or modify intent in workbench.
320. `P3.8e` allows a future `Open structured query` affordance only as explicit user click in explicit structured-query warning contexts, and opening the panel must not auto-submit.
321. `P3.8e` allows future prefill of the current RAG query only as local input state and explicitly forbids auto-submit.
322. `P3.8e` keeps first-version structured-query results read-only and keeps test-plan creation, candidate creation, build, publish, and mutation behavior out of the panel.
323. `P3.8e` records that the current `gameApi.query(...)` wrapper is not yet a sufficient product contract by itself because the frontend lacks typed request or response models, documented mode semantics, and a frozen read-only result shape.
324. `P3.8e` therefore defers direct panel-submit binding to a later narrow API contract or typing review rather than authorizing immediate frontend implementation.
325. `P3.8e` keeps `knowledge.build` and `knowledge.publish` out of the panel-entry requirement and recommends a dedicated structured-query read capability rather than treating `knowledge.read` as the permanent contract.
326. `P3.8e` preserves the `{ query }` RAG payload boundary, changes no backend `src`, changes no `console/src`, adds no new API, and does not change `P3.8c` workbench affordance behavior.
327. `P3.8e` is docs-only and does not rerun pytest.
328. `P3.8f` structured-query submit contract and typing review is now complete as a docs-only slice.
329. The review file for `P3.8f` is `docs/tasks/knowledge-p3-8f-structured-query-submit-contract-2026-05-09.md`.
330. `P3.8f` confirms that `gameApi.query(agentId, q, mode)` currently sends `POST /agents/{agentId}/game/index/query`.
331. `P3.8f` confirms that the current backend request shape is only `q` plus `mode`, with default mode `auto`.
332. `P3.8f` confirms that the current backend response shape is an untyped dict with top-level `mode` and `results` only and with observed branches `not_configured`, `exact_table`, `exact_field`, and `semantic_stub`.
333. `P3.8f` confirms that there is no stable backend enum or frontend type union for mode today and that `auto` is the only mode with explicit backend logic.
334. `P3.8f` freezes the first-version panel submit contract to query plus fixed `auto` mode only and forbids provider, model, provider hint, service config, and write-oriented flags.
335. `P3.8f` records that the current response is too loose for direct product use and therefore recommends a frontend typed wrapper or normalization layer over the existing endpoint rather than an immediate backend change.
336. `P3.8f` freezes a normalized read-only panel response contract with explicit request mode, result mode, status, message, warnings, items, and error fields, plus table-result and field-result display variants.
337. `P3.8f` allows source-like display only from already returned `source_path` and field `references` and authorizes no new citation artifact or raw-source endpoint.
338. `P3.8f` keeps prefill allowed only as local input state and keeps submit explicit user click only.
339. `P3.8f` keeps submit read-only and forbids test-plan creation, candidate creation, build, publish, and mutation behavior.
340. `P3.8f` keeps `knowledge.build` and `knowledge.publish` out of the submit requirement and allows temporary `knowledge.read` only as an interim bridge until a dedicated structured-query read capability exists.
341. `P3.8f` preserves the `{ query }` RAG boundary, changes no backend `src`, changes no `console/src`, adds no new API, and does not change `P3.8c` workbench affordance behavior.
342. `P3.8f` is docs-only and does not rerun pytest.
343. `P3.8g` minimal structured-query panel implementation is now complete as a frontend-only slice.
344. The closeout file for `P3.8g` is `docs/tasks/knowledge-p3-8g-minimal-structured-query-panel-closeout-2026-05-09.md`.
345. `P3.8g` adds `Open structured query` only to the static structured-query guardrail block and the existing `STRUCTURED_FACT_WARNING` warning row in GameProject.
346. `P3.8g` keeps panel opening explicit user click only and allows prefill from the current RAG query only as local panel state when the local draft is still empty.
347. `P3.8g` keeps submit explicit user click only, keeps submit disabled until a `selectedAgent` exists, and reuses `POST /agents/{agentId}/game/index/query` with only query plus fixed `auto` mode.
348. `P3.8g` lands a frontend typed wrapper and normalization layer so the UI no longer directly depends on the raw untyped `/game/index/query` response shape.
349. `P3.8g` normalizes read-only result display into table-result and field-result variants only.
350. `P3.8g` keeps source-like display limited to already returned `source_path`, `references`, and `tags` fields and adds no raw-source or citation endpoint.
351. `P3.8g` keeps local trusted fallback when explicit capability context is absent.
352. `P3.8g` disables both `Open structured query` and panel submit when explicit capability context exists but `knowledge.read` is missing and uses `Requires knowledge.read permission.` as the disabled copy.
353. `P3.8g` keeps `knowledge.build` and `knowledge.publish` out of the panel gate.
354. `P3.8g` preserves the `{ query }` RAG boundary, changes no backend `src`, adds no backend API, changes no provider selection, and does not change `P3.8c` workbench affordance behavior.
355. `P3.8g` ran frontend TypeScript no-emit, targeted ESLint, and `git diff --check`, and no frontend component test was run because no existing GameProject or RAG UI frontend test suite was found for this slice.
356. `P3.8h` RAG MVP interaction validation and closeout is now complete.
357. The closeout file for `P3.8h` is `docs/tasks/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md`.
358. `P3.8h` confirms that RAG Ask still sends only `{ query }`.
359. `P3.8h` confirms that `Open structured query` appears only in the static structured guardrail block and the `STRUCTURED_FACT_WARNING` warning row.
360. `P3.8h` confirms that opening structured query only opens the local panel and does not auto-submit, and that prefill remains local input-state only.
361. `P3.8h` confirms that structured-query submit remains fixed to `auto` mode and that result rendering remains read-only table-result or field-result display only.
362. `P3.8h` confirms that no test-plan, candidate, build, publish, or SVN behavior was added to the interaction surface.
363. `P3.8h` confirms that `Go to workbench` appears only in the static workbench guardrail block and the `CHANGE_QUERY_WARNING` warning row and still navigates only to `/numeric-workbench` with no freeform-query handoff.
364. `P3.8h` confirms that explicit capability context missing `knowledge.read` disables Ask, `Open structured query`, and `Submit structured query`, and that explicit capability context missing `workbench.read` disables `Go to workbench`.
365. `P3.8h` confirms that capability-context absence keeps local trusted fallback intact.
366. `P3.8h` ran frontend TypeScript no-emit, targeted ESLint, and `git diff --check` successfully.
367. `P3.8h` attempted a minimal browser smoke and reached console-shell load only; full in-app interaction smoke was limited by local frontend-backend environment issues rather than by new code defects in this slice.
368. `P3.8h` changes only `docs/tasks`, adds no backend code, adds no frontend behavior, adds no API, and allows `P3.8` MVP interaction to be treated as closed.
369. Final P3 RAG MVP gate review confirms that the current worktree still keeps all `P3.8` interaction behavior inside the frozen request, provider, router, and citation boundaries.
370. Final gate frontend validation reran successfully: TypeScript no-emit passed, targeted ESLint passed, and `git diff --check` passed.
371. Final gate backend focused pytest passed for the current RAG interaction slice: `56 passed` for `test_knowledge_rag_context.py`, `test_knowledge_rag_answer.py`, and `test_game_knowledge_rag_router.py`.
372. Final gate backend focused pytest also passed for the current RAG model/provider slice: `24 passed` for `test_knowledge_rag_provider_selection.py`, `test_knowledge_rag_model_registry.py`, `test_knowledge_rag_model_client.py`, and `test_knowledge_rag_external_model_client.py`.
373. Final gate confirms that no Python file is touched in the current P3.8 worktree, so no Python-side NUL-byte check was required for this round.
374. Final gate keeps real LLM integration, provider or model UI, raw-source or citation endpoints, and automatic test-plan, candidate, build, or publish behavior out of scope.
375. Final gate finds no remaining blocker inside the validated P3.8 MVP interaction surface and considers the slice commit-ready.
