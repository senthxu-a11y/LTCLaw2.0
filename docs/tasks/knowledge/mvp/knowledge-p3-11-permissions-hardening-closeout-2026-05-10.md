# Knowledge P3.11 Permissions Hardening Closeout

Date: 2026-05-10
Scope: backend permission hardening completion, final capability naming decision, frontend permission alignment, docs sync

## 1. Closeout Decision

P3.11 Permissions Hardening is completed for the current P0-P3 MVP slice.

This round does not continue external-provider work.

This round does not implement P20.

This round keeps external-provider frozen at P19 docs-only.

## 2. Code Review Conclusion

The pre-change review found that most of the P3 permission boundary was already implemented in backend routers and existing frontend gating.

The remaining hardening gap was not a broad missing permission layer.

The remaining gap was:

1. the checklist capability set no longer matched actual backend and frontend names
2. `knowledge.map.read` and `knowledge.candidate.read` or `knowledge.candidate.write` were already real runtime capability names in source, tests, and frontend state
3. NumericWorkbench export or draft-create UX existed, but its backend proposal-create path was not yet separately gated by `workbench.test.export`
4. docs, frontend, and backend therefore did not yet expose one final P3.11 naming decision

## 3. Final Capability Naming Decision

The final MVP capability vocabulary after P3.11 is:

1. `knowledge.read`
2. `knowledge.build`
3. `knowledge.publish`
4. `knowledge.map.read`
5. `knowledge.map.edit`
6. `knowledge.candidate.read`
7. `knowledge.candidate.write`
8. `workbench.read`
9. `workbench.test.write`
10. `workbench.test.export`

Naming conclusion:

1. `knowledge.map.read` is retained.
2. It is not replaced by broad `knowledge.read` in this slice because map review remains a narrower governance-oriented read surface than release listing, current-release status, query, and RAG read.
3. `knowledge.candidate.read` and `knowledge.candidate.write` are retained.
4. They are not replaced by `workbench.candidate.mark` in this slice because the current backend already distinguishes candidate read from candidate write, and collapsing those routes into one capability would change semantics.
5. `workbench.candidate.mark` is therefore treated as not adopted in the current MVP capability set.
6. `workbench.test.export` is retained and is now a real enforced gate for the existing workbench draft-export or proposal-create path.

## 4. Backend Endpoint To Capability Matrix

Current backend route matrix after P3.11 is:

1. `GET /game/knowledge/releases` -> `knowledge.read`
2. `GET /game/knowledge/releases/current` -> `knowledge.read`
3. `GET /game/knowledge/releases/status` -> `knowledge.read`
4. `GET /game/knowledge/releases/{release_id}/manifest` -> `knowledge.read`
5. `POST /game/knowledge/query` -> `knowledge.read`
6. `POST /game/knowledge/rag/context` -> `knowledge.read`
7. `POST /game/knowledge/rag/answer` -> `knowledge.read`
8. `POST /game/knowledge/releases/build` -> `knowledge.build`
9. `POST /game/knowledge/releases/build-from-current-indexes` -> `knowledge.build`
10. `POST /game/knowledge/releases/{release_id}/current` -> `knowledge.publish`
11. `GET /game/knowledge/map/candidate` -> `knowledge.map.read`
12. `GET /game/knowledge/map` -> `knowledge.map.read`
13. `PUT /game/knowledge/map` -> `knowledge.map.edit`
14. `GET /game/knowledge/test-plans` -> `workbench.read`
15. `POST /game/knowledge/test-plans` -> `workbench.test.write`
16. `GET /game/knowledge/release-candidates` -> `knowledge.candidate.read`
17. `POST /game/knowledge/release-candidates` -> `knowledge.candidate.write`
18. `POST /game/change/proposals` -> `workbench.test.export`

Important boundary notes:

