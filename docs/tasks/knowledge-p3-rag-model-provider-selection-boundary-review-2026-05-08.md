# Knowledge P3 RAG Model Provider Registry / Provider Selection Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-client-boundary-review-2026-05-08.md

## Review Goal

Define the backend boundary for provider registry and provider selection after `P3.rag-model-1`, without implementing any real external model or widening the existing RAG read boundary.

This review is docs-only. It does not add registry runtime code, does not add frontend UI, does not add public API, and does not connect any real external model.

## Current Baseline

The current baseline is:

1. `P3.rag-model-1` is completed.
2. A model-client protocol already exists.
3. `DeterministicMockRagModelClient` already exists.
4. The answer service already supports optional `model_client` injection.
5. Router code does not call any model directly.
6. Citation validation is already enforced after model-client output.
7. Insufficient context already degrades to `insufficient_context`.
8. No provider registry exists yet.
9. No provider selection layer exists yet.
10. No real LLM is connected yet.

## Core Boundary Rules

The provider registry and provider selection boundary must follow these rules:

1. Provider registry may select only model-client implementations and must not change retrieval or context-builder read boundaries.
2. Provider selection must not let router code call any model directly.
3. Provider selection must not let the answer service read artifacts directly.
4. Every provider must implement the existing `P3.rag-model-1` model-client protocol.
5. Every provider output must pass the same citation validation already applied against `context.citations`.
6. Provider output must not return out-of-context citations and be trusted directly.
7. Providers must not read raw source, pending state, SVN, or `candidate_evidence.jsonl`.
8. Provider selection must not enable embedding or vector-store work.
9. Provider selection must not add frontend RAG UI.
10. Provider selection must not bypass permission checks.
11. Provider selection must not turn local trusted fallback into a production permission strategy.

## Provider Types

Recommended provider types for the next phase are:

1. `deterministic_mock`: the existing mock adapter and the default safe provider.
2. `disabled`: an explicit no-real-model provider that preserves deterministic or no-LLM behavior, or returns `insufficient_context` when no grounded answer path is available.
3. `future_external`: documentation-only placeholder for later real external providers.

This review does not bind the design to any specific commercial model, provider brand, hosted API, or API-key scheme.

## Selection Source Order

Recommended provider selection order is:

1. Explicit backend function argument or dependency injection.
2. Server-side app or service config.
3. Environment variable only if a later review explicitly allows it.
4. Never directly from user query body.
5. Never from arbitrary frontend provider name without backend allowlist.

Additional rules:

1. Frontend must not be allowed to pass any provider name and select arbitrary backend model behavior.
2. If a later product slice allows request-level provider hinting, it must still pass backend allowlist validation.
3. Missing configuration must not auto-connect any external provider.

## Default And Fallback Strategy

Recommended strategy:

1. The default provider should be `deterministic_mock`.
2. If explicit provider initialization fails, the registry should fall back to `disabled` with a clear warning.
3. The system should not silently fall through to any real external provider.
4. The system should not treat local trusted fallback as a production authorization or provider-selection policy.

This review chooses fallback-to-`disabled` over silent external retries because the failure mode is clearer and safer.

## Explicit Non-Goals

This slice does not do any of the following:

1. No real LLM integration.
2. No provider registry runtime implementation.
3. No provider selection runtime implementation.
4. No embedding or vector store.
5. No frontend RAG UI.
6. No `candidate_evidence` RAG expansion.
7. No raw source read.
8. No `pending/test_plans.jsonl` read.
9. No `pending/release_candidates.jsonl` read.
10. No SVN read.
11. No context-builder boundary expansion.
12. No API expansion.

## Recommended Next Slice

Recommended next implementation slice: `P3.rag-model-2a` backend provider registry skeleton.

Scope for that slice:

1. Add backend registry structure and deterministic-mock provider lookup only.
2. Do not connect any real external model.
3. Do not change frontend behavior.
4. Do not add any new public API.
5. If answer endpoint later uses registry selection, selection must still come only from server-side config or backend dependency injection.
6. Focused tests should cover registry lookup and fallback behavior with mocked providers.

## Review Result

1. Provider registry and provider selection are now defined as backend-only model-client selection boundaries.
2. Retrieval, context assembly, router behavior, citation validation, permission checks, and frontend boundaries remain unchanged.
3. The recommended default provider is `deterministic_mock`.
4. The recommended initialization-failure fallback is `disabled` with a clear warning.
5. The next recommended step is `P3.rag-model-2a` backend provider registry skeleton rather than direct real-LLM integration.

## Implementation Status Update

Status as of 2026-05-08: the recommended `P3.rag-model-2a` backend provider registry skeleton is now implemented and revalidated after DLP/NUL clean repair.

Implemented scope:

1. The implementation files are `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` and `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`.
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py` was compatibility-checked only and did not gain new router semantics.
3. The focused test files are `tests/unit/game/test_knowledge_rag_model_client.py`, `tests/unit/game/test_knowledge_rag_model_registry.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
4. The registry API is `get_rag_model_client(provider_name=None, *, factories=None)` and `ResolvedRagModelClient(provider_name, client, warnings)`.
5. Runtime providers are limited to `deterministic_mock` and `disabled`.
6. `future_external` remains documentation-only and does not enter runtime providers.
7. `deterministic_mock` is the default provider.
8. Unknown provider names fail clearly with `ValueError` and do not fall back.
9. Provider factory initialization failure falls back to `disabled` with a clear warning.
10. `DisabledRagModelClient` returns empty `answer`, empty `citation_ids`, and `Model provider is disabled.` warning.
11. The registry does not read files, does not read environment variables, and does not connect any real external model.
12. Router was not modified.
13. Frontend was not modified.
14. No new public API was added.
15. Retrieval, context assembly, and citation-validation boundaries remain unchanged.
16. This slice hit DLP/NUL corruption during editing and then received a clean repair before final validation.

Validation summary:

1. Post-repair NUL checks reported `NUL=0` for `knowledge_rag_model_client.py`, `knowledge_rag_answer.py`, `knowledge_rag_model_registry.py`, `test_knowledge_rag_model_client.py`, `test_knowledge_rag_model_registry.py`, and `test_knowledge_rag_answer.py`.
2. Focused pytest result: `27 passed`.
3. Local pytest may emit `.pytest_cache` permission warnings, but they do not affect the passing result.
4. `git diff --check` reported no patch-format or whitespace errors and only existing CRLF/LF warnings.

## Follow-Up Recommendation

1. The next recommended step is `P3.rag-model-2b` service-layer provider selection boundary review or implementation planning.
2. Do not connect any real external model directly in that next slice.

## Subsequent Status Update

Status as of 2026-05-08: `P3.rag-model-2b` service-layer provider selection boundary review is now complete as a docs-only slice.

Follow-up update:

1. `P3.rag-model-2a` is now treated as the landed backend provider registry skeleton.
2. `P3.rag-model-2b` now defines that provider selection may happen only in backend service layer, app/service config, or dependency injection boundaries.
3. `P3.rag-model-2b` keeps routers thin, forbids query-body provider selection, and forbids arbitrary frontend provider selection.
4. `P3.rag-model-2b` keeps `get_rag_model_client(...)` as the only registry entry point for later service-layer wiring.
5. `P3.rag-model-2b` keeps `deterministic_mock` as default, keeps `disabled` explicit, and still forbids direct real-model integration.
6. The next recommended step is `P3.rag-model-2b` service-layer provider selection skeleton implementation or implementation planning rather than direct real-LLM integration.
