# Post-MVP Engineering Roadmap

Date: 2026-05-10

Status: planning guidance after Mac and Windows operator-side pilot validation.

This document is the active post-MVP engineering index. It is intentionally separate from `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md` so the accepted MVP record stays stable.

## Current Baseline

1. `P0-P3` MVP mainline is closed.
2. `Data-backed pilot readiness pass.` remains the mainline readiness result.
3. Mac operator-side pilot validation passed with known limitations.
4. Windows operator-side pilot validation passed with known limitations.
5. Current state is pilot usable, not production ready.
6. Runtime line remains:

```text
local project directory
-> app-owned indexes
-> formal map
-> knowledge release
-> current release
-> query / RAG / structured query / NumericWorkbench
```

7. SVN is not a knowledge runtime dependency.
8. External-provider remains frozen at `P3.external-provider-19`.
9. `P20` is still deferred until a new explicit backend-only slice opens it.

## Global Rules

1. Do not change accepted MVP semantics while opening post-MVP work.
2. Do not change release build, current release, rollback, formal map, current-release query, RAG context, structured query, or NumericWorkbench draft semantics unless the slice explicitly targets that surface.
3. Do not add provider, model, or API-key fields to Ask request bodies.
4. Do not expose provider, model, or API-key choice in GameProject RAG UI.
5. Do not make router code select providers.
6. Do not make `ProviderManager.active_model` or `SimpleModelRouter` control the RAG provider path without a separate review.
7. Do not turn test plans or NumericWorkbench fast-test results into formal knowledge by default.
8. Do not make administrator acceptance control ordinary fast tests or runtime provider selection.
9. Do not enable SVN commit or update integration inside the accepted MVP line.
10. Do not claim production readiness until a separate production-hardening gate passes.

## Parallel Engineering Lanes

1. Lane A: `docs/tasks/post-mvp/lane-a-controlled-windows-pilot-hardening-2026-05-10.md`
2. Lane B: `docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-2026-05-10.md`
3. Lane C: `docs/tasks/post-mvp/lane-c-delivery-operations-windows-startup-2026-05-10.md`
4. Lane D: `docs/tasks/post-mvp/lane-d-svn-legacy-boundary-cut-2026-05-10.md`
5. Lane E: `docs/tasks/post-mvp/lane-e-numeric-workbench-ux-hardening-2026-05-10.md`
6. Lane F: `docs/tasks/post-mvp/lane-f-production-hardening-scope-decision-2026-05-10.md`

## Parallelization Rules

1. Lane A and Lane C can run together if they touch different files.
2. Lane B can run in parallel with Lane A or Lane C because it should stay in backend RAG provider files and tests.
3. Lane D can run in parallel with Lane B only if it does not touch RAG provider files.
4. Lane E can run in parallel with Lane B only if it does not change RAG API schema or provider ownership.
5. Lane F should wait until at least one controlled pilot usage cycle or a real production decision trigger.
6. Do not run two workers on the same frontend files unless their write scopes are explicitly split.
7. Do not run two workers on `knowledge_rag_external_model_client.py` at the same time.
8. Each lane must produce its own closeout and must state whether it changed MVP behavior.

## Recommended Next-Start Order

1. Start controlled Windows pilot usage immediately.
2. Open Lane B P20 backend-only real LLM transport as the first implementation lane because useful planner RAG depends on a real answer model.
3. Open Lane C startup or doctor hardening in parallel if pilot operators hit setup friction.
4. Open Lane E workbench practical UX only after the first real planner session identifies UX pain.
5. Open Lane D SVN Phase 0/1 only after current delivery artifacts are stable.
6. Keep Lane F as a planning gate after real pilot feedback.
