# Lane B P20 Backend Real LLM Transport Checklist

Date: 2026-05-10

Status: executable checklist for Lane B. This checklist does not implement P20 by itself.

## Purpose

Turn Lane B into small GPT-5.4-sized slices so real LLM transport can be added without disturbing the accepted MVP.

The target is a backend-only, config-gated, reversible real HTTP transport path for RAG answer. It is not production rollout.

## Current Baseline

1. MVP is complete.
2. Data-backed pilot readiness passed.
3. Mac and Windows operator-side pilots passed with known limitations.
4. Current state is pilot usable, not production ready.
5. External-provider remains frozen at `P3.external-provider-19`.
6. `P20` through `P21.10` are now complete for the backend-only transport and backend-owned activation line.
7. Ask request schema must remain unchanged.
8. GameProject must not expose provider, model, or API-key controls.
9. Windows fake-endpoint verification is recorded in-repo.
10. Windows hot-reload kill-switch verification is recorded in-repo.
11. P22 DeepSeek controlled real-provider smoke has passed under backend-only and operator-only constraints.
12. MiniMax remains blocked and is not the current pass provider.
13. The P22 checklist is `docs/tasks/post-mvp/lane-b-p22-controlled-real-provider-smoke-checklist-2026-05-11.md`.
14. P22 closeout and provider decision are recorded at `docs/tasks/post-mvp/lane-b-p22-closeout-provider-decision-2026-05-11.md`.
15. The next recommended gate is `P24 Operator Startup And Secret-Management Hardening`, not production rollout.
16. P23 planning is recorded at `docs/tasks/post-mvp/lane-b-p23-controlled-pilot-deepseek-backend-config-plan-2026-05-11.md`.
17. P24 planning is recorded at `docs/tasks/post-mvp/lane-b-p24-operator-startup-secret-management-checklist-2026-05-11.md`.

## Non-Regression Rules

1. Do not change release build.
2. Do not change current release pointer semantics.
3. Do not change rollback semantics.
4. Do not change formal map save or status-edit semantics.
5. Do not change structured query behavior.
6. Do not change NumericWorkbench draft export or dry-run semantics.
7. Do not make test plans enter formal knowledge by default.
8. Do not make ordinary fast tests require administrator acceptance.
9. Do not enable SVN commit or update.
10. Do not claim production readiness.

## P20 Slice Map

1. `P20.0` Docs-only source baseline review.
2. `P20.1` Real transport implementation plan.
3. `P20.2` Transport request/response contract hardening.
4. `P20.3` Backend-only real HTTP transport implementation.
5. `P20.4` Config and credential smoke validation.
6. `P20.5` Answer-path integration validation.
7. `P20.6` Closeout and rollout boundary record.

Only one slice should be implemented at a time.

## P20.0 Source Baseline Review

Type: docs-only review.

Goal:

1. Reconfirm the current code state before any implementation.
2. Confirm P10/P11/P13/P18 hardening still exists.
3. Identify the exact minimal write surface for P20.

Read:

