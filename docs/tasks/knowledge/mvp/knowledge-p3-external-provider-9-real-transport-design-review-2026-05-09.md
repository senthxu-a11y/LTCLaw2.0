# Knowledge P3.external-provider-9 Real Transport Design Review

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8b-mocked-http-client-skeleton-closeout-2026-05-09.md
5. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8a-mocked-http-client-skeleton-implementation-plan-2026-05-09.md
6. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-7-real-provider-rollout-boundary-2026-05-09.md
7. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-6-runtime-allowlist-closeout-2026-05-09.md
8. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
9. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
10. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
11. src/ltclaw_gy_x/game/knowledge_rag_answer.py
12. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
13. src/ltclaw_gy_x/game/service.py
14. tests/unit/game/test_knowledge_rag_external_model_client.py
15. tests/unit/game/test_knowledge_rag_answer.py
16. tests/unit/game/test_knowledge_rag_provider_selection.py
17. tests/unit/game/test_knowledge_rag_model_registry.py
18. tests/unit/routers/test_game_knowledge_rag_router.py

## Nature Of This Round

This slice is a docs-only design review.

It is not implementation.

It is not a real provider rollout slice.

It does not connect a real LLM.

It does not perform real HTTP.

It does not introduce real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

It does not change router provider-selection authority.

It does not change `ProviderManager.active_model` behavior.

## Source-Based Review Conclusion

This review is based on current source code and current tests rather than on prior document assumptions.

Current source-truth conclusions are:

1. `ExternalRagModelClientConfig` now has both `enabled` and `transport_enabled` gates.
2. `enabled=True` does not by itself authorize transport execution.
3. `transport_enabled=False` returns `External provider adapter skeleton transport is not connected.` before credential resolution.
4. `transport_enabled=False` blocks both the credential resolver and injected transport.
5. `enabled=False` remains the adapter disabled path and also blocks resolver and transport.
6. mocked transport still enters only through injected `transport` or `responder` seams.
7. current RAG path still has no real HTTP client.
8. current RAG path still has no real credential resolver.
9. `future_external` still enters runtime path only through backend-owned `external_provider_config`.
10. backend-owned config coercion already preserves `transport_enabled` when it is present.
11. request-like `provider_name`, `model_name`, and `api_key` do not enter normalized prompt payload.
12. Ask request schema still exposes only `query`, `max_chunks`, and `max_chars`.
13. router still does not choose provider and still does not call `get_rag_model_client(...)` directly.
14. `build_rag_answer_with_service_config(...)` still remains the live backend-owned handoff entry.
15. `ProviderManager.active_model` still does not participate in RAG provider selection.
16. `no_current_release` and `insufficient_context` still return before provider initialization.
17. `candidate_evidence` still is not consumed by the current RAG provider path.
18. `game/service.py` still contains `SimpleModelRouter` with real-provider bridge logic, but that bridge is still outside the current RAG provider path.
19. `allowed_providers` and `allowed_models` currently block only when explicitly configured; when either is `None`, mocked transport is not blocked by allowlist logic.

## Current 8b Gate Confirmation

The current 8b gate does hold in the source baseline.

Confirmed current behavior:

1. `enabled=False` returns the disabled warning and prevents resolver or transport execution.
2. `transport_enabled=False` returns the not-connected warning and prevents resolver or transport execution.
3. `transport_enabled=True` still permits the mocked seam for focused tests only.
4. answer-layer grounding still occurs after model-client output and still owns citation validation against `context.citations`.
5. router still does not expose provider/model/api_key control to request callers.

## Real Transport Contract Boundary

Any future real transport slice must satisfy the following contract rules before implementation is accepted:

1. transport input must be only normalized `RagAnswerPromptPayload`.
2. transport input must not contain `provider_name`, `model_name`, `api_key`, credential objects, or `Authorization` header material.
3. provider and model must come only from backend-owned `ExternalRagModelClientConfig`.
4. credential must come only from backend-owned credential resolver or backend-owned secret store.
5. transport output must still pass through `_normalize_response(...)`.
6. transport must not bypass answer-layer citation grounding.
7. provider-returned `citation_ids` must still be validated by the answer layer against grounded context.
8. provider empty answer, missing citation ids, or out-of-context citation ids must still degrade to `insufficient_context`.
9. provider raw errors must not be exposed directly to ordinary users.
10. transport implementation must remain fully replaceable by mocked tests.

## Provider And Model Allowlist Hardening Boundary

Before any future real transport is accepted, allowlist behavior must be tightened beyond the current mocked baseline.

Required future hardening:

1. when `transport_enabled=True`, `allowed_providers` must exist and must be non-empty.
2. when `transport_enabled=True`, `allowed_models` must exist and must be non-empty.
3. `config.provider_name` must be present and must exist inside `allowed_providers`.
4. `config.model_name` must be present and must exist inside `allowed_models`.
5. blank provider name must clear-fail.
6. blank model name must clear-fail.
7. unknown provider must clear-fail.
8. unknown model must clear-fail.
9. silent fallback to another real provider is forbidden.
10. `deterministic_mock` and `disabled` behavior must remain unaffected.

## Credential Resolver Boundary

Any future real transport slice must preserve all of the following credential rules:

1. API key must not come from request body.
2. API key must not come from frontend.
3. API key must not come from docs, tasks, map, formal map, snapshot, or export artifacts.
4. API key must not enter prompt payload.
5. API key must not enter warnings, error responses, test fixtures, or ordinary logs.
6. env-var name may come from backend-owned config.
7. env-var value must not be written into docs, tests, snapshot, formal map, or export artifacts.
8. missing credential resolver must fail clearly.
9. blank credential must fail clearly.
10. credential failure must not fall back to another real provider.

