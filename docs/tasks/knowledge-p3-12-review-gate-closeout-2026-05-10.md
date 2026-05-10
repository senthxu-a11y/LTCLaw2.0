# Knowledge P3.12 Review Gate Closeout

Date: 2026-05-10
Scope: P3 review-gate closeout for the current P0-P3 MVP mainline, with blocker-fix scope limited to minimal documentation correction only

## 1. Closeout Decision

P3.12 P3 Review Gate is passed for the current P0-P3 MVP slice.

This round remains a review-gate and closeout round.

This round does not continue external-provider work.

This round does not implement P20.

The only blocker found during review was documentation drift in the earlier P3.11 closeout validation section.

No new product functionality was added in this round.

## 2. Gate Outcome

The P3.12 checklist is now closed as:

1. Map is editable through UX: passed, with the current conservative scope interpreted as saved formal-map save plus saved formal-map status editing in GameProject, not candidate-map editing and not relationship-editor scope.
2. RAG reads current release only: passed.
3. Precise values go through structured query: passed.
4. Release rollback works: passed.
5. Permission split is enforced: passed.

## 3. Gate Evidence

### 3.1 Map Is Editable Through UX

Current product truth is intentionally conservative:

1. GameProject loads candidate map and saved formal map separately.
2. Candidate map remains a review surface.
3. Formal map is editable through the existing save flow and saved-formal-map status edit flow.
4. Relationship editing remains deferred and is not treated as a blocker for the MVP gate.

Source evidence:

1. `console/src/pages/Game/GameProject.tsx` loads candidate map through `getMapCandidate(...)` and saved formal map through `getFormalMap(...)`.
2. `console/src/pages/Game/GameProject.tsx` exposes `handleSaveFormalMap(...)` and `handleSaveFormalMapDraft(...)` and gates them with `canSaveFormalMap` and `canSaveFormalMapDraft`.
3. `console/src/pages/Game/GameProject.tsx` explicitly states `Save a formal map first before editing statuses.` and keeps editing limited to saved formal-map status changes.
4. `src/ltclaw_gy_x/app/routers/game_knowledge_map.py` keeps read and write split at `GET /game/knowledge/map/candidate`, `GET /game/knowledge/map`, and `PUT /game/knowledge/map`.

Regression evidence:

1. `tests/unit/routers/test_game_knowledge_map_router.py` proves candidate-map read requires `knowledge.map.read`.
2. `tests/unit/routers/test_game_knowledge_map_router.py` proves saved-formal-map read requires `knowledge.map.read`.
3. `tests/unit/routers/test_game_knowledge_map_router.py` proves formal-map save requires `knowledge.map.edit` and still returns `formal_map_saved` when permitted.

### 3.2 RAG Reads Current Release Only

Source evidence:

1. `src/ltclaw_gy_x/game/knowledge_rag_context.py` resolves context through `get_current_release(project_root)`.
2. `src/ltclaw_gy_x/game/knowledge_rag_context.py` reads the selected release map through `load_knowledge_map(project_root, manifest.release_id)`.
3. Allowed release context indexes remain limited to release-owned `table_schema`, `doc_knowledge`, and `script_evidence`.
4. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` keeps the Ask request surface narrow at `query`, `max_chunks`, and `max_chars` only.

Regression evidence:

1. `tests/unit/game/test_knowledge_rag_context.py` proves current-release context reads only current-release artifacts and does not read `candidate_evidence.jsonl`, pending test plans, or pending release candidates.
2. `tests/unit/game/test_knowledge_rag_context.py` proves rollback immediately changes which release query and RAG context use.
3. `tests/unit/routers/test_game_knowledge_rag_router.py` covers `no_current_release` routing behavior on the existing RAG endpoints.

### 3.3 Precise Values Go Through Structured Query

Source evidence:

1. `console/src/pages/Game/GameProject.tsx` keeps the RAG entry read-only and explicitly warns that exact numeric or row-level facts should go through structured query, not the RAG entry.
2. `console/src/pages/Game/GameProject.tsx` opens structured query only through explicit user action and keeps submit explicit through `handleSubmitStructuredQuery(...)`.
3. `console/src/api/modules/gameStructuredQuery.ts` always submits `{ q, mode: 'auto' }` to `/game/index/query` and always normalizes the response as `request_mode: 'auto'`.
4. `src/ltclaw_gy_x/game/query_router.py` keeps `mode='auto'` limited to exact table match, then exact field match, then `semantic_stub`.

Validation evidence:

1. `docs/tasks/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md` already records that Ask stays on the current RAG path, structured query opens locally without auto-submit, and submit remains fixed to `mode="auto"`.
2. `tests/unit/game/test_knowledge_rag_answer.py` and `tests/unit/game/test_knowledge_map_candidate.py` retain the structured-query warning path for exact numeric or row-level facts.

### 3.4 Release Rollback Works

Source evidence:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_release.py` exposes structured release status with `current`, `previous`, and `history`.
2. `src/ltclaw_gy_x/app/routers/game_knowledge_release.py` keeps rollback on the existing `POST /game/knowledge/releases/{release_id}/current` path.
3. `src/ltclaw_gy_x/game/knowledge_release_store.py` keeps rollback narrow by updating only `releases/current.json` through `set_current_release(...)`.
4. `console/src/pages/Game/GameProject.tsx` exposes `Rollback to previous` UX and confirmation copy stating that rollback only switches the current-release pointer.

