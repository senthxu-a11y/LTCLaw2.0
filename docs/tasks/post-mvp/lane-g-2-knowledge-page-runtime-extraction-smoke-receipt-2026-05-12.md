# Lane G.2 Knowledge Page Runtime Extraction Smoke Receipt

- Date: 2026-05-12
- Scope: Lane G.2 route/runtime smoke only
- Source changes: none
- Commit: none
- Runtime launch: `e:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8110`
- Result: blocked

## Blocking reason

The running local app instance is serving a legacy packaged frontend from `src/ltclaw_gy_x/console`, not the current workspace frontend source under `console/`. Because of that asset mismatch, the runtime cannot validate the G.1/G.2 canonical routes introduced in source.

## Evidence

1. Server startup log reports `STATIC_DIR: E:\LTclaw2.0\src\ltclaw_gy_x\console`.
2. Canonical G.1/G.2 routes render an empty outlet only:
   - `/game/project` -> `<div class="page-content"></div>`
   - `/game/knowledge` -> `<div class="page-content"></div>`
   - `/game/advanced/svn` -> `<div class="page-content"></div>`
3. Existing legacy routes still render full pages:
   - `/game-project` renders the old monolithic Project page, including `Knowledge Release Status`, `知识问答`, and `Formal map review` in the same page.
   - `/svn-sync` renders the legacy sync status page.
   - `/knowledge-base` renders the legacy placeholder knowledge base page.
   - `/numeric-workbench` renders normally.
4. Packaged asset inspection under `src/ltclaw_gy_x/console/assets` shows the legacy route map and imports, including:
   - sidebar/path map using `/game-project`, `/svn-sync`, `/knowledge-base`, `/numeric-workbench`
   - route table redirecting `/game` -> `/game-project`
   - lazy imports for `../pages/Game/GameProject.tsx`, `../pages/Game/SvnSync.tsx`, `../pages/Game/KnowledgeBase.tsx`
   - no canonical route ownership for `/game/project`, `/game/knowledge`, or `/game/advanced/svn`
5. No decisive browser JS error was captured during the smoke run; the visible symptom is route non-match against the currently served packaged frontend.

## Smoke checklist

- App shell starts on `http://127.0.0.1:8110`: pass
- `/game/project` renders Project page: blocked by legacy packaged frontend; empty outlet observed
- `/game/knowledge` renders Knowledge page: blocked by legacy packaged frontend; empty outlet observed
- `/numeric-workbench` opens: pass
- `/game/advanced/svn` opens without 404: blocked by legacy packaged frontend; empty outlet observed
- SVN actions executed: no
- RAG/citation flow exercised: no, blocked before canonical Knowledge page rendered

## Classification

This smoke run is classified as `blocked`, not `fail`.

Reason: the active local runtime is not serving the current canonical route bundle from the workspace frontend source, so the observed blank canonical routes do not isolate a Lane G.2 source regression. Validating G.2 runtime behavior would require rebuilding or syncing the packaged frontend assets used by `src/ltclaw_gy_x/console`, which is outside this smoke scope and was explicitly not performed.