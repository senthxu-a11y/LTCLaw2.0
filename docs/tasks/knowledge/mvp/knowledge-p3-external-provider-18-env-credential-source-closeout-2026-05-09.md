# P3.external-provider-18 Backend Env-Var Credential Source Closeout

Date: 2026-05-09
Scope: backend-only env-var credential source implementation
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `tests/unit/game/`, and `tests/unit/routers/`

## Nature Of This Slice

This round is a backend-only env-var credential source implementation.

It is not production credential rollout.

It does not connect a real provider.

It does not send real HTTP.

It does not add secret-store integration.

It does not add config-file secret reads.

It does not load credentials from `ProviderManager`.

It does not connect `SimpleModelRouter` to the RAG path.

It does not add API.

It does not change frontend.

It does not change the Ask request schema.

Router, request, and frontend still have no provider-selection or credential-source authority for this path.

## What Changed

The implementation stays inside `knowledge_rag_external_model_client.py` plus focused external-client regression tests.

Landed runtime behavior:

1. A named backend-only env-aware default resolver now exists as `ExternalRagModelEnvCredentialResolver`.
2. Default external client construction now uses that env-aware resolver only when no injected `credential_resolver` and no responder-backed resolver are supplied.
3. The env-aware resolver still validates only backend-owned metadata shape: `provider_name`, `model_name`, and `env.api_key_env_var`.
4. The env-aware resolver reads `os.environ` only through `env.api_key_env_var` and only when credential resolution is actually reached.
5. Missing env metadata, blank env-var name, missing env value, blank env value, and env read exceptions all safely degrade to `External provider adapter skeleton is not configured.`
6. Resolved env-var values become `ExternalRagModelClientCredentials(api_key=...)` and continue through the existing transport contract.
7. Injected resolver seams still override the default env source unchanged.
8. Responder-backed resolver and transport seams still override the default env source unchanged.
9. The existing P13 default transport skeleton remains non-network and still safe-fails through `External provider adapter skeleton request failed.` even when env credentials resolve successfully.
10. No secret-like env value is exposed in warnings, response payloads, or request preview output.

## What Did Not Change

The following boundaries remain intact:

1. P10 allowlist hardening remains in force.
2. P11 gate-order hardening remains in force.
3. `ExternalRagModelClient.generate_answer(...)` still runs in this order: enabled gate, transport-enabled gate, payload normalization, allowlist validation, credential resolution, transport invocation, response normalization.
4. `enabled=False` still short-circuits before payload normalization and before env reads.
5. `transport_enabled=False` still short-circuits before payload normalization and before env reads.
6. Allowlist failure still short-circuits before resolver, transport, and env reads.
7. Payload normalization failure still occurs before resolver and env reads.
8. `future_external` still enters runtime only through backend-owned `external_provider_config`.
9. Ask request schema still remains only `query`, `max_chunks`, and `max_chars`.
10. Router still does not select provider and still does not call the provider registry directly.
11. `ProviderManager.active_model` still does not participate in RAG provider selection.
12. `SimpleModelRouter` still is not connected to the RAG path.
13. `secret_store` still is not connected to the RAG path.

## Files Changed

Source files changed:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

Test files changed:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`

Docs files changed:

1. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-18-env-credential-source-closeout-2026-05-09.md`
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`

No router, frontend, request-schema, provider-manager, secret-store, or `game/service.py` implementation files were changed in this slice.

## Focused Test Coverage Added Or Updated

External-client coverage added or updated for:

1. env-aware resolver returns normalized credentials from backend-owned env-var metadata
2. env-aware resolver does not import or access `secret_store` or `ProviderManager`
3. default resolver path still returns the safe not-configured warning when env config is absent
4. blank env-var name still returns the safe not-configured warning
5. missing env-var value still returns the safe not-configured warning
6. blank env-var value still returns the safe not-configured warning
7. env read exception still returns the safe not-configured warning without leaking secret-like text
8. env read only occurs after enabled gate, transport-enabled gate, payload normalization, and allowlist success
9. disabled, not-connected, allowlist-failure, and payload-normalization-failure paths do not read env
10. default env resolver plus injected transport success still uses the existing normalized response path
11. default env resolver plus default transport skeleton still safe-fails without network
12. injected resolver seam still overrides the default env source
13. responder seam still overrides the default env source

## Validation

Executed validation:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` -> `47 passed in 0.05s`
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py` -> `119 passed in 2.03s`
3. `git diff --check`
4. NUL-byte scan on touched Python and docs files
5. keyword review for prohibited rollout, credential-boundary drift, and request-schema drift phrases in touched files

## Boundary Check

This slice does not:

1. connect a real provider
2. send real HTTP
3. read secret-store values
4. read config-file secret values
5. load credentials from `ProviderManager`
6. connect `SimpleModelRouter`
7. add Ask request `provider`, `model`, or `api_key`
8. change frontend or `console/src`
9. change router provider authority
10. add admin UI
11. add a credential store
12. authorize production credential rollout

## Result

P3.external-provider-18 is complete as a backend-only env-var credential source implementation. The runtime path now has a backend-owned default env-aware resolver that reads only `env.api_key_env_var`, only after P10 and P11 guarded runtime gates succeed, and still safely degrades to the existing not-configured behavior on missing, blank, or failing env reads. Router, request, frontend, `ProviderManager.active_model`, `SimpleModelRouter`, and `secret_store` boundaries remain unchanged, while the P13 default transport skeleton remains non-network.

## Recommended Next Step

The next recommended step is not production rollout.

The next recommended step should be either:

1. a backend-only secret-source precedence review before any additional credential source is introduced
2. a backend-only real transport governance slice that keeps credential ownership and rollout approval separate