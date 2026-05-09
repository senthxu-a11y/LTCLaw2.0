# Knowledge P3.provider-credential-boundary-review

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-provider-selection-boundary-review-2026-05-08.md
5. docs/tasks/knowledge-p3-rag-model-3-external-provider-adapter-boundary-review-2026-05-08.md
6. docs/tasks/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md

## Review Goal

Freeze the credential, transport, timeout, retry, cost, logging, privacy, grounding, read, and failure boundaries that must be settled before any real external provider is connected.

This review is docs-only.

It does not modify backend code, frontend code, request schema, provider registry runtime, router behavior, or public API.

It does not implement a real provider.

## Confirmed Current Baseline

The current baseline is:

1. `P3.8` RAG MVP interaction and i18n closeout are complete.
2. The current GameProject RAG entry is still MVP-only and not production-grade RAG.
3. `Ask` still sends only `{ query }`.
4. The current frontend exposes no provider or model selector.
5. Runtime providers remain only `deterministic_mock` and `disabled`.
6. Provider selection is already constrained to backend service, config, and dependency-injection boundaries.
7. `ProviderManager.active_model` is still not approved as the RAG live source of truth.
8. Router still does not call provider code directly.
9. The answer service still consumes only bounded context payload and still performs citation validation against `context.citations`.
10. No real external LLM, credential store, or provider transport is implemented yet.

## Core Decision

Any future real external provider must remain a backend-only injected model client behind the existing provider-selection and answer-service boundaries.

The provider must never become a frontend-controlled, request-body-controlled, router-controlled, or raw-artifact-reading dependency.

## Boundary Answers

### 1. Where do credentials come from?

Credentials must be backend-owned only.

They must not come from:

1. frontend request body
2. RAG query body
3. GameProject UI state
4. provider hint fields added to the current RAG request contract
5. ad hoc per-request transport config

Allowed sources for a future real-provider path are:

1. server-side config for non-secret provider selection policy, model allowlist, timeout policy, and budget policy
2. backend-owned environment variables for secret material only if a later implementation explicitly opts in under the conditions below
3. a future backend credential store for durable, rotatable, non-frontend-owned secret storage

Environment variables are not approved as the live source of truth for provider or model selection.

If a later slice allows environment variables for credentials, that allowance must stay narrow and must require all of the following:

1. process-start or deployment-time ownership by the server, never request-time input
2. explicit backend config or DI still deciding provider and model selection
3. no frontend visibility and no serialization into API responses or warnings
4. no logging of raw env values
5. clear startup or first-use failure when required secret material is missing

A credential store is not implemented in this slice, but this review recommends that any path beyond single-deployment development use a dedicated backend credential store before real provider rollout.

### 2. Where does provider or model selection come from?

Provider and model selection remain backend-only.

They must not come from:

1. frontend provider UI
2. frontend model UI
3. RAG request body
4. provider hint fields in `Ask`
5. `ProviderManager.active_model` in this slice

Allowed control points remain:

1. backend service config
2. backend app config
3. explicit dependency injection

This review allows a future backend allowlist.

That allowlist should be backend-owned and should constrain:

1. allowed provider ids
2. allowed model ids per provider
3. whether a provider is enabled at all
4. which agent or service path may use which provider or model

### 3. What is the transport boundary?

The external provider client must remain a single injected model client behind the existing protocol boundary.

That means:

1. router must still not call provider code directly
2. router must still not construct provider payloads directly
3. answer service must still consume only bounded context payload plus query
4. provider adapter must receive only bounded payload prepared by the answer path
5. provider adapter must not read raw source, pending state, SVN, release artifacts, or candidate evidence directly

### 4. What are the timeout, retry, and cancellation rules?

Recommended first-version timeout policy:

1. one backend request timeout per external provider call
2. recommended default ceiling: 15 seconds
3. hard upper bound should remain backend-owned, not frontend-owned

Retry is not recommended for the first real-provider path by default.

Reason:

1. retry can amplify cost
2. retry can amplify latency
3. retry can duplicate provider-side spend on the same query
4. retry can complicate cancellation and failure semantics before budgets are in place

If a later slice introduces retry, it should default to at most one bounded retry on narrowly classified transport failures only, never on generic timeout, budget, or invalid-response cases.

Frontend behavior for timeout should remain conservative:

1. do not fabricate answer text
2. surface safe warning or failure copy
3. degrade to `insufficient_context` where the current answer contract requires safe non-answer fallback

### 5. What are the cost and token boundaries?

Yes, a future real-provider path must enforce bounded context size.

Minimum recommended backend guardrails:

1. max chunks
2. max chars
3. max output tokens or equivalent provider-specific response cap
4. optional per-request budget ceiling
5. optional per-agent budget ceiling for cumulative spend control

This review recommends keeping the existing bounded-context discipline mandatory and adding output-token caps before any real provider is connected.

Estimated cost recording is recommended, but only as backend-owned metadata.

Any cost recording must avoid leaking secret material and should not depend on frontend request fields.

### 6. What are the logging and privacy rules?

Logging must remain conservative.

Rules:

1. never log API key or other raw secret values
2. never log authorization headers
3. never log raw environment-variable values
4. apply redaction to any structured log fields that may accidentally carry secret-like values

For query and context logging:

1. full query logging should be treated as sensitive and should be avoidable or disabled by default for production-like paths
2. full chunk logging should not be enabled by default
3. citation payload logging may be allowed only in bounded diagnostic form and should remain limited to existing safe citation metadata already produced by the bounded context path

This review recommends explicit redaction support for:

1. secrets
2. authorization headers
3. provider request payload fields that may contain secret material
4. any debug fields that accidentally include query or chunk bodies beyond approved limits

### 7. What is the grounding and citation rule?

The grounding rule remains unchanged and mandatory.

Rules:

1. provider output citation ids must still validate only against `context.citations`
2. provider must not invent citation ids outside the provided context
3. provider must not invent new source references outside the bounded payload
4. if citation ids are invalid, the answer must degrade safely
5. if answer text is empty or unusable, the answer must degrade safely

Safe degradation in this path means warning plus `insufficient_context` where appropriate, never fabricated grounded answer.

### 8. What is the read boundary?

Provider client read authority remains strictly bounded.

Provider client must not read:

1. raw source
2. pending state
3. SVN
4. `candidate_evidence`
5. release artifacts directly

Provider client may see only the bounded payload handed in by the answer service.

### 9. What are the required failure modes?

The following failures must return safe non-fabricated outcomes:

1. credential missing
2. provider disabled
3. provider timeout
4. provider HTTP error
5. invalid provider response
6. cost or budget exceeded

Required behavior across these cases:

1. no fake grounded answer
2. safe warnings are allowed
3. `insufficient_context` is preferred where the current contract needs a safe non-answer path
4. internal provider failure must not expand retrieval scope or trigger alternate unsafe reads

### 10. What is the UI boundary?

The UI boundary remains frozen.

This slice does not authorize:

1. provider UI
2. model UI
3. GameProject request-shape change
4. GameProject provider hints
5. GameProject service-config controls

`Ask` must remain `{ query }` only.

## Policy Summary

The future real-provider path is allowed only if all of the following remain true:

1. provider and model selection remain backend-owned
2. credentials remain backend-owned
3. router remains thin
4. answer service remains bounded-input only
5. citation validation remains authoritative against `context.citations`
6. invalid grounding degrades safely
7. timeout, cost, and payload caps are backend-enforced
8. logs remain redacted and secret-safe
9. provider cannot read outside the bounded payload
10. frontend still exposes no provider or model control

## Explicit Non-Goals

This slice does not do any of the following:

1. implement a real external provider
2. add a new runtime provider
3. add a new API
4. modify GameProject
5. modify RAG request schema
6. read or implement env logic
7. connect `ProviderManager.active_model`
8. add frontend provider or model UI
9. add pytest or TypeScript validation

## Review Result

