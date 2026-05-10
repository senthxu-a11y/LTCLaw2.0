# Knowledge P3.10 Release Rollback UX/API Closeout

Date: 2026-05-10
Scope: backend plus minimal frontend MVP rollback UX/API

## 1. Closeout Decision

P3.10 Release Rollback UX/API is completed for the current MVP slice.

This round does not continue external-provider work.

This round does not implement P20.

This round keeps external-provider frozen at P19 docs-only.

## 2. Code Review Conclusion

The pre-change code review showed that the repository already had the core release primitives needed for rollback MVP:

1. Release history storage already existed under the app-owned release store.
2. Current pointer storage already existed in `releases/current.json` through `set_current_release(...)`.
3. Current-release keyword query already read through `get_current_release(...)`.
4. RAG current-release context already read through `get_current_release(...)`.
5. Existing GameProject UI already showed current release, release list, and manual `set current` action.
6. Existing router capability checks already used `knowledge.read` for read surfaces and `knowledge.publish` for `POST /releases/{release_id}/current`.

The actual gap was not missing rollback mechanics.

The actual gap was missing MVP rollback status UX/API around:

1. structured current or previous or history status
2. backend current marker in release history
3. backend previous-release derivation
4. explicit frontend rollback-to-previous affordance
5. explicit rollback confirmation
6. explicit no-previous safe state

## 3. Actual Modified Backend Files

