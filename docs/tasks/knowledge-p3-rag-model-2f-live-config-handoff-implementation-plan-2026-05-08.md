# Knowledge P3.rag-model-2f Live Config Handoff Implementation Plan

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-rag-model-2e-live-config-injection-boundary-review-2026-05-08.md
3. docs/tasks/knowledge-p3-rag-model-2d-closeout-2026-05-08.md
4. docs/tasks/knowledge-p3-rag-model-2d-implementation-plan-2026-05-08.md
5. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
6. docs/tasks/knowledge-p3-gate-status-2026-05-07.md

## Plan Goal

Break `P3.rag-model-2e` into the smallest implementation plan for handing backend-owned app or service config into the live RAG answer path.

This plan is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Core Planning Decision

The next implementation slice should preserve the current service-layer provider-selection boundary and add at most one very small live handoff helper.

Preferred shape:

1. keep `build_rag_answer_with_provider(...)` as the service-layer provider-selection entry point
2. add a thin helper such as `build_rag_answer_with_service_config(...)` in `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. let that helper pass a backend-owned app or service config object into the existing resolver path
4. keep provider-name resolution delegated to `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
5. keep provider instantiation delegated to `get_rag_model_client(...)`

Alternative acceptable shape:

1. extend `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py` with a narrowly named helper such as `resolve_rag_model_provider_name_from_service_config(...)`
2. keep `src/ltclaw_gy_x/game/knowledge_rag_answer.py` as the orchestrator that calls the resolver after early-return checks

Preferred choice rationale:

1. an answer-layer wrapper makes the live handoff explicit without teaching router code how provider selection works
2. a separate resolver helper remains possible, but it should not become a second provider-selection entry point

## Required Boundary Preservation

The next implementation slice must keep all of the following unchanged:

1. router does not choose provider
2. router does not call `get_rag_model_client(...)` directly
3. request body does not carry provider name
4. frontend does not control provider name
5. `get_rag_model_client(...)` remains the only registry entry point
6. unknown provider remains clear-fail
7. provider initialization failure remains fallback-to-disabled only with warning
8. `no_current_release` and `insufficient_context` must not trigger resolver or registry use
9. citation validation still trusts only `context.citations`
10. retrieval and context boundaries do not widen
11. runtime providers remain only `deterministic_mock` and `disabled`
12. no real external model is connected

## Planned Implementation Checklist

### 1. Add One Small Live Handoff Helper

Recommended primary option:

1. add `build_rag_answer_with_service_config(...)` to `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
2. accept `query`, `context`, and a backend-owned app or service config object
3. forward only explicit backend-owned config into the existing provider-resolution path
4. keep this helper thin and orchestration-only

Alternative acceptable option:

1. add `resolve_rag_model_provider_name_from_service_config(...)` to `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
2. keep `build_rag_answer_with_provider(...)` or a wrapper in `knowledge_rag_answer.py` responsible for the live call order and answer assembly

Decision guidance:

1. prefer `build_rag_answer_with_service_config(...)` if the next slice needs a clear service-facing entry point
2. prefer a named resolver extension only if it keeps the answer-layer entry point count stable and obvious

### 2. Keep Helper Placement Narrow

Recommended placement:

1. orchestration helper in `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
2. provider-name extraction helper in `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`

Do not place the new live handoff logic in:

1. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
2. `src/ltclaw_gy_x/providers/provider_manager.py`
3. `src/ltclaw_gy_x/game/config.py`

Reasoning:

1. registry should stay limited to provider allowlist and instantiation behavior
2. provider manager would widen global runtime-state coupling too early
3. config module changes would widen ownership and persistence concerns beyond this minimal slice

### 3. Allow Only Minimal Router Handoff If Needed

The next implementation may touch `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` only if that is strictly needed to pass backend-owned service config into the existing answer path.

If router changes are needed, router may only:

1. read a backend service-owned config field already available on the server side
2. pass that server-owned config object into a service-layer helper
3. keep request schema unchanged

Router must not:

1. parse provider name from request body
2. read provider choice from frontend input
3. call `get_rag_model_client(...)` directly
4. implement allowlist logic
5. decide fallback behavior

### 4. Preserve Early-Return Order

The next implementation must preserve this call order:

1. evaluate `no_current_release`
2. evaluate grounded context sufficiency
3. only then resolve provider name from explicit backend-owned config handoff
4. only then resolve provider client through `get_rag_model_client(...)`

This guarantees:

1. `no_current_release` does not trigger resolver or registry
2. `insufficient_context` does not trigger resolver or registry

### 5. Keep Runtime Providers Narrow

The next implementation must still allow only these runtime providers:

1. `deterministic_mock`
2. `disabled`

It must not add:

1. new runtime provider names
2. `future_external` runtime support
3. real external model connection

### 6. Keep Live Config Injection Server-Side Only

The next implementation may use only:

1. explicit backend-owned app config handoff
2. explicit backend-owned service config handoff
3. existing narrow resolver logic under `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`

It must not use:

1. request-body provider hint
2. frontend provider control
3. environment variables
4. `ProjectConfig.models`
5. `UserGameConfig`
6. `ProviderManager.active_model`

## Files To Change In The Next Implementation Slice

Recommended file touch set for the next code round:

1. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
3. `tests/unit/game/test_knowledge_rag_answer.py`
4. `tests/unit/game/test_knowledge_rag_provider_selection.py`

Optional and only if strictly needed for backend-owned config handoff:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`

