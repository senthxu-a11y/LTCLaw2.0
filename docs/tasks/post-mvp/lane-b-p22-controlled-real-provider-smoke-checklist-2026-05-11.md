# Lane B P22 Controlled Real Provider Smoke Checklist

Date: 2026-05-11
Status: planning checklist only
Scope: prepare the first controlled real-provider smoke without opening production rollout, frontend provider selection, or Ask schema expansion

## 1. Purpose

P22 exists to validate one real external provider path under the smallest operator-controlled conditions that can prove the backend-only transport line works beyond the local fake endpoint.

This checklist does not execute a real provider call by itself. It defines the entry conditions, stop conditions, execution split, and evidence required before any real provider smoke is attempted.

## 2. Current Baseline

The required baseline is:

1. P20 backend-only real HTTP transport is complete
2. P21 backend-owned config activation is complete
3. Windows fake-endpoint positive transport is verified
4. Windows hot-reload kill switch is verified
5. current state is backend-only, not production rollout, and not production ready
6. Ask request schema remains `query`, `max_chunks`, and `max_chars`
7. GameProject has no provider selector
8. `ProviderManager.active_model` does not control the ordinary RAG provider path
9. `SimpleModelRouter` does not control the ordinary RAG provider path
10. ordinary RAG Q&A does not write release, formal map, test plan, or workbench draft

## 3. Scope

P22 scope is intentionally narrow:

1. backend-only
2. operator-only
3. single provider
4. single model
5. single Windows machine
6. manual env secret
7. no frontend selector
8. no Ask schema expansion
9. no production rollout
10. no production readiness claim

## 4. Preconditions

P22 may start only after all of the following are true:

1. P21.11 Lane B closeout is complete
2. Windows fake-endpoint positive path has passed
3. Windows hot-reload kill switch has passed
4. operator rollback checklist exists
5. secret handling checklist exists
6. target Windows machine has a known current release
7. target Windows machine can restore `external_provider_config=null`
8. target Windows machine can restart LTCLaw and return to health, project config, and release status `200`
9. provider account and model choice are approved outside the repo
10. first prompt is low risk and grounded in already indexed current-release content

## 5. Secret Handling Checklist

P22 secret handling rules:

1. env stores the secret value
2. config stores only the env var name
3. no secret value in docs
4. no secret value in tasks
5. no secret value in tests
6. no secret value in fixtures
7. no secret value in logs
8. no secret value in receipts
9. no secret value in release artifacts
10. no secret value in formal map
11. no secret value in workbench export
12. warnings and errors must be redacted
13. provider raw error text must not be copied into operator-facing output
14. `Authorization` must remain transport-boundary-only
15. there is no API key UI

## 6. Provider Selection Constraints

P22 provider selection must remain backend-owned:

1. provider is read only from backend-owned config
2. model is read only from backend-owned config
3. API key value is read only from env through backend-owned env var name
4. request-owned `provider` is ignored
5. request-owned `model` is ignored
6. request-owned `api_key` is ignored
7. Ask schema remains unchanged
8. router does not select provider
9. `ProviderManager.active_model` remains outside ordinary RAG provider path
10. `SimpleModelRouter` remains outside ordinary RAG provider path

## 7. Smoke Procedure Draft

The P22 operator smoke should follow this draft order:

1. confirm repository commit and clean worktree
2. confirm Windows OS and LTCLaw startup command
3. confirm health, project config, and release status baseline
4. confirm current release id
5. confirm baseline `external_provider_config=null`
6. set real provider secret in process env only
7. save backend-owned `external_provider_config` with one provider and one model
8. confirm GET readback preserves config shape and does not echo secret
9. run one low-risk grounded RAG answer
10. confirm response is grounded by valid current-release citation
11. confirm request-owned `provider`, `model`, and `api_key` are ignored
12. confirm ordinary RAG did not write release, formal map, test plan, or workbench draft
13. set `transport_enabled=false`
14. confirm next answer does not call the real provider
15. restore `external_provider_config=null`
16. clear env secret from process/session
17. restart LTCLaw without secret
18. confirm baseline health, project config, release status, and current release

