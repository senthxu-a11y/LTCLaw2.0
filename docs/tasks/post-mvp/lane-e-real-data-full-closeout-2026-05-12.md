# Lane E Real-Data Full Closeout

Date: 2026-05-12
Status: pass
Mode: validation only
Repo: e:\LTclaw2.0
Branch: main

## Scope

This closeout validated the full Lane E real-data loop on a Windows target machine using the packaged local app runtime and real local project data.

Boundaries observed throughout this closeout:

1. Validation only. No backend, API, schema, or frontend source code change.
2. No commit created during this closeout task.
3. No SVN command run.
4. No publish action performed.
5. No formal knowledge release was published to any remote target.

## Environment

Windows packaged runtime launches used during closeout:

1. .venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8102
2. .venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8103

Runtime observations:

1. STATIC_DIR resolved to E:\LTclaw2.0\src\ltclaw_gy_x\console
2. Nacos SDK missing warning appeared but did not block validation.
3. TortoiseSVN not installed warning remained non-blocking.

Real local dataset:

1. E:\工作\资料\腾讯内部资料\中小型游戏设计框架

App-owned project storage used for evidence:

1. C:\Users\Admin\.ltclaw_gy_x\game_data\projects\中小型游戏设计框架-25f012e7d33d\project

## Baseline

Baseline current release before closeout validation:

1. local-realdata-bootstrap-20260512-1150

Baseline release counts:

1. table_schema = 18
2. doc_knowledge = 0
3. script_evidence = 0

Saved formal map baseline hash before closeout:

1. sha256:fb5ba6249991e9f80941918ce52c4ada0ef6c81243773441a1b81ea899a79e9b

## Phase Results

### Phase 0. Startup and environment confirmation

Result: pass

1. Packaged app started successfully on 8102 and later on 8103.
2. Browser-accessible pages included GameProject, Chat, and NumericWorkbench.
3. Packaged frontend assets were served from the expected STATIC_DIR.

### Phase 1. RAG and empty doc context validation

Result: pass

1. Baseline release answered table-structure questions correctly.
2. Question used: EquipEnhance 表里有哪些字段？
3. Baseline citations were table_schema plus manifest.
4. Empty document-library behavior remained correct for real data with no docs indexed.
5. Question used: 装备强化的说明在哪里？
6. Returned status remained insufficient_context with explicit no-document-library guidance.

### Phase 2. NumericWorkbench draft-only edit flow

Result: pass

1. Citation entry opened NumericWorkbench against real local data.
2. EquipEnhance row 5 field 强化所需金钱 was inspected and edited in draft-only flow.
3. Dirty state recorded the change from 71 to 72.
4. Session save succeeded.
5. The workbench remained explicitly draft-only and dry-run oriented.
6. No auto-publish or formal-release side effect occurred.

### Phase 3. Proposal visibility, detail, and preview

Result: pass

1. Exported draft remained visible through Chat's 策划改动提案 entry.
2. Proposal list showed persisted draft rows.
3. Proposal detail reopened successfully.
4. Dry-run preview remained recoverable with before 71 and after 72.

### Phase 4. Formal map status-only edit and revert

Result: pass

1. Saved formal map remained available in GameProject.
2. Status-only editing controls were usable.
3. A minimal status-only edit was saved successfully.
4. The status was then reverted successfully to the original state.
5. This flow did not build or publish a release by itself.

### Phase 5. Safe build from current indexes with saved formal map

Result: pass

Created release:

1. local-realdata-formalmap-smoke-20260512-1534

Build result:

1. Safe build succeeded from current server-side indexes.
2. Release snapshot directory existed under the app-owned project storage.
3. Snapshot contents included indexes, manifest.json, map.json, and release_notes.md.

Saved formal map evidence:

1. Saved formal map GET returned hash sha256:fb5ba6249991e9f80941918ce52c4ada0ef6c81243773441a1b81ea899a79e9b.
2. Saved formal map counts were systems 15, tables 18, docs 0, scripts 0, relationships 0.

Snapshot map evidence:

1. Release map.json release_id was local-realdata-formalmap-smoke-20260512-1534.
2. Snapshot map counts were systems 15, tables 18, docs 0, scripts 0, relationships 0.
3. Snapshot map counts matched the saved formal map counts.

### Phase 6. Set current to the new release and regression check

Result: pass

1. Set current switched the current release pointer to local-realdata-formalmap-smoke-20260512-1534.
2. This action did not rebuild, publish, or invoke SVN.
3. Post-switch RAG still answered the table-structure question correctly.
4. Citation composition changed from the earlier table_schema plus manifest shape to manifest plus map for this smoke release.
5. This citation shift was treated as acceptable because answer correctness held and the release had a saved formal map snapshot.

### Phase 7. Rollback to baseline and regression check

Result: pass

1. Rollback switched the current release pointer back to local-realdata-bootstrap-20260512-1150.
2. Rollback did not rebuild, publish, or invoke SVN.
3. Post-rollback RAG again answered the table-structure question correctly.
4. Citation composition returned to the earlier table_schema plus manifest shape.

### Phase 8. Restart persistence

Result: pass

Validation restarted the packaged app on port 8103 after stopping the 8102 runtime.

Confirmed after restart:

1. Current release persisted as local-realdata-bootstrap-20260512-1150.
2. Saved formal map remained visible with hash sha256:fb5ba6249991e9f80941918ce52c4ada0ef6c81243773441a1b81ea899a79e9b.
3. Saved formal map counts remained systems 15, tables 18, docs 0, scripts 0, relationships 0.
4. Proposal drawer still showed persisted draft entries.
5. Proposal detail still reopened and showed the EquipEnhance update_cell change for row 5 field 强化所需金钱 with new_value 72.
6. NumericWorkbench homepage still showed the persisted 默认会话 entry.
7. Observed workbench session state after restart: session container persisted, while the homepage summary showed 0 项修改, 0 张表, 0 条对话 at the time of restart validation.

## Final State

Final current release at closeout end:

1. local-realdata-bootstrap-20260512-1150

New release created during closeout and left available in release list:

1. local-realdata-formalmap-smoke-20260512-1534

Formal map outcome:

1. Saved formal map existed before and after closeout.
2. Status-only edit succeeded.
3. Revert to original status also succeeded.

Safe build outcome:

1. Succeeded.
2. Produced a releasable snapshot with map.json and manifest.json.

Rollback outcome:

1. Succeeded.
2. Restored the baseline current release pointer.

Proposal persistence outcome:

1. Passed across page reload and across full app restart.

## Non-Actions Confirmed

1. No SVN command run.
2. No publish performed.
3. No source code change.
4. No backend/API/schema change.
5. No commit created as part of this closeout.

## Deferred Items

The following remain intentionally outside this closeout scope:

1. SVN lane validation
2. doc_knowledge source availability and supported file-format expansion
3. relationship editor, graph canvas, and candidate-map editing beyond status-only operations

## Final Verdict

Lane E real-data full closeout result: pass

The Lane E real-data loop is closed on this Windows machine for the validated scope: startup, baseline RAG behavior, NumericWorkbench draft-only edit flow, proposal visibility and preview, saved formal map persistence, safe build from current indexes with saved formal map, set current, rollback, and restart persistence.