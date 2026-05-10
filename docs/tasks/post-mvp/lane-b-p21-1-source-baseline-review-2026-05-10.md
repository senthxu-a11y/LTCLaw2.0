# Lane B P21.1 Source Baseline Review

Date: 2026-05-10
Status: docs-only review.
Scope: confirm the smallest backend-owned config carrying surface for controlled real-LLM activation in the current RAG answer path.

## Review Target

Reviewed files:

1. docs/tasks/post-mvp/lane-b-p21-controlled-backend-config-activation-plan-2026-05-10.md
2. src/ltclaw_gy_x/game/service.py
3. src/ltclaw_gy_x/game/config.py
4. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
5. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
6. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
7. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py

## Current Source Baseline

1. P20 real HTTP transport already exists in the current RAG answer path.
2. ExternalRagModelClientConfig still defaults enabled=False and transport_enabled=False.
3. The only supported real-provider identifier in the current registry path is future_external.
4. build_rag_answer_with_service_config(query, context, game_service) still receives game_service directly from the router.
5. Ask request schema still accepts only query, max_chunks, and max_chars.
6. Router still does not choose provider and still does not forward provider, model, or api_key fields.
7. Answer path still requires grounded current-release context before provider initialization and still enforces citation validation on model output.
8. Current state remains backend-only, default-off, not production rollout, and not production ready.

## What build_rag_answer_with_service_config(...) Can Read Today

Current read path:

1. Router passes game_service into build_rag_answer_with_service_config(...).
2. build_rag_answer_with_service_config(...) delegates to build_rag_answer_with_provider(...).
3. build_rag_answer_with_provider(...) calls resolve_rag_model_provider_name(config_or_service) and resolve_external_rag_model_client_config(config_or_service).
4. knowledge_rag_provider_selection.py only looks for these direct or nested names:
   - rag_model_provider
   - knowledge_rag_model_provider
   - external_provider_config
   - service_config
   - app_config
   - config

Source-level consequence:

1. Current GameService does not expose service_config, app_config, config, rag_model_provider, knowledge_rag_model_provider, or external_provider_config.
2. Current GameService does expose project_config and user_config, but provider selection does not traverse project_config or user_config.
3. Therefore, the current game_service object is not yet a stable carrying surface for external_provider_config without a small future bridge.

## Stable Backend-Owned Surfaces Present Today

1. GameService.project_config is stable, backend-owned, and loaded through load_project_config(...).
2. GameService.user_config is backend-local but user-scoped and already carries user-specific SVN credentials and local-root settings.
3. ProjectConfig is project-scoped, versioned, YAML-backed, and already used as the main backend project configuration object.
4. UserGameConfig is not a good activation source for provider transport because it is user-scoped and already mixes local operator state plus decrypted secret-adjacent fields.

## Recommended Minimum Config Carrying Surface

Recommended source for P21.2 and later implementation:

1. Store external_provider_config on ProjectConfig as a new backend-owned project-scoped field.
2. Use GameService.project_config as the authoritative source object.
3. In the later implementation slice, add the thinnest possible bridge so the existing provider-selection contract can see that ProjectConfig.

Recommended bridge options for P21.2 evaluation:

1. Preferred: add a GameService.config property that returns project_config, then keep provider_selection.py unchanged because it already traverses config.
2. Alternate: extend provider_selection.py to traverse project_config explicitly.

Review recommendation:

1. Prefer GameService.config -> project_config because it reuses the existing provider-selection traversal contract and keeps the provider-selection surface narrow.
2. Keep external_provider_config physically defined on ProjectConfig, not on GameService runtime state and not on UserGameConfig.

## Why Request, Frontend, And Router Must Not Be Used

1. Router schema currently carries only query, max_chunks, and max_chars.
2. Keeping activation out of request body preserves backend ownership and avoids ordinary-user provider selection.
3. Keeping activation out of frontend state avoids adding provider selector, API-key UI, or model selector drift.
4. Keeping activation out of router logic preserves router authority boundaries; router should continue to pass only game_service into the answer path.
5. None of these surfaces are acceptable places to carry api_key, provider_name, model_name, or base_url.

## Why ProviderManager And SimpleModelRouter Must Stay Out

1. SimpleModelRouter in GameService is a separate bridge for other model-calling paths and is driven by ProviderManager.active_model.
2. The current RAG path does not use SimpleModelRouter for provider selection or transport.
3. ProviderManager.active_model is runtime-selected state, not the narrow backend-owned config contract already used by the RAG answer path.
4. Reusing ProviderManager or SimpleModelRouter here would blur control boundaries, create silent-switch risk, and conflict with the current backend-only explicit-config lane.
5. P21 should continue using the existing external_provider_config plus registry path, not the general provider-manager path.

## Existing Field Availability

1. ProjectConfig currently has no external_provider_config field.
2. UserGameConfig currently has no external_provider_config field.
3. GameService currently has no config property and no external_provider_config property.
4. Therefore P21 implementation will need a small field addition plus a small bridge addition, but not a router, request, or frontend change.

## Suggested New Field Name

Recommended field name:

1. external_provider_config

Recommended placement:

1. ProjectConfig.external_provider_config

Reason:

1. The name already matches the existing provider-selection contract.
2. Reusing the same field name avoids inventing a second activation vocabulary.
3. It keeps future config coercion aligned with ExternalRagModelClientConfig.

## Forbidden Sources Confirmed

These must remain forbidden for P21 activation input:

1. request body
2. frontend state or selector
3. router selection logic
4. ProviderManager.active_model
5. SimpleModelRouter
6. docs or task files
7. hard-coded secret literals in code or config examples

## P21.2 Recommended Construction Direction

P21.2 should freeze the smallest implementation plan around this shape:

1. Add external_provider_config to ProjectConfig.
2. Add a read-only GameService.config bridge that returns project_config, or choose the alternate explicit provider-selection traversal for project_config if the bridge is rejected.
3. Keep API key value in environment only.
4. Keep only env.api_key_env_var in ProjectConfig.
5. Keep router and Ask schema unchanged.
6. Keep ProviderManager and SimpleModelRouter out of the RAG path.
7. Keep activation backend-only, default-off, not production rollout, and not production ready.

## Review Conclusion

1. The current best minimal config source is GameService.project_config, carried by ProjectConfig.
2. The current game_service object does not yet expose a provider-selection-compatible config bridge.
3. P21 should not introduce a new request-owned, frontend-owned, or provider-manager-owned control surface.
4. P21.2 should freeze ProjectConfig.external_provider_config plus the smallest GameService-to-provider-selection bridge.