1. `docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md`
2. `docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-2026-05-10.md`
3. `docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-checklist-2026-05-10.md`
4. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
5. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-19-real-http-transport-governance-implementation-plan-2026-05-09.md`
6. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-18-env-credential-source-closeout-2026-05-09.md`
7. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-13-real-transport-skeleton-closeout-2026-05-09.md`
8. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-11-gate-order-hardening-closeout-2026-05-09.md`
9. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-10-allowlist-hardening-closeout-2026-05-09.md`

Review code:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
4. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
5. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
6. `tests/unit/game/test_knowledge_rag_external_model_client.py`
7. `tests/unit/game/test_knowledge_rag_answer.py`
8. `tests/unit/game/test_knowledge_rag_provider_selection.py`
9. `tests/unit/game/test_knowledge_rag_model_registry.py`
10. `tests/unit/routers/test_game_knowledge_rag_router.py`

Required findings:

1. Current gate order.
2. Current allowlist behavior.
3. Current credential resolver behavior.
4. Current default transport behavior.
5. Current provider registry allowlist.
6. Whether request-like `provider`, `model`, or `api_key` fields are ignored.
7. Whether router Ask schema remains unchanged.
8. Whether `ProviderManager.active_model` and `SimpleModelRouter` remain outside RAG provider path.

Output:

1. New docs-only review document:
   `docs/tasks/post-mvp/lane-b-p20-0-source-baseline-review-2026-05-10.md`
2. Update this checklist only if a source fact invalidates a later slice.

Validation:

1. `git diff --check`
2. touched-doc NUL check
3. keyword boundary review

Do not run pytest or TypeScript unless the review changes code, which it should not.

## P20.1 Real Transport Implementation Plan

Type: docs-only implementation plan.

Goal:

1. Convert source baseline into exact code and test changes for P20.3.
2. Decide whether to use stdlib-only HTTP or an existing dependency.
3. Freeze timeout, endpoint, payload, error mapping, and redaction rules.

Plan must define:

1. Exact provider identifier.
2. Exact model identifier source.
3. Exact backend-owned config shape.
4. Exact env var metadata source.
5. Whether endpoint is backend-owned config.
6. Timeout default.
7. Max response size or safe parse behavior.
8. Supported response shape.
9. Safe warning strings.
10. Tests to add or update.

Forbidden in plan:

1. UI provider selection.
2. Ask request schema expansion.
3. ProviderManager integration.
4. SimpleModelRouter integration.
5. secret store.
6. admin credential UI.
7. production rollout.

Output:

1. New plan:
   `docs/tasks/post-mvp/lane-b-p20-1-real-transport-implementation-plan-2026-05-10.md`

Validation:

1. `git diff --check`
2. touched-doc NUL check
3. keyword boundary review

## P20.2 Transport Contract Hardening

Type: optional code slice. Do this only if P20.0/P20.1 finds the contract needs hardening before real HTTP.

Goal:

1. Make transport inputs and outputs explicit before adding real HTTP.
2. Keep default behavior unchanged.

Allowed files:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Allowed changes:

1. typed request-preview helper
2. endpoint redaction helper
3. safe response parsing helper
4. explicit warning mapping helper
5. tests for redaction and malformed response handling

Forbidden changes:

1. no network call
2. no real provider
3. no credential behavior change
4. no router or frontend changes

Validation:

1. `python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py -q`
2. focused five-file RAG suite if behavior changes:
   - `tests/unit/game/test_knowledge_rag_external_model_client.py`
   - `tests/unit/game/test_knowledge_rag_answer.py`
   - `tests/unit/game/test_knowledge_rag_provider_selection.py`
   - `tests/unit/game/test_knowledge_rag_model_registry.py`
   - `tests/unit/routers/test_game_knowledge_rag_router.py`
3. `git diff --check`
4. touched Python/docs NUL check
5. keyword boundary review

Closeout:

1. New closeout:
   `docs/tasks/post-mvp/lane-b-p20-2-transport-contract-hardening-closeout-2026-05-10.md`

## P20.3 Backend-Only Real HTTP Transport Implementation

Type: code slice.

Goal:

1. Add the first backend-only real HTTP transport path.
2. Keep it default-off and gated.
3. Keep all selection and credentials backend-owned.

Allowed files:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`
3. narrow adjacent tests only if needed:
   - `tests/unit/game/test_knowledge_rag_answer.py`
   - `tests/unit/game/test_knowledge_rag_provider_selection.py`
   - `tests/unit/game/test_knowledge_rag_model_registry.py`
   - `tests/unit/routers/test_game_knowledge_rag_router.py`
4. P20 closeout docs under `docs/tasks/post-mvp/`

Implementation requirements:

1. Real HTTP path remains default-off.
2. `enabled=False` returns before payload normalization.
3. `transport_enabled=False` returns before payload normalization, credential resolver, and transport.
4. payload normalization happens before allowlist only when both gates are open.
5. allowlist failure blocks before resolver and transport.
6. credential miss blocks before transport.
7. request payload to provider contains only normalized prompt content and allowed backend config.
8. request payload does not contain API key, credential object, Authorization header, request body provider/model/api_key, raw release artifacts, or raw files.
9. Authorization header is built only inside transport call and never logged or returned.
10. provider raw error text is not returned to ordinary users.
11. response must go through `_normalize_response(...)`.
12. answer grounding and citation checks remain outside the transport.

Tests required:

1. default config does not call real HTTP.
2. `transport_enabled=False` does not call env credential resolver.
3. allowlist failure does not call env credential resolver.
4. missing credential does not call HTTP.
5. injected fake HTTP success returns normalized answer.
6. fake HTTP timeout maps to safe warning.
7. fake HTTP non-2xx maps to safe warning.
8. malformed provider JSON maps to safe warning.
9. provider response without usable answer maps to safe warning or insufficient context.
10. API key and Authorization never appear in warning, response, preview, fixture assertion text, or logs.
11. request-like provider/model/api_key fields remain ignored.
12. router Ask schema remains unchanged.
13. deterministic_mock and disabled still pass existing tests.

Validation:

1. focused external-client test file
2. focused five-file RAG suite
3. `git diff --check`
4. touched Python/docs NUL check
5. keyword boundary review

Closeout:

1. New closeout:
   `docs/tasks/post-mvp/lane-b-p20-3-real-http-transport-closeout-2026-05-10.md`

Allowed final wording:

1. `P20 backend-only real HTTP transport minimal implementation completed.`
2. `Real transport remains backend-owned, gated, and not production rollout.`
3. `Ask schema, router authority, frontend provider UI, ProviderManager, and SimpleModelRouter remain unchanged.`

