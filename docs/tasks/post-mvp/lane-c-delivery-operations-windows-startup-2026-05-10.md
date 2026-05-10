# Lane C: Delivery, Operations, And Windows Startup Hardening

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Make pilot startup and recovery repeatable for non-developer operators.
2. Reduce environment drift between Mac development and Windows usage.

## Why This Lane Matters

1. Pilot usability depends on repeatable startup, static bundle clarity, storage clarity, and recovery instructions, not only feature completeness.
2. The current validated baseline can still fail operationally when environment variables, ports, or static assets drift.
3. This lane improves delivery and operator confidence without changing accepted product semantics.

## Entry Conditions

1. Mac and Windows operator-side pilot validation remain accepted with known limitations.
2. The runtime line remains local project directory to app-owned indexes to formal map to knowledge release to current release.
3. The slice targets startup, doctor, packaging, or operator recovery rather than product feature expansion.

## Allowed Scope

1. Windows PowerShell startup scripts or documented commands.
2. `doctor` checks for `QWENPAW_WORKING_DIR`, `QWENPAW_CONSOLE_STATIC_DIR`, port availability, and project storage.
3. Clearer error output when console static bundle is stale or missing.
4. Docs for app-owned storage backup and cleanup.
5. Operator-side smoke scripts that do not modify product semantics.

## Forbidden Scope

1. No production installer claim.
2. No auto-update system.
3. No SVN integration.
4. No real-provider config UI.

## Expected Effect

1. Windows pilot can be started and diagnosed with fewer manual steps.
2. Operators can identify stale static bundle, missing local project directory, and storage root issues quickly.

## Minimum Validation

1. Re-run the touched startup, doctor, packaging, or recovery path.
2. If only docs or scripts changed, run the narrowest command validation that proves those instructions still match the validated runtime.
3. If code changes are needed, run only focused checks for the touched startup or delivery slice.
4. Always run `git diff --check`, touched-doc NUL check, and keyword boundary review on touched docs.

## Closeout Wording

1. Use `Lane C delivery and Windows startup hardening completed` only when the targeted operational slice is verified.
2. Keep wording at pilot hardening, not production deployment.
3. State clearly whether MVP behavior changed or remained unchanged.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane C: Delivery, operations, and Windows startup hardening。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-c-delivery-operations-windows-startup-2026-05-10.md，以及 docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-windows-operator-side-pilot-validation-2026-05-10.md。
不要改知识 release、formal map、RAG、structured query、NumericWorkbench 业务语义。
先复核 Windows operator-side validation 文档，再找启动、doctor、static bundle、port、project storage、local project directory 的最小硬化点。
如果只改 docs/scripts，按对应范围验证；如果改 Python/TS，跑 focused checks，不要扩大到无关产品行为。
```
