# Knowledge P3.rag-model-3 External Provider Adapter Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2g-closeout-2026-05-08.md
3. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2f-live-config-handoff-implementation-plan-2026-05-08.md
4. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
5. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md

## Review Goal

Define the backend boundary for any future real external provider adapter after the minimal live config handoff path has landed.

This review is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Confirmed Current Baseline

The current backend and boundary baseline is:

1. live RAG answer path already accepts backend-owned service config handoff
2. provider selection still flows through the resolver and get_rag_model_client(...)
3. router only hands off game_service and does not choose provider
4. request body still does not carry provider hint
5. frontend still does not control provider name
6. runtime providers remain only deterministic_mock and disabled
7. unknown provider still clear-fails
8. provider initialization failure still falls back only to disabled with warning
9. no_current_release and insufficient_context still return before provider selection
10. citation validation still trusts only context.citations
11. retrieval and context boundaries remain unchanged

## Core Decision

Any future real external provider adapter must sit behind the existing registry and client protocol boundaries.

That means:

1. the adapter belongs behind get_rag_model_client(...), not in router code and not in request handling
2. the adapter must satisfy the existing RagModelClient protocol contract
3. the adapter must receive only bounded prompt payload prepared by the existing answer path
4. the adapter must not gain authority to read artifacts, source trees, pending state, or SVN directly

## Boundary Answers

### 1. Where should a real external provider adapter live?

It should live in the backend model-client or provider-adapter layer behind the existing registry and answer-service orchestration boundaries.

It must not live in:

1. router code
2. request schema
3. frontend code
4. retrieval or context-builder code

### 2. Must the adapter implement the existing RagModelClient protocol?

Yes.

Any future external adapter must implement the existing RagModelClient protocol so the answer path remains provider-agnostic and does not grow provider-specific branching.

### 3. Must the adapter accept only bounded prompt payload?

Yes.

The adapter must accept only the already-bounded prompt payload produced by the current answer path.

It must not receive unbounded project state or independent artifact-reading authority.

### 4. May the adapter read release artifacts, raw source, pending state, or SVN directly?

No.

The adapter must not read:

1. release artifacts directly
2. raw source directly
3. pending state directly
4. SVN directly

Retrieval and context assembly remain outside the adapter boundary.

### 5. Where should credentials come from?

This slice does not implement credentials.

This review records only that credentials must be handled through a future dedicated backend-owned credential boundary and must not be sourced from request body or frontend input.

This review also does not approve environment variables as the live source of truth for provider selection or credentials in this slice.

### 6. May a future implementation reuse ProviderManager?

Not by default in this slice.

If a later implementation wants to reuse ProviderManager, that must be reviewed and implemented in a separate dedicated slice because it would widen runtime-state coupling and ownership boundaries.

### 7. May this slice add new runtime provider names?

No.

This slice is boundary review only and does not authorize any new runtime provider name.

### 8. How should external provider initialization failure degrade?

Future behavior must remain conservative:

1. fallback to disabled is allowed
2. explicit clear-fail is allowed when startup or configuration semantics require it
3. silent provider switching is not allowed

### 9. How should timeout, retry, cost, and token-limit behavior be constrained?

A future implementation must introduce explicit backend-side guardrails for:

1. timeout limits
2. retry policy
3. token or payload limits
4. cost or budget controls

These constraints must be defined before any real provider implementation lands.

### 10. How should model output continue to be citation-validated?

The current grounding rule remains unchanged.

Any future provider output must still be validated only against context.citations produced by the existing answer path.

### 11. If model output has no citation or out-of-context citation, must it degrade?

Yes.

If the model returns no citation or citation ids outside context.citations, the answer must degrade to insufficient_context.

### 12. May the model answer precise numeric facts?

No new exception is allowed.

Exact numeric or row-level facts must continue to follow the structured-query boundary rather than becoming a free-form RAG answer responsibility.

### 13. May modification intent go through RAG?

No new exception is allowed.

Modification or edit intent must continue to warn toward the workbench flow.

### 14. May candidate_evidence enter RAG in this slice?

No.

This slice does not authorize candidate_evidence as RAG input.

### 15. May embedding or vector store enter this slice?

No.

This slice does not authorize embedding or vector-store work.

### 16. May frontend RAG UI enter this slice?

No.

This slice is backend boundary review only.

## Explicit Non-Goals

This slice does not do any of the following:

1. implement a real external provider
2. add runtime provider names
3. modify provider registry code
4. modify router code
5. modify request schema
6. modify frontend
7. connect ProviderManager.active_model
8. read environment variables
9. implement API-key storage
10. add embedding or vector store
11. widen retrieval, context, or citation-validation boundaries

## Recommended Next Slice

Recommended next slice: P3.rag-model-3a external provider adapter implementation plan.

That slice should remain constrained as follows:

1. planning only
2. no direct real provider implementation
3. define adapter shape behind existing registry and client protocol boundaries
4. define credential boundary
5. define timeout, retry, token-limit, and cost policy
6. define grounding and citation regression test plan before any real provider implementation

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to git diff --check.

## Review Result

1. P3.rag-model-3 is complete as a docs-only external provider adapter boundary review.
2. Any future external provider adapter must live behind the existing registry and RagModelClient protocol boundaries.
3. Any future adapter must accept only bounded prompt payload and must not read release artifacts, raw source, pending state, or SVN directly.
4. This slice does not authorize new runtime provider names, ProviderManager reuse by default, request-body or frontend provider control, candidate_evidence RAG usage, embedding, or vector store.
5. The next step, if this path continues, should be P3.rag-model-3a external provider adapter implementation plan rather than direct provider implementation.