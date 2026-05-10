# Lane B P20.3 Real HTTP Transport Closeout

Date: 2026-05-10
Status: completed code slice
Scope: backend-only real HTTP transport minimal implementation for the current RAG external-provider path

## 1. Actual Changed Files

1. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_external_model_client.py
3. docs/tasks/post-mvp/lane-b-p20-3-real-http-transport-closeout-2026-05-10.md

## 2. Whether Source Changed

1. Yes.
2. Source changes were limited to knowledge_rag_external_model_client.py.

## 3. Whether Frontend Changed

1. No.
2. No frontend or console files were changed.

## 4. Whether Tests Changed

1. Yes.
2. Test changes were limited to tests/unit/game/test_knowledge_rag_external_model_client.py.

## 5. Whether Real HTTP Transport Was Added

1. Yes.
2. P20 backend-only real HTTP transport minimal implementation completed.
3. The implementation uses the existing httpx dependency.
4. The transport remains backend-owned, gated, and default-off.

## 6. Whether Production Rollout Was Added

1. No.
2. This slice is not production rollout.
3. Current state remains not production ready.

## 7. Whether Ask Schema Changed

1. No.
2. Ask request schema remains unchanged.

## 8. Whether Frontend Provider UI Changed

1. No.
2. No provider, model, or API-key UI was added.

## 9. Whether ProviderManager or SimpleModelRouter Changed

1. No.
2. ProviderManager.active_model remains out of the current RAG provider path.
3. SimpleModelRouter remains out of the current RAG provider path.

## 10. Real HTTP Implementation Summary

1. Added a concrete ExternalRagModelHttpTransport that extends the existing transport contract.
2. The real transport consumes the P20.2 outbound request builder output instead of re-deriving request shape inline.
3. The transport uses synchronous httpx.Client with fixed timeout and trust_env=False.
4. Proxy is used only when backend-owned config explicitly supplies one.
5. Authorization is built only inside the real HTTP call path.
6. Authorization never enters request preview, warnings, result payload, or test fixture text.
7. The HTTP call uses POST with JSON body and Content-Type: application/json.
8. Response bodies are fed through the P20.2 safe provider parser before final normalization.
9. Raw provider responses are not returned directly to the user.
10. Raw provider errors are not returned directly to the user.

## 11. Gate-Order Preservation Summary

The required gate order remains unchanged:

1. enabled gate
2. transport_enabled gate
3. payload normalization
4. allowlist validation
5. credential resolution
6. transport invocation
7. response normalization

Preserved behavior:

1. enabled=False still short-circuits before payload normalization and before HTTP.
2. transport_enabled=False still short-circuits before payload normalization and before HTTP.
3. allowlist failure still blocks before resolver and before HTTP.
4. missing credential still blocks before HTTP.
5. _normalize_response(...) remains the final response normalization path.
6. Answer grounding and citation checks remain in the answer path and are not bypassed by the HTTP transport.

## 12. Default-Off and Kill-Switch Summary

1. enabled=False remains the adapter kill switch.
2. transport_enabled=False remains the transport and credential kill switch.
3. Missing endpoint or base_url prevents HTTP calls.
4. Missing allowlists prevent credential resolution and HTTP calls.
5. Disallowed provider or model prevents credential resolution and HTTP calls.
6. Missing env credential prevents HTTP calls.
7. Resolver exception prevents HTTP calls and still maps to a safe warning.
8. Default config does not call httpx.

## 13. Redaction and DLP Summary

1. API key value does not enter request body.
2. API key value does not enter request preview.
3. API key value does not enter warnings or result payload.
4. Authorization header is only sent to the fake or real HTTP call boundary and is not surfaced elsewhere.
5. Endpoint query strings remain redacted in preview and debug-safe output.
6. Proxy userinfo and query strings remain redacted in preview and debug-safe output.
7. Tests use placeholder secrets only.
8. No real secret was added to docs, tests, or fixtures.

## 14. Test Results

Executed validation:

1. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py -q -> 72 passed in 0.05s
2. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py -q -> 144 passed in 1.88s

## 15. git diff --check Result

1. clean

## 16. NUL Check Result

1. touched Python and docs files NUL=0

## 17. Keyword Boundary Review Result

1. clean in meaning
2. This slice does not claim production provider rollout completed.
3. This slice does not claim real provider rollout completed.
4. This slice does not claim Ask request now supports provider, model, or api_key.
5. This slice does not claim frontend provider selector implemented.
6. This slice does not claim ProviderManager active_model now controls the RAG provider.
7. This slice does not claim SimpleModelRouter connected to the RAG provider path.

## 18. Next Recommendation

1. P20.4 Config And Credential Smoke Validation.
2. Keep the next slice backend-owned, default-off, and not production rollout.
3. Keep Ask schema, router authority, frontend provider UI, ProviderManager, and SimpleModelRouter unchanged.