# Post-MVP Data-Backed Final Regression Receipt

Date: 2026-05-10

## Scope

This round is a final regression receipt over the accepted P0-P3 MVP and the prior real-data pilot validation.

It did not add new feature scope.

It did not continue `P20`.

It did not reopen real external-provider rollout, real HTTP transport, request-schema widening, provider or model UI, relationship editor, graph canvas, or SVN commit integration.

The goal was to reconfirm that the current MVP remains pilot-usable on the real local project directory and that the two prior real-data blockers stay fixed.

## Re-audited Blocker Fixes

### 1. `game/index/status` configured-runtime crash

Re-audited file:

1. `src/ltclaw_gy_x/game/retrieval.py`

Regression target:

1. `load_doc_chunk_index(...)` must resolve the effective local project root before reading retrieval status paths.
2. `GET /api/agents/default/game/index/status` must not fail once a real local project directory is configured.

Regression coverage in this round:

1. focused source re-audit confirmed the fix is still present
2. live HTTP smoke returned `200` from `GET /api/agents/default/game/index/status`
3. live response showed `configured=true` and `table_count=8` against the real directory

### 2. `build-from-current-indexes` project-level persistence mismatch

Re-audited file:

1. `src/ltclaw_gy_x/game/index_committer.py`

Regression target:

1. current table, dependency, and registry artifacts must be written into project-level app-owned paths
2. safe release build must read those project-level artifacts successfully
3. commit eligibility must stay gated when those files are outside the working copy

Regression coverage in this round:

1. focused source re-audit confirmed the project-level persistence logic is still present
2. focused backend tests were refreshed to match the intended behavior and then passed
3. live rebuild wrote `project/indexes/table_indexes.json`, `dependency_graph.json`, and `registry.json`
4. live `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` succeeded twice on the real directory

## Focused Backend Regression

Executed command:

1. `/Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_release_store.py tests/unit/game/test_knowledge_release_query.py tests/unit/game/test_knowledge_release_service.py tests/unit/game/test_knowledge_rag_context.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_index_committer.py tests/unit/game/test_index_registry.py tests/unit/routers/test_game_knowledge_release_router.py tests/unit/routers/test_game_knowledge_query_router.py tests/unit/routers/test_game_knowledge_rag_router.py tests/unit/routers/test_game_knowledge_map_router.py tests/unit/routers/test_game_knowledge_test_plans_router.py tests/unit/routers/test_game_knowledge_release_candidates_router.py tests/unit/routers/test_game_change_router.py tests/unit/app/test_capabilities.py -q`

Observed progression:

1. first run: `3 failed, 176 passed in 2.19s`
2. failures were stale assertions in `tests/unit/game/test_index_committer.py` and `tests/unit/game/test_index_registry.py`
3. after minimal test-only correction: narrow rerun `10 passed in 0.48s`
4. final focused rerun: `179 passed in 1.77s`

Interpretation:

1. no new product regression was found in the audited source paths
2. the only repair needed in this round was to update stale tests so they assert the current intended persistence model

## Frontend Validation

Executed command:

1. `cd /Users/Admin/LTCLaw2.0/console && ./node_modules/.bin/tsc --noEmit -p tsconfig.app.json && ./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/NumericWorkbench.tsx && npm run build`

Result:

1. TypeScript no-emit passed
2. targeted ESLint returned `0 errors` and `10 warnings`
3. warnings were existing `react-hooks/exhaustive-deps` warnings in `NumericWorkbench.tsx`
4. production bundle build passed
5. Vite reported a pre-existing circular chunk warning only

Command choice note:

1. local binaries were used intentionally to avoid earlier workspace wrapper or approve-builds interference

## Real Data-Backed Smoke

Real local project directory:

1. `/Users/Admin/CodeBuddy/20260501110222/test-data`

Dedicated runtime root:

1. `/tmp/ltclaw-data-backed`

Verified runtime state:

1. `my_role=maintainer`
2. `svn_local_root=/Users/Admin/CodeBuddy/20260501110222/test-data`
3. `GET /api/agents/default/game/index/status` returned `configured=true` and `table_count=8`

Executed smoke evidence:

1. `POST /api/agents/default/game/index/rebuild` scanned 8 real `.xlsx` files and indexed 8 tables
2. `GET /api/agents/default/game/index/tables` returned 8 indexed tables
3. `GET /api/agents/default/game/index/tables/角色属性表/rows?offset=0&limit=3` returned real rows including row `4001` with `weaponId=1002`
4. `GET /api/agents/default/game/project/storage` resolved project-level app-owned storage under `/tmp/ltclaw-data-backed/game_data/projects/test-data-201b6e029661`
5. project-level current-index files existed under `project/indexes/`
6. formal map save succeeded and preserved 8 active table refs
7. `build-from-current-indexes` created `pilot-final-reg-r1-1778382520` and `pilot-final-reg-r2-1778382520`
8. set-current succeeded on both new releases
9. rollback back to `pilot-final-reg-r1-1778382520` succeeded
10. current-release keyword query returned `角色属性表.xlsx`
11. current-release RAG context returned 1 chunk and 1 citation
12. current-release RAG answer returned grounded output with 1 citation and no warning
13. structured query returned `exact_field` for `weaponId` and `exact_table` for `角色属性表`
14. draft proposal create returned `status=draft`
15. proposal dry-run returned a real change from `before=1002` to `after=1003`

## Browser-Level UX Recheck

Verified in the latest production bundle served by the isolated runtime:

1. `GameProject` loaded with current release state visible
2. the structured-query affordance required explicit user open
3. opening the panel did not auto-submit
4. the submit button stayed disabled until text was entered
5. after entering `weaponId`, explicit submit returned a read-only success result with `result_mode=exact_field`
6. `NumericWorkbench` route loaded successfully
7. a saved workbench session opened successfully
8. the workbench remained in draft or session mode and did not publish anything automatically

## Documentation Sync

This receipt updates the mainline record by referencing the final regression round in:

1. `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-data-backed-pilot-closeout-2026-05-10.md`
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

## Final Judgment

### Data-backed pilot readiness pass.

Why this passes:

1. the two prior real-data blockers were re-audited and revalidated
2. focused backend regression is green after aligning stale tests to the intended persistence model
3. frontend validation is green apart from pre-existing warnings
4. the real local project directory still supports rebuild, formal-map save, release build, set-current, rollback, current-release query, current-release RAG, structured query, and draft export dry-run
5. the browser-level MVP interaction rules remain explicit-open and explicit-submit, with no accidental publish path

### Not production ready

Remaining known limitations:

1. this environment still has table data only, so `doc_knowledge` and `script_evidence` remain empty
2. real provider rollout, real HTTP provider transport, and provider or model UI remain intentionally out of scope
3. SVN commit integration is still not part of this pilot receipt
