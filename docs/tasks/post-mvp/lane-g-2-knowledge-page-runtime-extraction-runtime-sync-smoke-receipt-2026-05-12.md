# Lane G.2 Knowledge Page Runtime Sync Smoke Receipt

- Date: 2026-05-12
- Scope: Lane G.2 runtime asset sync and smoke rerun only
- Commit: none
- Runtime launch: `e:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8102`
- Result: fail

## Allowed scope applied

- Rebuilt `console/dist` from current workspace frontend.
- Synced generated frontend assets into `src/ltclaw_gy_x/console`, which is the runtime `STATIC_DIR` on Windows.
- No SVN commands were executed.
- No backend, schema, API, NumericWorkbench, or other business-behavior changes were made in this runtime-sync phase.
- One pre-sync source-level import-path correction in `console/src/pages/Game/Knowledge/index.tsx` remained necessary so the frontend build could succeed, but it did not alter business behavior.

## Build and packaged asset sync

1. Build source: `console/dist`
2. Active packaged entry after sync:
   - `src/ltclaw_gy_x/console/index.html` now points to `/assets/index-Cu4rBtaC.js`
3. Packaged asset verification after sync confirmed the runtime now serves the canonical G.1/G.2 bundle:
   - `index-Cu4rBtaC.js` contains `/game/project`, `/game/knowledge`, `/game/map`, `/game/advanced`, `/game/advanced/svn`
   - redirect `/game -> /game/project`
   - redirect `/game-project -> /game/project`
   - redirect `/svn-sync -> /game/advanced/svn`
   - lazy import for `../pages/Game/Knowledge/index.tsx`
   - `GameProject-BB0ClO1v.js` contains the Project-page Knowledge CTA text and `Open Knowledge page`
   - `index-Clu_Arre.js` contains `Knowledge Release Status`, RAG status UI, citations block, and `Knowledge Status`
4. Node syntax-check over packaged `.js` assets completed without reported syntax errors.
5. `git diff --check` returned no output.

## Runtime evidence

1. Startup log confirmed the active static root is still the packaged directory:
   - `STATIC_DIR: E:\LTclaw2.0\src\ltclaw_gy_x\console`
2. `http://127.0.0.1:8102/game/knowledge` rendered the dedicated Knowledge page successfully.
3. `http://127.0.0.1:8102/game/advanced/svn` rendered successfully.
4. `http://127.0.0.1:8102/numeric-workbench` rendered successfully.
5. `http://127.0.0.1:8102/svn-sync` redirected to `http://127.0.0.1:8102/game/advanced/svn` successfully.
6. `http://127.0.0.1:8102/game/project` did not render the Project page. Instead, the app-level error boundary rendered `页面出现异常`.

## Failing behavior

- Browser console on `/game/project` reported:
  - `ReferenceError: Modal is not defined`
  - top frame: `assets/GameProject-BB0ClO1v.js`
- This corresponds to the source page using `<Modal>` while the top-level imports only include:
  - `Alert, Select, Space, Tag, Tooltip, Typography` from `antd`
- Source evidence:
  - `console/src/pages/Game/GameProject.tsx` uses `<Modal>` near the create-agent wizard block.
  - `console/src/pages/Game/GameProject.tsx` does not import `Modal` from `antd`.

## Smoke checklist

- App shell starts on `http://127.0.0.1:8102`: pass
- Packaged runtime serves synced canonical frontend assets: pass
- `/game/project` renders Project page: fail
- `/game/knowledge` renders Knowledge page: pass
- `/game/advanced/svn` renders Advanced SVN page without 404: pass
- `/numeric-workbench` opens: pass
- `/svn-sync` compat redirect reaches `/game/advanced/svn`: pass
- Structured query panel can open from Knowledge page: pass
- Workbench handoff button from Knowledge page navigates to `/numeric-workbench`: pass
- RAG request from Knowledge page returns a runtime result block: pass
- Citation list returned from tested RAG question: no; the tested question returned `依据不足` and `没有返回引用`
- SVN actions executed: no

## Page observations

### Project page

- Not blank anymore; the stale packaged-asset blocker is resolved.
- Current regression is a real frontend runtime error on the canonical Project route.
- Because the Project page crashes during render, runtime confirmation that formal-map editing remains available only there could not be completed in this smoke rerun.

### Knowledge page

- Dedicated Knowledge route is active and owns runtime blocks for:
  - Knowledge Release Status
  - RAG ask flow
  - structured query panel
  - workbench handoff button
  - readonly candidate/saved formal map summaries under `Knowledge Status`
- Tested RAG question: `哪些系统和技能成长有关？`
- Observed result:
  - state `依据不足`
  - release id `local-realdata-bootstrap-20260512-1150`
  - warning `No grounded context was available for a safe answer.`
  - citations block rendered `没有返回引用`

## Classification

This rerun is classified as `fail`, not `blocked`.

Reason:

- The stale packaged frontend blocker has been removed.
- The runtime is now serving the synced canonical G.1/G.2 assets from `src/ltclaw_gy_x/console`.
- The remaining issue is a concrete frontend regression on the canonical Project route: missing `Modal` at runtime.