# Knowledge P3.external-provider-12 Real Transport Skeleton Implementation Plan

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-11-gate-order-hardening-closeout-2026-05-09.md
2. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-10-allowlist-hardening-closeout-2026-05-09.md
3. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-9-real-transport-design-review-2026-05-09.md
4. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8b-mocked-http-client-skeleton-closeout-2026-05-09.md
5. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8a-mocked-http-client-skeleton-implementation-plan-2026-05-09.md
6. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-7-real-provider-rollout-boundary-2026-05-09.md
7. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
8. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
9. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
10. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
11. src/ltclaw_gy_x/game/knowledge_rag_answer.py
12. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
13. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
14. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
15. src/ltclaw_gy_x/game/service.py
16. tests/unit/game/test_knowledge_rag_external_model_client.py
17. tests/unit/game/test_knowledge_rag_answer.py
18. tests/unit/game/test_knowledge_rag_provider_selection.py
19. tests/unit/game/test_knowledge_rag_model_registry.py
20. tests/unit/routers/test_game_knowledge_rag_router.py

## Nature Of This Round

This slice is a docs-only implementation plan.

It is not implementation.

It is not production rollout.

It does not connect a real provider.

It does not send real HTTP.

It does not introduce real credential material.

It does not add API.

It does not change frontend.

It does not change the Ask request schema.

It does not change router provider-selection authority.

It does not change `ProviderManager.active_model` behavior.

It does not connect `SimpleModelRouter` to the RAG path.

This round records the next implementation contract only.

## Source-Based Baseline

This plan is based on current source code and current tests rather than on prior docs alone.

Current source-truth baseline:

1. `ExternalRagModelClient.generate_answer(...)` now checks `enabled` first.
2. `ExternalRagModelClient.generate_answer(...)` now checks `transport_enabled` second.
3. Only `enabled=True` plus `transport_enabled=True` enters `_normalize_prompt_payload(...)`.
4. P10 allowlist hardening is live in source: `allowed_providers` must be non-empty, `allowed_models` must be non-empty, `provider_name` must be non-empty and allowed, and `model_name` must be non-empty and allowed.
5. Allowlist failure still occurs before credential resolution and before injected transport.
6. Current external client still has only injected `transport` and injected `responder` seams.
7. Current code still has no real HTTP client.
8. Current code still has no real credential resolver.
9. Ask request schema still exposes only `query`, `max_chunks`, and `max_chars`.
10. Router still does not choose provider and still does not call `get_rag_model_client(...)` directly.
11. `ProviderManager.active_model` still does not participate in RAG provider selection.
12. `SimpleModelRouter` still exists only outside the RAG path.
13. `no_current_release` and `insufficient_context` still short-circuit before provider initialization.
14. `candidate_evidence` still does not automatically enter RAG provider input.
15. `ExternalRagModelEnvConfig.api_key_env_var` still exists as backend-owned config shape, but current source still does not read real env-var values.

P10 and P11 are required preconditions for the next implementation round and are already complete in source.

## Next-Round Allowed Code Surface

The next round, recommended as `P3.external-provider-13` real transport skeleton implementation, must stay narrow.

Maximum allowed semantic implementation surface:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

Allowed only if strictly necessary for narrow plumbing or regression protection:

1. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`

Not allowed in the next round:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `console/src/`
3. provider-manager-related code
4. `src/ltclaw_gy_x/game/service.py`
5. `SimpleModelRouter`
6. Ask request or response schema

## What The Next Round May Do

The next round may implement only a real transport skeleton, not a production transport path.

Allowed next-round work:

1. add a transport helper or class that is injectable and disabled by default
2. keep transport backend-owned and reachable only through explicit backend-owned config
3. keep transport fully replaceable by mocks and test doubles
4. define request-building shape for a future HTTP call without emitting a real request
5. preserve `_normalize_response(...)` as the only response-normalization path
6. preserve answer-layer grounding as the only citation-grounding authority
7. preserve answer-layer degradation for empty answer, empty citation ids, or out-of-context citation ids
8. preserve P10 allowlist hardening and P11 gate-order hardening as hard prerequisites before any transport seam is attempted

The next round must still not access the real network in tests or default runtime behavior.

## What The Next Round Still Must Not Do

The next implementation round must explicitly forbid all of the following:

1. connect a production provider
2. send real HTTP
3. introduce a real API key
4. read real env-var values
5. add Ask request `provider`, `model`, or `api_key`
6. change frontend
7. give router provider-selection authority
8. connect `ProviderManager.active_model` to RAG provider selection
9. connect `SimpleModelRouter` to the RAG path
10. describe mocked or skeleton transport as a production provider
11. implement a credential store
12. implement admin UI
13. perform runtime rollout
14. implement cost billing or real quota accounting
15. widen retrieval or automatically inject `candidate_evidence`

## Transport Contract For The Next Round

The next-round skeleton transport contract must be explicit.

Required call contract:

1. input payload: normalized `RagAnswerPromptPayload`
2. input config: backend-owned `ExternalRagModelClientConfig`
3. input credentials: backend-owned `ExternalRagModelClientCredentials`

The input payload must not contain:

1. `provider_name`
2. `model_name`
3. `api_key`
4. credential object
5. `Authorization` header material
6. raw request-body-owned provider hints

Config fields that the next-round skeleton may read are limited to:

1. `provider_name`
2. `model_name`
3. `timeout_seconds`
4. `max_output_tokens`
5. `base_url`
6. `proxy`
7. `allowed_providers`
8. `allowed_models`
9. `max_prompt_chars`
10. `max_output_chars`

Credential object fields must remain minimal:

1. `api_key`
2. `endpoint`, only if strictly required by the skeleton seam

Output contract:

1. transport output must be a mapping
2. final normalized model response must still be produced only through `_normalize_response(...)`
3. normalized shape must remain limited to `answer`, `citation_ids`, and `warnings`
4. transport must not directly construct final answer payloads returned by the answer service
5. transport must not directly access release artifacts outside the already-supplied prompt payload
6. transport must not read files, SVN, snapshots, formal maps, docs, or task artifacts

## Credential Resolver Boundary For The Next Round

The next-round implementation should not implement a real credential resolver.

Required plan conclusion:

1. next-round real transport skeleton implementation does not implement a real credential resolver
2. next-round path still allows only injected `credential_resolver`
3. injected resolver is only a backend-owned seam for tests or explicit backend-owned injection
4. next round must not read `os.environ`
5. next round must not read a secret store
6. next round must not read secret values from config files
7. next round must not write env-var values into docs, tests, or logs
8. missing `credential_resolver` must continue to return `External provider adapter skeleton is not configured.`
9. blank credential must continue to return `External provider adapter skeleton is not configured.`
10. credential failure must not fall back to another provider

## HTTP Skeleton Design Requirements

The next-round skeleton design must answer these implementation questions without widening into rollout:

1. whether to add a helper or class such as `ExternalRagModelHttpTransportSkeleton`
2. whether that helper stays in `knowledge_rag_external_model_client.py` or a new backend-only file, with strong preference for staying local unless file size or clarity makes a helper extraction necessary
3. default construction must not enable any real network path
4. skeleton may define request-building shape only and must not emit a request by default
5. any HTTP-like failure simulation must happen only through injected transport or a test double
6. timeout, HTTP error, auth failure, rate limit, model not found, invalid response, and oversized response all must map to safe redacted warnings
7. warning text must not contain provider raw error text, `api_key`, `Authorization`, or secret-bearing endpoint fragments
8. output size must remain protected by `max_output_chars`
9. prompt size must remain protected by `max_prompt_chars`
10. retry must remain disabled unless separately reviewed later

## Error Mapping Requirements

The next-round skeleton must preserve at least the following warning mappings:

1. timeout -> `External provider adapter skeleton timed out.`
2. provider HTTP error -> `External provider adapter skeleton HTTP error.`
3. invalid response -> `External provider adapter skeleton returned an invalid response.`
4. generic request failure -> `External provider adapter skeleton request failed.`
5. missing credential -> `External provider adapter skeleton is not configured.`
6. missing transport -> `External provider adapter skeleton transport is not connected.`
7. disabled -> `External provider adapter skeleton is disabled.`
8. provider not allowed -> `External provider adapter skeleton provider is not allowed.`
9. model not allowed -> `External provider adapter skeleton model is not allowed.`
10. any new auth, rate-limit, or model-not-found warning must stay generic and redacted

## Redaction, DLP, And Logging Requirements

The next-round skeleton must preserve and document the following DLP and redaction rules:

1. API key must not enter prompt payload
2. API key must not enter warnings
3. API key must not enter error responses
4. API key must not enter logs
5. API key must not enter docs or task artifacts
6. API key must not enter snapshot, formal-map, or export artifacts
7. `Authorization` header must never be logged
8. provider raw response must not be logged by default
9. endpoint values with secret-like query strings must not be logged
10. tests must use placeholders only and must not use real secret-like keys
11. touched-file NUL checking remains part of validation
12. any DLP failure must block future rollout approval

## API, Router, And Frontend Boundary Freeze

The next round must keep all of the following frozen:

1. Ask request schema does not gain `provider`, `model`, or `api_key`
2. router does not directly call the registry
3. router does not choose provider
4. frontend does not expose provider, model, or API key inputs
5. `service_config` does not come from request body
6. `ProviderManager.active_model` does not participate in RAG provider selection
7. `SimpleModelRouter` does not connect to the RAG path
8. any administrator or config-management path requires a separate review and must not be mixed into ordinary Ask

## Focused Test Matrix For The Next Round

The next-round implementation must use the following focused test files:

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_provider_selection.py`
4. `tests/unit/game/test_knowledge_rag_model_registry.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

External-client tests required:

1. disabled branch before normalization
2. not-connected branch before normalization
3. `transport_enabled=True` malformed payload still validates
4. missing `allowed_providers` blocks resolver and transport
5. missing `allowed_models` blocks resolver and transport
6. provider not allowed blocks resolver and transport
7. model not allowed blocks resolver and transport
8. missing credential resolver returns not configured
9. blank credential returns not configured and remains redacted
10. injected transport success
11. injected transport timeout
12. injected transport HTTP error
13. injected transport invalid response shape
14. injected transport generic failure
15. request-like `provider_name`, `model_name`, and `api_key` remain ignored
16. response truncation still respects `max_output_chars`
17. default path still performs no network, file, or env I/O

Answer-layer tests required:

1. external warning response degrades to `insufficient_context`
2. provider answer with valid grounded citation returns `answer`
3. provider answer without citation degrades
4. provider answer with out-of-context citation degrades
5. `no_current_release` does not initialize provider
6. `insufficient_context` does not initialize provider

Router tests required:

1. request injection of `provider`, `model`, `api_key`, and `service_config` remains ignored
2. router does not call registry directly
3. router only passes `game_service` into the answer service
4. Ask schema remains unchanged

Provider-selection and registry regression still must prove:

1. backend-owned external config remains the only source of provider and model selection
2. deterministic mock and disabled paths remain unchanged
3. unknown provider still clear-fails
4. provider-factory failure still falls back only to disabled with warnings

## Completion Standard For This Plan

This plan is complete only if it clearly states that:

1. P12 is docs-only implementation planning
2. P12 does not change runtime behavior
3. the next round still is not production rollout
4. the next round still must not send real HTTP
5. the next round still must not introduce real credential material
6. the next round still must not change API, router, frontend, or Ask request schema
7. P10 and P11 hardening are already completed preconditions
8. the next recommended slice is `P3.external-provider-13` real transport skeleton implementation, not production rollout

## Source-Level Risks Or Follow-Ups

Any future deviation between code and docs must be recorded as a risk or follow-up rather than described as a completed capability.

Current source-level notes to preserve:

1. `ExternalRagModelEnvConfig.api_key_env_var` exists in config shape, but current source still does not read env values
2. current transport seam is still fully injected, so any next-round helper must preserve that seam rather than silently replacing it with a real client
3. current answer-layer grounding remains the controlling boundary for citations and must not be moved into transport code

## Recommended Next Slice

The next recommended slice is `P3.external-provider-13` real transport skeleton implementation.

That next slice must remain backend-only, skeleton-only, and non-production.

It must not be a production rollout slice.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review confirming that the text does not claim completed rollout, completed real HTTP, completed credential resolver implementation, or widened request/router/frontend authority.