Backend source files changed in this slice:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_release.py`

Backend behavior added in this file:

1. `GET /game/knowledge/releases/status` now returns structured release status.
2. The status payload now includes `current`, `previous`, and `history`.
3. Release history items now include `release_id`, `created_at`, `label`, `is_current`, and `indexes`.
4. History is sorted by `(created_at, release_id)` descending.
5. `previous` is derived as the first older available release after the current release in that history order.
6. The existing `POST /game/knowledge/releases/{release_id}/current` endpoint remains the rollback setter.
7. The existing setter still reuses `set_current_release(...)` and still only changes the current pointer.
8. Read and setter endpoints now map unexpected metadata failures to safe error responses instead of leaking internals.

## 4. Actual Modified Frontend Files

Frontend files changed in this slice:

1. `console/src/api/types/game.ts`
2. `console/src/api/modules/gameKnowledgeRelease.ts`
3. `console/src/pages/Game/GameProject.tsx`

Frontend behavior added in this slice:

1. The release panel now reads structured release status from `GET /game/knowledge/releases/status`.
2. The panel now shows current release and previous release explicitly.
3. The panel keeps the existing release history list.
4. The panel now exposes an explicit `Rollback to previous` button.
5. The rollback button is disabled when no previous release exists.
6. The rollback button is disabled when the caller lacks `knowledge.publish` under explicit capability context.
7. Switching current release now asks for explicit confirmation before calling the backend setter.
8. After a successful rollback or selected-release switch, the panel refreshes release status.
9. The frontend still adds no provider, model, or API key UI.

## 5. Actual Modified Tests

Tests changed in this slice:

1. `tests/unit/game/test_knowledge_release_store.py`
2. `tests/unit/routers/test_game_knowledge_release_router.py`
3. `tests/unit/game/test_knowledge_rag_context.py`

New or expanded coverage in this slice includes:

1. rollback updates only the current pointer
2. rollback does not modify release artifacts
3. rollback does not modify pending test plans
4. rollback does not modify release candidates
5. rollback does not modify working formal map
6. missing release id fails without creating a new current pointer
7. release status returns current marker
8. previous release can be derived from structured history
9. no previous release is safe
10. read capability is required for release status when explicit capability context exists
11. publish capability is required for rollback when explicit capability context exists
12. status endpoint hides internal metadata details on failure
13. current-release keyword query follows restored current release after rollback
14. RAG current-release context follows restored current release after rollback

## 6. Release History Read Path

Release history is now read through the existing app-owned release store, then shaped by the release router status endpoint.

Implementation detail:

1. `list_releases(project_root)` still reads manifests from the existing release store.
2. `GET /game/knowledge/releases/status` sorts those manifests by `(created_at, release_id)` descending.
3. The router compares each history item against `get_current_release(project_root)` to mark `is_current`.
4. The router labels the current item as `current` and all others as `available`.

The status response is structured, not a loose dict.

## 7. Previous Release Definition

In this slice, `previous release` is defined as:

1. the first older available release after the current release in the router's descending `(created_at, release_id)` history order

Implications:

1. If current release is the newest release, previous is the next older release.
2. If current release has already been rolled back to an older release, previous becomes the next older available release behind it.
3. If there is no such older release, `previous` is `null` and the frontend shows a safe disabled state.

## 8. Set Current Release Implementation

This slice reuses the existing current setter.

Implementation detail:

1. Rollback still uses `POST /api/agents/{agentId}/game/knowledge/releases/{release_id}/current`.
2. The route still requires `knowledge.publish`.
3. The route still calls existing `set_current_release(project_root, release_id)`.
4. The setter still first loads the target manifest to ensure the release exists.
5. Only after that validation does it atomically write `releases/current.json`.

Validation outcome:

1. existing release id succeeds
2. missing release id returns 404
3. invalid release id still returns validation error

## 9. Rollback Mutation Boundary

This slice confirms and regression-tests that rollback only changes the current pointer.

Rollback in this slice does not:

1. create a new release
2. rebuild release artifacts
3. publish a release
4. modify `manifest.json`
5. modify `map.json`
6. modify release notes
7. modify pending test plans
8. modify release candidates
9. modify `working/formal_map.json`
10. modify formal map approval state

## 10. Current-Release Query And RAG Behavior

This slice verifies the runtime read effect of rollback.

Observed result:

1. `query_current_release(...)` still reads through `get_current_release(...)`.
2. `build_current_release_context(...)` still reads through `get_current_release(...)`.
3. After `set_current_release(...)` points back to an older release, both keyword query and RAG context immediately read the restored current release.

This slice adds no delayed rebuild step and no cache-invalidation side workflow.

## 11. Permission Boundary

Permission behavior in this slice is:

1. read-only status surfaces require `knowledge.read` when explicit capability context exists
2. rollback setter requires `knowledge.publish` when explicit capability context exists
3. a caller with `knowledge.build` but without `knowledge.publish` still cannot rollback
4. a caller with `knowledge.publish` can rollback
5. in local trusted mode with no capability context, legacy local behavior remains unchanged

Frontend behavior follows the same boundary:

1. read-only users can view release status
2. read-only users cannot trigger rollback
3. no-previous state disables rollback even for publish-capable callers

## 12. No-Previous Behavior

When no previous release exists:

1. backend status response returns `previous = null`
2. frontend shows `No previous knowledge release`
3. frontend disables `Rollback to previous`
4. no internal error is thrown

## 13. Validation Result

Backend validation completed in this slice:

1. `50 passed in 1.90s`
2. Command scope:
3. `tests/unit/game/test_knowledge_release_store.py`
4. `tests/unit/routers/test_game_knowledge_release_router.py`
5. `tests/unit/game/test_knowledge_rag_context.py`
6. `tests/unit/routers/test_game_knowledge_query_router.py`

Frontend validation completed in this slice:

1. local binary `./node_modules/.bin/tsc --noEmit -p tsconfig.app.json` passed
2. local binary `./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/api/modules/gameKnowledgeRelease.ts src/api/types/game.ts` passed
3. editor diagnostics on the touched frontend files reported no errors

Environment note:

1. the `pnpm` wrapper path was blocked by `pnpm approve-builds` or ignored-build-script environment enforcement in this workspace
2. validation still completed successfully through the local `node_modules/.bin` binaries

## 14. Boundary Confirmation

This slice does not:

1. continue external-provider work
2. implement P20
3. add real HTTP transport
4. add real provider connection
5. change provider or model selection
6. change Ask request schema
7. give router provider-selection authority
8. add frontend provider, model, or API key controls
9. turn ordinary RAG Q&A into a write flow
10. move ordinary fast-test behavior into formal knowledge acceptance
11. reuse admin acceptance for runtime provider or credential approval
12. touch SVN commit or update integration
13. perform a broad refactor

## 15. Next Step

The next recommended step is:

1. P3.11 Permissions Hardening

The next recommended step is not:

1. external-provider P20