## 8. Pass Criteria

P22 pass requires all of the following:

1. one real provider answer succeeds
2. answer includes valid grounded citation
3. no secret leak is found in response, warning, receipt, log, or config readback
4. request-owned `provider`, `model`, and `api_key` are ignored
5. kill switch works without restart
6. cleanup restores `external_provider_config=null`
7. cleanup removes the real provider secret from runtime env
8. baseline returns to health, project config, and release status `200`
9. ordinary RAG Q&A does not write release
10. ordinary RAG Q&A does not write formal map
11. ordinary RAG Q&A does not write test plan
12. ordinary RAG Q&A does not write workbench draft

## 9. Stop Conditions

The operator must stop immediately if any of these occur:

1. any secret appears in logs
2. any secret appears in receipt
3. any secret appears in response
4. any secret appears in config readback
5. provider returns an ungrounded answer
6. citation validation fails
7. kill switch fails
8. ordinary RAG writes any release state
9. ordinary RAG writes formal map
10. ordinary RAG writes test plan
11. ordinary RAG writes workbench draft
12. project config cannot restore to `null`
13. `external_provider_config` readback differs from saved backend-owned config
14. provider raw error text is exposed to ordinary response output
15. target app cannot return to baseline health

## 10. Explicitly Out Of Scope

P22 does not include:

1. production rollout
2. production ready claim
3. ordinary user provider selector
4. multi-provider routing
5. multi-model routing
6. API key UI
7. Ask schema provider, model, or api_key fields
8. real provider default enablement
9. enterprise audit workflow
10. provider choice by router
11. provider choice by frontend
12. provider choice by `ProviderManager.active_model`
13. provider choice by `SimpleModelRouter`

## 11. Recommended Execution Split

Recommended split:

1. P22.1 source and config review
2. P22.2 operator runbook
3. P22.3 Windows real-provider smoke execution
4. P22.4 closeout and production-hardening gate decision

## 12. P22.1 Source And Config Review

Type: docs-only review.

Goal:

1. confirm current P21.10 code still matches the backend-owned provider boundary
2. confirm config shape is sufficient for the chosen provider
3. confirm secret source remains env-only
4. confirm no request, router, frontend, `ProviderManager`, or `SimpleModelRouter` authority has appeared

Output:

1. `docs/tasks/post-mvp/lane-b-p22-1-source-config-review-2026-05-11.md`

## 13. P22.2 Operator Runbook

Type: docs-only runbook.

Goal:

1. define exact Windows commands
2. define exact redacted receipt fields
3. define exact rollback steps
4. define exact cleanup confirmation

Output:

1. `docs/tasks/post-mvp/lane-b-p22-2-controlled-real-provider-smoke-runbook-2026-05-11.md`

## 14. P22.3 Windows Real-Provider Smoke Execution

Type: operator execution.

Goal:

1. run one low-risk real-provider request from Windows
2. verify grounded answer and no-write behavior
3. verify kill switch without restart
4. restore baseline

Output:

1. `docs/tasks/post-mvp/lane-b-p22-3-windows-real-provider-smoke-receipt-2026-05-11.md`

## 15. P22.4 Closeout And Production-Hardening Gate Decision

Type: docs-only closeout and decision.

Goal:

1. decide whether P22 evidence is enough to open production-hardening planning
2. explicitly avoid default production rollout
3. record any provider-specific risks or blocks

Output:

1. `docs/tasks/post-mvp/lane-b-p22-4-closeout-production-hardening-gate-2026-05-11.md`

## 16. Current Decision

Current decision:

1. P22 is planned
2. P22 is not executed
3. P22 is not production rollout
4. P22 is not production ready
5. next work should start with P22.1 source and config review
