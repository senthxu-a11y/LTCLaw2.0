# Knowledge P3.external-provider-8a Mocked HTTP Client Skeleton Implementation Plan

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-external-provider-7-real-provider-rollout-boundary-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-6-runtime-allowlist-closeout-2026-05-09.md
6. docs/tasks/knowledge-p3-external-provider-5-runtime-allowlist-implementation-plan-2026-05-09.md
7. docs/tasks/knowledge-p3-external-provider-4-runtime-allowlist-boundary-2026-05-09.md
8. docs/tasks/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md
9. docs/tasks/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md
10. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
11. src/ltclaw_gy_x/game/knowledge_rag_answer.py
12. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
13. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
14. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
15. src/ltclaw_gy_x/game/service.py

## Purpose

Define the docs-only implementation plan for a mocked HTTP client skeleton that can validate the external-provider transport seam before any real provider rollout is attempted.

This slice is docs-only.

It is not code implementation.

It is not real provider rollout.

It does not connect a real LLM.

It does not perform real HTTP.

It does not introduce real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

It does not change router provider-selection authority.

It does not change `ProviderManager.active_model` behavior.

## Source-Based Code Review Conclusion

This plan is based on the current source code rather than on documentation assumptions.

Current source-truth conclusions are:

1. `future_external` has entered the backend runtime allowlist in `knowledge_rag_model_registry.py`.
2. answer-layer provider resolution now routes through the registry rather than directly instantiating the external client.
3. `future_external` enters runtime path only when backend-owned `external_provider_config` is explicitly present.
4. missing `external_provider_config` for `future_external` currently clear-fails.
5. `ExternalRagModelClient` is still an injected-transport skeleton and still has no real HTTP client.
6. there is still no real credential resolver wired into the current RAG path.
7. Ask request schema still has no provider, model, or api_key fields.
8. router still does not choose provider and still does not call the registry directly.
9. `ProviderManager.active_model` still is not wired into the RAG provider path.
10. `no_current_release` and `insufficient_context` still return before provider initialization.
11. `candidate_evidence` still does not automatically trigger RAG provider input.
12. `game/service.py` does contain `SimpleModelRouter` with real-provider bridge logic for a different game path, but current RAG router, answer, registry, and external-client path do not use that bridge.

Source-based risk note:

1. future mocked HTTP client skeleton work must not accidentally reuse `SimpleModelRouter` or `ProviderManager.active_model` as a shortcut into the RAG provider path
2. if documentation and source diverge later, implementation planning must continue to treat source as controlling truth

## Next-Round Minimal Construction Scope

The next implementation round may touch only the minimum files needed to validate the mocked HTTP client seam.

