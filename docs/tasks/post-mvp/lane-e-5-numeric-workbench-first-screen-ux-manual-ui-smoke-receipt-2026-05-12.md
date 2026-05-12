# Lane E.5 NumericWorkbench First-Screen UX Manual UI Smoke Receipt

Date: 2026-05-12
Status: blocked
Scope: manual browser smoke for E.5 NumericWorkbench first-screen compression and citation target state

## 1. Final Result

1. final_result: blocked
2. blocker_type: runtime frontend instance did not reflect current E.5 frontend source
3. source_changes_made_during_smoke: no

## 2. Environment

1. OS: Windows
2. repo root: `E:\LTclaw2.0`
3. existing reachable app before smoke: `http://127.0.0.1:8092`
4. fresh LTClaw app started during smoke: `http://127.0.0.1:8094`
5. attempted current-source frontend dev server: `http://127.0.0.1:5173`

## 3. Startup And Access Methods Attempted

### 3.1 Existing app reuse on 8092

1. port probe confirmed `8092` returned HTTP 200
2. GameProject RAG query was executed successfully in browser
3. returned citation used table `DaShenScore`, source path `配置表/DaShenScore.csv`, row `4`

### 3.2 Current-source Vite dev server on 5173

Command used:

1. `Push-Location .\console; $env:VITE_API_BASE_URL='http://127.0.0.1:8092'; & .\node_modules\.bin\vite.cmd --host 127.0.0.1 --port 5173`

Observed result:

1. Vite started successfully
2. browser requests from `5173` to `8092` were blocked by CORS
3. this prevented a valid manual smoke against the current-source frontend through Vite

### 3.3 Fresh LTClaw app on 8094

Command used:

1. `.\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8094`

Observed server log:

1. app started successfully
2. log reported `STATIC_DIR: E:\LTclaw2.0\src\ltclaw_gy_x\console`

## 4. What Was Checked In Browser

### 4.1 RAG citation retrieval

Browser flow on `8092`:

1. opened `http://127.0.0.1:8092/game-project`
2. submitted question `DaShenScore 表主要包含什么内容？请只根据引用片段回答。`
3. received citation for `DaShenScore`
4. citation metadata visible in UI included source path `配置表/DaShenScore.csv` and row `4`

### 4.2 NumericWorkbench route checks

WorkBench routes opened in browser used:

1. `http://127.0.0.1:8092/numeric-workbench?...`
2. `http://127.0.0.1:8094/numeric-workbench?...`

Representative citation-target query used:

1. `table=DaShenScore`
2. `from=rag-citation`
3. `citationId=citation-001`
4. `citationTitle=DaShenScore`
5. `citationSource=配置表/DaShenScore.csv`
6. `row=4`
7. `field=大神段位排名`

## 5. Actual Observations

### 5.1 Existing 8092 app did not expose E.5 UI

Observed in browser and DOM text:

1. the page still showed the old workbench header/subtitle shape
2. the page still showed the old `当前 0 项待保存` toolbar count
3. the new compact citation status bar strings were not present
4. `Focused citation target in current table` was not present
5. `Citation target not found in current table` was not present
6. `Citation table could not be opened` was not present
7. the old large-top layout was still effectively what the running frontend exposed

### 5.2 Vite current-source frontend was not usable for smoke

Observed in browser console:

1. requests to `http://127.0.0.1:8092/api/...` failed due missing `Access-Control-Allow-Origin`
2. this blocked using the current-source frontend served from `5173` for manual UI smoke

### 5.3 Fresh 8094 LTClaw app still served stale frontend behavior

Observed in browser text after launching `8094`:

1. the page still did not contain the new compact status-bar strings
2. the page still showed old subtitle text ending in `保存当前会话`
3. the expected E.5 citation target strings were absent
4. the route did not provide a valid browser surface for verifying E.5 found / row-missing / field-missing / table-missing states

## 6. Exact Blocker

Exact blocker:

1. a valid browser runtime serving the current E.5 frontend implementation was not available during this smoke
2. the pre-existing `8092` instance was stale relative to current `console/src` changes
3. the fresh `8094` app instance served static frontend assets from `src/ltclaw_gy_x/console`, which did not reflect the current E.5 `console/src` implementation under test
4. the current-source Vite server on `5173` could not be used as a fallback because backend API requests to `8092` were blocked by CORS

Because of this blocker, the following checks could not be validly passed or failed against the actual E.5 implementation in browser:

1. compact citation status bar visibility for the current implementation
2. found-state copy `Focused citation target in current table`
3. row-missing copy `Citation target not found in current table`
4. field-missing copy `Citation target not found in current table`
5. table-missing copy `Citation table could not be opened`
6. empty-table-list final-edge behavior in a runtime known to include the current E.5 code

## 7. Validation Notes

1. no source files were edited during this smoke attempt
2. the blocker is environmental/runtime-serving, not a newly discovered source-level regression in E.5 itself
3. smoke should be rerun only after the runtime serves the current `console/src` frontend implementation

## 8. Recommended Next Step

1. refresh or rebuild the frontend assets that the LTClaw app actually serves from `src/ltclaw_gy_x/console`, or provide a same-origin dev path for current `console/src`
2. rerun the manual UI smoke without widening E.5 scope once the runtime matches the implementation under test