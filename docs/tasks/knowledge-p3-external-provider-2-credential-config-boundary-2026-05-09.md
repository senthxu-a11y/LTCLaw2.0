# Knowledge P3.external-provider-2 Credential/Config Skeleton Implementation Closeout

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-provider-credential-boundary-review-2026-05-09.md
5. docs/tasks/knowledge-p3-rag-model-provider-selection-boundary-review-2026-05-08.md
6. docs/tasks/knowledge-p3-rag-model-3-external-provider-adapter-boundary-review-2026-05-08.md

## Closeout Goal

Close out the backend-only credential/config skeleton implementation after the earlier boundary review and record what landed without authorizing real provider rollout.

This closeout is docs-only.

The recorded implementation remains a backend-only credential/config skeleton.

It does not add frontend provider/model UI, does not change the request schema, does not add API, and does not authorize runtime rollout.

It does not connect a real provider.

## Confirmed Current Baseline

The current baseline is:

1. `P3.external-provider-1` is complete as a backend external provider adapter skeleton.
2. The current slice has now landed the next backend-only credential/config skeleton layer on that adapter boundary.
3. The current implementation is still not a real LLM integration.
4. The current implementation still does not perform real HTTP.
5. The current implementation still does not read real credential material.
6. Runtime providers still remain only `deterministic_mock` and `disabled`.
7. Frontend still exposes no provider or model UI.
8. `Ask` still sends only `{ query }`.
9. Router still does not directly choose provider.
10. Citation validation still remains owned by the answer service and still validates only against `context.citations`.

## Core Decision

The landed credential/config skeleton remains backend-owned, disabled-by-default, and outside the request or frontend surface.

It defines backend-only config and resolver shapes, but it does not grant runtime rollout, frontend control, request-body control, or real provider connectivity.

## Implemented Shape

The landed backend-owned config shape includes:

1. `enabled`
2. `provider_name`
3. optional `model_name`
4. `timeout_seconds` with default `15`
5. optional `base_url`
6. optional `proxy`
7. optional `max_output_tokens`
8. `allowed_providers`
9. `allowed_models`
10. optional env config entry shape

The landed credential boundary also adds a backend-owned credential request shape that carries provider name, optional model name, and optional env entry metadata into the credential resolver abstraction.

The responder compatibility bridge remains limited to local fake transport and test seam compatibility.

## Landed Behavior

### 1. Credential source

Credential handling remains backend-owned only.

Credential material still does not come from:

1. frontend UI
2. request body
3. RAG query body
4. GameProject state
5. ad hoc per-request transport config

Env remains only an optional backend-owned entry shape in this slice.

It still does not authorize frontend-driven or request-driven secret input, and it still does not authorize live runtime rollout from env presence alone.

Missing credential now records the intended safe implementation behavior:

1. return a controlled backend warning
2. do not fabricate answer text
3. degrade to safe non-answer behavior

### 2. Provider config source

Provider and model selection remain backend-only.

They still do not come from:

1. frontend provider UI
2. frontend model UI
3. request body
4. query body
5. GameProject state
6. `ProviderManager.active_model`

Allowed control points remain:

1. backend app config
2. backend service config
3. explicit dependency injection

The landed implementation now includes backend allowlist shape and disabled-by-default enablement.

### 3. Allowlist and disabled-by-default behavior

`enabled` defaults to false.

Allowlist validation now occurs before credential resolver and transport.

That means:

1. explicit enable flag is required
2. allowlist membership is required
3. usable credential source is required
4. missing any of the above keeps the provider effectively disabled
5. allowlist failure degrades safely without entering the external call path

### 4. Runtime enablement

Current runtime providers still remain only `deterministic_mock` and `disabled`.

This slice does not add runtime provider rollout.

Future runtime allowlist entry for any external provider remains blocked until a later dedicated rollout review.

### 5. Secret handling and transport boundary

The implementation still does not perform real HTTP and still does not read real credential material.

The secret-handling boundary remains conservative:

1. API key must never be logged raw
2. Authorization header must never be logged raw
3. raw credential material must never be logged raw
4. env entry shape still does not authorize raw secret exposure

`proxy` and `base_url` remain backend-owned config shape only in this slice.

### 6. Safe degradation

The implementation now records and proves the following safe degradation behavior:

1. missing credential does not generate fake answer
2. disabled state does not generate fake answer
3. allowlist failure does not generate fake answer
4. allowlist failure does not enter credential resolver or transport
5. the answer path still degrades conservatively rather than fabricating grounded output

### 7. Early-return boundary

`no_current_release` and `insufficient_context` still do not trigger provider/config/credential path execution.

That boundary remains ahead of provider resolution and ahead of external adapter credential behavior.

### 8. Request-boundary proof

The implementation now proves that request-like provider hints do not participate in selection.

Recorded proof shape:

1. Ask payload still remains `{ query }`
2. request-like `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection
3. backend config or DI remains the only provider-selection source in this slice

## Implementation Result

1. `P3.external-provider-2` implementation is complete.
2. The implementation is still a credential/config skeleton and is not real external provider integration.
3. The implementation does not perform real HTTP.
4. The implementation does not read real credential material.
5. The implementation adds no frontend provider/model UI.
6. The implementation adds no RAG request schema change.
7. The implementation adds no runtime provider rollout.
8. Runtime providers still remain only `deterministic_mock` and `disabled`.
9. `enabled` defaults to false.
10. Allowlist validation occurs before credential resolver and transport.
11. Missing credential, disabled state, and allowlist failure all degrade safely and do not generate fake answer.
12. `no_current_release` and `insufficient_context` still do not trigger provider/config/credential path execution.
13. Request-like `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection.

## Recommended Next Slice

The next reasonable step is backend service config wiring boundary review, followed by backend service config wiring skeleton implementation, still backend-only and still without runtime rollout.

That next slice should:

1. freeze how backend service config is handed into the existing answer path without widening router authority
2. keep runtime providers limited to `deterministic_mock` and `disabled`
3. keep GameProject, request schema, endpoint surface, and router boundary unchanged
4. keep real provider rollout deferred

## Validation Note

Recorded implementation validation from the code round:

1. focused pytest: `59 passed in 1.04s`
2. NUL check for the touched Python files: all `0`
3. `git diff --check` reported no whitespace error for this slice
4. the only `git diff --check` output was pre-existing unrelated line-ending warnings for docs/tasks/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md, scripts/README.md, scripts/migrate_to_cdev.ps1, and scripts/wheel_build.ps1

This closeout pass itself is docs-only.

This docs-only pass does not run pytest.

This docs-only pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation error checking and docs diff whitespace checking.