Planned code surface for the next round, but not this round:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, only if config coercion needs a narrow follow-up
3. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`, only if allowlist or feature-flag guard needs a narrow follow-up
4. `tests/unit/game/test_knowledge_rag_external_model_client.py`
5. `tests/unit/game/test_knowledge_rag_model_registry.py`
6. `tests/unit/game/test_knowledge_rag_answer.py`
7. `tests/unit/game/test_knowledge_rag_provider_selection.py`
8. `tests/unit/routers/test_game_knowledge_rag_router.py`
9. if narrow redaction or DLP tests are added, they should live in a focused backend unit-test file rather than expand API or frontend scope

This round does not modify any of those files.

## Mocked HTTP Client Seam Design Requirements

The next implementation round must define the mocked transport seam with the following constraints:

1. transport interface remains injectable and must still accept a mocked transport implementation
2. default behavior must not send real HTTP
3. without an explicit backend feature flag, external transport must not be enabled
4. without a credential resolver, the external path must explicitly return `not configured`
5. without `allowed_providers` and `allowed_models`, future real rollout must not treat the path as safe to call
6. mocked transport exists only to validate the contract and must not be treated as a production real provider
7. transport input must contain only normalized prompt payload and must not contain request-like `provider`, `model`, or `api_key`
8. transport output must still pass through the response normalizer
9. provider raw exceptions must not be shown directly to ordinary users
10. timeout, HTTP error, invalid response, and request-failed conditions must map to internal warning or error behavior

## Credential Source Design Requirements

The next implementation round must preserve the following credential rules:

1. API key must not come from request body
2. API key must not come from frontend
3. API key must not come from docs, tasks, map, formal map, snapshot, or export data
4. API key must not enter prompt payload
5. API key must not enter normal warnings, error responses, committed fixtures, or ordinary logs
6. credential resolver may read only from backend-owned config or a backend-owned secret store
7. env-var name may come from backend-owned config, but env-var value must not be written into docs or tests
8. missing credential must fail clearly and must not silently fall back to another real provider
9. disabled path must remain safe and usable

## Provider And Model Allowlist Constraints

The next implementation round must preserve the following allowlist rules:

1. provider must be inside backend-owned `allowed_providers`
2. model must be inside backend-owned `allowed_models`
3. if `allowed_providers` is empty or missing, future real rollout must not call a real provider
4. if `allowed_models` is empty or missing, future real rollout must not call a real provider
5. unknown provider must fail clearly
6. unknown model must fail clearly
7. fallback to another real provider is forbidden
8. `deterministic_mock` and `disabled` behavior must remain intact

## Runtime Feature Flag And Rollback Switch Requirements

The next implementation round must define the following feature-flag and rollback behavior:

1. real external transport remains off by default
2. feature flag must remain backend-owned
3. feature flag must not come from request, router, or frontend
4. rollback switch must be able to disable real transport
5. after rollback, `deterministic_mock` and `disabled` must still remain available
6. when feature flag is off, real provider transport must not initialize
7. `no_current_release` and `insufficient_context` still must not initialize provider transport

## HTTP And Error-Mapping Test Requirements

The next mocked transport implementation round must include focused tests for at least the following behaviors:

1. success response
2. timeout
3. provider HTTP error
4. authentication failure
5. rate-limit or quota error
6. model not found
7. invalid JSON or invalid response shape
8. oversized response
9. empty answer
10. citation ids outside grounded context
11. provider exception
12. missing credential
13. missing allowed provider or model
14. disabled config

## Logging, Redaction, And DLP Requirements

The next implementation round must define and test the following logging and redaction rules:

1. Authorization header must not be logged
2. API key must not be logged
3. provider raw response must not be logged by default
4. query, context, chunks, and answer logging must have explicit level and truncation rules
5. source_path, release_id, and citation logging scope must be explicit
6. ordinary warning or error text must not contain secret material
7. debug logging must remain off by default
8. docs, tasks, snapshot, formal map, and export artifacts must not receive credential material
9. test fixtures must use placeholders only and must not contain secret-like values

## API, Router, And Frontend Boundary

The next implementation round must continue to preserve these boundaries:

1. Ask request schema must not add provider, model, or api_key
2. router must not call the registry directly
3. router must not choose provider
4. frontend must not add provider, model, or API key inputs
5. any administrator real-provider configuration must use a separate backend or admin path rather than the ordinary Ask path
6. `ProviderManager.active_model` must not participate in RAG provider selection

## Focused Test Plan For The Next Implementation Round

The next implementation round should run focused tests in these files:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_model_registry.py`
3. `tests/unit/game/test_knowledge_rag_answer.py`
4. `tests/unit/game/test_knowledge_rag_provider_selection.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

Expected new or strengthened assertions by file:

1. `test_knowledge_rag_external_model_client.py`: mocked transport success, timeout, provider error, invalid response, missing credential redaction, allowlist missing or denied, disabled path remains safe
2. `test_knowledge_rag_model_registry.py`: feature-flag guard, clear-fail versus disabled fallback, no request-owned selection, `deterministic_mock` and `disabled` remain intact
3. `test_knowledge_rag_answer.py`: `no_current_release` and `insufficient_context` still perform no provider init, citation-boundary preservation, request-like provider/model/api_key ignored
4. `test_knowledge_rag_provider_selection.py`: request-like provider/model/api_key ignored, backend-owned config only, no `ProviderManager.active_model` coupling
5. `test_game_knowledge_rag_router.py`: router request-injection ignored, router still does not call registry, router still does not choose provider

## Prohibited Items

This plan explicitly forbids the following in the current round:

1. modifying `src/`
2. modifying `console/src/`
3. adding a real HTTP client
4. calling a real provider
5. writing a real API key
6. adding Ask request `provider`, `model`, or `api_key`
7. changing frontend
8. changing `ProviderManager.active_model` behavior
9. running pytest
10. running TypeScript
11. describing this round as shipped implementation
12. describing this round as completed production rollout
13. describing mocked transport as a production provider

## Recommended Next Slice

The next recommended slice is mocked HTTP client skeleton implementation, not production real provider rollout.

## Plan Decision

1. `P3.external-provider-8a` mocked HTTP client skeleton implementation plan is complete as a docs-only slice.
2. This plan is based on current source code rather than on documentation assumptions alone.
3. Current runtime and provider-selection boundaries remain unchanged.
4. The plan defines the minimum next-round file scope, seam rules, credential rules, allowlist rules, feature-flag rules, redaction rules, and focused test plan needed before any real rollout work.
5. This plan is not code implementation.
6. This plan is not real provider rollout.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation diff whitespace checking and keyword review confirming that the slice is not described as shipped implementation, completed rollout, or production provider enablement.
