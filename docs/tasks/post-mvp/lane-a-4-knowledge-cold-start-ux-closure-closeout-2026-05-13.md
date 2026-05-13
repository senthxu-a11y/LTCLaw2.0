# Lane A.4 Knowledge Cold-Start UX Closure Closeout

Date: 2026-05-13
Status: completed
Classification: post-MVP / MVP-aligned UX closure / pilot blocker hardening

## 1. Scope

1. This slice implemented the Knowledge-page cold-start UX closure for first-release bootstrap only.
2. The implementation stayed inside the existing frontend Knowledge page and existing frontend game API client.
3. No accepted MVP semantics were reopened.
4. This closeout does not claim production rollout and does not claim production ready.
5. Product conclusion remains pilot usable and not production ready.

## 2. Implementation Files

1. `console/src/api/modules/game.ts`
2. `console/src/pages/Game/Knowledge/index.tsx`
3. `docs/tasks/post-mvp/lane-a-4-knowledge-cold-start-ux-closure-closeout-2026-05-13.md`

## 3. Backend Endpoint Change

1. New backend endpoint added: no.
2. The slice reused the existing `GET /game/index/status` endpoint to distinguish cold-start indexes-missing versus indexes-ready page states.
3. The slice reused the existing `POST /game/index/rebuild` endpoint through the existing frontend game API module.
4. The slice did not change `POST /game/knowledge/releases/build-from-current-indexes` semantics.

## 4. Rebuild Entry Behavior

1. When the Knowledge page is in first-release bootstrap state and current table indexes are missing, it now shows an explicit `Rebuild current indexes` action.
2. The rebuild action is surfaced in the main Knowledge release card and in the candidate-map no-current-release info state.
3. The Build release modal also shows the rebuild action when the first-release prerequisite is missing.
4. Rebuild failure is shown as a dedicated rebuild error state and is not labeled as a release-build failure.
5. Rebuild success is shown as a dedicated success state and does not auto-trigger any release build.

## 5. Refresh Behavior After Rebuild

1. Rebuild success refreshes release status.
2. Rebuild success refreshes candidate map.
3. Rebuild success refreshes formal map.
4. Rebuild success refreshes build candidates and prerequisite state when the Build release modal is open.
5. Rebuild success refreshes current index status so the page can switch from indexes-missing to indexes-ready messaging.

## 6. Release Build Behavior

1. Rebuild success does not auto-build a release.
2. Rebuild success does not auto-set a current release.
3. The operator must still click Build release explicitly after rebuild succeeds.
4. Existing current-release projects remain on their normal release, rollback, and query paths.

## 7. Permission And 403 Behavior

1. Backend rebuild permission remains maintainer-only.
2. Consumer or 403 rebuild attempts now surface as recoverable rebuild errors on the Knowledge page.
3. The page keeps the cold-start rebuild entry visible after a 403 so the state remains understandable and retryable under the correct role.
4. The slice did not change `knowledge.build`, `knowledge.map.read`, `knowledge.map.edit`, or rollback semantics.

## 8. Manual Smoke Result

Environment used:

1. Existing runtime on `http://127.0.0.1:8092` for current-release baseline validation.
2. Isolated fresh working-dir runtime on `http://127.0.0.1:8093` for maintainer cold-start validation.
3. Isolated fresh working-dir runtime on `http://127.0.0.1:8094` for consumer / 403 cold-start validation.
4. The isolated runtimes reused the existing real project config and user config from the validated Windows sample, while keeping separate working directories so release and index artifacts stayed isolated.

Scenario A: no current release, no formal map, current table indexes already exist, Build release succeeds.

1. Covered on the isolated `8093` runtime after rebuild refreshed the page into indexes-ready state.
2. The page showed `Current table indexes are ready for first-release bootstrap`.
3. The Build release modal used the indexes-ready bootstrap wording.
4. Manual Build release succeeded and created a new available release entry with `table_schema: 18`.

Scenario B: no current release, no formal map, no current table indexes, page prompts rebuild, user triggers rebuild, rebuild succeeds, and Build release then succeeds.

1. `8093` initial state was `current=None`, `history=0`, `table_count=0`.
2. The Knowledge page immediately showed `Current table indexes are required before the first release build` and a visible `Rebuild current indexes` action.
3. Clicking `Rebuild current indexes` succeeded and showed `Current table indexes rebuilt. Indexed 18 table files.`
4. The page refreshed into the indexes-ready state without auto-building a release.
5. The operator then explicitly clicked Build release and bootstrap release creation succeeded.

Scenario C: rebuild fails or returns 403, page shows a recoverable error and does not mislabel it as a release-build failure.

1. `8094` initial state was configured as `consumer` with `current=None`, `history=0`, `table_count=0`.
2. The Knowledge page still showed the cold-start rebuild entry.
3. Clicking `Rebuild current indexes` returned backend `403`.
4. The page showed `Current table index rebuild is temporarily unavailable` with the recoverable detail `Only maintainers can rebuild index`.
5. The page did not relabel that failure as a release-build failure.

Scenario D: existing current-release project keeps normal build, rollback, query, and RAG behavior.

1. `8092` retained current release `local-realdata-bootstrap-20260512-1150`.
2. The current-release page did not show the cold-start rebuild warning because the project was not in bootstrap state.
3. Current-release release list, current pointer display, candidate map, and formal map all remained readable.
4. `POST /api/agents/default/game/knowledge/rag/answer` on `8092` returned `mode=answer`, `release_id=local-realdata-bootstrap-20260512-1150`, and `2` citations.

## 9. Validation Result

1. `git status --short --branch`
2. `cd console ; .\node_modules\.bin\tsc.cmd --noEmit -p tsconfig.json` -> passed.
3. `.\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_knowledge_release_router.py tests\unit\routers\test_game_knowledge_map_router.py tests\unit\routers\test_game_knowledge_rag_router.py` -> passed (`57 passed`).
4. `.\.venv\Scripts\python.exe -m pytest tests\unit\routers\test_game_index_impact.py` -> passed (`4 passed`).
5. Frontend test infrastructure note: `console/package.json` does not provide a dedicated frontend test script, so this slice used TypeScript validation plus manual browser smoke; no large new test framework was added.
6. `git diff --check`
7. touched-doc NUL check
8. keyword boundary review

## 10. Boundary Confirmation

1. No Ask schema change.
2. No provider, model, or api_key UI.
3. No RAG or provider ownership change.
4. No Knowledge release governance change.
5. No rollback semantic change.
6. No SVN sync, update, or commit change.
7. No relationship editor.
8. No graph canvas.
9. No broader map governance redesign.
10. No multi-step persisted onboarding system.
11. No P24 conclusion change.
12. No Lane G continuation.

## 11. Final Conclusion

1. Lane A.4 Knowledge cold-start UX closure is completed.
2. The Knowledge page now closes the 0-to-1 cold-start loop by exposing explicit rebuild action and refresh behavior while keeping release build as a separate explicit user step.
3. No backend endpoint was added.
4. The slice remains post-MVP pilot blocker hardening only.
5. Product conclusion remains pilot usable and not production ready.