Regression evidence:

1. `tests/unit/routers/test_game_knowledge_release_router.py` proves the status endpoint returns `current`, `previous`, and ordered `history`.
2. `tests/unit/routers/test_game_knowledge_release_router.py` proves set-current requires `knowledge.publish` and succeeds when that capability is present.
3. `tests/unit/game/test_knowledge_rag_context.py` proves query and current-release RAG context follow the restored release after rollback.

### 3.5 Permission Split Is Enforced

Source evidence:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_release.py` keeps release read, build, and publish split across `knowledge.read`, `knowledge.build`, and `knowledge.publish`.
2. `src/ltclaw_gy_x/app/routers/game_knowledge_map.py` keeps `knowledge.map.read` and `knowledge.map.edit` separate.
3. `src/ltclaw_gy_x/app/routers/game_knowledge_test_plans.py` keeps `workbench.read` and `workbench.test.write` separate.
4. `src/ltclaw_gy_x/app/routers/game_knowledge_release_candidates.py` keeps `knowledge.candidate.read` and `knowledge.candidate.write` separate.
5. `src/ltclaw_gy_x/app/routers/game_change.py` keeps workbench draft export or proposal creation on `workbench.test.export`.
6. `console/src/pages/Game/NumericWorkbench.tsx` separately gates read, write, and export through `canReadWorkbench`, `canWriteWorkbench`, and `canExportWorkbench`.

Regression evidence:

1. `tests/unit/routers/test_game_knowledge_release_router.py` covers `knowledge.read` and `knowledge.publish` gating.
2. `tests/unit/routers/test_game_knowledge_map_router.py` covers `knowledge.map.read` and `knowledge.map.edit` gating.
3. `tests/unit/routers/test_game_knowledge_test_plans_router.py` covers `workbench.read` and `workbench.test.write` gating.
4. `tests/unit/routers/test_game_knowledge_release_candidates_router.py` covers `knowledge.candidate.read` and `knowledge.candidate.write` gating.
5. `tests/unit/routers/test_game_change_router.py` covers `workbench.test.export` gating.

## 4. Minimal Blocker Fix

The only blocker found in this review round was stale wording in the existing P3.11 closeout.

That document previously said that additional closeout validation still remained after the slice, but the relevant focused validation had already been completed later in the same workstream.

This round corrects that stale statement and records the actual completed validation summary instead.

## 5. Validation Result

Focused validation for this review gate remained narrow and evidence-driven.

Executed focused regression:

1. `68 passed in 1.98s`
2. Covered release status and rollback, formal map read and save gates, current-release RAG context, test-plan read or write gates, release-candidate gates, and workbench export gate.
3. Test files covered:
   - `tests/unit/routers/test_game_knowledge_release_router.py`
   - `tests/unit/routers/test_game_knowledge_map_router.py`
   - `tests/unit/game/test_knowledge_rag_context.py`
   - `tests/unit/routers/test_game_knowledge_test_plans_router.py`
   - `tests/unit/routers/test_game_knowledge_release_candidates_router.py`
   - `tests/unit/routers/test_game_change_router.py`
4. `git diff --check` passed.
5. Touched-file NUL check passed.
6. Keyword and boundary review passed.
7. No frontend code was changed in P3.12, so frontend validation is inherited from P3.10 and P3.11 and the P3.12 pass used static source review for frontend gate evidence.

## 6. Boundary Confirmation

This review-gate closeout does not:

1. add new product functionality
2. continue external-provider implementation
3. implement P20
4. add real provider selection UI
5. change Ask request schema
6. expand relationship editing beyond the existing deferred boundary
7. collapse the final MVP permission split into broader capability names

## 7. Next Step

The P0-P3 MVP mainline gate is now closed through P3.12.

Any next step should be a new scoped slice, not implicit continuation of frozen external-provider work.
