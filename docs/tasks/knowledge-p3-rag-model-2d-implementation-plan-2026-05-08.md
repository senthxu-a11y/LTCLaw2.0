# Knowledge P3 RAG Model 2d Implementation Plan

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
3. docs/tasks/knowledge-p3-rag-model-2b-closeout-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-2c-config-injection-boundary-review-2026-05-08.md
5. docs/tasks/knowledge-p3-gate-status-2026-05-07.md

## Plan Goal

Break `P3.rag-model-2c` into a narrow implementation checklist for the next backend-only code slice.

This plan is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Core Planning Decision

The next implementation slice should add one small service-layer resolver helper such as `resolve_rag_model_provider_name(...)`, or an equivalent helper with the same boundary.

Purpose of this helper:

1. Resolve provider name from backend dependency injection or strictly server-side service config.
2. Keep provider-selection rules out of router code.
3. Keep request body, frontend, environment variables, and broader provider runtime state out of scope.
4. Feed the resolved provider name into `build_rag_answer_with_provider(...)` without bypassing `get_rag_model_client(...)`.

## Required Boundary Preservation

The next implementation slice must keep all of the following unchanged:

1. Router does not choose provider.
2. `build_rag_answer_with_provider(...)` remains the service-layer provider-selection entry point.
3. `get_rag_model_client(...)` remains the only registry entry point.
4. Unknown provider remains clear-fail.
5. Provider initialization failure remains fallback-to-disabled only.
6. `no_current_release` and `insufficient_context` must not trigger provider selection.
7. Citation validation still trusts only `context.citations`.
8. Retrieval and context boundaries do not widen.

## Planned Implementation Checklist

### 1. Add Small Resolver Helper

Add one small backend helper such as `resolve_rag_model_provider_name(...)`.

The helper should:

1. accept explicit backend DI value first
2. accept strictly server-side service config second
3. normalize empty or whitespace provider name to `None` or the deterministic default path according to the existing answer or registry rules
4. not read request body
5. not read frontend input
6. not read environment variables
7. not read `ProviderManager.active_model`
8. not instantiate providers directly

### 2. Wire Resolver Into Service-Layer Answer Path

The next implementation should wire the helper into the service-layer answer path only.

Recommended rule:

1. resolve provider name after `no_current_release` and grounded-context checks
2. pass the resolved provider name only into `build_rag_answer_with_provider(...)`
3. keep `build_rag_answer_with_provider(...)` delegating registry resolution to `get_rag_model_client(...)`

### 3. Keep Runtime Providers Narrow

The next implementation must still allow only these runtime providers:

1. `deterministic_mock`
2. `disabled`

It must not add:

1. new runtime provider names
2. real external model connection
3. `future_external` runtime support

### 4. Keep Config Injection Server-Side Only

The next implementation may use only:

1. backend dependency injection
2. strictly server-side service config

It must not use:

1. request body provider hint
2. frontend provider control
3. environment variables
4. `ProjectConfig.models`
5. `UserGameConfig`
6. `ProviderManager.active_model`

## Files To Change In The Next Implementation Slice

Recommended file touch set for the next code round:

1. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
2. one small new helper module under `src/ltclaw_gy_x/game/` for provider-name resolution
3. `tests/unit/game/test_knowledge_rag_answer.py`
4. one focused new unit-test file under `tests/unit/game/` for the resolver helper

Optional and only if strictly needed:

1. `src/ltclaw_gy_x/game/service.py` for a narrow server-side service-config handoff

## Files That Should Not Change In The Next Implementation Slice

The next code slice should not modify these files unless a later review explicitly widens scope:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_model_client.py`
4. `src/ltclaw_gy_x/game/config.py`
5. `src/ltclaw_gy_x/providers/provider_manager.py`
6. any `console/src/` file
7. any request or response schema for the RAG router

Reasoning:

1. Router file should stay out of provider-selection logic.
2. Registry and client modules already encode the supported-provider, clear-fail, and fallback-disabled rules.
3. `config.py` and `ProviderManager` would widen scope into persistent or global model-management concerns too early.
4. Frontend and request schema must remain unchanged in this slice.

## Focused Test Checklist For The Next Implementation Slice

The next code round should add or update tests for these cases:

1. resolver returns explicit DI provider name when provided
2. resolver falls back to server-side service config when DI override is absent
3. resolver does not read request body, environment variables, or frontend input
4. unknown configured provider still clear-fails through registry path
5. provider initialization failure still falls back only to `disabled`
6. `no_current_release` still returns before resolver or provider selection is used
7. `insufficient_context` still returns before resolver or provider selection is used
8. citation validation still accepts only `context.citations`
9. resolved-provider warnings still merge into answer warnings
10. router request schema and router behavior remain unchanged

Recommended focused test files:

1. `tests/unit/game/test_knowledge_rag_answer.py`
2. one new focused test file for the resolver helper under `tests/unit/game/`
3. optionally existing router regression coverage, but only to confirm no schema or behavior widening

## Acceptance Criteria For The Next Implementation Slice

The next code round is acceptable only if all of the following remain true:

1. provider name is resolved only from backend DI or strictly server-side service config
2. router still does not choose provider
3. request body still does not carry provider name
4. frontend still does not control provider name
5. runtime providers remain only `deterministic_mock` and `disabled`
6. unknown provider still clear-fails
7. provider initialization failure still falls back only to `disabled`
8. `no_current_release` and `insufficient_context` still return before provider selection
9. `get_rag_model_client(...)` remains the only registry entry point
10. retrieval, context, and citation-validation boundaries remain unchanged
11. no real external model is connected
12. no new API or request-schema change is added

## Explicit Non-Goals

This plan keeps all of the following out of the next implementation slice:

1. real external provider integration
2. new runtime provider names
3. `ProviderManager.active_model` adoption
4. environment-variable-driven provider selection
5. request-body provider hint
6. frontend provider control
7. raw-source read
8. pending test-plan or release-candidate read as RAG input
9. `candidate_evidence.jsonl` boundary expansion
10. embedding or vector store
11. formal-map or P3.7 UI changes

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to `git diff --check`.

## Plan Result

1. `P3.rag-model-2d` is complete as a docs-only implementation plan.
2. The next code slice should add one small service-layer resolver helper and keep provider selection bounded to backend DI or service config only.
3. The next code slice should stay limited to `deterministic_mock` and `disabled`.
4. The next code slice should avoid router, frontend, global provider runtime, request schema, and real external model integration.