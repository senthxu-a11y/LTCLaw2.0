# Post-MVP Windows Operator-Side Pilot Validation

Date: 2026-05-10
Scope: operator-side pilot validation on the Windows target machine / target runtime environment after final handoff packaging, reusing the already accepted MVP/operator path without expanding scope

## 1. Overall Result

Windows operator-side pilot pass with known limitations.

Why this passes:

1. the target runtime was live and healthy on the Windows target machine
2. the target machine successfully saved and reused a real Chinese-path local project directory after switching request bodies to Python/urllib UTF-8 JSON
3. real index rebuild, formal map read/save, release build, set current, rollback by current-pointer switch, current-release query, current-release RAG, structured query, NumericWorkbench draft proposal dry-run, and draft test-plan create/list all executed successfully on the target environment
4. browser smoke, frontend TypeScript no-emit, targeted ESLint, and Windows-side production build rerun exposed no new blocking frontend issue for the validated operator flow

Why this is still only a pilot pass with known limitations:

1. the system remains not production ready
2. no real provider, real HTTP transport, or real LLM is configured
3. SVN CLI and TortoiseSVN are absent on this machine, but that did not block full rescan fallback
4. NumericWorkbench still exposes the pre-existing `Select model` control inside the workbench chat shell, but that is not GameProject RAG provider rollout and no API key UI was required for the validated operator flow
5. focused backend pytest was not rerun on this Windows machine because the configured venv does not include `pytest` (`No module named pytest`)

## 2. Target Environment

Target machine / target runtime facts validated in this round:

1. operating system: Windows 11 Pro `10.0.26200`
2. repo path: `E:\LTclaw2.0`
3. Python: `3.12.3`
4. Node: `v24.15.0`
5. npm: `11.12.1`
6. pnpm: not on `PATH`
7. backend runtime port: `127.0.0.1:8092`
8. backend startup command in the validated live process:
   - `QWENPAW_WORKING_DIR=C:\ltclaw-data-backed`
   - `QWENPAW_CONSOLE_STATIC_DIR=E:\LTclaw2.0\console\dist`
   - `.\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092`
9. `python -m ltclaw` did not work in this repo/runtime on the target machine and was not used for the validated path
10. frontend serving mode: backend-served production static bundle from `console/dist`

## 3. Configuration

Target-machine configuration confirmed in this round:

1. local project directory: `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
2. runtime root: `C:\ltclaw-data-backed`
3. app-owned project storage root: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d`
4. project config path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\project\config\project_config.yaml`
5. current-index path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\project\indexes`
6. user config path: `C:\ltclaw-data-backed\game_data\user\game_user.yaml`
7. workbench path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\agents\default\sessions\default\workbench`
8. proposal path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\agents\default\sessions\default\tools\proposals`
9. static bundle path: `E:\LTclaw2.0\console\dist`
10. SVN CLI: absent on this machine
11. TortoiseSVN: absent on this machine
12. absence of SVN/Tortoise did not block operator validation because `POST /game/index/rebuild` and the app-owned current-index path both worked through full rescan fallback

## 4. Validation Matrix

### A. Environment / Startup

Validated:

1. the Windows target runtime served backend APIs and backend-served `console/dist` successfully on `127.0.0.1:8092`
2. `GET /api/version` returned `1.0.0`
3. `GET /api/agents/default/game/index/status` returned `configured=true`
4. `GET /api/agents/default/game/project/storage` resolved the expected app-owned storage tree and the configured Chinese-path local project directory
5. no SVN commit/update step was required to start or use the validated operator flow
6. no API key UI was required anywhere in the validated operator flow

### B. Project Configuration / Chinese Path Handling

Validated:

1. saving target-machine `user_config` and `project/config` with a Chinese Windows local project path succeeded when the request body was sent as Python/urllib UTF-8 JSON
2. direct PowerShell JSON bodies were not reliable on this target machine for Chinese path payloads because the console encoding corrupted the path into `???`
3. after saving through Python/urllib UTF-8 JSON, the configured local project directory remained readable through the normal project/storage endpoints
4. this round therefore validates the Windows operator path with a real Chinese local project directory, while also recording the PowerShell encoding limitation as an operator-side workaround rather than a source fix

### C. Index Rebuild

Validated:

1. `POST /api/agents/default/game/index/rebuild` completed successfully on the target environment
2. the real Windows dataset indexed `18` tables, not the `8`-table Mac receipt dataset
3. `GET /api/agents/default/game/index/tables` returned `total=18`
4. sampled table rows returned real Windows-side data
5. current-index files existed under the project-level app-owned path:
   - `project/indexes/table_indexes.json`
   - `project/indexes/dependency_graph.json`
   - `project/indexes/registry.json`

### D. Formal Map

Validated:

1. a minimal formal map was saved successfully for the real Windows dataset
2. the saved formal map contained `1` system and `18` tables
3. `PUT /api/agents/default/game/knowledge/map` succeeded in a reversible status-edit check and was then restored
4. formal-map save remained separate from release build and release publish
5. candidate-map generation was release-based as designed and required a current release before use

### E. Release / Current / Rollback

Validated:

