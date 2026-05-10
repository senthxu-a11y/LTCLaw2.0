# Knowledge P3.external-provider-4 Runtime Allowlist Boundary Review

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md
6. src/ltclaw_gy_x/game/knowledge_rag_answer.py
7. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
8. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
9. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
10. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py

## Purpose

Define the boundary for a future runtime allowlist decision after `P3.external-provider-3` and before any runtime rollout.

This slice is docs-only.

It does not modify backend code, frontend code, request schema, registry contents, or public API.

It does not add `future_external` to `SUPPORTED_RAG_MODEL_PROVIDERS`.

It does not connect a real LLM.

It does not perform real HTTP.

It does not connect real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

## Current Code Facts

The current code path confirms the following:

1. `build_rag_answer_with_service_config(...)` remains the only approved live handoff entry for backend-owned config.
2. Router code calls the answer helper with `game_service` and does not directly call `get_rag_model_client(...)`.
3. Backend-owned `external_provider_config` is interpreted only inside the answer/provider-selection layer.
4. Request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection.
5. Ask request schema for this path still remains `{ query }` plus existing debug bounds only.
6. `SUPPORTED_RAG_MODEL_PROVIDERS` still contains only `deterministic_mock` and `disabled`.
7. `future_external` still is not a runtime supported provider.
8. The external client remains a disabled-by-default skeleton and still does not perform real transport.
9. `no_current_release` and `insufficient_context` still return before provider/config/credential/transport execution.
10. Citation grounding still remains owned by the answer service and only accepts citation ids already present in `context.citations`.
11. `candidate_evidence` still remains outside default RAG reads.
12. `ProviderManager.active_model` still is not an allowed provider-selection source for this path.
13. Env reads are still unimplemented and are not allowed as request-time provider selection.

## What This Review Does Not Authorize

This review does not authorize any of the following:

1. adding `future_external` to `SUPPORTED_RAG_MODEL_PROVIDERS`
2. real LLM execution
3. real HTTP transport
4. real credential integration
5. new endpoint or API surface
6. frontend provider or model control
7. Ask request schema changes
8. request-body provider/model/api_key ownership
9. router-side provider selection
10. router-side direct registry calls
11. fallback from one real provider to another real provider
12. runtime rollout

## Runtime Allowlist Entry Conditions

`future_external` may enter the runtime provider set only in a later dedicated implementation slice after this boundary review is accepted.

That future entry must remain backend-owned.

The controlling decision must come from backend-owned config interpretation and registry decision, not from router, request body, frontend UI, or agent active-model state.

The minimum future entry conditions are cumulative rather than optional.

All of the following must be true at the same time before `future_external` may be added to the runtime provider set:

1. a dedicated implementation slice explicitly expands the runtime allowlist rather than implicitly treating config presence as runtime support
2. `enabled` remains false by default and explicit backend-owned enablement is required
3. backend-owned credential presence is available through the approved credential boundary
4. provider allowlist explicitly includes `future_external`
5. model allowlist explicitly includes the selected model
6. timeout policy is explicitly defined and enforced by backend-owned config
7. cost policy is explicitly defined and enforced by backend-owned config
8. privacy and logging policy is explicitly defined and enforced by backend-owned config
9. provider initialization and transport path remain backend-owned and never request-selected
10. focused tests prove that request body, router, frontend, and `ProviderManager.active_model` still cannot select provider
11. focused tests prove that unsupported provider or model never reaches credential resolution or transport
12. a later rollout review explicitly approves runtime entry after the implementation exists

Config presence alone is not enough.

Credential presence alone is not enough.

Env presence alone is not enough.

Service-config wiring alone is not enough.

## Required Failure Behavior

The future implementation must preserve explicit failure semantics.

Required rules:

1. unknown provider must clear-fail and must not silently switch to another provider
2. provider init failure may only clear-fail or fall back to `disabled`
3. provider init failure must not fall back to another real provider
4. disabled config must return safe non-answer behavior and must not generate fake answer text
5. missing credential must return safe non-answer behavior and must not generate fake answer text
6. provider not allowed must not enter credential resolution or transport
7. model not allowed must not enter credential resolution or transport
8. `future_external` not in the runtime allowlist must clear-fail before runtime selection
9. runtime fallback to `disabled` is acceptable only when the code path is explicit and warning-bearing
10. clear-fail must remain preferable to silent provider substitution

