# Lane A.1 Windows Controlled Pilot Smoke Receipt

Date: 2026-05-13
Status: partial
Scope: controlled Windows pilot smoke on latest main using the validated ltclaw.exe startup path, Lane C startup doctor, and the Knowledge first-release bootstrap bugfix without changing code

## 1. Final Result

1. final result: partial
2. mainline startup, health, project config, release status, Knowledge first-release bootstrap, and NumericWorkbench entry all passed in this round
3. baseline Ask in Chat knowledge-query mode reproduced a blocking runtime error and therefore prevented a full pass result
4. product state remains pilot usable and not production ready
5. this receipt does not claim production rollout or production ready

## 2. Commit And Environment

1. commit hash: `2a584632c18aa295b8905810e798cd8de1c3e574`
2. repo root: `E:\LTclaw2.0`
3. operating system: `Microsoft Windows NT 10.0.26200.0`
4. primary pilot runtime: `http://127.0.0.1:8092`
5. isolated bootstrap-validation runtime: `http://127.0.0.1:8093`
6. agent id: `default`
7. working dir for primary runtime: `C:\ltclaw-data-backed`
8. working dir for isolated runtime: `C:\ltclaw-data-backed-lane-a1`
9. console static dir: `E:\LTclaw2.0\console\dist`

## 3. Doctor Result

`python -m ltclaw_gy_x doctor windows-startup --host 127.0.0.1 --port 8092 --agent-id default` passed with the following operator-facing checks:

1. `QWENPAW_WORKING_DIR` explicitly set and existing: pass
2. `QWENPAW_CONSOLE_STATIC_DIR` explicitly set and existing: pass
3. resolved static dir with `index.html`: pass
4. target port `127.0.0.1:8092` available before startup: pass
5. local project directory configured and readable: `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
6. first-release bootstrap prerequisite already visible in the main runtime: `18` current table index entries available

Interpretation:

1. Lane C startup doctor is usable in the real Windows operator flow on latest main
2. the doctor output correctly surfaces the first-release prerequisite instead of hiding it behind a later failure

## 4. App Startup Result

Primary runtime startup command:

```powershell
E:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092
```

Observed result:

1. startup succeeded
2. backend served `console/dist`
3. server reported `Server ready in 0.065s` and background startup completed in `27.059s`
4. Uvicorn bound to `http://127.0.0.1:8092`
5. `default` and `LTCLAW-GY.X_QA_Agent_0.2` workspaces both started

Non-blocking startup notes:

1. `nacos-sdk-python` not installed warning remained non-blocking
2. `TortoiseSVN not installed` warnings remained non-blocking for this pilot path

## 5. Health / Project Config / Release Status

Primary runtime API checks:

1. `GET /api/agent/health` -> `200`, payload `status=healthy`, `runner=ready`
2. `GET /api/agents/default/game/project/config` -> `200`, project config loaded, `external_provider_config=null`
3. `GET /api/agents/default/game/project/user_config` -> `200`, `my_role=maintainer`
4. `GET /api/agents/default/game/project/storage` -> `200`, app-owned storage resolved under `C:\ltclaw-data-backed`
5. `GET /api/agents/default/game/knowledge/releases/status` -> `200`
6. current release in the primary runtime remained `win-op-r1-1778393517`
7. release history count in the primary runtime remained `2`
8. `GET /api/agents/default/game/index/status` -> `200`, `table_count=18`, `configured=true`

Interpretation:

1. P24 startup baseline remained intact on latest main
2. the Knowledge bootstrap bugfix did not regress the normal current-release baseline

## 6. Knowledge First-Release Smoke

To validate the no-current-release path without mutating the primary runtime, an isolated runtime was started on `127.0.0.1:8093` with a fresh working dir and the current `user_config` / `project_config` replayed into it.

Observed sequence:

