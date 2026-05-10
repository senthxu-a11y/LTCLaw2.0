# Lane B P20.2 Transport Contract Hardening Closeout

Date: 2026-05-10
Status: completed code slice
Scope: backend-only transport contract hardening for the current RAG external-provider path

## 1. Actual Changed Files

Changed files in this slice:

1. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_external_model_client.py
3. docs/tasks/post-mvp/lane-b-p20-2-transport-contract-hardening-closeout-2026-05-10.md

## 2. Whether Source Changed

1. Yes.
2. Source changes were limited to knowledge_rag_external_model_client.py.

## 3. Whether Frontend Changed

1. No.
2. No console or frontend files were touched.

## 4. Whether Tests Changed

1. Yes.
2. Test changes were limited to tests/unit/game/test_knowledge_rag_external_model_client.py.

## 5. Whether Real HTTP Was Added

1. No.
2. This slice did not add any real HTTP call.
3. This slice did not use httpx to send requests.
4. The default transport remains non-network safe failure.

## 6. Whether Real Provider Was Added

1. No.
2. No real provider SDK was added.
3. No openai, anthropic, or other real provider path was connected.

## 7. Whether Ask Schema Changed

1. No.
2. Ask request schema remains unchanged.
3. Router ownership remains unchanged.

## 8. Whether Frontend Provider UI Changed

1. No.
2. No provider, model, or API-key UI was added.

## 9. Helper Summary

Outbound request builder:

1. Added a dedicated outbound request contract builder inside the external transport skeleton surface.
2. The builder now constructs a stable internal request mapping from normalized payload plus backend-owned config plus credential metadata.
3. The builder includes backend-owned model selection only.
4. The builder excludes API key values.
5. The builder excludes credential objects.
6. The builder excludes Authorization material.
7. The builder excludes request-owned provider, model, and api_key fields.
8. The builder excludes candidate_evidence.

Redaction helper:

1. Redaction is now centralized through a transport locator helper.
2. Query strings are removed.
3. URL userinfo is removed.
4. Redacted output is safe for preview and test assertions.

Safe parser:

1. Added a dedicated provider response parser for mapping, string, bytes, and bytearray inputs.
2. The parser accepts only the minimal response contract.
3. Malformed JSON maps to invalid response.
4. Unsupported shape maps to invalid response.
5. Empty answer maps to invalid response.

Warning mapper:

1. Added an explicit warning-code mapper for fixed safe warning text.
2. Timeout, HTTP error, invalid response, request failed, not configured, provider not allowed, model not allowed, disabled, and not connected now map through a single helper.
3. Warning text does not contain API key values, Authorization, or raw provider error text.

## 10. Gate-Order Preservation Summary

The required gate order remains unchanged:

1. enabled gate
2. transport_enabled gate
3. payload normalization
4. allowlist validation
5. credential resolution
6. transport invocation
7. response normalization

Preserved runtime behavior:

1. enabled=False still short-circuits before payload normalization.
2. transport_enabled=False still short-circuits before payload normalization.
3. allowlist failure still blocks before resolver and transport.
4. missing credential still blocks transport.
5. _normalize_response(...) remains the final response normalization path.
6. The default transport remains non-network safe failure.

## 11. Test Results

Executed validation:

1. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py -q -> 61 passed in 0.03s
2. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py -q -> 133 passed in 2.01s

## 12. git diff --check Result

1. clean

## 13. NUL Check Result

1. touched Python and docs files NUL=0

## 14. Keyword Boundary Review Result

1. clean in meaning
2. This slice does not claim production provider rollout completed.
3. This slice does not claim real provider rollout completed.
4. This slice does not claim real HTTP transport enabled.
5. This slice does not claim Ask request now supports provider, model, or api_key.
6. This slice does not claim frontend provider selector implemented.
7. This slice does not claim ProviderManager active_model now controls the RAG provider.
8. This slice does not claim SimpleModelRouter connected to the RAG provider path.
9. Current state remains not production ready.

## 15. Next Recommendation

Next recommended slice:

1. P20.3 Backend-Only Real HTTP Transport Implementation.

Constraints for the next slice remain:

1. Keep the transport backend-only.
2. Keep Ask schema unchanged.
3. Keep frontend provider UI unchanged.
4. Keep ProviderManager.active_model out of the RAG path.
5. Keep SimpleModelRouter out of the RAG path.
6. Do not describe the next slice as production rollout.