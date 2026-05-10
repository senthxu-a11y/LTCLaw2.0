# Lane B P20.4 Config And Credential Smoke Closeout

Date: 2026-05-10
Status: completed test slice
Scope: config and credential smoke validation for the current backend-only real HTTP transport path

## 1. Actual Changed Files

1. tests/unit/game/test_knowledge_rag_external_model_client.py
2. docs/tasks/post-mvp/lane-b-p20-4-config-credential-smoke-closeout-2026-05-10.md

## 2. Whether Source Changed

1. No.
2. No source file changes were required for this smoke slice.

## 3. Whether Frontend Changed

1. No.
2. No frontend or console files were changed.

## 4. Whether Tests Changed

1. Yes.
2. Test changes were limited to tests/unit/game/test_knowledge_rag_external_model_client.py.

## 5. Whether Real External Network Was Called

1. No.
2. No real external network was called in tests.
3. Tests used fake httpx client boundaries and controlled local responses only.

## 6. Whether Production Rollout Was Added

1. No.
2. Backend-only real HTTP transport remains gated, default-off, and not production rollout.
3. Current state remains not production ready.

## 7. Whether Ask Schema Changed

1. No.
2. Ask request schema remains unchanged.

## 8. Whether Frontend Provider UI Changed

1. No.
2. Frontend provider UI remains unchanged.

## 9. Config Gate Summary

Validated smoke behavior:

1. enabled=False does not call the credential resolver.
2. enabled=False does not call httpx.
3. transport_enabled=False does not call the credential resolver.
4. transport_enabled=False does not call httpx.
5. Missing allowed_providers does not call the credential resolver or httpx.
6. Empty allowed_providers does not call the credential resolver or httpx.
7. Missing allowed_models does not call the credential resolver or httpx.
8. Empty allowed_models does not call the credential resolver or httpx.
9. Existing disallowed provider and disallowed model gate tests remain passing.
10. Missing base_url or endpoint does not call httpx.
11. Blank base_url or endpoint does not call httpx.
12. Config-only kill switch behavior remains intact without source changes.

## 10. Credential Gate Summary

Validated smoke behavior:

1. Missing env config metadata does not call httpx.
2. Missing env.api_key_env_var does not call httpx.
3. Blank env.api_key_env_var does not call httpx.
4. Existing env var name with missing env value does not call httpx.
5. Existing env var name with blank env value does not call httpx.
6. Resolver exception does not call httpx.
7. Missing credential warnings do not leak placeholder secret values.
8. Resolver exception warnings do not leak raw exception text.
9. Valid placeholder env value enters only the fake http boundary and does not leak into result, warning, preview, or body.

## 11. Endpoint and Proxy Redaction Summary

1. Endpoint query string redaction remains covered and passing.
2. Proxy userinfo redaction remains covered and passing.
3. Proxy query string redaction remains covered and passing.
4. httpx client construction is now smoke-tested to prove trust_env=False.
5. Proxy is passed into httpx only when backend-owned config explicitly supplies one.

## 12. Success Path Smoke Summary

1. Complete backend-owned config plus allowlist plus credential plus fake httpx success returns normalized response.
2. Success path remains backend-owned.
3. Request body does not contain API key.
4. Request preview does not contain API key.
5. Warnings and result do not contain API key.
6. Authorization exists only at the fake http boundary.
7. Model selection continues to come from backend-owned config.
8. Request-like provider, model, and api_key fields remain ignored.

## 13. Failure Path Smoke Summary

1. Timeout still maps to the safe timeout warning.
2. Non-2xx still maps to the safe HTTP error warning.
3. Connection error still maps to the safe request-failed warning.
4. Malformed JSON still maps to the invalid-response warning.
5. Unsupported response shape still maps to the invalid-response warning.
6. Empty answer still maps to the invalid-response warning.
7. Raw provider error text does not enter warnings or result payloads.

## 14. Router and Answer Integration Boundary Summary

Reviewed and revalidated through the five-file suite:

1. Ask schema still accepts only query, max_chunks, and max_chars.
2. Request body provider, model, and api_key fields do not participate in selection.
3. no_current_release still does not initialize the provider path.
4. insufficient_context still does not initialize the provider path.
5. Valid context plus backend service config remains the only route into the provider path.
6. Router authority, ProviderManager, and SimpleModelRouter remain unchanged.

## 15. Secret and DLP Verification Summary

1. Placeholder secret TEST_API_KEY_SHOULD_NOT_LEAK was used for smoke validation.
2. Secret assertions verified absence from response strings.
3. Secret assertions verified absence from warning strings.
4. Secret assertions verified absence from request preview strings.
5. Secret assertions verified absence from request body strings.
6. No real API key was written to docs, tests, logs, or fixtures.

## 16. Test Results

Executed validation:

1. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py -q -> 87 passed in 0.10s
2. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py -q -> 159 passed in 1.77s

## 17. git diff --check Result

1. clean

## 18. NUL Check Result

1. touched Python and docs files NUL=0

## 19. Keyword Boundary Review Result

1. clean in meaning
2. This slice does not claim production provider rollout completed.
3. This slice does not claim real provider rollout completed.
4. This slice does not claim Ask request now supports provider, model, or api_key.
5. This slice does not claim frontend provider selector implemented.
6. This slice does not claim ProviderManager active_model now controls the RAG provider.
7. This slice does not claim SimpleModelRouter connected to the RAG provider path.

## 20. Next Recommendation

1. P20.5 Answer-Path Integration Validation.
2. Keep the next slice backend-only real HTTP transport aware, but still not production rollout.
3. Keep Ask schema, frontend provider UI, router authority, ProviderManager, and SimpleModelRouter unchanged.