## Router / Request Boundary

The router and request boundary remain frozen.

Required rules:

1. router still must not choose provider
2. router still must not directly call `get_rag_model_client(...)`
3. router still must not create credential resolvers
4. router still must not create transport objects
5. Ask request schema still must not add provider, model, or api_key fields
6. request provider/model/api_key fields still must be ignored if present in request-like payloads
7. frontend UI still must not expose provider or model selection for this path
8. backend-owned config remains the only approved provider-selection source
9. `ProviderManager.active_model` still must not become a provider source for this path

## Credential / Transport Boundary

Credential and transport authority remain backend-owned only.

Required rules:

1. no real credential material may come from request body
2. no real credential material may come from frontend state
3. future env reads, if ever allowed, must occur only as backend-owned startup-time or config-time behavior
4. env reads must not become request-time provider selection
5. no credential lookup should happen for `no_current_release`
6. no credential lookup should happen for `insufficient_context`
7. no transport should happen for `no_current_release`
8. no transport should happen for `insufficient_context`
9. no transport should happen when allowlist, enablement, or credential requirements fail

## Testing Requirements For Future Implementation

Any later implementation that proposes runtime allowlist entry must prove at least the following:

1. `future_external` not yet in the runtime allowlist still clear-fails
2. runtime providers still default to only `deterministic_mock` and `disabled`
3. backend-owned config allowlist must pass before any external client is created
4. disabled config does not produce fake answer
5. missing credential does not produce fake answer
6. provider or model not allowed does not enter transport
7. request provider/model/api_key fields are ignored
8. router does not call the registry directly
9. `no_current_release` and `insufficient_context` do not trigger provider path
10. model response citation ids outside `context.citations` are still rejected by the answer service

Future adjacent regression should also keep proving the following unchanged rules:

1. citation grounding remains answer-service-owned and limited to `context.citations`
2. `candidate_evidence` does not automatically enter RAG
3. provider init failure does not switch to another real provider
4. backend-owned env or config normalization does not become request-time selection

## Recommended Next Slice

The next recommended slice is a runtime allowlist implementation plan.

That plan should:

1. define the concrete backend-owned config and registry changes required for runtime entry
2. define exact clear-fail versus `disabled` fallback rules
3. define startup-time or config-time env normalization rules if env support is later approved
4. define focused tests for allowlist gating, missing credential, init failure, and transport suppression
5. remain explicitly separate from real provider connectivity rollout

The next slice should not directly connect a real provider.

## Review Decision

1. `P3.external-provider-4` runtime allowlist boundary review is complete as a docs-only slice.
2. This review does not change runtime allowlist membership.
3. `future_external` remains outside `SUPPORTED_RAG_MODEL_PROVIDERS` in this slice.
4. Runtime providers still remain only `deterministic_mock` and `disabled`.
5. Real LLM, real HTTP, real credential integration, new API, frontend change, and Ask request-schema change all remain out of scope.
6. Router and request body still have no provider-selection authority.
7. The future runtime entry for `future_external` must be backend-owned and must require disabled-by-default, credential presence, provider allowlist, model allowlist, and timeout/cost/privacy policy together.
8. Unknown provider must clear-fail rather than silently switch.
9. Provider init failure may only clear-fail or fall back to `disabled`, never to another real provider.
10. `no_current_release` and `insufficient_context` still must bypass provider, credential, and transport work.
11. Citation grounding remains answer-service-owned and limited to `context.citations`.
12. `candidate_evidence` still does not automatically enter RAG.
13. `ProviderManager.active_model` still is not an approved provider source.
14. Any future env read must remain backend-owned startup-time or config-time behavior, not request-time selection.

## Validation Note

This pass is docs-only.

This pass does not run pytest.

This pass does not run TypeScript.

Post-edit validation for this pass is limited to documentation diff whitespace checking and keyword review to confirm that the slice is not described as runtime rollout or real provider integration.