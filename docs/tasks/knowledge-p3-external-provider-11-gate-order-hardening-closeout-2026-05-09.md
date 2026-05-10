# P3.external-provider-11 Gate-Order Hardening Closeout

Date: 2026-05-09
Scope: backend-only gate-order hardening for the mocked external-provider skeleton path
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/` and `tests/unit/game/`, plus router boundary tests under `tests/unit/routers/`

## Nature Of This Slice

This round is a gate-order hardening implementation.

It is not real provider rollout.

It adds no real HTTP.

It adds no real credential.

It adds no API.

It does not change frontend.

It does not change the Ask request schema.

Router, request, and frontend still have no provider-selection authority for this path.

`ProviderManager.active_model` still does not participate in RAG provider selection.

`SimpleModelRouter` still is not connected to the RAG provider path.

## What Changed

The implementation is intentionally narrow and stays inside `ExternalRagModelClient.generate_answer(...)` plus focused tests.

Current runtime behavior:

1. `enabled=False` now returns `External provider adapter skeleton is disabled.` before payload normalization.
2. `enabled=True` with `transport_enabled=False` now returns `External provider adapter skeleton transport is not connected.` before payload normalization.
3. disabled and not-connected branches no longer attempt prompt-payload normalization for malformed direct payload input.
4. disabled and not-connected branches still do not call credential resolver.
5. disabled and not-connected branches still do not call injected transport.
6. disabled and not-connected branches still do not require `allowed_providers`.
7. disabled and not-connected branches still do not require `allowed_models`.
8. only `enabled=True` and `transport_enabled=True` now proceeds into `_normalize_prompt_payload(...)`.
9. when transport is enabled, malformed payload behavior remains unchanged: non-mapping, malformed `chunks`, and `max_prompt_chars` violations still raise the same validation exceptions.
10. P10 allowlist hardening remains in place after payload normalization.
11. allowlist failure still blocks credential resolver and transport.
12. mocked transport seam still enters only through injected `transport` or `responder`.
13. normalized transport payload still excludes request-like `provider_name`, `model_name`, and `api_key` fields.
14. backend-owned config still remains the source of provider and model selection.

## Files Changed

Source file changed:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

Test files changed:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Docs files changed:

1. `docs/tasks/knowledge-p3-external-provider-11-gate-order-hardening-closeout-2026-05-09.md`
2. `docs/tasks/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md`

No answer-layer, registry, provider-selection, router, frontend, or Ask request-schema implementation changes were required in this slice.

## Test Coverage Added Or Updated

Focused external-client tests now cover:

1. disabled client plus non-mapping malformed payload returns disabled warning without exception.
2. disabled client plus malformed mapping payload returns disabled warning without exception.
3. not-connected client plus non-mapping malformed payload returns not-connected warning without exception.
4. not-connected client plus malformed mapping payload returns not-connected warning without exception.
5. early disabled and not-connected branches do not call resolver.
6. early disabled and not-connected branches do not call transport.
7. transport-enabled path still raises `RAG prompt payload must be a mapping.` for non-mapping payload.
8. transport-enabled path still raises `RAG prompt payload chunks must be a list.` for malformed chunks.
9. transport-enabled path still raises the existing `max_prompt_chars` validation error for oversize prompt input.
10. P10 allowlist hardening cases remain covered.
11. request-like payload injection remains covered.
12. mocked transport success path remains covered.

## Validation

Executed validation:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` -> `29 passed in 0.04s`
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py`
3. `git diff --check`
4. NUL-byte scan on touched Python and docs files
5. keyword review for prohibited rollout and integration phrases in touched files

## Boundary Check

This slice does not:

1. connect a real provider
2. send real HTTP
3. introduce a real API key
4. read real env var values
5. add Ask request `provider`, `model`, or `api_key`
6. change frontend or `console/src`
7. connect `ProviderManager.active_model`
8. connect `SimpleModelRouter` to the RAG path
9. implement a real credential resolver
10. implement an HTTP transport client

## Result

P3.external-provider-11 is complete as a backend-only gate-order hardening slice. Disabled and not-connected states now short-circuit before payload normalization, while transport-enabled path still performs the existing payload validation and still preserves P10 allowlist hardening. The next recommended step is a real transport skeleton implementation plan rather than any production rollout.