Forbidden final wording:

1. `production provider rollout completed`
2. `real provider rollout completed`
3. `Ask request now supports provider/model/api_key`
4. `frontend provider selector implemented`
5. `ProviderManager active_model now controls RAG provider`
6. `SimpleModelRouter connected to RAG provider path`

## P20.4 Config And Credential Smoke Validation

Type: execution validation slice.

Goal:

1. Prove the real HTTP path can be enabled only through backend-owned config.
2. Prove missing or wrong config fails safely.

Allowed scope:

1. test configuration
2. local env placeholder names
3. mocked or controlled endpoint smoke
4. docs closeout

Forbidden scope:

1. no real secret values in docs, fixtures, screenshots, logs, or commits
2. no UI credential entry
3. no admin credential store
4. no production rollout claim

Required validation:

1. disabled config safe-fails.
2. missing allowlist safe-fails.
3. missing env value safe-fails.
4. valid backend-owned config plus controlled fake endpoint succeeds.
5. real key value does not appear in git diff.
6. endpoint query strings are redacted.
7. rollback/kill switch by config works.

Closeout:

1. New closeout:
   `docs/tasks/post-mvp/lane-b-p20-4-config-credential-smoke-closeout-2026-05-10.md`

## P20.5 Answer-Path Integration Validation

Type: execution validation slice.

Status:

1. completed

Goal:

1. Prove real-transport answer remains grounded in current-release context.
2. Prove no provider call happens for no-current-release or insufficient-context early returns.

Required validation:

1. no current release does not initialize provider.
2. insufficient context does not initialize provider.
3. valid current-release context can call real transport only when all gates pass.
4. provider answer with missing citations is rejected or downgraded.
5. provider answer with out-of-range citations is rejected or downgraded.
6. candidate evidence does not automatically enter provider prompt.
7. ordinary RAG Q&A does not write release, formal map, test plan, or workbench draft.

Suggested tests:

1. `tests/unit/game/test_knowledge_rag_answer.py`
2. `tests/unit/routers/test_game_knowledge_rag_router.py`
3. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Closeout:

1. New closeout:
   `docs/tasks/post-mvp/lane-b-p20-5-answer-path-integration-closeout-2026-05-10.md`

## P20.6 Lane B Closeout And Next Gate

Type: docs-only closeout.

Status:

1. completed

Goal:

1. Summarize what P20 changed and did not change.
2. Decide whether controlled pilot can use real LLM backend config.
3. Decide the next gate before any production rollout.

Must record:

1. exact files changed
2. exact tests run
3. secret/redaction verification
4. default-off behavior
5. kill-switch behavior
6. no Ask schema change
7. no frontend provider selector
8. no ProviderManager or SimpleModelRouter control
9. not production ready
10. next gate recommendation

Possible next gates:

1. controlled real LLM pilot with backend-owned config
2. provider rollout admin/config boundary review
3. production-hardening scope decision
4. stop and collect pilot feedback

Closeout:

1. New closeout:
   `docs/tasks/post-mvp/lane-b-p20-6-lane-closeout-and-next-gate-2026-05-10.md`

## Required Focused Test Suite

Use actual repo paths if names differ:

```text
tests/unit/game/test_knowledge_rag_external_model_client.py
tests/unit/game/test_knowledge_rag_answer.py
tests/unit/game/test_knowledge_rag_provider_selection.py
tests/unit/game/test_knowledge_rag_model_registry.py
tests/unit/routers/test_game_knowledge_rag_router.py
```

## Required Hygiene Checks

For every slice:

1. `git diff --check`
2. touched Python/docs NUL check
3. keyword boundary review
4. no real secret in diff
5. no source, frontend, or test changes outside slice scope

Keyword review must not find positive claims for:

1. `production ready`
2. `production provider rollout completed`
3. `real provider rollout completed`
4. `Ask request now supports provider/model/api_key`
5. `frontend provider selector implemented`
6. `ProviderManager active_model now controls RAG provider`
7. `SimpleModelRouter connected to RAG provider path`

Allowed only when negated or scoped:

1. `not production ready`
2. `deferred`
3. `backend-only`
4. `not production rollout`
5. `future scoped lane`

## Done Definition For Lane B

Lane B is complete only when:

1. real HTTP transport exists behind backend-owned config
2. default behavior remains disabled or safe
3. env credential source remains backend-owned
4. allowlist remains hard gate
5. request/router/frontend cannot choose provider, model, or API key
6. provider raw errors and secrets are redacted
7. answer output remains normalized and grounded
8. focused RAG provider suite passes
9. closeout documents record not production ready
10. controlled pilot can enable real LLM only by backend config
11. Windows fake-endpoint and kill-switch receipts are recorded before any real-provider smoke planning