Allowed optional router-touch reason:

1. hand off backend service-owned config into a service-layer helper without adding provider-selection logic to router code

## Files That Should Not Change In The Next Implementation Slice

The next code slice should not modify these files unless a later review explicitly widens scope:

1. any `console/src/` file
2. any request or response schema for the RAG router
3. `src/ltclaw_gy_x/providers/provider_manager.py`
4. `src/ltclaw_gy_x/game/config.py`
5. `ProjectConfig.models`-owning surfaces
6. `UserGameConfig`-owning surfaces
7. environment variable handling
8. runtime provider list definitions

Reasoning:

1. frontend and request schema must remain unchanged in this slice
2. provider manager and config surfaces would widen ownership too early
3. runtime provider list changes would turn this into a provider-expansion slice instead of a handoff slice

## Focused Test Checklist For The Next Implementation Slice

The next code round should add or update tests for these cases:

1. no config uses the default `deterministic_mock` path
2. service config `disabled` resolves to disabled provider
3. service config unknown provider clear-fails
4. provider factory failure still falls back to `disabled` with warning
5. `no_current_release` returns before resolver or registry call
6. `insufficient_context` returns before resolver or registry call
7. router or request body cannot pass provider name as live provider control
8. router does not call `get_rag_model_client(...)`
9. citation ids outside `context.citations` still degrade to grounded failure behavior
10. runtime providers remain unchanged

Recommended focused test files:

1. `tests/unit/game/test_knowledge_rag_answer.py`
2. `tests/unit/game/test_knowledge_rag_provider_selection.py`
3. optionally existing router regression coverage only to confirm no request-schema or provider-choice widening

## Acceptance Criteria For The Next Implementation Slice

The next code round is acceptable only if all of the following remain true:

1. the slice implements only minimal live config handoff and does not become a real external model integration
2. backend-owned app or service config is handed into the answer path explicitly rather than through hidden runtime state
3. router, if touched, only performs backend-owned config handoff and does not implement provider selection
4. request body still does not carry provider name
5. frontend still does not control provider name
6. runtime providers remain only `deterministic_mock` and `disabled`
7. unknown provider still clear-fails
8. provider initialization failure still falls back only to `disabled` with warning
9. `no_current_release` and `insufficient_context` still return before provider selection
10. `get_rag_model_client(...)` remains the only registry entry point
11. citation validation still trusts only `context.citations`
12. retrieval and context boundaries remain unchanged
13. no new API or request-schema change is added

## Explicit Non-Goals

This plan keeps all of the following out of the next implementation slice:

1. real external provider integration
2. OpenAI or any other external model integration
3. new runtime provider names
4. request-body provider hint
5. frontend provider control
6. `ProviderManager.active_model` adoption
7. environment-variable-driven provider selection
8. embedding or vector store
9. `candidate_evidence.jsonl` boundary expansion
10. formal-map or P3.7 UI changes

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to `git diff --check`.

## Plan Result

1. `P3.rag-model-2f` is complete as a docs-only implementation plan.
2. The next code slice should add only a minimal live config handoff into the existing answer path.
3. Router may be touched only to hand off backend-owned service config and must not choose provider.
4. Runtime providers must remain limited to `deterministic_mock` and `disabled`.
5. The next step should be `P3.rag-model-2g` minimal live config handoff implementation rather than direct real external model integration.