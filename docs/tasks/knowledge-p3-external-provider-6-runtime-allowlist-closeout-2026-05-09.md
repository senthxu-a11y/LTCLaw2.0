# Knowledge P3.external-provider-6 Backend-Only Minimal Runtime Allowlist Closeout

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-external-provider-5-runtime-allowlist-implementation-plan-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-4-runtime-allowlist-boundary-2026-05-09.md
6. docs/tasks/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md
7. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
8. src/ltclaw_gy_x/game/knowledge_rag_answer.py
9. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
10. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
11. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
12. tests/unit/game/test_knowledge_rag_model_registry.py
13. tests/unit/game/test_knowledge_rag_answer.py
14. tests/unit/game/test_knowledge_rag_provider_selection.py
15. tests/unit/game/test_knowledge_rag_external_model_client.py
16. tests/unit/routers/test_game_knowledge_rag_router.py

## Closeout Goal

Close out the backend-only minimal runtime allowlist implementation for `future_external` after `P3.external-provider-5`, without widening into real provider rollout.

This closeout records a backend-only minimal runtime allowlist change.

It does not authorize real provider integration.

It does not connect a real LLM.

It does not perform real HTTP.

It does not connect real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

## Implemented Result

The landed implementation is intentionally narrow.

Current result:

1. `future_external` now exists inside the backend runtime provider allowlist.
2. Runtime entry for `future_external` is still backend-owned and still requires backend-owned config interpretation.
3. The live handoff path still remains `build_rag_answer_with_service_config(...)`.
4. Router still does not choose provider and still does not call `get_rag_model_client(...)` directly.
5. Request-body provider/model/api_key fields still do not participate in provider selection.
6. `ProviderManager.active_model` still does not participate in provider selection for this path.
7. `no_current_release` and `insufficient_context` still return before provider initialization.
8. The external client still remains disabled-by-default skeleton-only.
9. Citation grounding still remains answer-service-owned and limited to `context.citations`.
10. `candidate_evidence` still does not become automatic RAG provider input.

## Code Path Outcome

The minimal code-path change is:

1. runtime provider allowlist ownership now lives in `knowledge_rag_model_registry.py`
2. `future_external` runtime support is now resolved through the registry rather than through a direct answer-layer bypass
3. answer-layer early returns and final warning merge remain in `knowledge_rag_answer.py`
4. backend-owned `external_provider_config` still remains the only external-config source
5. missing or invalid external config for runtime-supported `future_external` now clear-fails rather than silently switching provider
6. provider initialization failure still may fall back only to `disabled` and still may not fall back to another real provider

The semantic implementation files for this slice are:

1. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_model_registry.py`
4. `tests/unit/game/test_knowledge_rag_answer.py`

The boundary-anchor files for this slice remained unchanged but were revalidated by focused tests:

1. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
3. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
4. `tests/unit/game/test_knowledge_rag_provider_selection.py`
5. `tests/unit/game/test_knowledge_rag_external_model_client.py`
6. `tests/unit/routers/test_game_knowledge_rag_router.py`

## Boundary Preservation

The following boundaries remain preserved:

1. this slice is backend-only minimal runtime allowlist, not real provider integration
2. this slice adds no real HTTP
3. this slice adds no real credential integration
4. this slice adds no API
5. this slice adds no frontend change
6. this slice adds no Ask request-schema change
7. router/request/UI still have no provider-selection authority
8. `future_external` reaches runtime path only when backend-owned config explicitly selects it
9. request-like provider/model/api_key fields remain ignored
10. `ProviderManager.active_model` remains out of scope
11. unknown provider still fails clearly
12. missing or invalid config still fails clearly or stays on the existing safe path
13. early-return paths still do not trigger provider initialization
14. `candidate_evidence` still does not enter provider input

## Validation Result

Focused validation recorded for this slice:

1. focused pytest: `86 passed in 1.44s`
2. focused scope: `test_knowledge_rag_model_registry.py`, `test_knowledge_rag_answer.py`, `test_knowledge_rag_provider_selection.py`, `test_knowledge_rag_external_model_client.py`, and `test_game_knowledge_rag_router.py`
3. NUL check: touched backend and focused test files were checked for NUL bytes
4. `git diff --check`: required as final whitespace validation for touched files

This closeout pass itself does not run frontend validation.

## Next Step

The next recommended step is a later dedicated rollout review, not direct real-provider connection in this slice.

That later step, if ever approved, must still keep runtime selection backend-owned and must still remain separate from real transport or credential integration.

## Closeout Decision

1. `P3.external-provider-6` backend-only minimal runtime allowlist implementation is complete.
2. `future_external` now exists in the backend runtime provider allowlist, but only backend-owned config may place it on the runtime path.
3. The implementation remains skeleton-only and is not real provider integration.
4. Real LLM, real HTTP, real credential integration, API expansion, frontend changes, and Ask request-schema changes all remain out of scope.
5. Router, request body, frontend UI, and `ProviderManager.active_model` still do not choose provider for this path.
6. Unknown provider still clear-fails.
7. Missing or invalid config still clear-fails or degrades only through the existing safe path.
8. Early-return and citation-grounding boundaries remain preserved.