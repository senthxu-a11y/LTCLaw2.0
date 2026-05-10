# Task Folder Archive Plan

Date: 2026-05-10

Status: planning record updated after the docs/tasks knowledge-folder organization slice.

## Current Assessment

The Knowledge/RAG P0-P3 MVP task line is complete and has passed data-backed, Mac operator-side, and Windows operator-side pilot validation.

However, `docs/tasks` should not be treated as globally complete. The folder still contains older or separate task lines such as:

1. `MIGRATION_CHECKLIST.md`
2. `R6-writeback-tasks.md`
3. `phase1-tasks.md`

Those files were not validated as part of the Knowledge/RAG MVP closeout. They remain outside the organized Knowledge task folders.

## Current Folder Layout

The current docs-only organization keeps Knowledge history, pilot validation, status entry points, and active post-MVP planning separated:

```text
docs/tasks/knowledge/
docs/tasks/knowledge/mvp/
docs/tasks/knowledge/pilot-validation/
docs/tasks/knowledge/status/
docs/tasks/post-mvp/
```

## Folder Meanings

1. `docs/tasks/knowledge/mvp/` holds completed Knowledge/RAG MVP historical tasks, reviews, closeouts, and final handover.
2. `docs/tasks/knowledge/pilot-validation/` holds completed post-MVP pilot, readiness, handoff, validation, and receipt records.
3. `docs/tasks/knowledge/status/` holds the current status-entry documents that still govern the accepted MVP and pilot baseline.
4. `docs/tasks/post-mvp/` holds active post-MVP planning, roadmap, lane documents, and folder-organization guidance.

## Current Entry Documents

The current Knowledge status entry documents are now:

1. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
2. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

The current post-MVP planning entry documents are now:

1. `docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md`
2. `docs/tasks/post-mvp/README.md`

## Rules For Future Organization Slices

1. This remains docs-only unless separately reopened.
2. Do not edit source code.
3. Do not edit frontend code.
4. Do not edit tests.
5. Do not move non-Knowledge files unless a separate review confirms they belong to the same archive line.
6. Preserve path linkability by updating references whenever Knowledge docs move again.
7. Run link/reference search after moves.
8. Run `git diff --check`.
9. Run touched-doc NUL check.
10. Run keyword boundary review and keep current state as pilot usable, not production ready.

## Prompt For Future Docs-Only Organization Work

```text
接手当前仓库，只执行 docs/tasks 目录整理或 archive 相关 docs-only 工作。

先阅读：
1. docs/tasks/post-mvp/task-folder-archive-plan-2026-05-10.md
2. docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md
3. docs/tasks/knowledge/README.md
4. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
5. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
6. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md

只做文档目录整理、README、索引、路径更新和引用修复。
不要改 src/、console/src/、tests/，不要改任何已验收 MVP 语义，不要把当前状态写成 production ready。

验证至少包括：
1. git status --short --branch
2. git diff --check
3. touched-doc NUL check
4. 引用检查和人工判断
5. keyword boundary review
```
