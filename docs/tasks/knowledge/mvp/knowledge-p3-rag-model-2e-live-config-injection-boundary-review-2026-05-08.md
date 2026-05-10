# Knowledge P3.rag-model-2e Live Config Injection Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2c-config-injection-boundary-review-2026-05-08.md
3. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2d-implementation-plan-2026-05-08.md
4. docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2d-closeout-2026-05-08.md
5. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
6. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md

## Review Goal

Define whether and how backend app or service config may be injected into the live RAG answer path after the minimal 2d resolver helper landed.

This review is docs-only. It does not modify backend code, frontend code, routers, request schema, or public API.

This docs-only pass did not rerun pytest.

## Confirmed Current Baseline

The current code and boundary baseline is:

1. `build_rag_answer_with_provider(...)` remains the service-layer provider-selection entry point.
2. `get_rag_model_client(...)` remains the only registry entry point.
3. The 2d helper resolves provider name only from explicit backend-passed object or mapping fields.
4. The current helper supports direct or nested `config`-style resolution for `rag_model_provider` and `knowledge_rag_model_provider`.
5. `no_current_release` and `insufficient_context` still return before resolver or registry use.
6. Router request body still does not carry provider name.
7. Frontend still does not control provider name.
8. Runtime providers remain only `deterministic_mock` and `disabled`.
9. Unknown provider still clear-fails.
10. Provider factory initialization failure still falls back only to `disabled`.
11. Citation validation still trusts only `context.citations`.

## Core Decision

Live backend app or service config may enter the RAG answer path only through explicit server-side handoff into the existing backend service path.

That means:

1. a backend-owned app or service config object may be passed explicitly into the RAG answer path
2. the answer path may resolve provider name from that explicit handoff using the existing narrow helper boundary
3. the live path must still resolve provider only through `get_rag_model_client(...)`
4. the live path must not read provider name from request body, frontend state, router choice, environment variables, or global provider runtime state

## Boundary Answers

### 1. Where may live config handoff happen?

At an explicit backend service-composition boundary above `build_rag_answer_with_provider(...)`.

Allowed examples in principle:

1. a backend app-layer service object passes a server-owned config object into the existing answer path
2. a backend game service passes a server-owned config object into the existing answer path
3. a narrow internal caller passes an explicit provider override for tests or controlled backend use

Disallowed examples:

1. request body carries provider name
2. frontend sends provider control
3. router chooses provider directly
4. answer path pulls provider from ambient global runtime state

### 2. What should the live source of truth be?

The source of truth should remain explicit backend-owned app or service config passed into the answer path, not hidden runtime state.

This keeps provider selection observable, reviewable, and bounded to the backend service layer.

### 3. Are environment variables allowed for the live path?

No.

Environment-variable-driven selection remains out of scope because it would add hidden runtime control and broaden the operational boundary before the live handoff shape is settled.

### 4. May request body or frontend pass provider name for live path selection?

No.

This review does not allow request-level provider hint or frontend provider control.

### 5. May router choose provider?

No.

Router must remain thin and must not become the provider-selection surface.

### 6. May `ProjectConfig.models`, `UserGameConfig`, or `ProviderManager.active_model` become the live source of truth in this slice?

No.

This review does not adopt project-local metadata, user config, or global provider runtime state as the live RAG provider authority.

If a later slice wants to bridge any of these surfaces into the RAG answer path, that requires a separate review because it would widen the ownership and runtime-control surface significantly.

### 7. How is the allowlist preserved when live config is handed off?

Live handoff may carry only a provider name that still resolves through `get_rag_model_client(...)`.

That means the current allowlist remains unchanged:

1. `deterministic_mock`
2. `disabled`

No additional runtime provider becomes allowed in this slice.

### 8. How are unknown provider and provider initialization failure handled?

Rules remain unchanged:

1. unknown provider is a configuration error and must clear-fail
2. provider initialization failure may fall back only to `disabled`

### 9. How do we preserve early-return and citation boundaries in the live path?

The call order must remain:

1. evaluate `no_current_release`
2. evaluate grounded context sufficiency
3. only after those gates resolve provider name and provider client

Citation validation must still trust only `context.citations`.

### 10. What does this slice explicitly not authorize?

This review does not authorize:

1. real external LLM integration
2. OpenAI or any other external provider integration
3. request-body provider hint
4. frontend provider control
5. router provider selection
6. environment-variable-driven provider choice
7. `ProjectConfig.models` as live provider authority
8. `UserGameConfig` as live provider authority
9. `ProviderManager.active_model` as live provider authority

## Recommended Next Slice

Recommended next slice: `P3.rag-model-2f` minimal live config handoff implementation planning.

That slice should stay constrained as follows:

1. pass backend-owned app or service config explicitly into the existing answer path
2. keep router unchanged
3. keep request schema unchanged
4. keep frontend unchanged
5. keep runtime providers limited to `deterministic_mock` and `disabled`
6. keep real external models out of scope

## Validation Note

This slice is docs-only.

This docs-only pass did not rerun pytest.

Post-edit validation for this pass is limited to `git diff --check`.

## Review Result

1. `P3.rag-model-2e` is complete as a docs-only live backend app/service config injection boundary review.
2. Live config injection is allowed only through explicit server-side handoff into the existing backend answer path.
3. Request body, frontend, router, environment variables, `ProjectConfig.models`, `UserGameConfig`, and `ProviderManager.active_model` are not adopted as the live provider source of truth in this slice.
4. Runtime providers remain limited to `deterministic_mock` and `disabled`, unknown provider remains clear-fail, and provider initialization failure remains fallback-to-disabled only.
5. The next step, if implementation is desired, should be `P3.rag-model-2f` planning rather than direct external model integration.