# Lane E.9 Real-Data Formal Map Smoke Receipt (2026-05-12)

## Scope

- Goal: verify the current real-data formal map MVP loop end to end:
  - candidate map visible
  - Save as formal map works
  - saved formal map becomes visible
- Boundaries respected:
  - no SVN command run
  - no SVN sync/update/commit click
  - no publish
  - no set-current click
  - no release build click
  - no backend/API/schema change
  - no frontend source change
  - no commit
  - formal map write to app-owned state was allowed for this smoke

## Runtime

- App startup command:
  - `.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8101`
- App port:
  - `8101`
- Startup log:
  - `e:\LTclaw2.0\logs\lane-e-9-runtime-smoke-8101-20260512.log`
- STATIC_DIR confirmed from runtime log:
  - `E:\LTclaw2.0\src\ltclaw_gy_x\console`

## Real-Data Baseline

- Local data directory remained:
  - `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
- Current release baseline in GameProject:
  - `local-realdata-bootstrap-20260512-1150`
- Release counts shown in current release panel:
  - `table_schema = 18`
  - `doc_knowledge = 0`
  - `script_evidence = 0`

## Formal Map Review Entry

- Opened:
  - `http://127.0.0.1:8101/game-project`
- Located `Formal map review` section.
- Clicked `刷新` inside that section to refresh/load map review data.
- Did not click any of the following:
  - `Build release`
  - `Current` / set-current controls
  - `Publish`
  - `Rollback to previous`
  - any SVN sync/update/commit control

## Candidate Map Result

- candidate map visible: `yes`
- candidate map release id:
  - `local-realdata-bootstrap-20260512-1150`
- candidate map summary shown in UI:
  - `systems 15`
  - `tables 18`
  - `docs 0`
  - `scripts 0`
  - `relationships 0`
- Empty doc/script state handling:
  - UI showed `No docs`
  - UI showed `No scripts`
  - this was treated as expected real-data state, not a failure

## Save As Formal Map Result

- Clicked `Save as formal map` in `Formal map review`.
- Save result:
  - server log recorded `PUT /api/agents/default/game/knowledge/map HTTP/1.1" 200 OK`
  - `Saved formal map` panel became populated immediately after save
- Save-success evidence observed after save:
  - `Saved formal map` section visible
  - `map_hash` visible
  - `updated_at` visible
  - `updated_by` visible
  - no API failure toast/message observed

## Saved Formal Map Metadata

- saved formal map visible: `yes`
- saved formal map hash:
  - `sha256:fb5ba6249991e9f80941918ce52c4ada0ef6c81243773441a1b81ea899a79e9b`
- saved formal map updated_at:
  - `2026/5/12 15:08:07` in UI
  - `2026-05-12T07:08:07.213936Z` via read-only GET
- saved formal map updated_by:
  - `Default`
- saved formal map summary in UI:
  - `systems 15`
  - `tables 18`
  - `docs 0`
  - `scripts 0`
  - `relationships 0`

## Candidate vs Saved Map Consistency

- Consistency check result: `pass`
- UI steady state showed saved formal map counts aligned with candidate map counts.
- Read-only GET verification also matched:
  - candidate release id `local-realdata-bootstrap-20260512-1150`
  - candidate counts `15 / 18 / 0 / 0 / 0`
  - formal counts `15 / 18 / 0 / 0 / 0`

## Status-Only Edit Observation

- status-only edit entry present: `yes`
- Evidence:
  - `Save status changes` button visible in `Saved formal map`
  - system rows exposed status combobox controls after save
- Action taken:
  - read-only confirmation only
  - no status value changed
  - no `Save status changes` write attempted

## Optional API Recheck

- Performed read-only GET only:
  - `GET /api/agents/default/game/knowledge/map/candidate`
  - `GET /api/agents/default/game/knowledge/map`
- GET result summary:
  - candidate mode: `candidate_map`
  - formal mode: `formal_map`
  - both endpoints returned counts consistent with the UI

## Browser / API / Log Notes

- No browser-side error toast was observed during refresh, save, or post-save review.
- No formal-map API failure message was observed in the UI.
- Runtime log showed formal-map GET/PUT traffic returning `200 OK`.
- Unrelated environment/runtime warnings still appeared in startup logs:
  - `Nacos SDK ... is not available`
  - `TortoiseSVN not installed`
- These warnings did not block formal map candidate loading or save.

## Boundary Statement

- no SVN command run
- no SVN sync/update/commit click
- no publish
- no set-current click
- no release build click

## Final Result

- final result: `pass`
- summary: on real local data and packaged runtime at port `8101`, the formal map MVP loop worked as expected. The candidate map for release `local-realdata-bootstrap-20260512-1150` was visible with `tables 18` and empty doc/script states handled normally, `Save as formal map` persisted app-owned formal map state, the saved formal map became visible with hash/update metadata, status-only edit controls appeared, and no SVN, publish, set-current, or release-build actions were performed.