1. isolated runtime health -> `200`
2. isolated `release status` before any build -> `200` with `current=null`, `history=[]`
3. `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` before any current table indexes -> `400`
4. error detail before indexes existed: `Current table indexes are required to build the first knowledge release`
5. `POST /api/agents/default/game/index/rebuild` -> `200`, indexed `18` files/tables
6. isolated `index status` after rebuild -> `200`, `table_count=18`
7. `POST /api/agents/default/game/knowledge/releases/build-from-current-indexes` after rebuild -> `200`
8. bootstrap release id created successfully: `lane-a1-bootstrap-20260513`
9. isolated `release status` after bootstrap -> `200`, history contains `lane-a1-bootstrap-20260513` as an available release and still no current pointer
10. isolated `GET /api/agents/default/game/knowledge/map/candidate` after bootstrap but before set-current -> `404` with `No current knowledge release is set`

Interpretation:

1. the first-release deadlock is no longer present
2. the prerequisite failure is now explicit and operator-readable when current table indexes are missing
3. after indexes exist, first-release bootstrap succeeds on a fresh runtime without a saved formal map and without an existing current release
4. candidate-map behavior after bootstrap remains consistent with existing current-release semantics and is not changed by this slice

## 7. Ask / RAG Baseline

RAG baseline that passed:

1. `POST /api/agents/default/game/knowledge/query` with `DaShenScore 折算群分数是什么` -> `200`
2. response mode was `current_release_keyword`
3. response used current release `win-op-r1-1778393517`
4. response returned a grounded result for table `DaShenScore`

Ask baseline that failed in the real UI flow:

1. opened `http://127.0.0.1:8092/chat`
2. switched Chat mode to `知识查询`
3. submitted `DaShenScore 折算群分数是什么？`
4. request entered the normal Chat flow and invoked `game_describe_field` and `game_query_tables`
5. Chat then failed with `AGENT_UNKNOWN_ERROR`
6. visible error text: `Unknown agent error: TypeError: The tool function must return a ToolResponse object, or an AsyncGenerator/Generator of ToolResponse objects, but got <class 'dict'>`

Interpretation:

1. release-backed RAG retrieval itself is still working
2. the interactive Chat Ask path for knowledge-query mode is currently regressed on latest main
3. because this is a real operator-facing baseline failure, the round is recorded as `partial` rather than `pass`

Minimal repair suggestion only, not executed in this round:

1. align `game_query_tables` and `game_describe_field` in `src/ltclaw_gy_x/agents/tools/gamedev_tools.py` with the runtime tool contract so they return `ToolResponse` objects instead of raw `dict`
2. re-run the exact same Chat knowledge-query prompt after that contract fix

## 8. NumericWorkbench Baseline

NumericWorkbench baseline checks passed:

1. `GET /numeric-workbench` returned `200`
2. backend served the expected frontend assets for the page
3. browser snapshot showed the session list page rendered with `默认会话` and `继续会话`
4. the page still stated that the workflow is draft-only and does not write formal knowledge release automatically
5. `GET /api/agents/default/game/workbench/context?tableIds=EquipEnhance&limitPerTable=3` -> `200`
6. `POST /api/agents/default/game/workbench/preview` for `Item / row_id=1000001 / field=小类型 / new_value=9` -> `200`, dry-run item `ok=true`

Interpretation:

1. NumericWorkbench entry remains usable in the latest main pilot flow
2. this round did not perform any new UX change, publish, or formal release write

## 9. Cleanup

Cleanup actions at close of the smoke run:

1. both LTCLAW app processes started for this round were terminated after evidence capture
2. no `LTCLAW_RAG_API_KEY` secret was injected in this round
3. therefore there was no live secret value to rotate or redact at teardown time
4. the temporary runtime working dir created for isolated bootstrap validation was removed after the run

## 10. Boundaries Preserved

This round did not do any of the following:

1. change RAG or provider ownership
2. add frontend provider, model, or api_key UI
3. change Ask schema
4. touch SVN sync, update, or commit paths
5. continue Lane G
6. claim production rollout
7. claim production ready

## 11. Final Conclusion

1. conclusion: `partial`
2. Lane C doctor is usable in the real Windows pilot startup flow on latest main
3. P24 startup baseline remains usable on latest main
4. the Knowledge first-release bootstrap bugfix is validated in a fresh no-current-release runtime, including the explicit missing-table-index prerequisite error and the post-index bootstrap success path
5. NumericWorkbench baseline remains usable
6. latest main remains pilot usable and not production ready
7. the remaining blocker discovered in this round is the Chat `知识查询` Ask path runtime tool-return mismatch