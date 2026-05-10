# Knowledge P3.rag-model-3a External Provider Adapter Implementation Plan

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-3-external-provider-adapter-boundary-review-2026-05-08.md
3. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2g-closeout-2026-05-08.md
4. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
5. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md

## Plan Goal

Break P3.rag-model-3 into the smallest implementation plan for a future external provider adapter skeleton.

This plan is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Core Planning Decision

The next implementation slice should remain skeleton-only.

Preferred shape:

1. add a small adapter module such as src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. or, if the repository prefers a more conservative surface, add src/ltclaw_gy_x/game/knowledge_rag_provider_adapters.py
3. define one adapter class that implements RagModelClient
4. accept only RagAnswerPromptPayload as input
5. return only RagModelClientResponse as output
6. keep all real network I/O out of the slice

Reasoning:

1. this preserves the current provider-agnostic answer path
2. this preserves the registry as the only provider-resolution entry point
3. this lets the repository validate contract shape before discussing real provider behavior

## Planned File Surface For The Next Implementation Slice

Recommended future file touch set:

1. src/ltclaw_gy_x/game/knowledge_rag_model_client.py for any strictly necessary protocol-type exposure only
2. one new adapter module:
   src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
   or
   src/ltclaw_gy_x/game/knowledge_rag_provider_adapters.py
3. tests/unit/game/test_knowledge_rag_model_client.py only if protocol or type exposure needs focused coverage
4. one new focused adapter test file under tests/unit/game/

Optional and only if a later slice explicitly chooses to wire a skeleton behind an allowlist:

1. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
2. tests/unit/game/test_knowledge_rag_model_registry.py

Planning rule:

1. do not assume registry changes are required in the first skeleton slice
2. prefer validating adapter contract in isolation before any registry expansion discussion

## Adapter Class Plan

The future adapter class should:

1. implement RagModelClient
2. expose the same generate_answer contract as the existing client protocol expects
3. accept only RagAnswerPromptPayload prepared by the current answer path
4. return only RagModelClientResponse
5. avoid provider-specific branching in answer-service code

The future adapter class must not:

1. read release artifacts directly
2. read raw source directly
3. read pending state directly
4. read SVN directly
5. inspect request payloads directly
6. inspect frontend state directly

## Input And Output Contract Plan

Future adapter input contract:

1. input type must be RagAnswerPromptPayload
2. input must already be bounded by the existing answer path
3. input must not be widened to raw project state

Future adapter output contract:

1. output type must be RagModelClientResponse
2. answer text may be empty only if the adapter intends the answer path to degrade
3. citation ids must refer only to ids that can later be validated against context.citations
4. warnings may be included, but grounding authority remains outside the adapter

## I O And Runtime Behavior Plan

The next implementation slice should remain skeleton-only.

That means:

1. no real network I/O
2. no real provider SDK call
3. no real credential loading
4. no real timeout or retry loop implementation

Instead, the future skeleton slice may define:

1. injected secret or config placeholder shape
2. timeout config placeholder shape
3. retry config placeholder shape
4. token-limit config placeholder shape
5. cost or budget config placeholder shape

## Credential Boundary Plan

The next skeleton slice should define only backend-injected placeholder shape for credentials or secrets.

It must not:

1. read environment variables
2. read request body
3. read frontend input
4. implement API-key storage

## Registry And Provider-Name Plan

The next skeleton slice should not default to adding a real runtime provider name.

Conservative plan:

1. keep runtime provider list unchanged by default
2. validate adapter contract in isolation first
3. only discuss a later allowlist addition in a separate explicit step if skeleton wiring truly needs it

If a later slice insists on allowlist wiring for skeleton validation, that wiring must remain conservative and must not become real-provider activation.

## ProviderManager Plan

The next skeleton slice must not connect ProviderManager.active_model.

If future work wants ProviderManager integration, that must be handled in a separate review and implementation slice.

## Focused Test Plan For The Next Implementation Slice

The next code round should add or update tests for these cases:

1. adapter class conforms to RagModelClient contract
2. adapter accepts RagAnswerPromptPayload only
3. adapter returns RagModelClientResponse only
4. adapter does not perform network I/O in the skeleton slice
5. adapter does not read artifacts, raw source, pending state, or SVN
6. answer layer still rejects out-of-context citation ids
7. answer layer still degrades for empty answer or missing citation ids
8. structured-query warning still appears for exact numeric or row-level prompts
9. workbench warning still appears for modification-intent prompts
10. router, request body, and frontend still do not participate in provider selection

Recommended future test files:

1. one new focused adapter test file under tests/unit/game/
2. tests/unit/game/test_knowledge_rag_answer.py
3. optionally tests/unit/game/test_knowledge_rag_model_registry.py only if a later slice truly adds skeleton wiring
4. existing router regression coverage only to confirm no request or router widening

## Acceptance Criteria For The Next Implementation Slice

The next code round is acceptable only if all of the following remain true:

1. the slice remains skeleton-only and does not call a real external API
2. adapter contract is defined behind RagModelClient without widening answer-service logic
3. adapter accepts only RagAnswerPromptPayload
4. adapter returns only RagModelClientResponse
5. adapter does not read artifacts, raw source, pending state, or SVN
6. router remains unchanged
7. request schema remains unchanged
8. frontend remains unchanged
9. ProviderManager remains disconnected
10. environment variables remain unused
11. citation validation still trusts only context.citations
12. empty answer or missing citation output still degrades to insufficient_context
13. structured-query boundary remains unchanged
14. workbench-flow boundary remains unchanged

## Explicit Non-Goals

This plan keeps all of the following out of the next implementation slice:

1. real external API calls
2. API-key storage
3. environment-variable reads
4. ProviderManager.active_model integration
5. frontend changes
6. request-schema changes
7. router changes
8. embedding or vector store
9. candidate_evidence RAG usage
10. numeric-fact bypass around structured query
11. modification-intent bypass around workbench flow

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to git diff --check.

## Plan Result

1. P3.rag-model-3a is complete as a docs-only external provider adapter implementation plan.
2. The next code slice should be a skeleton-only adapter implementation rather than a real provider integration.
3. The future skeleton should define adapter contract, placeholder config shape, and tests without real network I/O.
4. The next step, if this path continues, should be P3.rag-model-3b external provider adapter skeleton implementation.