## HTTP Client Boundary

The future real transport design must define, but this round does not implement, the following HTTP-client decisions:

1. request method and endpoint source.
2. timeout default and timeout maximum.
3. retry policy and retry eligibility.
4. authentication failure behavior.
5. rate-limit or quota behavior.
6. model-not-found behavior.
7. invalid JSON behavior.
8. invalid response-shape behavior.
9. oversized response behavior.
10. provider timeout behavior.
11. network-failure behavior.
12. provider 5xx behavior.
13. internal warning or error mapping for all provider and transport failures.
14. prohibition on leaking provider raw errors to ordinary users.

## Redaction, DLP, And Logging Boundary

Any future real transport slice must define all of the following logging and redaction rules:

1. `Authorization` header must never be logged.
2. API key must never be logged.
3. credential request logging must never include secret value.
4. provider raw response must not be logged by default.
5. query, context, chunks, and answer logging must have explicit level and truncation rules.
6. `source_path`, `release_id`, and citation logging scope must be explicit.
7. warnings and error responses must not contain secret material.
8. debug logging must remain off by default.
9. tests and fixtures must use placeholders only and must not use real secret-like values.
10. docs, tasks, snapshot, formal map, and export artifacts must not receive credential material.

## Runtime Gate And Rollback Boundary

Any future real transport slice must preserve the following runtime-gate and rollback rules:

1. real transport must remain off by default.
2. `transport_enabled` must remain backend-owned config only.
3. any future feature flag must not come from request, router, or frontend.
4. rollback switch must be able to disable real transport.
5. after rollback, `deterministic_mock` and `disabled` must remain available.
6. `transport_enabled=False` must not call resolver.
7. `transport_enabled=False` must not call transport.
8. `no_current_release` and `insufficient_context` must not initialize provider.
9. disabled path must not initialize resolver or transport.
10. initialization failure must not silently switch to another real provider.

## API, Router, And Frontend Boundary

The following boundaries remain frozen for any future real transport work unless a later separate review explicitly changes them:

1. Ask request schema must not add provider, model, or api_key.
2. router must not call the registry directly.
3. router must not choose provider.
4. frontend must not add provider, model, or API key input.
5. administrator real-provider configuration must use a separate backend or admin configuration path.
6. `ProviderManager.active_model` must not participate in RAG provider selection.
7. `SimpleModelRouter` must not be connected to the RAG provider path without a separate dedicated review.

## Required Test Matrix For A Future Real Transport Slice

The next real transport skeleton implementation plan must cover at least the following focused tests:

1. `transport_enabled=False` blocks resolver and transport.
2. `enabled=False` blocks resolver and transport.
3. `transport_enabled=True` with missing `allowed_providers` fails.
4. `transport_enabled=True` with missing `allowed_models` fails.
5. provider not allowed fails.
6. model not allowed fails.
7. missing credential fails with redacted output.
8. blank credential fails with redacted output.
9. request-like provider/model/api_key remains ignored.
10. mocked transport success.
11. mocked timeout.
12. mocked HTTP error.
13. mocked authentication failure.
14. mocked rate-limit behavior.
15. mocked model-not-found behavior.
16. mocked invalid JSON or invalid shape behavior.
17. mocked oversized response behavior.
18. provider returns empty answer.
19. provider returns out-of-context citation ids.
20. `no_current_release` performs no provider init.
21. `insufficient_context` performs no provider init.
22. router request injection remains ignored.
23. logs and errors contain no `api_key`, secret, or `Authorization` material.

## Source-Level Risks

The current source baseline still carries the following risks that must be closed before any future real rollout:

1. current allowlist logic does not block mocked transport when `allowed_providers` or `allowed_models` is `None`; real transport must tighten this into a hard requirement.
2. `generate_answer(...)` currently normalizes payload before checking `enabled` or `transport_enabled`; future real transport work must decide whether gates should move earlier so disabled or not-connected states do not still process malformed direct payloads.
3. `SimpleModelRouter` already contains a real-provider bridge outside the RAG path; future work must not attach it to the RAG path without a separate review.
4. `build_rag_answer_with_provider(...)` still has a `provider_name` argument even though router and UI do not expose it; future work must not route that parameter into request or frontend control.

## Prohibited Items In This Round

This design review explicitly forbids the following in the current round:

1. modifying `src/`
2. modifying `console/src/`
3. implementing a real HTTP client
4. calling a real provider
5. writing a real API key
6. adding Ask request `provider`, `model`, or `api_key`
7. changing frontend
8. changing `ProviderManager.active_model` behavior
9. connecting `SimpleModelRouter` to the RAG path
10. running pytest
11. running TypeScript
12. describing this round as a shipped implementation
13. describing this round as a finished production rollout
14. describing mocked transport as a production provider

## Recommended Next Slice

The next recommended slice is a real transport skeleton implementation plan or an allowlist hardening implementation slice.

It is not a production real-provider rollout recommendation.

## Review Decision

1. `P3.external-provider-9` real transport design review is complete as a docs-only slice.
2. This review is based on current source code and current tests.
3. Current 8b gate behavior remains valid in the source baseline.
4. Real transport contract boundaries are now documented for a later slice.
5. Credential, DLP, redaction, allowlist hardening, runtime-gate, rollback, router, and frontend boundaries are now documented for a later slice.
6. This review does not change runtime behavior.
7. This review does not authorize real provider rollout.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation diff whitespace checking and keyword review confirming that the slice is not described as a shipped implementation, enabled real HTTP, enabled production provider behavior, or request-owned provider selection.
