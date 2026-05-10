# Knowledge P3.external-provider-5 Runtime Allowlist Implementation Plan

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-external-provider-4-runtime-allowlist-boundary-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md
6. docs/tasks/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md
7. src/ltclaw_gy_x/game/knowledge_rag_answer.py
8. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
9. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
10. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
11. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
12. tests/unit/game/test_knowledge_rag_answer.py
13. tests/unit/game/test_knowledge_rag_provider_selection.py
14. tests/unit/game/test_knowledge_rag_model_registry.py
15. tests/unit/game/test_knowledge_rag_external_model_client.py
16. tests/unit/routers/test_game_knowledge_rag_router.py

## Purpose

Define the smallest future backend-only code plan that would allow `future_external` to enter the runtime allowlist after `P3.external-provider-4`, without authorizing real provider rollout.

This slice is docs-only.

It does not modify backend code, frontend code, tests, request schema, registry contents, or public API.

It does not add `future_external` to `SUPPORTED_RAG_MODEL_PROVIDERS` in this slice.

It does not connect a real provider.

It does not connect a real LLM.

It does not perform real HTTP.

It does not connect real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

## Current Planning Baseline

The current baseline for this plan is:

1. `build_rag_answer_with_service_config(...)` remains the only approved live handoff entry.
2. Router remains thin and still must not choose provider or call `get_rag_model_client(...)` directly.
3. Provider selection remains backend-owned inside the answer/provider-selection layer.
4. Runtime providers still remain only `deterministic_mock` and `disabled`.
5. `future_external` still remains outside `SUPPORTED_RAG_MODEL_PROVIDERS`.
6. The external client remains disabled-by-default and skeleton-only.
7. `no_current_release` and `insufficient_context` still return before provider/config/credential/transport work.
8. Citation grounding still remains answer-service-owned and limited to `context.citations`.
9. `candidate_evidence` still remains outside automatic RAG input.
10. `ProviderManager.active_model` still remains out of scope.

## Minimal Code Construction Checklist

The future implementation should stay as small as possible and should remain backend-only.

The minimum code construction checklist is:

1. In `knowledge_rag_model_registry.py`, introduce a runtime-supported provider constant for `future_external` and make runtime allowlist membership explicit in one place.
2. In `knowledge_rag_model_registry.py`, extend the registry factory seam so the registry can own runtime support for `future_external` without shifting provider selection into router code.
3. In `knowledge_rag_model_registry.py`, keep the default runtime set conservative: only `deterministic_mock`, `disabled`, and newly approved `future_external`; do not add any second real provider.
4. In `knowledge_rag_answer.py`, keep `no_current_release` and `insufficient_context` ahead of all provider, credential, resolver, and transport work.
5. In `knowledge_rag_answer.py`, keep final warning merge and final answer shaping in the answer layer.
6. In `knowledge_rag_answer.py`, remove or narrow any direct external-provider bypass that would make registry allowlist ownership ambiguous once `future_external` becomes runtime-supported.
7. In `knowledge_rag_answer.py`, preserve clear-fail semantics for unknown provider values and preserve explicit warning-bearing fallback only to `disabled` when provider initialization fails.
8. In `knowledge_rag_provider_selection.py`, keep provider resolution backend-owned and keep request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields ignored.
9. In `knowledge_rag_provider_selection.py`, keep external config extraction tied to backend-owned `external_provider_config` only.
10. In `knowledge_rag_external_model_client.py`, keep `enabled` default false and keep allowlist, credential, timeout, and non-answer behavior checks ahead of transport.
11. In `knowledge_rag_external_model_client.py`, keep the runtime-supported `future_external` client skeleton-only: no real transport wiring, no real HTTP implementation, no real credential source implementation.
12. In `game_knowledge_rag.py`, keep the router unchanged except for any test-safe imports that are strictly required by refactoring; do not add provider selection logic.

The minimum file set that should be expected for the future implementation is:

1. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
4. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
5. `tests/unit/game/test_knowledge_rag_model_registry.py`
6. `tests/unit/game/test_knowledge_rag_answer.py`
7. `tests/unit/game/test_knowledge_rag_provider_selection.py`
8. `tests/unit/game/test_knowledge_rag_external_model_client.py`
9. `tests/unit/routers/test_game_knowledge_rag_router.py`

Optional code widening is not part of the minimum plan.

Specifically not required for this future slice:

1. new endpoint
2. new request fields
3. frontend provider selection
4. new real provider adapter
5. real transport implementation
6. real credential resolver implementation

## Minimal Test Checklist

The future implementation should land only with focused tests that prove the runtime allowlist changed and that all existing boundaries remained intact.

Minimum focused test checklist:

1. `test_knowledge_rag_model_registry.py` must flip the runtime allowlist expectation from “`future_external` not supported” to explicit runtime support for `future_external` only.
2. `test_knowledge_rag_model_registry.py` must still prove unknown provider clear-fails.
3. `test_knowledge_rag_model_registry.py` must still prove provider init failure falls back only to `disabled` with explicit warnings.
4. `test_knowledge_rag_model_registry.py` must still prove the registry does not read files or env as request-time selection.
5. `test_knowledge_rag_answer.py` must prove backend-owned external config can resolve to runtime-supported `future_external` without widening request ownership.
6. `test_knowledge_rag_answer.py` must prove disabled config does not produce fake answer.
7. `test_knowledge_rag_answer.py` must prove missing credential does not produce fake answer.
8. `test_knowledge_rag_answer.py` must prove allowlist failure does not enter transport.
9. `test_knowledge_rag_answer.py` must prove provider init failure does not switch to another real provider.
10. `test_knowledge_rag_answer.py` must still prove `no_current_release` and `insufficient_context` bypass provider resolution and registry calls.
11. `test_knowledge_rag_provider_selection.py` must still prove request-like provider fields are ignored.
12. `test_knowledge_rag_provider_selection.py` must still prove backend-owned nested `external_provider_config` is the only external config source.
13. `test_knowledge_rag_external_model_client.py` must still prove allowlist checks happen before credential resolution and transport.
14. `test_knowledge_rag_external_model_client.py` must still prove disabled, missing credential, provider-not-allowed, and model-not-allowed paths return safe non-answer behavior.
15. `test_game_knowledge_rag_router.py` must still prove router does not call the registry directly and still only hands off through `build_rag_answer_with_service_config(...)`.
16. Answer-path tests must still prove model citation ids outside `context.citations` are rejected.

Recommended future command set for that later implementation round:

1. run focused pytest only for the five files above
2. run adjacent router plus answer/provider/registry regression if the registry seam changes
3. run `git diff --check` on the touched backend and test files

This plan itself does not run pytest.

## Prohibited Items

The future implementation must not use runtime allowlist work as a shortcut to broader rollout.

Prohibited items:

1. do not add a real provider connection
2. do not add real HTTP
3. do not add real credential material or raw secret reads
4. do not add request-body provider/model/api_key ownership
5. do not let router choose provider
6. do not let router call `get_rag_model_client(...)` directly
7. do not let `ProviderManager.active_model` become a provider source
8. do not add frontend provider or model selection
9. do not add Ask request fields
10. do not add a second real provider while landing `future_external`
11. do not let unknown provider silently switch to another provider
12. do not let provider init failure fall back to another real provider
13. do not let `candidate_evidence` automatically enter RAG
14. do not move citation-grounding authority out of the answer service
15. do not turn env reads into request-time provider selection

## Rollback Risks And Exit Criteria

The future implementation is small, but the rollback risks are specific and should be called out before code lands.

Primary rollback risks:

1. adding `future_external` to the runtime allowlist could unintentionally weaken current clear-fail behavior for unknown providers
2. widening registry support could accidentally bypass answer-layer warning merge or answer-layer early-return guards
3. refactoring the registry seam could accidentally move provider choice into router or request-like inputs
4. runtime support could accidentally instantiate the external client before allowlist, credential, or disabled checks are satisfied
5. runtime support could accidentally treat env presence as request-time selection
6. test expectation flips could mask a silent provider switch instead of explicit clear-fail or `disabled` fallback

Rollback exit criteria for the future implementation round should be explicit.

Immediate rollback or revert should happen if any of the following appears:

1. router starts calling the registry directly
2. request-like provider/model/api_key fields begin affecting provider selection
3. `no_current_release` or `insufficient_context` starts resolving provider or credential paths
4. unknown provider stops clear-failing
5. provider init failure starts switching to another real provider
6. disabled config or missing credential begins generating fake answer text
7. citation ids outside `context.citations` stop being rejected
8. any code path introduces real HTTP, real credential integration, or real provider rollout in the same slice

Recommended rollback shape for the future implementation round:

1. revert registry allowlist expansion first
2. revert answer-layer registry handoff changes second
3. keep router unchanged throughout rollback
4. keep test assertions for router/request boundary until the end of rollback

## Recommended Next Slice After This Plan

The next recommended slice is a backend-only minimal runtime allowlist implementation.

That next slice should:

1. land only the minimum code and test changes listed above
2. keep the external client skeleton-only and disabled-by-default
3. keep real provider rollout deferred to a later dedicated review
4. stop after focused backend validation rather than widening into frontend or transport work

## Plan Decision

1. `P3.external-provider-5` runtime allowlist implementation plan is complete as a docs-only slice.
2. This plan defines the minimum backend files, test files, and behavior checks for a future runtime allowlist implementation.
3. This plan does not change runtime allowlist membership in the current code.
4. `future_external` still remains outside `SUPPORTED_RAG_MODEL_PROVIDERS` in the current code.
5. The plan still forbids real provider connection, real LLM execution, real HTTP, real credential integration, frontend provider control, and Ask request-schema changes.
6. The plan keeps router/request/UI ownership unchanged and keeps provider selection backend-owned.
7. The plan makes rollback triggers explicit before any code implementation begins.
8. The next recommended slice is backend-only minimal runtime allowlist implementation, not real provider rollout.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation diff whitespace checking and keyword review to confirm that the slice is not described as real provider rollout or real provider integration.