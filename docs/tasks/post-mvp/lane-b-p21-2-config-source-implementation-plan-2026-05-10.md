# Lane B P21.2 Config Source Implementation Plan

Date: 2026-05-10
Status: docs-only plan.
Scope: freeze the smallest implementation needed to make backend-owned external_provider_config reachable from the existing RAG answer path.

## Goal

1. Finalize the minimum P21.3 code slice for backend-owned config activation.
2. Reuse the existing provider-selection traversal contract instead of opening any new request, frontend, or router source.
3. Keep the feature default disabled, backend-only, not production rollout, and not production ready.

## 1. Recommended Minimum Implementation

P21.3 should implement exactly this minimum shape:

1. Add external_provider_config to ProjectConfig.
2. Keep that field backend-owned and project-scoped.
3. Add a read-only GameService.config property that returns self.project_config.
4. Reuse the existing provider_selection traversal for config rather than inventing a new source path.
5. Do not add any request-owned, frontend-owned, or router-owned provider entry point.
6. Do not connect ProviderManager.active_model.
7. Do not connect SimpleModelRouter.
8. Do not change Ask schema.
9. Do not change frontend.

Why this is the preferred minimum:

1. provider_selection.py already traverses config.
2. GameService already owns project_config as the stable backend project config object.
3. A read-only GameService.config bridge is smaller and less invasive than broadening provider_selection traversal rules.
4. This keeps the activation surface explicit, reversible, and backend-owned.

## 2. Recommended Field Shape

ProjectConfig.external_provider_config should use a mapping-compatible shape that can be coerced by the existing config parser:

```python
external_provider_config = {
    "enabled": False,
    "transport_enabled": False,
    "provider_name": "future_external",
    "model_name": None,
    "allowed_providers": ["future_external"],
    "allowed_models": [],
    "base_url": None,
    "timeout_seconds": 15.0,
    "max_output_tokens": None,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {
        "api_key_env_var": None
    }
}
```

Shape rules:

1. Defaults must stay disabled.
2. No real API key value may appear in ProjectConfig.
3. allowed_models defaulting to empty must continue to block real HTTP through allowlist failure.
4. transport_enabled=False must continue to block credential resolution and HTTP transport.
5. provider_name should stay fixed to future_external in this lane.
6. env must store only api_key_env_var metadata.

## 3. P21.3 Allowed Edit Surface

Allowed source changes:

1. src/ltclaw_gy_x/game/config.py
2. src/ltclaw_gy_x/game/service.py

Allowed minimum tests:

1. tests/unit/game/test_knowledge_rag_provider_selection.py
2. tests/unit/game/test_knowledge_rag_answer.py
3. tests/unit/game/test_service.py if a small GameService config-bridge test is needed

Do not widen scope unless a local blocker is proven:

1. Do not change src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py unless a P20 gate regression is discovered.
2. Do not change src/ltclaw_gy_x/app/routers/game_knowledge_rag.py.
3. Do not change frontend files.
4. Do not change ProviderManager.
5. Do not change SimpleModelRouter.

## 4. P21.3 Required Test Points

P21.3 must verify at least the following:

1. ProjectConfig.external_provider_config defaults to disabled.
2. GameService.config returns project_config.
3. build_rag_answer_with_service_config(..., game_service) can resolve external_provider_config through game_service.config.external_provider_config.
4. Default disabled still means no env read and no httpx call.
5. transport_enabled=False still means no env read and no httpx call.
6. Missing or empty allowlist still means no env read and no httpx call.
7. Request-like provider, model, and api_key fields still do not participate in selection.
8. no_current_release still does not initialize provider.
9. insufficient_context still does not initialize provider.
10. Only valid grounded context plus backend-owned config can enter provider path.
11. Ask router schema remains unchanged.

If P21.3 touches external client for a real blocker, then the external-client focused suite must be rerun.

## 5. Forbidden Changes

The following remain explicitly forbidden:

1. No request body schema change.
2. No frontend provider selector.
3. No API key stored in project config.
4. No secret loading from docs or task files.
5. No ProviderManager.active_model integration.
6. No SimpleModelRouter integration.
7. No production rollout.
8. No ordinary-user provider, model, or api_key controls.
9. No ordinary RAG write path into release, formal map, test plan, or workbench draft.

## 6. Validation Plan For P21.3

Required validation command:

```bash
.venv/bin/python -m pytest \
  tests/unit/game/test_knowledge_rag_provider_selection.py \
  tests/unit/game/test_knowledge_rag_answer.py \
  tests/unit/game/test_service.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  -q
```

Conditional extra validation:

```bash
.venv/bin/python -m pytest tests/unit/game/test_knowledge_rag_external_model_client.py -q
```

Run the extra external-client suite only if P21.3 touches external client code because of a proven local blocker.

## 7. Next Step

1. The next step is P21.3 backend config activation implementation.
2. That next step is still not production rollout.
3. That next step does not activate real provider access for ordinary users.
4. That next step does not open frontend UI.
5. Real operator activation remains a later validation slice, not this implementation plan.

## Implementation Freeze Summary

1. ProjectConfig gains external_provider_config.
2. GameService gains a read-only config bridge to project_config.
3. provider_selection keeps using its current config traversal contract.
4. External transport remains default disabled until backend-owned config explicitly opens all gates.
5. Request, frontend, router, ProviderManager, and SimpleModelRouter remain outside the RAG provider control path.