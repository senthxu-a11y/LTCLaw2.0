# P3.external-provider-15 Credential Resolver Skeleton Closeout

Date: 2026-05-09
Scope: backend-only credential resolver skeleton implementation
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `tests/unit/game/`, and `tests/unit/routers/`

## Nature Of This Slice

This round is a backend-only credential resolver skeleton implementation.

It is not production credential rollout.

It does not connect a real provider.

It does not send real HTTP.

It does not introduce a real credential source.

It does not read env-var values.

It does not integrate a secret store.

It does not read config-file secret values.

It does not load credentials from `ProviderManager`.

It does not connect `SimpleModelRouter` to the RAG path.

It does not add API.

It does not change frontend.

It does not change the Ask request schema.

Router, request, and frontend still have no provider-selection authority for this path.

## What Changed

The implementation stays inside `knowledge_rag_external_model_client.py` plus focused external-client regression tests.

Landed runtime behavior:

1. A named backend-only credential resolver skeleton now exists as `ExternalRagModelCredentialResolverSkeleton`.
2. The default external client construction now uses that resolver skeleton when no injected `credential_resolver` or responder-backed resolver is supplied.
3. The resolver skeleton validates only backend-owned metadata shape: `provider_name`, `model_name`, and `env.api_key_env_var` as a variable name only.
4. The resolver skeleton returns `None` by default and therefore drives the existing safe not-configured path.
5. The resolver skeleton does not read `os.environ`, does not open files, does not open sockets, does not import or access `secret_store`, and does not import or access `ProviderManager`.
6. Injected resolver seams still work unchanged.
7. Injected resolver success plus injected transport success still uses the existing normalized response path.
8. Injected resolver success plus the existing P13 default transport skeleton still safe-fails through `External provider adapter skeleton request failed.`
9. Resolver exceptions are now mapped back to the safe not-configured warning rather than surfacing raw exception text.
10. Blank `api_key` still maps to `External provider adapter skeleton is not configured.`

## What Did Not Change

The following boundaries remain intact:

1. P10 allowlist hardening remains in force.
2. P11 gate-order hardening remains in force.
3. `ExternalRagModelClient.generate_answer(...)` still runs in this order: enabled gate, transport-enabled gate, payload normalization, allowlist validation, credential resolution, transport invocation, response normalization.
4. `enabled=False` still short-circuits before payload normalization.
5. `transport_enabled=False` still short-circuits before payload normalization.
6. Allowlist failure still short-circuits before resolver and transport.
7. `future_external` still enters runtime only through backend-owned `external_provider_config`.
8. Ask request schema still remains only `query`, `max_chunks`, and `max_chars`.
9. Router still does not select provider and still does not call the provider registry directly.
10. `ProviderManager.active_model` still does not participate in RAG provider selection.
11. `SimpleModelRouter` still is not connected to the RAG path.
12. P13 transport skeleton remains non-network and still produces redacted request preview only.

## Files Changed

Source files changed:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

Test files changed:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Docs files changed:

1. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-15-credential-resolver-skeleton-closeout-2026-05-09.md`
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

No router, frontend, request-schema, provider-manager, secret-store, or `game/service.py` implementation files were changed in this slice.

## Focused Test Coverage Added Or Updated

External-client coverage added or updated for:

1. named resolver skeleton returns `None` by default
2. resolver skeleton performs no file, env, socket, secret-store, or provider-manager import access
3. missing or default resolver path still returns the safe not-configured warning
4. resolver returning `None` still returns the safe not-configured warning
5. blank credential still returns the safe not-configured warning
6. resolver exception now returns the safe not-configured warning without leaking secret-like text
7. P10 allowlist blocking behavior still prevents resolver and transport calls
8. P11 disabled and not-connected gates still prevent resolver and transport calls before normalization
9. injected resolver plus injected transport success path still normalizes answer, citation ids, and warnings
10. injected resolver plus default P13 transport skeleton still safe-fails without network
11. request preview still excludes `api_key`, `Authorization`, and request-owned provider/model/api_key fields
12. endpoint query strings still remain redacted in preview output

## Validation

Executed validation:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` -> `34 passed in 0.04s`
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py` -> `106 passed in 1.93s`
3. `git diff --check`
4. NUL-byte scan on touched Python and docs files
5. keyword review for prohibited rollout, credential, request-schema, and provider-boundary phrases in touched files

## Boundary Check

This slice does not:

1. connect a real provider
2. send real HTTP
3. read env-var values
4. read a secret store
5. read config-file secret values
6. load credentials from `ProviderManager`
7. connect `SimpleModelRouter`
8. add Ask request `provider`, `model`, or `api_key`
9. change frontend or `console/src`
10. change router provider authority
11. add admin UI
12. add a credential store
13. authorize production credential rollout

## Result

P3.external-provider-15 is complete as a backend-only credential resolver skeleton implementation. The runtime path now has an explicit named default resolver skeleton that validates only backend-owned metadata shape and safely degrades to the existing not-configured behavior without reading env values, secret stores, config-file secrets, or provider-manager state. P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton all remain preserved, while router, request, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` boundaries remain unchanged.

## Recommended Next Step

The next recommended step is not production rollout.

The next recommended step is either:

1. an admin config boundary review for future backend-owned credential governance
2. a credential source governance plan that defines future secret-source precedence, redaction, rollback, and review gates before any later production work