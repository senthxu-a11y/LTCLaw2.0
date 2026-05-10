# Knowledge P3.external-provider-7 Real Provider Rollout Boundary Review

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-external-provider-6-runtime-allowlist-closeout-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-5-runtime-allowlist-implementation-plan-2026-05-09.md
6. docs/tasks/knowledge-p3-external-provider-4-runtime-allowlist-boundary-2026-05-09.md
7. docs/tasks/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md
8. docs/tasks/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md
9. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
10. src/ltclaw_gy_x/game/knowledge_rag_answer.py
11. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
12. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
13. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py

## Purpose

Define the boundary, gates, test matrix, and rollback conditions that must be satisfied before any later slice may claim real provider rollout after `P3.external-provider-6`.

This slice is docs-only.

It does not modify backend code, frontend code, tests, request schema, registry contents, or public API.

It does not change current runtime behavior.

It does not connect a real provider.

It does not connect a real LLM.

It does not perform real HTTP.

It does not introduce real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

It does not complete real provider rollout in this slice.

## Current Code Facts

The current post-`P3.external-provider-6` baseline is:

1. `future_external` already exists in the backend runtime allowlist.
2. answer-layer runtime support now resolves through the registry rather than through an answer-layer external-client bypass.
3. `future_external` enters runtime path only when backend-owned `external_provider_config` is explicitly present.
4. missing `external_provider_config` for `future_external` now clear-fails.
5. the current system still is not real provider integration.
6. there is still no real LLM, no real HTTP, and no real credential integration.
7. there is still no API change, no frontend change, and no Ask request-schema change.
8. router, request body, and frontend still have no provider-selection authority.
9. request-body `provider`, `model`, and `api_key` still do not participate in selection.
10. `ProviderManager.active_model` still is not a RAG provider source.
11. `no_current_release` and `insufficient_context` still must bypass provider initialization.
12. `candidate_evidence` still must not automatically enter RAG provider input.

## What This Review Does Not Authorize

This review does not authorize any of the following:

1. real provider rollout implementation
2. real provider connection
3. real HTTP transport
4. real credential integration
5. runtime behavior change
6. request-schema expansion for provider, model, or api_key
7. frontend provider or model controls
8. router-side provider selection
9. router-side direct registry calls
10. `ProviderManager.active_model` influence on RAG provider selection
11. silent switch from one real provider to another real provider
12. production rollout in this slice

## Credential Boundary

Any future real provider rollout must satisfy all of the following credential rules:

1. real API key must not come from request body
2. real API key must not come from frontend
3. real API key must not be written into knowledge map, formal map, release snapshot, export output, docs, or tasks artifacts
4. real API key must not appear in logs, error responses, or committed test fixtures
5. credential source must remain backend-owned config or a backend-owned secure secret store
6. missing credential must clear-fail or degrade through explicit disabled-safe behavior
7. missing credential must not fall back to another real provider
8. disabled path must continue to be safe and usable after rollout machinery exists

## Provider And Model Allowlist Boundary

Any future real provider rollout must satisfy all of the following allowlist rules:

1. provider must be inside a backend-owned allowlist
2. model must be inside a backend-owned model allowlist
3. unknown provider must fail clearly
4. unknown model must fail clearly
5. request, router, and frontend must not choose real provider or model
6. `ProviderManager.active_model` must not affect RAG provider selection
7. silent switch to another real provider is forbidden

## Runtime Rollout Boundary

Any future real provider rollout must satisfy all of the following runtime rules:

1. real provider must be enabled only through explicit backend feature flag or backend-owned config
2. default runtime state must still not call a real provider
3. rollout must be able to narrow by environment, service instance, or game or knowledge scope before broader use
4. runtime failures must map to explicit internal failure modes rather than ad hoc behavior
5. `no_current_release`, `insufficient_context`, `disabled`, and comparable early-return paths must not initialize the real provider
6. `candidate_evidence` must not automatically trigger real provider calls

