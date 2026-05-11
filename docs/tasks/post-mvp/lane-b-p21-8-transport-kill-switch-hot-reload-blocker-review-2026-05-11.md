# Lane B P21.8 Transport Kill-Switch Hot-Reload Blocker Review

Date: 2026-05-11
Status: docs-only review completed
Scope: backend-only source review of the transport kill-switch hot-reload blocker; no source, frontend, or test changes

## 1. Current Completion Status

Current repo state at review start:

1. branch was `main`
2. working tree was clean
3. `32b7879` was the local `main` HEAD
4. `b7467b2` was present on local `main`
5. P20 backend-only real HTTP transport was already completed
6. P21.1 through P21.4 backend config activation was already completed
7. P21.5 Windows fake-endpoint smoke was already recorded as pass with caveat
8. P21.6 and P21.7 config persistence plus file-backed loading hardening were already completed and landed on `main`

This round did not:

1. modify `src/`
2. modify `console/src/`
3. modify `tests/`
4. connect any real external provider
5. change Ask schema
6. add any frontend provider selector
7. connect `ProviderManager.active_model`
8. connect `SimpleModelRouter`
9. perform production rollout

## 2. P21.5 Caveat Summary

The carry-forward caveat from the Windows operator smoke remained:

1. after persisting `transport_enabled=false` through `PUT /api/agents/default/game/project/config`, the next immediate RAG answer could still hit the fake endpoint once
2. after a full app restart, the same kill switch prevented further fake-endpoint traffic
3. this means cold-start file-backed loading worked, but hot-reload suppression was not yet reliable enough for rollout

Practical status:

1. this is still not production ready
2. this is still not production rollout

## 3. Reviewed Source Surface

This review read the following code paths:

1. `src/ltclaw_gy_x/app/routers/game_project.py`
2. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
3. `src/ltclaw_gy_x/game/service.py`
4. `src/ltclaw_gy_x/game/config.py`
5. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
6. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
7. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
8. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
9. `src/ltclaw_gy_x/cli/app_cmd.py`

## 4. Source Review Findings

### 4.1 Save path does await reload

`PUT /game/project/config` in `game_project.py`:

1. validates and saves the typed `ProjectConfig`
2. updates `user_config.svn_local_root` when needed
3. explicitly awaits `game_service.reload_config()` before returning success

Conclusion:

1. the route already intends to complete the in-process reload before the `PUT` response returns
2. P21.9 should not be framed as “add missing await to reload” because that await already exists

### 4.2 `reload_config()` does replace live project config

`GameService.reload_config()` in `service.py`:

1. clears `_project_config` and related runtime components
2. reloads `_user_config`
3. reloads `_project_config` from file-backed `project_config.yaml`
4. rebuilds runtime components
5. optionally restarts the watcher

Conclusion:

1. reload does replace the live in-memory `_project_config`
2. the project-config reference is not permanently stale after a successful reload

### 4.3 `GameService.config` stays live

`GameService.config` is only:

1. `return self.project_config`
2. `project_config` is only `return self._project_config`

Conclusion:

1. code reading `game_service.config` reaches the current `_project_config`
2. there is no separate config snapshot object in this property chain

### 4.4 Answer path reads service config on demand

`POST /game/knowledge/rag/answer` in `game_knowledge_rag.py`:

1. resolves the live `game_service` from workspace
2. builds grounded context
3. calls `build_rag_answer_with_service_config(..., game_service)`

`build_rag_answer_with_service_config()` in `knowledge_rag_answer.py` then:

1. resolves provider name from the passed `game_service`
2. resolves external client config from the passed `game_service`
3. constructs a model client for that call through `get_rag_model_client(...)`

Conclusion:

1. the answer path is not wired to a pre-captured project config snapshot
2. in the normal no-race case, each answer request should consult current service state

### 4.5 No provider-config cache was found

`resolve_external_rag_model_client_config(...)` in `knowledge_rag_provider_selection.py`:

1. recursively walks the passed object
2. checks `external_provider_config`
3. checks nested `service_config`, `app_config`, and `config`
4. coerces a fresh `ExternalRagModelClientConfig`

Conclusion:

1. no cache or memoized provider-config result was found here
2. no stale external-config singleton was found here

### 4.6 No model-client cache was found

`get_rag_model_client(...)` in `knowledge_rag_model_registry.py`:

1. builds a factory map per call
2. instantiates the requested client per call
3. returns a fresh `ResolvedRagModelClient`

`ExternalRagModelClient` in `knowledge_rag_external_model_client.py`:

1. stores config on the instance
2. does not register itself in any shared registry
3. does not expose cross-request reuse in the reviewed path

Conclusion:

1. no cross-request external client cache was found in the reviewed path
2. no hot-reload blocker was found in client reuse or client registry state

### 4.7 This is not a multi-worker propagation issue