1. `P3.provider-credential-boundary-review` is complete as a docs-only boundary review.
2. Credentials are frozen as backend-owned only and are disallowed from frontend or request-body sources.
3. Provider and model selection remain backend-only and are still disallowed from frontend UI, request body, and `ProviderManager.active_model` in this slice.
4. Any future external provider must remain a single injected model client behind the existing service-layer and registry boundaries.
5. Timeout, retry, cost, token, logging, privacy, grounding, read, and failure boundaries are now frozen enough to start a later backend-only external-provider adapter skeleton review or skeleton implementation.
6. Real external provider integration is still not implemented.

## Implementation Status Addendum

`P3.external-provider-1`, corresponding to `P3.rag-model-3b`, is now complete as a backend external provider adapter skeleton implementation.

That implementation status remains inside the boundaries frozen by this review:

1. the slice is still skeleton only and is not real external provider integration
2. the slice does not connect a real LLM
3. the slice does not perform real HTTP
4. the slice does not read real credential material
5. the slice does not read environment variables
6. the slice does not add frontend provider or model UI
7. the slice does not modify the RAG request schema
8. runtime providers still remain only `deterministic_mock` and `disabled`
9. the provider client still does not read raw source, pending state, SVN, `candidate_evidence`, or release artifacts directly
10. citation validation still remains in the answer service and still validates only against `context.citations`

`P3.external-provider-2` is now also complete as a backend-only credential/config skeleton implementation.

That follow-up implementation sharpens the boundary further:

1. backend app config, backend service config, and dependency injection remain the only approved provider/model selection sources
2. frontend UI, request body, query body, and temporary transport config remain disallowed as credential or provider-selection sources
3. env remains only an optional backend-owned entry shape under strict backend-defined naming, server-owned lifetime, no-log constraints, and never as frontend or request input
4. explicit enable flag and backend allowlist are now part of the landed credential/config skeleton before any later runtime allowlist entry
5. `ProviderManager.active_model` remains out of scope
6. runtime providers still remain only `deterministic_mock` and `disabled`
7. `enabled` defaults to false, so the implementation remains disabled-by-default
8. allowlist validation now occurs before credential resolver and transport
9. missing credential, disabled state, and allowlist failure all degrade safely and do not generate fake answer
10. request-like `provider_name`, `model_name`, and `api_key` fields still do not participate in provider selection
11. `no_current_release` and `insufficient_context` still do not trigger provider/config/credential path execution

## Recommended Next Slice

The next reasonable step is backend service config handoff or assembly-point boundary review, still without any real provider connection.

That next slice should:

1. review backend service config handoff into the existing answer path without widening router authority
2. keep runtime providers limited to `deterministic_mock` and `disabled` until a later real-provider rollout review
3. keep credentials backend-owned and keep real-provider connectivity unimplemented
4. keep GameProject and request schema unchanged
5. keep router and answer boundaries unchanged

## Service Config Wiring Addendum

`P3.external-provider-3` is now complete as a docs-only backend service config wiring boundary review.

That follow-up review sharpens the next implementation boundary further:

1. the approved live handoff entry remains `build_rag_answer_with_service_config(...)`
2. the preferred live handoff anchor remains a backend-owned injected service object, currently `game_service`, or a backend-owned config object derived from it
3. router may obtain backend-owned service/app objects only to hand off an existing backend-owned object and remains forbidden from direct `get_rag_model_client(...)` calls, provider/model resolution, request-hint parsing, resolver creation, and transport creation
4. the answer service remains the only approved service-config interpretation point and the only approved warning-merge point
5. `no_current_release` and `insufficient_context` still remain ahead of any service-config/provider resolution
6. `ProviderManager.active_model` remains out of scope
7. env reads remain unimplemented and still cannot become request-time provider selection
8. runtime providers still remain only `deterministic_mock` and `disabled`, and external provider still cannot enter runtime allowlist without a later dedicated rollout review

## Validation Note

This slice is docs-only.

This docs-only pass does not run pytest.

This docs-only pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation error checking.
