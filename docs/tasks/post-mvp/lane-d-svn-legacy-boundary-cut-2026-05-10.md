# Lane D: SVN Phase 0/1 Legacy Boundary Cut

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Make clear that SVN is a legacy or admin source-control adapter, not the knowledge runtime line.
2. Hide ordinary SVN main entry points from normal product navigation.
3. Reduce new knowledge code references to `svn_root` naming while preserving old compatibility.

## Why This Lane Matters

1. The accepted MVP already proved that knowledge runtime is local-first and app-owned rather than SVN-driven.
2. Leaving SVN visually central would confuse future work and risk architectural drift back into the runtime line.
3. This lane isolates legacy source-control concerns without deleting old compatibility surfaces.

## Entry Conditions

1. The current accepted baseline already treats SVN as not a knowledge runtime dependency.
2. Current pilot usage is stable enough that legacy-boundary cleanup can be handled as a scoped follow-on slice.
3. The slice must preserve existing compatibility and must not reopen SVN write flows.

## Allowed Scope

1. Docs boundary for SVN legacy position.
2. Frontend navigation hiding for ordinary `SvnSync` entry points.
3. Small backend helper naming around `local project directory` or `project_root` that internally reads legacy SVN-named fields when required.
4. Comments marking `game_svn.py` as a legacy or admin source-control surface.

## Forbidden Scope

1. Do not delete `svn_client.py`, `svn_watcher.py`, `svn_committer.py`, or `game_svn.py`.
2. Do not add SVN credential UI.
3. Do not add SVN commit or update.
4. Do not make source revision the knowledge release version.
5. Do not reconnect RAG, query, formal map, or release build to SVN.

## Expected Effect

1. Ordinary planner and knowledge flows stop presenting SVN as the primary product line.
2. Future SVN work, if any, is clearly admin, audit, or source-control scope.

## Minimum Validation

1. Re-check the touched navigation, docs, or helper naming boundary.
2. If frontend or backend code changes are required, run the narrowest focused validation for the touched legacy boundary.
3. Confirm no SVN commit or update path was enabled by the slice.
4. Run `git diff --check`, touched-doc NUL check, and keyword boundary review.

## Closeout Wording

1. Use `Lane D SVN legacy boundary cut completed` only for a scoped boundary cleanup.
2. Do not write `SVN commit integration enabled` or `SVN update integration enabled`.
3. State clearly that SVN remains deferred as a runtime dependency.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane D: SVN Phase 0/1 legacy boundary cut。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-d-svn-legacy-boundary-cut-2026-05-10.md 和 docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md。
目标是把 SVN 定位成 legacy/admin source-control adapter，而不是 knowledge runtime dependency。
不删除 SVN backend files，不加 credential，不加 commit/update，不把 RAG/query/formal map/release build 接回 SVN。
优先做 docs boundary、普通 SVN 导航隐藏、project-root resolver 命名收敛和 legacy 注释。
```