## HTTP Client Boundary

Any future real transport slice must define these HTTP-client rules before rollout is approved:

1. explicit timeout policy
2. explicit retry strategy
3. explicit maximum response size or parsing guard
4. explicit provider-error to internal-error mapping
5. explicit rate-limit and quota error handling
6. explicit behavior for network failure, authentication failure, model-not-found, and invalid-response cases
7. provider raw errors must not be exposed directly to ordinary users

## Logging And DLP Boundary

Any future real rollout must define and document logging and DLP behavior before code lands.

Required rules:

1. query logging level must be explicit
2. context and retrieved-chunk logging level must be explicit
3. answer logging level must be explicit
4. citation, source_path, and release_id logging level must be explicit
5. credential, authorization header, and provider raw response text must not enter ordinary logs
6. error logs must be redacted
7. debug logging must be disabled by default
8. DLP policy must define which fields may be logged, which must be hashed or truncated, and which must never be logged
9. any rollout that bypasses SVN or local-file import assumptions must still prove that real credential material is not written into docs, tasks, snapshot, formal map, or export artifacts

## API, Router, And Frontend Boundary

Any future real rollout must preserve the following UI and API constraints unless a later separate review explicitly changes them:

1. Ask request schema must not gain provider, model, or api_key fields in this path
2. router must still pass only query and existing fields
3. router must still not directly call the provider registry
4. frontend must still not expose provider, model, or API key inputs for ordinary Ask
5. any administrator real-provider configuration must use a separate backend or admin configuration path rather than the ordinary Ask path

## Testing Matrix For A Future Real Rollout Slice

Before any real provider rollout implementation is accepted, the next code slice must include at least the following focused tests:

1. registry allowlist tests
2. provider-selection tests
3. answer-path tests
4. external-client config-validation tests
5. mocked HTTP client success and failure tests
6. credential-missing tests
7. unknown provider and unknown model tests
8. router request-injection tests
9. `no_current_release` and `insufficient_context` no-init tests
10. log-redaction tests
11. docs, export, and formal-map credential-exclusion tests

The future rollout slice should also prove:

1. rate-limit and quota error handling is explicit
2. provider raw errors are not leaked to ordinary users
3. rollout disable switch returns the path to existing safe behavior without API or frontend widening

## Rollback Conditions

Any future real rollout slice must define immediate rollback or feature-flag disable triggers.

At minimum, rollback or rollout disable must happen if any of the following appears:

1. request, router, or frontend can choose provider, model, or api_key
2. credential material appears in logs, error responses, docs, snapshot, formal map, or export output
3. unknown provider or unknown model silently falls back
4. `no_current_release` or `insufficient_context` triggers real provider initialization
5. provider raw error is leaked to user-facing responses
6. real provider becomes enabled by default
7. focused tests or DLP or redaction tests fail
8. the rollout diff introduces unrelated API, frontend, or request-schema expansion

## Recommended Next Slice

The next recommended slice is a real provider rollout implementation plan or, if transport seams must be proven first, a mocked HTTP client skeleton plan.

That next slice must still not be direct production rollout.

## Review Decision

1. `P3.external-provider-7` real provider rollout boundary review is complete as a docs-only slice.
2. This review is not an implementation.
3. This review does not change runtime behavior.
4. This review does not connect a real provider.
5. This review does not perform real HTTP.
6. This review does not introduce real credential material.
7. The review records the credential, allowlist, runtime, HTTP, logging, DLP, API, router, frontend, testing, and rollback gates that must exist before any future real rollout.
8. Router, request body, frontend UI, and `ProviderManager.active_model` still have no provider-selection authority for this path.
9. Current backend runtime allowlist support for `future_external` still is not sufficient to authorize real provider rollout.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation diff whitespace checking and keyword review confirming that the slice is not described as implementation completed or real provider rollout completed.