# Knowledge P1 Gate Status

Date: 2026-05-07

Authority:

1. docs/plans/knowledge-architecture-handover-2026-05-06.md
2. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md
3. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
4. docs/tasks/knowledge/mvp/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
5. docs/tasks/knowledge/mvp/knowledge-p1-boundary-audit-2026-05-07.md

## Scope Snapshot

P0 is complete.

P1.1-P1.9d are complete for the current MVP slice:

1. Release path helpers.
2. Minimal release/map/manifest/test plan/release candidate models.
3. Release store, builders, service, release router, and current-release query router/service.
4. Release query path guard for manifest index path escape.
5. Safe backend `build-from-current-indexes` endpoint sourced from server-owned state.
6. Minimal frontend Knowledge Release Status UI in GameProject.
7. Minimal frontend release API wrapper for list/current/set-current/build-from-current-indexes.
8. Minimal frontend build modal/button bound only to the safe endpoint.

The completed frontend scope now includes P1.9a and P1.9d:

1. View current knowledge release.
2. View release list.
3. Set current release.
4. Build release via the safe server-side endpoint with narrow intent fields only.

The original full-payload build endpoint remains non-productized.

Gate interpretation:

1. P1 is complete for a local-first MVP loop in a trusted or single-user context.
2. P1 is not complete as a hardened multi-role governance surface.
3. Backend capability checks for build, set-current, full-payload build, and future map edit remain follow-up work.

## Verified Items

The current P1 gate results are:

1. Build release: passed.
2. Set current: passed.
3. Query current release: passed.
4. No raw source read in release query path: passed.
5. No SVN write/commit in new release query path: passed.
6. Old index/workbench representative regression: passed.
7. Safe build-from-current-indexes boundary: passed.
8. Frontend build button bound only to safe endpoint: passed.
9. Backend regression: `18 passed`.
10. Frontend release UI typecheck: passed.

## Risks And Notes

1. game_project.py and game_svn.py still have historical dirty changes in the worktree; any later touch to those files should be confirmed separately before editing.
2. The current build endpoint accepts a full derived payload and should still be treated as an internal skeleton, not a normal frontend build button target.
3. P1.8 current-release query is keyword-only; it is not RAG.
4. The current P1.9d build modal sends only `release_id` and `release_notes`; release candidate selection UX is still deferred.
5. Several Python files in this Windows workspace had DLP/NUL corruption and were rewritten as clean UTF-8 before the final regressions.
6. Release build and set-current still need backend role/capability checks before multi-user usage.
7. The frontend build button is not itself a security boundary; backend enforcement is still required.

## Recommendation For Next Step

P1 is now closed. The next recommended step is P2 test plan store:

1. Add app-owned test plan storage separate from release assets.
2. Keep release candidate selection separate from ordinary test plan state.
3. Reuse the same local-first boundary discipline: app-owned storage, no raw source copy, no SVN write in normal test-plan flows.
