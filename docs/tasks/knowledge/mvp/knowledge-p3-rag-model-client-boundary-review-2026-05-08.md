# Knowledge P3 RAG / Model-Client Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md

## Review Goal

Define the next mainline boundary for moving from the deterministic or no-LLM answer skeleton to a pluggable backend model-client without breaking the existing RAG read boundary.

This review is docs-only. It does not implement a model client, add frontend UI, add new API, or widen retrieval inputs.

## Current Baseline

The current baseline is:

1. P3.2 context builder is completed and reads only current-release, release-owned artifacts.
2. P3.2b debug context endpoint is completed.
3. P3.4 deterministic or no-LLM answer service is completed.
4. P3.4b debug answer endpoint is completed.
5. The answer service consumes only `query` plus the existing P3.2 context payload.
6. The answer service does not read release artifacts directly.
7. Citations are sourced only from `context.citations`.
8. `no current release` and `insufficient_context` still return clearly.
9. `candidate_evidence.jsonl` remains excluded from default RAG or context reads.
10. P3.7 formal map MVP is conservatively complete, but that does not mean RAG is complete.

## Required Model-Client Boundary

The model-client boundary for the next mainline must be:

1. Any real LLM must be reached only through a single injected model client.
2. Router code must not call an LLM directly.
3. The answer service must not bypass the context builder to read release artifacts.
4. Model-client input must be a bounded prompt payload containing only `query`, context chunks, citations, release metadata, and policy hints.
5. Model-client output must pass citation validation before it becomes the final answer payload.
6. Citations may reference only `citation_id` values already present in `context.citations`.
7. If the model returns citations outside the provided context, those citations must be dropped or the answer must degrade to warnings-only behavior.
8. If context is insufficient, the service must still return `insufficient_context` rather than fabricate unsupported claims.
9. This slice must not add embedding or vector-store work.
10. This slice must not add frontend RAG UI.
11. This slice must not widen `candidate_evidence` RAG usage.
12. This slice must not read raw source, pending state, or SVN.

## Preservation Rules

The current RAG read boundary remains unchanged:

1. Release-owned artifact reads still happen only inside the existing context builder path.
2. The router remains a thin orchestration layer.
3. The answer service remains downstream of `query + context` rather than becoming a retrieval layer.
4. Citation grounding remains mandatory even if a real model is introduced later.

## Recommended Next Slice

Recommended next implementation slice: `P3.rag-model-1` backend model-client protocol plus deterministic or mock adapter.

Requirements for that slice:

1. Add only a backend protocol or interface plus a deterministic or mock adapter boundary.
2. Use mock model client implementations in tests.
3. Do not connect any real external model yet.
4. Do not add frontend RAG UI.
5. Do not modify retrieval or context-builder read boundaries.

## Implementation Status Update

`P3.rag-model-1` is now implemented as the minimum backend model-client slice.

Implemented scope:

1. The implementation files are `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` and `src/ltclaw_gy_x/game/knowledge_rag_answer.py`.
2. The test files are `tests/unit/game/test_knowledge_rag_model_client.py` and `tests/unit/game/test_knowledge_rag_answer.py`.
3. The model-client protocol or interface was added.
4. The bounded prompt payload now contains only `query`, `release_id`, `built_at`, `chunks`, `citations`, and `policy_hints`.
5. The bounded model-client response contains only `answer`, `citation_ids`, and optional `warnings`.
6. `DeterministicMockRagModelClient` was added and uses only the provided payload.
7. The mock adapter does not read files and does not call a real model.
8. `build_rag_answer` now supports optional `model_client` injection while preserving the prior deterministic or no-LLM behavior when none is provided.
9. When `model_client` is present, the answer service only converts `query + context` into the bounded payload and still does not reread artifacts.
10. Router behavior remains unchanged and still does not call any model directly.
11. Returned `citation_ids` are validated against `context.citations`.
12. Out-of-context `citation_id` values are dropped and appended to warnings.
13. If all returned citations are invalid or the answer is not grounded, the result degrades to `insufficient_context`.
14. `no_current_release` still returns directly without calling the model client.
15. Insufficient grounded context still returns `insufficient_context` and does not trust model output.

Validation summary:

1. Focused pytest result: `15 passed`.
2. NUL check result: the 4 touched Python files were rechecked as `NUL=0`.
3. `git diff --check` reported no patch-format errors and only existing CRLF or LF warnings.
4. Local pytest may still emit environment-specific `.pytest_cache` permission warnings, but the focused tests passed.

Explicitly not done in `P3.rag-model-1`:

1. No real LLM connection.
2. No provider registry.
3. No provider selection.
4. No embedding or vector store.
5. No frontend RAG UI.
6. No `candidate_evidence` RAG expansion.
7. No raw source read.
8. No `pending/test_plans.jsonl` read.
9. No `pending/release_candidates.jsonl` read.
10. No SVN read.
11. No context-builder boundary expansion.
12. No new API.

## Next Recommended Slice

The next recommended step after `P3.rag-model-1` is `P3.rag-model-2` backend provider registry or provider selection boundary review as a docs-only slice.

Do not connect a real external model before that review lands.

## Review Result

1. The next mainline should move to a single injected backend model-client boundary.
2. Retrieval and context assembly boundaries remain unchanged.
3. Citation validation remains mandatory and bounded to `context.citations`.
4. `P3.rag-model-1` is now complete as the minimum backend model-client protocol plus deterministic or mock adapter slice.
5. The next recommended step is `P3.rag-model-2` backend provider registry or provider selection boundary review rather than direct real-model integration.

## Implementation Follow-Up

`P3.rag-model-2` boundary review is now the required bridge before any registry skeleton or future external provider work.

The next implementation slice after that review should be `P3.rag-model-2a` backend provider registry skeleton.

Direct real-model integration remains out of scope until a later dedicated external-provider review lands.

This follow-up keeps real external providers out of scope until a later dedicated review lands.
