# Post-MVP Data-Backed Pilot Validation Closeout

Date: 2026-05-10

## Scope

Goal: validate that the accepted P0-P3 MVP can run on a real local project directory with real current-index data and at least one current knowledge release, rather than only in isolated degraded smoke.

This round stayed inside the approved pilot scope:

1. local-first project configuration
2. current indexes from real local files
3. conservative formal-map save and reuse
4. knowledge release build, set-current, and rollback
5. current-release query and RAG
6. structured query
7. NumericWorkbench draft export path

This round did not reopen deferred scope:

1. `P20`
2. real external provider or real HTTP transport
3. relationship editor or graph canvas
4. SVN commit integration as a pilot blocker

## Real Environment Used

Dedicated validation working root:

1. `/tmp/ltclaw-data-backed`

Real local project directory:

1. `/Users/Admin/CodeBuddy/20260501110222/test-data`
2. contains 8 real `.xlsx` tables:
   - `Buff效果表.xlsx`
   - `元素表.xlsx`
   - `关卡掉落表.xlsx`
   - `怪物表.xlsx`
   - `技能伤害表.xlsx`
   - `等级成长表.xlsx`
   - `装备表.xlsx`
   - `角色属性表.xlsx`

Dedicated runtime launch:

1. `QWENPAW_WORKING_DIR=/tmp/ltclaw-data-backed`
2. `QWENPAW_CONSOLE_STATIC_DIR=/Users/Admin/LTCLaw2.0/console/dist`
3. `/Users/Admin/LTCLaw2.0/.venv/bin/ltclaw app --host 127.0.0.1 --port 8092`

Configured runtime state:

1. `my_role=maintainer`
2. `svn_local_root=/Users/Admin/CodeBuddy/20260501110222/test-data`
3. project config saved into app-owned storage, not the source project root

## Real Blockers Found And Fixed

### 1. Configured `/game/index/status` crashed

Observed behavior:

1. once a real local project directory was configured, `GET /api/agents/default/game/index/status` returned `500`
2. stack trace showed `NameError: name 'svn_root' is not defined`

Root cause:

1. `load_doc_chunk_index(...)` in `src/ltclaw_gy_x/game/retrieval.py` used `svn_root` without resolving it locally

Fix:

1. resolve `svn_root = _resolve_svn_root(game_service)` inside `load_doc_chunk_index(...)`
2. use the same resolved root for both chunk-path and status-path reads

Validation:

1. after restart, the same status endpoint returned `200`
2. response included `configured=true` instead of crashing

### 2. `build-from-current-indexes` could not see rebuilt indexes

Observed behavior:

1. `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` returned `400`
2. detail was `Current table indexes are not available`
3. meanwhile rescan had already written session-cache artifacts successfully

Root cause:

1. `IndexCommitter` wrote current indexes into session cache
2. safe release build reads project-level app-owned current-index paths
3. project-level `table_indexes.json` was not being written under the new app-owned path model

Fix:

1. `src/ltclaw_gy_x/game/index_committer.py` now always writes project-level current-index artifacts
2. SVN commit attempts remain gated so only files actually inside the working copy are eligible for commit

Validation:

1. after restart and `POST /game/index/rebuild`, these files existed under project-level storage:
   - `project/indexes/table_indexes.json`
   - `project/indexes/dependency_graph.json`
   - `project/indexes/registry.json`
2. `POST /game/knowledge/releases/build-from-current-indexes` then succeeded through the HTTP API

## Executed Validation

### 1. Real index generation

Executed:

1. `POST /api/agents/default/game/index/rebuild`

Result:

1. scanned files: 8
2. indexed tables: 8
3. `GET /api/agents/default/game/index/status` returned:
   - `configured=true`
   - `table_count=8`
   - `doc_count=0`
   - `code_file_count=0`

Real-data evidence:

1. `GET /api/agents/default/game/index/tables` listed 8 indexed tables
2. `GET /api/agents/default/game/index/tables/角色属性表/rows?offset=0&limit=3` returned real rows
3. sample row proved actual data access rather than metadata-only indexing:
   - row `4001`
   - `weaponId=1002`
   - `armorId=1006`

