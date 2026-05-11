# Lane B P21.10 Second Generation Barrier Closeout

Date: 2026-05-11
Status: backend narrow follow-up completed on Mac dev machine
Scope: add a second generation barrier at the transport-sensitive answer boundary; no frontend changes and no real provider connectivity

## 1. Actual Modified Files

This round modified:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
3. `tests/unit/routers/test_game_knowledge_rag_router.py`
4. `tests/unit/game/test_knowledge_rag_answer.py`
5. `docs/tasks/post-mvp/lane-b-p21-10-second-generation-barrier-closeout-2026-05-11.md`

This round did not modify:

1. `console/src/`
2. Ask schema
3. frontend provider selector
4. `ProviderManager`
5. `SimpleModelRouter`
6. external client implementation
7. provider registry
8. provider selection traversal rules

## 2. Fix Approach

P21.10 keeps P21.9 in place and adds the missing final generation guard at the provider-selection boundary.

What changed:

1. `knowledge_rag_answer.py` now defines `RagAnswerConfigGenerationChangedError`
2. `build_rag_answer_with_provider(...)` and `build_rag_answer_with_service_config(...)` now accept an optional `expected_generation`
3. after grounded-context validation and immediately before provider selection, the answer layer compares `expected_generation` against the current `config_generation`
4. if the generation does not match, the answer layer raises `RagAnswerConfigGenerationChangedError` before provider resolution and before any external transport can start
5. `game_knowledge_rag.py` now catches that signal, rebuilds context once against the latest live generation, and retries once
6. if the retry also sees unsettled generation, the router fails closed with `insufficient_context` and a safety warning

## 3. Where The Second Barrier Lives

The second barrier now sits at the transport-sensitive boundary itself.

Placement:

1. it is enforced inside `build_rag_answer_with_provider(...)`
2. it runs after grounded-context validation
3. it runs before `resolve_rag_model_provider_name(...)`
4. it runs before `resolve_external_rag_model_client_config(...)`
5. it runs before `get_rag_model_client(...)`
6. it therefore runs before any external transport can be initialized or invoked

## 4. Window Coverage Result

This round closes the gap identified in the P21.9 code review.

Covered windows now are:

1. reload during context build
2. reload after context build but before provider selection
3. repeated reload churn across both of those steps, which now fails closed

Practical result:

1. the answer path no longer relies only on the earlier context-build barrier
2. the final external-provider boundary now has its own generation check

## 5. Hot-Reload Kill-Switch Coverage

The reviewed hot path is now covered for the backend-owned kill-switch states that matter for the Windows caveat.

Covered outcomes:

1. `transport_enabled=false` hot reload does not reach fake transport after generation re-check and retry handling
2. `enabled=false` hot reload does not reach fake transport after generation re-check and retry handling
3. `allowed_models=[]` hot reload does not reach fake transport after generation re-check and retry handling
4. repeated generation churn fails closed before external transport
5. stable enabled config with grounded context still reaches the fake provider path

## 6. Boundaries Preserved

The following boundaries remain unchanged:

1. Ask schema still only exposes `query`, `max_chunks`, and `max_chars`
2. frontend remains unchanged
3. no frontend provider selector was added
4. `ProviderManager.active_model` still does not control the ordinary RAG provider path
5. `SimpleModelRouter` still is not connected to the ordinary RAG provider path
6. ordinary RAG Q&A still does not write release, formal map, test plan, or workbench draft artifacts
7. no real external provider was connected
8. this is still not production ready
9. this is still not production rollout

## 7. Test Result

Focused validation command:

```bash
.venv/bin/python -m pytest tests/unit/game/test_service.py tests/unit/routers/test_game_knowledge_rag_router.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_external_model_client.py -q
```

Observed result:

1. `189 passed in 1.78s`

What this validation demonstrates:

1. generation changes during context build still re-read to the latest config
2. generation changes after context build but before provider selection now trigger a retry on fresh context instead of stale transport use
3. repeated generation changes fail closed
4. `transport_enabled=false`, `enabled=false`, and empty `allowed_models` remain transport-blocking on the hot path
5. stable enabled config still reaches the fake provider path when grounded context is valid
6. no-current-release and insufficient-context paths still do not initialize provider selection

## 8. Recommendation

P21.10 is the first backend state where the reviewed code now matches the intended Windows kill-switch behavior closely enough to justify the next operator validation step.

Recommended next step:

1. proceed to the Windows P21.5 kill-switch smoke rerun to confirm that saving `transport_enabled=false` no longer allows the next immediate RAG answer to hit the fake endpoint
