# Knowledge P3 RAG Model 2c Config Injection Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
3. docs/tasks/knowledge-p3-rag-model-2b-closeout-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-service-selection-boundary-review-2026-05-08.md
5. docs/tasks/knowledge-p3-gate-status-2026-05-07.md

## Review Goal

Define where RAG provider configuration may enter the backend service layer after `P3.rag-model-2b`, without implementing config injection, without changing routers, and without connecting any real external model.

This review is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Confirmed Current Baseline

The current code baseline is:

1. `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` already defines `RagModelClient`, `DeterministicMockRagModelClient`, and `DisabledRagModelClient`.
2. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py` already exposes `get_rag_model_client(provider_name=None, *, factories=None)`.
3. Runtime providers are currently limited to `deterministic_mock` and `disabled`.
4. `future_external` remains documentation-only and is not allowed to enter runtime providers.
5. Unknown provider names already clear-fail.
6. Provider initialization failure already falls back only to `disabled`.
7. `src/ltclaw_gy_x/game/knowledge_rag_answer.py` already provides `build_rag_answer(...)` and `build_rag_answer_with_provider(...)`.
8. Service-layer provider selection already happens only through `get_rag_model_client(...)`.
9. `no_current_release` and `insufficient_context` already return before provider selection or provider call.
10. Citation validation already trusts only `context.citations`.
11. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` still calls `build_rag_answer(...)` directly.
12. Router request body does not carry provider name.
13. `src/ltclaw_gy_x/game/config.py` already contains `ProjectConfig.models` and `UserGameConfig`, but neither is currently the RAG provider-selection source.
14. `src/ltclaw_gy_x/game/service.py` and `src/ltclaw_gy_x/providers/provider_manager.py` already participate in broader model runtime concerns outside this narrow RAG path.

## Core Decision

`P3.rag-model-2c` should define app/service config injection boundary only.

Recommended provider-selection entry order:

1. Explicit backend dependency injection for tests and narrow internal callers.
2. Server-side app or service config owned by the RAG backend path.
3. No project-config-driven selection in this slice.
4. No user-config-driven selection in this slice.
5. No environment-variable-driven selection in this slice.
6. No request-body-driven or frontend-driven selection in this slice.

## Boundary Answers

### 1. Where should RAG provider configuration enter the service layer?

It should enter through explicit backend dependency injection first, then through server-side app or service config.

The service layer remains the first runtime point that may resolve a provider name into `get_rag_model_client(...)`.

### 2. Is app config, service config, project config, or dependency injection preferred?

Preferred order:

1. dependency injection for narrow tests or internal callers
2. app or service config for normal runtime selection
3. not project config in this slice
4. not user config in this slice

Rationale:

1. `ProjectConfig` is project-owned local project metadata and should not become the first backend runtime control surface for model-provider choice.
2. `UserGameConfig` currently carries local-user or SVN-adjacent concerns and should not become the first provider-selection control plane for this RAG slice.
3. Backend-controlled app or service config keeps provider choice in a server-side runtime boundary rather than in project data or request payload.

### 3. Are environment variables allowed?

No.

This slice explicitly keeps environment-variable-driven provider selection out of scope because it would broaden hidden runtime control without a dedicated allowlist, rollout, and observability decision.

### 4. May request body or frontend pass provider name?

No.

Request schema must remain unchanged, and frontend must not pass arbitrary provider names.

### 5. May router choose provider?

No.

Router must remain thin and must not select provider directly.

### 6. Should this slice connect `ProviderManager.active_model`?

No.

This slice only reviews the boundary and does not adopt `ProviderManager.active_model` as the RAG provider source of truth.

If a later slice wants to bridge broader provider runtime state into RAG provider selection, that requires a separate review because it would widen the runtime control surface and couple this narrow RAG path to global model-management semantics.

### 7. How should provider allowlist be preserved?

Provider allowlist should remain the registry allowlist already enforced by `get_rag_model_client(...)` and `SUPPORTED_RAG_MODEL_PROVIDERS`.

Config injection must not bypass the registry.

Config may carry only a provider name that still resolves through the existing registry path.

### 8. If config carries an unknown provider name, should it clear-fail or degrade to `disabled`?

Unknown provider must clear-fail.

Unknown provider name is a configuration error, not an initialization error, so it must not silently degrade to `disabled`.

### 9. May provider initialization failure fall back only to `disabled`?

Yes.

That rule remains unchanged.

Initialization failure may fall back only to `disabled` with clear warning and must not silently switch to any real external provider.

### 10. How should warnings enter answer warnings?

Registry or resolution warnings must continue to merge into answer warnings.

The current `P3.rag-model-2b` warning-merge rule remains the correct model for any future 2d implementation.

### 11. How do we guarantee `no_current_release` and `insufficient_context` do not trigger provider selection?

Any future config injection implementation must preserve the current call order:

1. evaluate `no_current_release`
2. evaluate grounded context sufficiency
3. only after those gates resolve provider selection

Config lookup itself must not be moved ahead of these early-return checks if that lookup would initialize or resolve a provider.

### 12. How do we keep retrieval, context, and citation boundaries from widening?

The boundary remains:

1. retrieval and context assembly stay inside the existing current-release context builder
2. answer service still consumes only derived `query + context`
3. citation validation still trusts only `context.citations`
4. no raw source read
5. no pending-state read
6. no `candidate_evidence.jsonl` expansion
7. no SVN read

Config injection must not add any side path that rereads artifacts or substitutes a new citation authority.

## Explicit Non-Goals

This slice does not do any of the following:

1. No real external LLM integration.
2. No new runtime provider.
3. No new API.
4. No request-schema change.
5. No frontend change.
6. No router change.
7. No raw-source read.
8. No pending test-plan or release-candidate read as RAG input.
9. No `candidate_evidence.jsonl` boundary expansion.
10. No embedding or vector store.
11. No formal-map or P3.7 UI change.

## Recommended Next Slice

Recommended next slice: `P3.rag-model-2d` app/service config injection implementation.

That slice should remain constrained as follows:

1. still only `deterministic_mock` and `disabled` as runtime providers
2. still no real external provider
3. still no request-body provider control
4. still no router provider selection
5. still no frontend provider control

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to `git diff --check`.

## Review Result

1. `P3.rag-model-2c` is complete as a docs-only app/service config injection boundary review.
2. Provider configuration should enter through backend dependency injection first, then server-side app or service config.
3. `ProjectConfig.models`, `UserGameConfig`, request body, frontend, router, environment variables, and `ProviderManager.active_model` are not adopted as the source of truth in this slice.
4. Unknown provider remains clear-fail, provider initialization failure remains fallback-to-disabled only, and warning merge remains in the answer path.
5. The next step, if implementation is desired, should be `P3.rag-model-2d` rather than direct real-model integration.