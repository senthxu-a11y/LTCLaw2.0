# Knowledge P3 RAG Model Service-Layer Provider Selection Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-client-boundary-review-2026-05-08.md
5. docs/tasks/knowledge-p3-rag-model-provider-selection-boundary-review-2026-05-08.md

## Review Goal

Define the backend boundary for service-layer provider selection after `P3.rag-model-2a`, without implementing new runtime behavior, adding public API, or connecting any real external model.

This review is docs-only. It does not modify backend code, frontend code, routers, public API, retrieval behavior, or model integrations.

## Current Baseline

The current baseline is:

1. `P3.rag-model-1` model-client protocol and deterministic/mock adapter are complete.
2. `P3.rag-model-2` provider registry and provider selection boundary review is complete.
3. `P3.rag-model-2a` backend provider registry skeleton is complete.
4. Runtime providers are currently limited to `deterministic_mock` and `disabled`.
5. `future_external` remains documentation-only and does not enter runtime providers.
6. The answer service already supports optional `model_client` injection and still consumes only `query + context` derived payload.
7. Routers remain thin and do not select providers or call models directly.
8. No real external model is connected.

## Core Boundary

Service-layer provider selection must follow these rules:

1. Provider selection may happen only in backend service layer, app config, service config, or dependency-injection boundaries.
2. Router code must remain thin and must not choose providers directly.
3. Router code must not call any model directly.
4. The service layer may call only the existing `get_rag_model_client(...)` registry entry point.
5. The default provider remains `deterministic_mock`.
6. `disabled` is an explicit provider state, not a silent error sink.
7. Unknown provider names must fail clearly and must not fall back.
8. Provider initialization failure may fall back only to `disabled` and must return a clear warning.
9. Provider initialization failure must not silently switch to any real external provider.

## Request And Frontend Boundary

The request boundary remains strict:

1. Provider name must not be read from query body.
2. Frontend must not be allowed to pass arbitrary provider names for direct backend selection.
3. If a future product slice wants request-level provider hinting, that requires a separate boundary review.
4. Any future request-level provider hint must pass backend allowlist validation.
5. This slice does not add frontend RAG UI or frontend provider controls.

## Answer-Service Boundary

The answer path remains constrained as follows:

1. `no_current_release` must still return before any model client is selected or called.
2. `insufficient_context` must still return before any model client is selected or called.
3. The answer service must still consume only the existing P3.2 context payload and derived prompt payload.
4. The answer service must not directly read release artifacts, raw source, pending state, or SVN state.
5. Citation validation must remain centralized in the existing `P3.rag-model-1` answer path.
6. Registry warnings should be merged into answer warnings rather than discarded.
7. Provider selection must not widen retrieval, context assembly, or citation-validation boundaries.

## Configuration Boundary

Recommended selection sources remain:

1. Explicit backend dependency injection.
2. Server-side app or service config.
3. No environment-variable-driven selection in this slice.
4. No request-body-driven selection in this slice.

This review intentionally keeps environment-driven provider choice out of scope because it would broaden runtime control surface without first defining allowlist and rollout rules.

## Explicit Non-Goals

This slice does not do any of the following:

1. No real LLM integration.
2. No real external provider wiring.
3. No router change.
4. No frontend change.
5. No public API change.
6. No embedding or vector store.
7. No frontend RAG UI.
8. No `candidate_evidence` expansion.
9. No raw source read.
10. No pending-state read.
11. No SVN read.

## Recommended Next Slice

Recommended next implementation slice: `P3.rag-model-2b` service-layer provider selection skeleton or implementation planning.

Scope for that slice:

1. Add service-layer wiring that selects a provider through `get_rag_model_client(...)` only.
2. Keep routers unchanged and thin.
3. Merge registry warnings into answer warnings.
4. Preserve early return behavior for `no_current_release` and `insufficient_context`.
5. Do not connect any real external model.

## Review Result

1. Service-layer provider selection is now defined as a backend-only service/config/DI concern.
2. Router, frontend, public API, retrieval, context, and citation-validation boundaries remain unchanged.
3. The next step may wire provider selection only through the existing registry API.
4. The next step must not directly connect any real external model.