`cli/app_cmd.py` calls `uvicorn.run(..., workers=1)`.

Conclusion:

1. this is not a case where one worker handled the save while another worker still served the answer with old state
2. full restart success is not explained by worker fan-out

## 5. Most Likely Root Cause

The most likely blocker is a request-ordering and in-process concurrency window, not config persistence and not provider/client caching.

Most likely sequence:

1. one request persists kill-switch changes and begins `reload_config()`
2. another RAG answer request can still enter the answer path before the new kill-switch state is the only admissible state for that service instance
3. because there is no reload lock, config generation token, or request barrier shared between `PUT /game/project/config` and `POST /game/knowledge/rag/answer`, the hot path has no explicit coordination point proving it must observe the post-save generation before transport selection
4. once the process is fully restarted, all requests necessarily start from the file-backed disabled state, so the fake endpoint is no longer reachable

Why this fits the evidence better than other explanations:

1. file-backed cold-start behavior already proves the persisted config is correct
2. the reviewed code does not show a provider-config cache or external-client cache that would survive restart only
3. the reviewed app runs with one worker, so the stale hit is more consistent with an in-process timing gap than cross-worker divergence

## 6. Causes Considered And Rejected

The review rejected these as the primary root cause for P21.5's caveat:

1. save route forgot to await reload
2. `reload_config()` forgot to replace `_project_config`
3. `GameService.config` returns a separate stale snapshot
4. `game_knowledge_rag.py` binds to a frozen project config instead of the live service
5. `resolve_external_rag_model_client_config(...)` caches external config across requests
6. `get_rag_model_client(...)` caches provider clients across requests
7. `ExternalRagModelClient` is reused across requests in the reviewed answer path
8. multiple uvicorn workers kept divergent in-memory state

These remain possible but lower-confidence secondary explanations without stronger evidence:

1. an operator smoke step may have issued the answer request before the save request had truly completed end-to-end
2. an already-started answer request may have crossed the selection point before the kill switch update became visible

Those two cases still point to the same architectural gap: there is no explicit reload barrier around transport-sensitive answer selection.

## 7. Recommended P21.9 Minimal Fix

Recommended direction: add a small in-process config generation barrier between project-config reload and external-transport answer selection.

Why this is the minimal and lowest-risk fit:

1. it directly addresses the only unguarded boundary still consistent with the reviewed code
2. it does not require changing Ask schema
3. it does not require any frontend change
4. it does not require connecting `ProviderManager` or `SimpleModelRouter`
5. it preserves the current backend-owned provider-selection architecture
6. it keeps the fix local to the backend runtime state boundary instead of widening the surface area

Recommended minimal shape for P21.9:

1. add a reload generation counter or equivalent monotonic version on `GameService`
2. advance that generation only after reload completes successfully
3. ensure the answer path resolves external transport only against the current completed generation
4. if a request started against an older generation and external transport would otherwise be used, force a re-read or fail closed to the disabled path rather than sending HTTP with stale selection state

Practical design intent:

1. after saving `transport_enabled=false`, the next answer request should either see the disabled generation or fail closed
2. it should not be able to continue using the pre-save transport-enabled state once the save route has returned success

## 8. Not Recommended For P21.9

These options are not recommended as the primary P21.9 fix:

1. only “ensure reload completes before save returns”
   - the current save route already awaits `reload_config()`
2. only “make answer path read `game_service.project_config` every time”
   - the reviewed path already effectively does this through `game_service`
3. add an explicit reload endpoint and require operators to call it manually
   - that adds operational complexity while the current save route already performs reload
4. document that kill switch requires restart
   - that would formalize an open blocker instead of fixing it and would not match the intended hot-reload architecture

## 9. P21.9 Required Test Points

P21.9 must verify all of the following without app restart:

1. after saving `transport_enabled=false`, ordinary RAG answer no longer calls the fake endpoint
2. after saving `enabled=false`, ordinary RAG answer no longer calls the fake endpoint
3. after clearing `allowed_models`, ordinary RAG answer no longer calls the fake endpoint
4. request body `provider`, `model`, and `api_key` still do not participate in provider selection
5. Ask schema remains unchanged
6. frontend remains unchanged
7. `ProviderManager` and `SimpleModelRouter` remain outside the ordinary RAG provider path
8. ordinary RAG Q&A still does not write release, formal map, test plan, or workbench draft artifacts

## 10. Final Assessment

P21.8 review conclusion:

1. the reviewed code does not support a root-cause claim of stale persisted config, stale `GameService.config`, provider-config caching, model-client caching, or multi-worker divergence
2. the most likely remaining blocker is missing in-process synchronization between config reload completion and transport-sensitive answer selection
3. the smallest architecture-aligned P21.9 fix is a backend-only reload generation barrier that makes the kill switch fail closed on hot reload
4. this remains not production ready
5. this remains not production rollout
