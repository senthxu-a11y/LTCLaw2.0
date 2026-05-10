# P3.external-provider-13 Real Transport Skeleton Closeout

Date: 2026-05-09
Scope: backend-only real transport skeleton implementation
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `tests/unit/game/`, and `tests/unit/routers/`

## Nature Of This Slice

This round is a backend-only real transport skeleton implementation.

It is not production rollout.

It does not connect a real provider.

It does not send real HTTP.

It does not introduce a real credential.

It does not read real env-var values.

It does not add API.

It does not change frontend.

It does not change the Ask request schema.

Router, request, and frontend still have no provider-selection authority for this path.

`ProviderManager.active_model` still does not participate in RAG provider selection.

`SimpleModelRouter` still is not connected to the RAG provider path.

## What Changed

The implementation stays inside `knowledge_rag_external_model_client.py` plus focused external-client regression tests.

Landed runtime behavior:

1. A named backend-only skeleton transport now exists as `ExternalRagModelHttpTransportSkeleton`.
2. The skeleton is non-network by design and does not call `requests`, `httpx`, `urllib` HTTP clients, `openai`, or `anthropic`.
3. The skeleton does not open sockets.
4. The skeleton does not read files.
5. The skeleton does not read `os.environ`.
6. The skeleton does not read a secret store.
7. The skeleton can build a redacted request preview for contract testing.
8. The request preview contains no `api_key` value, no `Authorization` header material, and no request-owned provider/model/api_key fields.
9. URL-like preview fields are redacted to remove query strings.
10. When the default skeleton transport is invoked without a test double, it fails safely and the client maps that failure to `External provider adapter skeleton request failed.`
11. Injected transport success and injected transport failure paths remain supported and unchanged.
12. Final response normalization still occurs only through `_normalize_response(...)`.

## What Did Not Change

The following boundaries remain intact:

1. P10 allowlist hardening remains in force.
2. P11 gate-order hardening remains in force.
3. `ExternalRagModelClient.generate_answer(...)` still runs in this order: enabled gate, transport-enabled gate, payload normalization, allowlist validation, credential resolution, transport presence or invocation, response normalization.
4. Missing credential resolver still returns `External provider adapter skeleton is not configured.`
5. Blank credential still returns `External provider adapter skeleton is not configured.`
6. Credential failure still does not fall back to another provider.
7. Ask request schema still remains only `query`, `max_chunks`, and `max_chars`.
8. Router still does not select provider and still does not call the registry directly.
9. Answer layer still owns citation grounding and still degrades empty answer, missing citation ids, and out-of-context citation ids to `insufficient_context`.
10. `no_current_release` and `insufficient_context` still return before provider initialization.
11. `candidate_evidence` still does not automatically enter provider input.

## Files Changed

Source files changed:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

Test files changed:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Docs files changed:

1. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-13-real-transport-skeleton-closeout-2026-05-09.md`
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

No router, frontend, request-schema, provider-manager, or `game/service.py` implementation files were changed in this slice.

## Focused Test Coverage Added

External-client coverage added or updated for:

1. named skeleton transport request preview is redacted
2. request preview contains no `api_key` field name or value
3. request preview contains no `Authorization` material
4. request preview ignores request-like provider/model/api_key fields
5. request preview redacts query-string-bearing URL fields
6. skeleton transport performs no file, env, or socket I/O
7. default skeleton invocation returns the safe request-failed warning without leaking secret-like text
8. disabled branch before normalization still passes
9. not-connected branch before normalization still passes
10. transport-enabled malformed payload validation still passes
11. P10 allowlist blocking behavior still passes
12. missing credential and blank credential behavior still pass
13. injected transport success, timeout, HTTP error, invalid response, and generic failure paths still pass
14. `max_output_chars` truncation still passes

## Validation

Executed validation:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` -> `32 passed in 0.04s`
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py` -> `104 passed in 1.91s`
3. `git diff --check`
4. NUL-byte scan on touched Python and docs files
5. keyword review for prohibited rollout, credential, and production-transport phrases in touched files

## Boundary Check

This slice does not:

1. connect a real provider
2. send real HTTP
3. introduce a real API key
4. read real env-var values
5. add Ask request `provider`, `model`, or `api_key`
6. change frontend or `console/src`
7. change router implementation
8. connect `ProviderManager.active_model`
9. connect `SimpleModelRouter` to the RAG path
10. implement a real credential resolver
11. implement a credential store
12. implement admin UI
13. implement runtime rollout
14. implement cost billing or real quota accounting
15. describe the skeleton as a production provider

## Result

P3.external-provider-13 is complete as a backend-only real transport skeleton implementation. The runtime path now has an explicit named non-network transport skeleton that can express redacted request-building shape for tests and default to safe failure without any real HTTP or real credential sourcing. P10 allowlist hardening and P11 gate-order hardening remain preserved, while router, request, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` boundaries remain unchanged.

## Recommended Next Step

The next recommended step is not production rollout.

The next recommended step is either:

1. a credential resolver boundary or implementation plan, still backend-only and non-production
2. an admin config boundary review for later backend-owned provider configuration, still separate from Ask and frontend request ownership