1. `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` created two Windows validation releases:
   - `win-op-r1-1778393517`
   - `win-op-r2-1778393517`
2. set-current succeeded on the new Windows release list
3. rollback succeeded by switching the current pointer back to the previous Windows release
4. after rollback, release status returned to `current=win-op-r1-1778393517`
5. browser and API evidence both showed rollback copy/behavior as current-pointer switch only
6. manifest mtimes for the release artifacts stayed unchanged across set-current and rollback, confirming no rebuild, publish, or release-artifact mutation occurred during rollback

### F. Query / RAG

Validated:

1. ordinary current-release query returned release-owned results on the Windows dataset
2. current-release RAG context and answer both executed successfully against the Windows current release
3. the returned RAG path remained grounded to current-release evidence and did not require a real provider or API key UI
4. release-status snapshots before and after ordinary query/RAG remained unchanged, confirming ordinary query and RAG did not write release state

### G. Structured Query

Validated in both API and browser flow:

1. browser UX kept structured query behind explicit `Open structured query`
2. opening the panel did not auto-submit
3. `Submit structured query` stayed disabled before input
4. Windows-side API validation returned `mode=exact_table` for `DaShenScore`
5. Windows-side API validation returned `mode=exact_field` for `折算群分数`
6. this round therefore records the actual Windows data example as `DaShenScore / 折算群分数`, not the Mac receipt's `weaponId`
7. the path remained read-only and did not write formal knowledge or release state

### H. NumericWorkbench

Validated:

1. browser navigation from GameProject `Go to workbench` opened `/numeric-workbench`
2. NumericWorkbench session list loaded and the default session opened successfully
3. the session workflow remained local/session-oriented: select tables, edit, inspect impact, save current session, export draft
4. `导出草稿` was visible and stayed disabled at `0` pending changes
5. API-level draft proposal create succeeded with `status=draft`
6. Windows-side dry-run succeeded on the real dataset for `Item`, `row_id=1000001`, `field=小类型`, from `before=1` to `after=9`
7. test-plan create succeeded with `status=draft`
8. test-plan list succeeded and returned the created draft-plan state successfully
9. release status remained unchanged before and after draft proposal create/dry-run and test-plan create/list, confirming draft export and draft test plans do not enter formal knowledge by default
10. ordinary fast-test / test-plan create did not require `knowledge.publish`

### I. Frontend Boundary Smoke

Validated:

1. GameProject loaded with release status visible
2. rollback UX was visible and explained as pointer switch only
3. GameProject RAG copy still says the entry point does not expose provider or model selection
4. structured query remained explicit-open and explicit-submit
5. NumericWorkbench loaded and the default session opened
6. NumericWorkbench still showed the pre-existing `Select model` control inside workbench chat
7. no API key UI was required anywhere in the validated operator flow
8. no SVN commit/update step appeared as an MVP-required mainflow action

Observed limitation that does not block this pilot pass:

1. the global app shell and NumericWorkbench chat still expose an existing model-selection surface
2. that surface is not GameProject RAG provider rollout, does not add API key entry, and did not change the validated operator path

### J. Build / Static Verification

Validated or explicitly waived on the target machine:

1. focused backend pytest was attempted on the Windows target machine but could not run because the configured venv does not include `pytest`
2. frontend TypeScript no-emit passed on the target machine
3. targeted ESLint returned `0 errors / 10 existing warnings`
4. the warnings remained existing `react-hooks/exhaustive-deps` warnings in `console/src/pages/Game/NumericWorkbench.tsx`
5. the Windows production build rerun exposed no new blocking error in this validation slice
6. the visible build warning remained the same non-blocking circular chunk warning only

## 5. Deviations From Previous Receipts

Compared with the previous Mac/operator and data-backed receipts:

1. the target machine is Windows rather than macOS
2. the local project directory is a different real dataset path: `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
3. the runtime root is `C:\ltclaw-data-backed`, not `/tmp/ltclaw-data-backed`
4. the validated startup command is `.\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092`, not `python -m ltclaw`
5. the Windows real dataset indexed `18` tables rather than the Mac receipt's `8`
6. this round records `DaShenScore / 折算群分数` as the real structured-query example rather than reusing the Mac `weaponId` example
7. this round required a Windows-specific operator workaround for Chinese-path JSON bodies: Python/urllib UTF-8 JSON instead of direct PowerShell JSON
8. focused backend pytest was not available in the Windows venv and is therefore explicitly waived in this closeout rather than reported green

## 6. Fixes If Any

No source, frontend, or test fix was needed in this round.

1. no backend business source changed
2. no frontend source changed
3. no tests changed
4. the only operational workaround was sending Chinese-path HTTP JSON bodies through Python/urllib UTF-8 requests on Windows
5. this closeout is docs-only

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

Recommended next step after this Windows target-machine validation:

1. start controlled pilot usage on the validated target machines
2. keep operator runbooks aligned with the validated Windows startup path, app-owned storage path, and Chinese-path JSON-body workaround
3. if SVN work is needed later, open SVN Phase 0/1 as a separate scoped slice
4. if production hardening is needed later, open a separate post-MVP production-hardening scope decision instead of extending this pilot closeout