1. build release still does not imply publish or rollback
2. publish or rollback still does not imply build
3. map read still does not imply map edit
4. candidate read still does not imply candidate write
5. workbench test write still does not imply knowledge.publish
6. workbench test export is now separate from workbench test write
7. local trusted fallback remains unchanged and still allows requests when explicit capability context is absent
8. missing explicit capability still returns `Missing capability: xxx`

## 5. Frontend Action To Capability Matrix

Current frontend action matrix after P3.11 is:

1. GameProject build release button -> `knowledge.build`
2. GameProject set current or rollback button -> `knowledge.publish`
3. GameProject release status or query or RAG ask surfaces -> `knowledge.read`
4. GameProject candidate-map and saved-formal-map load or refresh -> `knowledge.map.read`
5. GameProject save formal map and save formal-map status changes -> `knowledge.map.edit`
6. GameProject build-modal release-candidate list loading -> `knowledge.candidate.read`
7. NumericWorkbench page read entry and existing data-load gating -> `workbench.read`
8. NumericWorkbench ordinary fast-test write and save-test-plan flow remain under `workbench.test.write`
9. NumericWorkbench draft export or proposal-create button now uses `workbench.test.export`

Frontend boundary notes:

1. frontend disabled state now matches backend capability names for build, publish, map review, map save, workbench read, workbench write, and workbench export
2. missing capability copy remains concise and action-scoped
3. permission errors still do not mention administrator acceptance for ordinary fast-test flows
4. no provider, model, or API key UI was added

## 6. Read-Only User Summary

A read-only user with only `knowledge.read` and without the other write or governance capabilities can:

1. read release list, current release, release status, release manifest, query, and RAG answer surfaces

That user cannot:

1. build release
2. publish or rollback release
3. read candidate-map or saved-formal-map review surfaces unless `knowledge.map.read` is also granted
4. save formal map
5. read or write release-candidate state unless `knowledge.candidate.read` or `knowledge.candidate.write` is also granted
6. write test plans unless `workbench.test.write` is granted
7. export workbench draft proposals unless `workbench.test.export` is granted

## 7. Workbench Flow Boundary Summary

The workbench fast-test boundary after P3.11 is:

1. `workbench.read` allows existing NumericWorkbench read surfaces and test-plan read surfaces
2. `workbench.test.write` allows test-plan write without requiring `knowledge.publish`
3. `workbench.test.export` now separately controls the existing draft-export or proposal-create path
4. workbench write or export still does not imply build or publish
5. workbench flow therefore remains grantable without `knowledge.publish`

## 8. Actual Modified Files

Backend source changed in this slice:

1. `src/ltclaw_gy_x/app/routers/game_change.py`

Frontend source changed in this slice:

1. `console/src/pages/Game/NumericWorkbench.tsx`

Tests changed in this slice:

1. `tests/unit/routers/test_game_change_router.py`

Docs changed in this slice:

1. `docs/tasks/knowledge/mvp/knowledge-p3-11-permissions-hardening-closeout-2026-05-10.md`
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

## 9. Validation Result

Focused backend validation completed in this slice:

1. `tests/unit/routers/test_game_change_router.py` -> `7 passed in 2.05s`

Completed closeout validation summary for the full P3.11 slice:

1. focused backend pytest across affected permission routers and tests -> `86 passed in 2.26s`
2. focused new export-gate router validation -> `7 passed in 2.05s`
3. frontend TypeScript no-emit passed
4. targeted frontend ESLint passed with 0 errors and only pre-existing warnings remaining
5. `git diff --check` passed
6. touched-file NUL check passed
7. keyword and boundary review passed

## 10. Boundary Confirmation

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
10. move ordinary fast-test behavior into formal knowledge by default
11. use administrator acceptance for runtime provider or credential approval
12. add SVN commit or update integration
13. perform a broad refactor

## 11. Next Step

The next recommended step is:

1. P3.12 P3 Review Gate

The next recommended step is not:

1. external-provider P20