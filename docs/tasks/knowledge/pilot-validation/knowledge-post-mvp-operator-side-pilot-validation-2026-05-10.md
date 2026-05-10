# Post-MVP Operator-Side Pilot Validation

Date: 2026-05-10
Scope: operator-side pilot validation on the target machine / target runtime environment after final handoff packaging

## 1. Overall Result

Operator-side pilot pass with known limitations.

Why this passes:

1. the target runtime was already live and healthy on the target machine
2. local project directory configuration was present and readable
3. real index rebuild, formal map read/save, release build, set current, rollback, query, RAG, structured query, NumericWorkbench draft export or dry-run, and draft test-plan paths all executed successfully on the target environment
4. focused backend regression and frontend static validation reran green on the target machine

Why this is still only a pilot pass with known limitations:

1. the system remains not production ready
2. no real provider, real HTTP transport, or real LLM is configured
3. SVN CLI is absent on this machine, but that did not block full rescan fallback
4. NumericWorkbench still exposes the pre-existing chat model selector inside the workbench chat shell, but that is not GameProject RAG provider rollout and no API key UI was required for the validated operator flow

## 2. Target Environment

Target machine / target runtime facts validated in this round:

1. operating system: macOS 26.4.1
2. architecture: arm64
3. repo path: `/Users/Admin/LTCLaw2.0`
4. Python: `3.12.13`
5. Node: `v26.0.0`
6. npm: `11.12.1`
7. pnpm: `11.0.8`
8. backend runtime port: `127.0.0.1:8092`
9. backend startup command in the live process:
   - `QWENPAW_WORKING_DIR=/tmp/ltclaw-data-backed`
   - `QWENPAW_CONSOLE_STATIC_DIR=/Users/Admin/LTCLaw2.0/console/dist`
   - `/Users/Admin/LTCLaw2.0/.venv/bin/ltclaw app --host 127.0.0.1 --port 8092`
10. frontend serving mode: backend-served production static bundle from `console/dist`

## 3. Configuration

Target-machine configuration confirmed in this round:

1. local project directory: `/Users/Admin/CodeBuddy/20260501110222/test-data`
2. runtime root: `/tmp/ltclaw-data-backed`
3. app-owned project storage root: `/tmp/ltclaw-data-backed/game_data/projects/test-data-201b6e029661`
4. current user role: `maintainer`
5. user config path: `/tmp/ltclaw-data-backed/game_data/user/game_user.yaml`
6. static bundle path: `/Users/Admin/LTCLaw2.0/console/dist`
7. SVN CLI: absent on this machine
8. TortoiseSVN: not present / not applicable on this macOS target machine
9. absence of SVN/Tortoise did not block operator validation because `POST /game/index/rebuild` and the app-owned current-index path both worked through full rescan fallback

## 4. Validation Matrix

### A. Environment / Startup

Validated:

1. `ltclaw doctor` passed the target runtime root, static dir, API health, version, and console-over-HTTP checks
2. `GET /api/agent/health` returned `{"status":"healthy","mode":"daemon_thread","runner":"ready"}`
3. `GET /api/version` returned `1.0.0`
4. `GET /api/agents/default/game/index/status` returned `configured=true`
5. `GET /api/agents/default/game/project/storage` resolved the expected app-owned storage tree and the configured local project directory
6. no SVN commit/update step was required to start or use the validated operator flow
7. doctor reported no custom provider warnings and no active LLM slot, which is acceptable for this pilot slice because real provider / real HTTP / real LLM remain out of scope

### B. Index Rebuild

Validated:

1. `POST /api/agents/default/game/index/rebuild` completed successfully on the target environment
2. `GET /api/agents/default/game/index/status` reported `table_count=8`
3. `GET /api/agents/default/game/index/tables` returned `total=8`
4. `GET /api/agents/default/game/index/tables/角色属性表/rows?offset=0&limit=3` returned real rows
5. sampled row `4001` returned `weaponId=1002`, `armorId=1006`, and `skill1Id=2001`
6. current-index files existed under the project-level app-owned path:
   - `project/indexes/table_indexes.json`
   - `project/indexes/dependency_graph.json`
   - `project/indexes/registry.json`

