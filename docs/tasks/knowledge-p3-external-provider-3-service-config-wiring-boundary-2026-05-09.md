# Knowledge P3.external-provider-3 Backend Service Config Wiring Boundary Review

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-provider-credential-boundary-review-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md
6. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
7. src/ltclaw_gy_x/game/knowledge_rag_answer.py
8. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py

## Review Goal

Freeze the backend service config handoff boundary for the live RAG answer path after `P3.external-provider-2` and before any service-config wiring implementation begins.

This slice is docs-only.

It does not modify backend code, frontend code, request schema, router behavior, runtime provider registry, or public API.

It does not implement service config wiring.

It does not connect a real provider.

## Confirmed Current Baseline

The current baseline is:

1. `P3.external-provider-2` is complete as a backend-only credential/config skeleton implementation.
2. The current external layer is still not real external provider integration.
3. The current implementation still does not perform real HTTP.
4. The current implementation still does not read real credential material.
5. The current implementation still does not add frontend provider/model UI.
6. The current implementation still does not change the RAG request schema.
7. Runtime providers still remain only `deterministic_mock` and `disabled`.
8. `enabled` still defaults to false.
9. Allowlist validation still occurs before credential resolver and transport.
10. Missing credential, disabled state, and allowlist failure still degrade safely.
11. `no_current_release` and `insufficient_context` still return before provider/config/credential path execution.
12. Request-like `provider_name`, `model_name`, and `api_key` fields still do not participate in provider selection.
13. The live router path currently calls `build_rag_answer_with_service_config(body.query, context, game_service)` and does not call `get_rag_model_client(...)` directly.

## Core Decision

Future live service-config wiring must continue to enter the RAG answer path through a backend-owned object handed into the answer service, not through router-side provider selection and not through request-time provider hints.

The current `build_rag_answer_with_service_config(...)` handoff shape remains the only approved live handoff entry.

## Boundary Answers

### 1. Config handoff source

The preferred live config source remains a backend-owned service object or config object passed explicitly into the answer helper.

Current anchor:

1. the router already resolves `game_service`
2. the router already passes that backend-owned object into `build_rag_answer_with_service_config(...)`

Approved future sources for the live RAG answer path are:

1. explicit dependency injection of a backend-owned service object
2. backend-owned service config already attached to `game_service`
3. backend-owned nested config fields such as `service_config`, `app_config`, or `config` reachable from the injected object
4. backend-owned agent service profile data only if it is first normalized into the handed-off backend-owned object before the answer path consumes it

Not-approved live sources are:

1. request body
2. query body
3. frontend UI state
4. router-built provider/model hint objects
5. per-request temporary provider config
6. `ProviderManager.active_model`

`app.state` may hold upstream defaults or already-assembled backend-owned config, but it is not approved as a router-side ad hoc provider-selection source.

If app-level defaults are used later, they must be normalized into the backend-owned service object or config object before the live answer path consumes them.

`ProviderManager.active_model` remains disallowed.

### 2. Router boundary

`game_knowledge_rag.py` may continue to read backend-owned app or service objects only to obtain the existing injected handoff object.

The router remains forbidden from:

1. calling `get_rag_model_client(...)` directly
2. resolving provider or model names directly
3. parsing request-body provider/model hints
4. creating credential resolver instances for the external path
5. creating transport objects for the external path

The router is allowed only to:

1. validate capability and request contract
2. build grounded context
3. obtain a backend-owned service object
4. pass that backend-owned object into the answer helper

So the router remains a thin handoff surface only.

### 3. Answer service boundary

`build_rag_answer_with_service_config(...)` remains the only approved live handoff entry for backend-owned config.

That means:

1. the answer service remains the place where service config is interpreted for provider selection
2. the answer service remains the place where provider-resolution warnings are merged into answer warnings
3. the router must not duplicate that logic

Service config must still not be resolved before the two current early-return boundaries:

1. `no_current_release`
2. `insufficient_context`

So future service-config parsing or normalization must happen only after those early returns have already been ruled out.

Config warnings should merge only in the answer layer.

Recommended merge rule:

1. config-resolution warnings may prepend or merge into answer warnings
2. model-client warnings may continue to merge with answer warnings
3. the answer layer remains the only place that assembles the final warning list

Degradation rules:

1. missing config should keep the current default behavior rather than forcing router-side failure
2. disabled provider should degrade to disabled safe fallback
3. unknown provider must not silently switch provider; clear fail or explicit disabled-style warning is acceptable only if implemented in the answer-layer boundary

### 4. External config object boundary

