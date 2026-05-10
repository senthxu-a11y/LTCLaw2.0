# P3.external-provider-10 Allowlist Hardening Closeout

Date: 2026-05-09
Scope: backend-only allowlist hardening for the mocked external-provider skeleton already landed in 8b
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/` and `tests/unit/game/`, plus router boundary tests under `tests/unit/routers/`

## What changed

This slice hardens the existing mocked external-provider skeleton so that `transport_enabled=True` now requires a complete backend-owned provider and model selection allowlist before credential resolution or transport can run.

Implemented runtime behavior:

1. `enabled=False` still returns `External provider adapter skeleton is disabled.` and does not require allowlists.
2. `enabled=True` with `transport_enabled=False` still returns `External provider adapter skeleton transport is not connected.` and does not require allowlists.
3. `enabled=True` with `transport_enabled=True` now treats provider and model allowlists as hard gates.
4. When `transport_enabled=True`, `allowed_providers` must normalize to a non-empty set or the client returns `External provider adapter skeleton provider is not allowed.`
5. When `transport_enabled=True`, `provider_name` must normalize to a non-empty value and be present in `allowed_providers`, or the client returns the same provider warning.
6. When `transport_enabled=True`, `allowed_models` must normalize to a non-empty set or the client returns `External provider adapter skeleton model is not allowed.`
7. When `transport_enabled=True`, `model_name` must normalize to a non-empty value and be present in `allowed_models`, or the client returns the same model warning.
8. These allowlist failures occur before credential resolver execution.
9. These allowlist failures occur before injected transport execution.
10. Request-like payload fields remain ignored by the external client prompt normalization path and are not promoted into backend-owned selection state.

## Files changed

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`
3. `tests/unit/game/test_knowledge_rag_answer.py`
4. `tests/unit/routers/test_game_knowledge_rag_router.py`

No router implementation, request schema, frontend, real HTTP transport, credential sourcing, registry provider list, or real provider rollout changes were made in this slice.

## Test coverage added or updated

Focused tests now cover:

1. `transport_enabled=True` with `allowed_providers=None` blocks before resolver and transport.
2. `transport_enabled=True` with `allowed_providers=()` blocks before resolver and transport.
3. `transport_enabled=True` with `allowed_models=None` blocks before resolver and transport.
4. `transport_enabled=True` with `allowed_models=()` blocks before resolver and transport.
5. blank `provider_name` blocks before resolver and transport.
6. blank `model_name` blocks before resolver and transport.
7. answer-path degradation when backend-owned config enables transport but omits provider or model allowlist.
8. router boundary still ignores request-injected `provider`, `model`, `api_key`, and `service_config` fields.

## Validation

Executed validation:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` -> `23 passed in 0.03s`
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py` -> `95 passed in 2.02s`
3. `git diff --check`
4. NUL-byte scan on touched Python and docs files
5. keyword review for prohibited rollout terms in touched files

## Boundary check

This slice does not:

1. add real HTTP transport
2. add real credential resolution
3. widen router authority
4. change request schema
5. expose provider or model controls to frontend
6. authorize real provider rollout

## Result

P3.external-provider-10 is complete as a backend-only hardening slice. The mocked external-provider path now requires explicit backend-owned transport authorization and explicit non-empty backend-owned provider and model allowlists before any credential or transport seam can execute.