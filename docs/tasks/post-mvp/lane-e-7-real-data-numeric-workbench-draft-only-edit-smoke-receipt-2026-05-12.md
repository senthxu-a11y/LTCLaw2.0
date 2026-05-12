# Lane E.7 Real-Data NumericWorkbench Draft-Only Edit Smoke Receipt (2026-05-12)

## Scope

- Target: use the real local data project to verify the citation-to-NumericWorkbench edit workflow end to end.
- Required slices:
  - found target from real citation
  - lightweight dirty edit
  - save session
  - export draft dry-run
- Boundaries respected:
  - no SVN command run
  - no publish
  - no formal release write
  - no backend/API/schema change
  - no NumericWorkbench business-logic change

## Runtime

- App startup command:
  - `.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8099`
- App port:
  - `8099`
- Runtime URL:
  - `http://127.0.0.1:8099/game-project`
- Startup log file:
  - `e:\LTclaw2.0\logs\lane-e-7-runtime-smoke-8099-20260512.log`
- Startup log confirmed packaged static dir:
  - `E:\LTclaw2.0\src\ltclaw_gy_x\console`

## Real-Data Preconditions

- Local project remained the real Windows dataset:
  - `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
- Current release in GameProject remained:
  - `local-realdata-bootstrap-20260512-1150`
- Release counts observed in GameProject:
  - `table_schema = 18`
  - `doc_knowledge = 0`
  - `script_evidence = 0`

## Entry Path

### Citation source check

- Asked in GameProject:
  - `EquipEnhance 表里有哪些字段？`
- Result:
  - `answer`
  - `table_schema` citation returned for `EquipEnhance`
  - `manifest` citation returned for release `local-realdata-bootstrap-20260512-1150`

### Open in workbench

- Clicked `Open in workbench` from the `EquipEnhance` table_schema citation.
- NumericWorkbench opened on the real citation target route with context including:
  - table `EquipEnhance`
  - row `5`
  - citation id `citation-001`

## NumericWorkbench Boundary Evidence

- Workbench header/subtitle still stated draft-only behavior.
- Compact status bar showed:
  - `Draft-only`
  - `Dry-run`
  - `No auto-publish. No formal knowledge release write. Save and export behavior stays manual.`
- Citation status bar showed:
  - `Opened from a RAG citation`
  - `table: EquipEnhance`
  - `row: 5`
  - `Citation: EquipEnhance (配置表/EquipEnhance.csv)`
  - `Focused citation target in current table Table: EquipEnhance, row: 5`

## Dirty Edit Smoke

- Located row `5` in `EquipEnhance` and edited one numeric field manually.
- Edited field:
  - `强化所需金钱`
- Value change:
  - `71 -> 72`
- Result after pressing Enter:
  - dirty count changed from `0` to `1`
  - right-side dirty list showed one manual change item:
    - table `EquipEnhance`
    - row `5`
    - field `强化所需金钱`
    - delta `71 -> 72`

## Save Session Smoke

- Clicked `保存当前会话`.
- Result:
  - success toast appeared:
    - `已保存到本地会话：默认会话`
  - header save button became disabled afterward
  - compact status changed to `本地会话已保存`
- Scope note:
  - save affected only the local workbench session state
  - dirty change remained available for later export/review as expected

## Export Draft Dry-Run Smoke

- Clicked `导出草稿` from the dirty list panel.
- Draft modal opened with explicit boundary text:
  - `This exports a draft proposal only. It does not publish automatically or write formal knowledge release.`
- Export preview correctly summarized the single change:
  - `EquipEnhance / 5 / 强化所需金钱`
  - `71 -> 72`
- Confirmed export.
- Result:
  - success toast appeared:
    - `草案已生成`

## SVN / Publish Statement

- SVN not tested
- no SVN command run
- no publish action executed
- no formal knowledge release write was triggered in this smoke

## Final Result

- final result: `pass`
- summary: the real-data citation-to-NumericWorkbench workflow succeeded end to end on packaged runtime. A real `EquipEnhance` citation opened the correct table/row target, one lightweight manual dirty edit (`71 -> 72`) was recorded, local session save succeeded, and export draft dry-run succeeded with explicit draft-only / no-publish / no-formal-release boundaries preserved.