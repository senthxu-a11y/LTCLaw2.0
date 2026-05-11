# Lane B P21.9 Transport Kill-Switch Hot-Reload Closeout

Date: 2026-05-11
Status: backend minimal fix completed on Mac dev machine
Scope: backend-only hot-reload kill-switch fix plus focused unit validation; no frontend changes and no real provider connectivity

## 1. Actual Modified Files

This round modified:

1. `src/ltclaw_gy_x/game/service.py`
2. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
3. `tests/unit/game/test_service.py`
4. `tests/unit/routers/test_game_knowledge_rag_router.py`
5. `docs/tasks/post-mvp/lane-b-p21-9-transport-kill-switch-hot-reload-closeout-2026-05-11.md`

This round did not modify:

1. `console/src/`
2. Ask request schema
3. frontend provider selector
4. `ProviderManager`
5. `SimpleModelRouter`
6. production rollout behavior

## 2. Fix Approach

P21.9 implemented the minimal generation-barrier approach recommended by P21.8.

What changed:

1. `GameService` now owns `_config_generation` with a read-only `config_generation` property
2. generation starts at `0`
3. `reload_config()` increments generation only after reload completes successfully
4. `POST /game/knowledge/rag/answer` now snapshots generation before the first context build
5. if generation changes during that first context build, the router re-reads current-release context and continues with the latest live `game_service` config
6. if generation changes again during that second read, the router fails closed and returns a safe `insufficient_context` response instead of risking stale external transport

This keeps the fix local to the hot answer path and does not widen the provider-selection surface.

## 3. Generation Barrier Behavior

The final behavior is:

1. if `config_generation` is unchanged across the request setup path, ordinary RAG answer behavior stays the same
2. if generation changes once, the router discards the first context view, rebuilds context, and uses the latest live config for provider selection
3. if generation changes twice in the same request setup window, the router fails closed with a safety warning and does not enter external transport

Fail-closed warning used by the router:

1. `RAG answer config changed repeatedly during request. External transport was skipped until reload settles.`

## 4. Kill-Switch Hot Path Coverage

This round added unit coverage for the hot-reload boundary and revalidated the existing external-provider guardrails.

Covered outcomes:

1. `GameService.config_generation` exists at startup and starts at `0`
2. successful `reload_config()` increments generation
3. unchanged-generation answer requests keep prior behavior
4. single-generation-change answer requests re-read context and use the latest config bridge
5. repeated-generation-change answer requests fail closed before answer building
6. after a generation-triggered re-read, updated backend-owned configs with `enabled=false` do not reach transport
7. after a generation-triggered re-read, updated backend-owned configs with `transport_enabled=false` do not reach transport
8. after a generation-triggered re-read, updated backend-owned configs with empty `allowed_models` do not reach transport

This is the intended closure for the P21.5 caveat on the reviewed backend path. A Windows rerun is still required to confirm the operator-side fake-endpoint receipt now loses the extra hot-path HTTP call.

## 5. Boundaries Preserved

The following boundaries remain unchanged:

1. Ask schema still only exposes `query`, `max_chunks`, and `max_chars`
2. frontend remains unchanged
3. no frontend provider selector was added
4. `ProviderManager.active_model` still does not control the ordinary RAG provider path
5. `SimpleModelRouter` still is not connected to the ordinary RAG provider path
6. no real external provider was connected
7. no real secret value was introduced
8. ordinary RAG Q&A still does not write release, formal map, test plan, or workbench draft artifacts
9. this is still not production ready
10. this is still not production rollout

## 6. Test Result

Focused validation command:

```bash
.venv/bin/python -m pytest \
  tests/unit/game/test_service.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  tests/unit/game/test_knowledge_rag_answer.py \
  tests/unit/game/test_knowledge_rag_provider_selection.py \
  tests/unit/game/test_knowledge_rag_external_model_client.py \
  -q
```

Observed result:

1. `185 passed in 1.58s`

What this validation demonstrates:

1. the generation counter is present and increments on successful reload
2. router hot-reload behavior is covered for single-change re-read and repeated-change fail-closed paths
3. static external-provider guardrails still prevent HTTP transport when disabled, transport-disabled, or missing allowlist state is active

## 7. Next Step Suggestion

Recommended next step:

1. rerun the Windows P21.5 fake-endpoint kill-switch smoke on the operator machine to confirm that saving `transport_enabled=false` no longer allows the next immediate RAG answer to hit the fake endpoint
