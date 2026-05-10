# Lane B P21.3 Backend Config Activation Closeout

Date: 2026-05-10
Status: completed minimal backend config bridge.

## Actual Changed Files

1. src/ltclaw_gy_x/game/config.py
2. src/ltclaw_gy_x/game/service.py
3. tests/unit/game/test_knowledge_rag_provider_selection.py
4. tests/unit/game/test_knowledge_rag_answer.py
5. tests/unit/game/test_service.py
6. docs/tasks/post-mvp/lane-b-p21-3-backend-config-activation-closeout-2026-05-10.md

## Outcome

1. ProjectConfig.external_provider_config is now a fixed backend-owned field.
2. The field defaults to None.
3. GameService.config now provides a read-only bridge to project_config.
4. This is a backend-only config bridge, not production rollout.
5. Default behavior remains disabled.

## Boundaries Preserved

1. Ask schema was not changed.
2. Frontend was not changed.
3. ProviderManager.active_model was not connected to the RAG path.
4. SimpleModelRouter behavior was not changed.
5. No real API key was written into config.
6. Ordinary RAG Q&A remains no-write.

## Validation Summary

1. answer path can now resolve backend-owned external_provider_config through game_service.config -> project_config.
2. Default disabled and transport-disabled paths still safe-fail before env and HTTP.
3. Missing allowlist still blocks before env and HTTP.
4. Router schema and router authority remain unchanged.

## Next Step

1. P21.4 config activation smoke validation.
2. Keep the lane backend-only, default disabled, not production rollout, and not production ready.