### C. Formal Map

Validated:

1. `GET /api/agents/default/game/knowledge/map` returned the saved formal map successfully
2. the saved formal map contained `1` system and `8` active tables
3. `PUT /api/agents/default/game/knowledge/map` succeeded in a reversible status-edit check
4. the validation temporarily changed `table:Buff效果表` from `active` to `deprecated`, confirmed save mode `formal_map_saved`, and then restored it back to `active`
5. after restore, the formal map still contained `8` active tables and `updated_by=operator-side-validation-restore`
6. this formal-map validation did not build a release and did not publish a release

### D. Release / Current / Rollback

Validated:

1. `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` created release `operator-side-1778385716`
2. `POST /api/agents/default/game/knowledge/releases/operator-side-1778385716/current` succeeded
3. release status then showed `current=operator-side-1778385716` and `previous=pilot-final-reg-r2-1778382520`
4. rollback succeeded by switching current back to `pilot-final-reg-r1-1778382520`
5. after rollback, release status again showed `current=pilot-final-reg-r1-1778382520` and `previous=pilot-real-data-r2-api`
6. `history_count_after=5`
7. pre-existing release `manifest.json` mtimes stayed unchanged across set-current and rollback for:
   - `pilot-final-reg-r2-1778382520`
   - `pilot-final-reg-r1-1778382520`
   - `pilot-real-data-r2-api`
   - `pilot-real-data-r1-direct`
8. this confirms rollback remained a current-pointer switch only and did not rebuild, publish, or modify existing release artifacts

### E. Query / RAG

Validated:

1. `POST /api/agents/default/game/knowledge/query` with `weaponId` returned `1` result from `角色属性表.xlsx`
2. `POST /api/agents/default/game/knowledge/rag/context` returned `mode=context`, `release_id=pilot-final-reg-r1-1778382520`, `1` chunk, and `1` citation
3. `POST /api/agents/default/game/knowledge/rag/answer` returned `mode=answer`, `release_id=pilot-final-reg-r1-1778382520`, `1` citation, and no warning
4. the returned answer stayed grounded to current-release table-schema evidence
5. no `no_current_release` response appeared in the normal operator path because a current release existed
6. a release-status snapshot before and after query/RAG remained unchanged, confirming ordinary RAG Q&A did not write release state

### F. Structured Query

Validated in both API and browser flow:

1. browser UX kept structured query behind explicit `Open structured query`
2. opening the panel did not auto-submit
3. `Submit structured query` stayed disabled before input
4. after entering `weaponId`, explicit submit returned `result_mode=exact_field`
5. API validation also returned `mode=exact_field` for `weaponId`
6. API validation returned `mode=exact_table` for `角色属性表`
7. the path remained read-only and did not write formal knowledge or release state

### G. NumericWorkbench

Validated:

1. browser navigation from GameProject `Go to workbench` opened `/numeric-workbench`
2. NumericWorkbench session list loaded and the default session opened successfully
3. the session workflow remained local/session-oriented: select tables, edit, inspect impact, save current session, export draft
4. `导出草稿` was visible and stayed disabled at `0` pending changes
5. API-level draft proposal create succeeded with `status=draft`
6. proposal dry-run succeeded and returned a real change from `before=1002` to `after=1003` for `角色属性表.weaponId`
7. test-plan create succeeded with `status=draft`
8. test-plan list succeeded and returned `listed_count=1`
9. release status remained unchanged before and after draft proposal create/dry-run and test-plan create/list, confirming draft export and draft test plans do not enter formal knowledge by default
10. ordinary fast-test / test-plan create did not require `knowledge.publish`

### H. Permissions / Boundaries

Confirmed in this round:

1. the current runtime role in the target environment is `maintainer`
2. source/router audit still matches the final capability matrix:
   - `knowledge.read`
   - `knowledge.build`
   - `knowledge.publish`
   - `knowledge.map.read`
   - `knowledge.map.edit`
   - `knowledge.candidate.read`
   - `knowledge.candidate.write`
   - `workbench.read`
   - `workbench.test.write`
   - `workbench.test.export`
3. live operator actions that succeeded in this round aligned with those capability boundaries
4. read-only negative-path denial was not live-replayed on this target machine because web auth is disabled and the current runtime uses local trusted fallback when explicit capability context is absent
5. the focused backend regression reran green at `179 passed`, preserving the route-level capability enforcement already accepted in the mainline
6. rollback still requires the publish boundary, and draft export still uses the workbench export boundary

### I. Frontend Boundary Smoke

Validated:

1. GameProject loaded with release status visible
2. rollback UX was visible
3. GameProject RAG copy still says the entry point does not expose provider or model selection
4. structured query remained explicit-open and explicit-submit
5. NumericWorkbench loaded and the default session opened
6. no API key UI was required anywhere in the validated operator flow
7. no SVN commit/update step appeared as an MVP-required mainflow action

Observed limitation that does not block this pilot pass:

1. the global app shell and NumericWorkbench chat still expose an existing `Select model` control
2. that control is not GameProject RAG provider rollout, does not add API key entry, and did not change Ask request shape
3. this round therefore preserves the no-real-provider boundary while recording that pre-existing workbench chat model-selection UI still exists

### J. Build / Static Verification

Validated on the target machine:

1. focused backend pytest reran at `179 passed in 2.09s`
2. frontend TypeScript no emit passed
3. targeted ESLint returned `0 errors / 10 existing warnings`
4. warnings remained the existing `react-hooks/exhaustive-deps` warnings in `NumericWorkbench.tsx`
5. production build passed
6. Vite reported the same non-blocking circular chunk warning only

## 5. Deviations From Previous Data-Backed Receipt

Compared with the previous data-backed receipt:

1. the target dataset path is the same: `/Users/Admin/CodeBuddy/20260501110222/test-data`
2. the runtime root is the same: `/tmp/ltclaw-data-backed`
3. the target environment already had a live app process on `8092`, so this round validated the existing running target instance rather than bootstrapping a brand-new one from zero
4. this round created one additional release for validation: `operator-side-1778385716`
5. this round added a reversible formal-map status-edit check that was not explicitly recorded in the previous receipt
6. this round added live draft test-plan create/list confirmation in addition to draft proposal create/dry-run
7. this round explicitly confirmed that SVN CLI is absent on the target machine and that full rescan fallback still makes the operator path usable
8. this round also recorded that NumericWorkbench still shows the pre-existing chat `Select model` control, while GameProject RAG continues not to expose provider/model/API key controls

## 6. Fixes If Any

No source, frontend, or test fix was needed in this round.

1. no backend business source changed
2. no frontend source changed
3. no tests changed
4. this closeout is docs-only

## 7. Boundaries Preserved

This round explicitly preserves the following boundaries:

1. not production ready
2. `P20` deferred
3. no real provider
4. no real HTTP transport
5. no real LLM
6. no provider/model/API key UI added for GameProject RAG
7. Ask request schema unchanged
8. SVN Phase 0/1 deferred
9. SVN commit/update not enabled
10. test plans do not enter formal knowledge by default
11. ordinary RAG Q&A does not write release
12. administrator acceptance is only about formal knowledge governance, not ordinary fast test or runtime provider control

## 8. Next Recommendation

Recommended next step after this target-machine validation:

1. start controlled pilot usage on the target machine
2. keep operator runbooks aligned with the validated startup path and app-owned storage path
3. if SVN work is needed later, open SVN Phase 0/1 as a separate scoped slice
4. if production hardening is needed later, open a separate post-MVP production-hardening scope decision instead of extending this pilot closeout