### 2. Formal map save and reuse

Executed:

1. save minimal formal map covering all 8 indexed tables under one conservative system group
2. read formal map back through `GET /api/agents/default/game/knowledge/map`

Result:

1. formal map save succeeded
2. formal map read succeeded
3. saved map contains 8 active table refs and no docs or scripts

### 3. Knowledge release build and current pointer

Executed:

1. direct service-path bootstrap build: `pilot-real-data-r1-direct`
2. HTTP API build-from-current-indexes: `pilot-real-data-r2-api`
3. set current to each release via publish endpoint
4. rollback by switching current back to the previous release

Result:

1. both releases were built successfully
2. `GET /api/agents/default/game/knowledge/releases/status` reported correct current/previous/history state
3. rollback remained a pointer switch only and worked as intended

Artifact counts for the built releases:

1. `table_schema`: 8
2. `doc_knowledge`: 0
3. `script_evidence`: 0
4. `candidate_evidence`: 0

### 4. Current-release query and RAG

Executed:

1. `POST /api/agents/default/game/knowledge/query` with `weaponId`
2. `POST /api/agents/default/game/knowledge/rag/context`
3. `POST /api/agents/default/game/knowledge/rag/answer`

Result:

1. current-release keyword query returned `角色属性表.xlsx`
2. RAG context returned a current-release citation from `indexes/table_schema.jsonl`
3. RAG answer returned grounded output with the same citation and no warning

### 5. Structured query

Executed:

1. `POST /api/agents/default/game/index/query` with `{q: "weaponId", mode: "auto"}`
2. `POST /api/agents/default/game/index/query` with `{q: "角色属性表", mode: "auto"}`

Result:

1. field query returned `mode=exact_field`
2. table query returned `mode=exact_table`
3. the exact table result included real source path, primary key, row count, and indexed fields

### 6. NumericWorkbench fast-test/export path

Executed:

1. create a draft proposal against real table `角色属性表`
2. operation: update row `4001`, field `weaponId`, new value `1003`
3. run proposal dry-run

Result:

1. proposal create succeeded with `status=draft`
2. dry-run returned real value transition `before=1002`, `after=1003`
3. release history remained unchanged, confirming draft export does not automatically enter the formal knowledge release

## Pilot Judgment

### Pass

The MVP is pilot-usable for a real table-backed local project directory once the operator completes the expected environment setup.

Specifically validated:

1. a real local project directory can be configured
2. real current indexes can be generated from that directory
3. a conservative formal map can be saved and reused
4. at least one real current knowledge release can be built and switched
5. current-release query, structured query, and RAG all operate on real release data
6. NumericWorkbench draft export remains separate from formal knowledge governance

### Remaining limitations that are acceptable for this pilot

1. this environment had table data only, so `doc_knowledge` and `script_evidence` stayed empty
2. SVN watcher logs still report missing TortoiseSVN or CLI support on this machine, but force-full-rescan fallback was sufficient for pilot validation
3. this round still does not validate real provider rollout, real HTTP transport, or SVN commit flows

## Final Conclusion

The requested stricter validation goal is met:

1. a real local project directory was used
2. real current indexes were generated from that directory
3. at least one real current knowledge release existed and was exercised
4. release status, set-current, rollback, formal-map reuse, structured query, current-release query, RAG, and NumericWorkbench draft export all ran against that real data path

The two product blockers encountered in this stricter round were both narrow implementation defects in configured runtime paths, and both are now fixed in source:

1. `src/ltclaw_gy_x/game/retrieval.py`
2. `src/ltclaw_gy_x/game/index_committer.py`

## Final Regression Receipt Follow-Up

Status as of 2026-05-10 later round:

1. final regression receipt completed in `docs/tasks/knowledge-post-mvp-data-backed-final-regression-receipt-2026-05-10.md`
2. focused backend regression reran green at `179 passed`
3. frontend validation reran green apart from pre-existing NumericWorkbench warnings
4. real data-backed smoke reran green on the same local project directory and isolated runtime root
5. outcome remains `Data-backed pilot readiness pass.` and still not production ready