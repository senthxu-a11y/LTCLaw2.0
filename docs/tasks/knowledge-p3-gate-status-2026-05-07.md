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
12. The next recommended step is `P3.rag-model-2d` app/service config injection implementation planning before any real external model integration.

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
29. The current slice is still not a shipped RAG product or full map-governance product surface because no real LLM, app/service config injection code implementation, embedding flow, frontend RAG UI, relationship editor, or graph canvas has been added.
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
72. `P3.rag-model-2d` app/service config injection implementation plan is now complete as a docs-only slice.
73. `P3.rag-model-2d` recommends a small service-layer resolver helper such as `resolve_rag_model_provider_name(...)` or an equivalent helper that resolves provider name only from backend DI or service config.
74. `P3.rag-model-2d` keeps `build_rag_answer_with_provider(...)` as the service-layer entry point and `get_rag_model_client(...)` as the only registry entry point.
75. `P3.rag-model-2d` keeps router provider selection, request-body provider hint, frontend provider control, environment variables, `ProviderManager.active_model`, and real external providers out of scope for the next code slice.
76. `P3.rag-model-2d` keeps the next implementation limited to runtime providers `deterministic_mock` and `disabled` only.
77. `P3.rag-model-2d` defines the expected file-touch set, do-not-touch set, focused tests, and acceptance criteria for the next implementation round.
78. `P3.rag-model-2d` is docs-only, did not rerun pytest, and adds no backend code, no frontend code, no router change, and no public API.
79. The next recommended step is execution of the `P3.rag-model-2d` plan as a narrow backend-only code slice rather than direct real-model integration.