It is allowed for the `P3.external-provider-2` config shape to be embedded inside backend service config.

That embedding must remain backend-owned.

Recommended shape:

1. service config may carry ordinary provider-selection fields
2. service config may carry a nested external-provider config object using the `P3.external-provider-2` shape
3. the nested object must still keep `enabled` default false

Allowlist remains mandatory before any later external runtime rollout is considered.

So external provider cannot become rollout-eligible later unless:

1. explicit enable flag exists
2. explicit provider/model allowlist exists
3. credential resolver boundary exists
4. later rollout review approves runtime allowlist entry

Credential resolver is allowed only as an injected dependency.

It remains disallowed for router code to create the resolver directly.

### 5. Env boundary

This slice still does not implement env reads.

If a later slice allows env-backed secret resolution, env parsing must remain in backend-owned config or credential-resolution layers.

That means:

1. router must not read env for provider selection
2. request handling must not read env for provider selection
3. env must not become a request-time provider-selection mechanism

Env remains disallowed as request-time provider selection.

### 6. Runtime provider allowlist

This slice still keeps runtime providers limited to `deterministic_mock` and `disabled`.

External provider still cannot enter the runtime provider allowlist in this slice.

A future external provider may enter the runtime provider allowlist only after:

1. service config wiring implementation lands
2. disabled-by-default and allowlist semantics remain intact end to end
3. credential resolution remains backend-owned and safe
4. focused tests prove no request-driven selection and no unsafe fallback
5. a separate rollout review explicitly approves runtime entry

So yes, a separate rollout review is still required.

### 7. Testing requirements for future implementation

The future service-config wiring implementation must prove at least the following:

1. no config keeps current default behavior or `deterministic_mock` path rather than forcing request-driven provider choice
2. disabled config produces disabled safe fallback
3. unknown provider produces clear fail or explicit disabled-style warning without silent switching
4. request-body provider/model hints are ignored
5. router does not call `get_rag_model_client(...)` directly
6. `no_current_release` and `insufficient_context` do not resolve config or provider
7. external `enabled=false` does not call transport
8. missing credential does not fake answer
9. runtime providers remain unchanged

### 8. UI/API boundary

The UI and API boundary remain frozen.

This slice does not authorize:

1. GameProject provider/model UI
2. Ask payload changes beyond `{ query }`
3. new endpoint
4. RAG request schema change
5. `ProviderManager.active_model`

## Review Result

1. `P3.external-provider-3` boundary review is complete.
2. The follow-on backend service config wiring skeleton implementation is also complete.
3. Live config enters the RAG answer path only through `build_rag_answer_with_service_config(...)` using backend-owned service/config state.
4. The answer/provider-selection layer interprets backend-owned `external_provider_config`.
5. The router remains forbidden from provider/model resolution, request-hint parsing, resolver creation, transport creation, and direct `get_rag_model_client(...)` calls.
6. Request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection.
7. Ask request schema remains query-only for this path.
8. `future_external` may reach the external client skeleton only through backend-owned config interpretation, but it still cannot be selected as a runtime provider.
9. Runtime providers still remain only `deterministic_mock` and `disabled`.
10. The slice adds no real LLM, no real HTTP, no real credential, no new API, no frontend change, and no runtime rollout.
11. `ProviderManager.active_model` remains out of scope.
12. Env reads remain unimplemented and remain disallowed as request-time provider selection.
13. NUL repair in related tests was validation recovery only and not logic expansion.

## Recommended Next Slice

The next reasonable step is runtime allowlist boundary review.

That next slice should:

1. decide when `future_external` may enter the runtime provider set
2. decide the exact backend-only enablement conditions
3. keep the router thin
4. keep request/provider/model/api_key hints out of request body
5. keep real external provider rollout deferred until the allowlist rule is explicitly accepted

## Validation Note

Implementation validation recorded for the wiring skeleton:

1. focused pytest: `84 passed in 11.05s`
2. coverage included `test_game_knowledge_rag_router.py`, `test_knowledge_rag_answer.py`, `test_knowledge_rag_provider_selection.py`, `test_knowledge_rag_model_registry.py`, and `test_knowledge_rag_external_model_client.py`
3. focused NUL check: 9 related files were `NUL=0`
4. slice-related `git diff --check` had empty output
5. `test_knowledge_rag_model_registry.py` and `test_knowledge_rag_external_model_client.py` were rewritten as clean UTF-8 only to restore test collection after NUL pollution, with no logic expansion

This docs-only pass does not run pytest.

This docs-only pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation error checking and docs diff whitespace checking.
