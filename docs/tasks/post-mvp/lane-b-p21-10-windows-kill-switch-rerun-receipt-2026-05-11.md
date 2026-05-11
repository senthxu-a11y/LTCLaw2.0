# Lane B P21.10 Windows Kill-Switch Rerun Receipt

Date: 2026-05-11
Status: passed
Scope: Windows test-machine rerun of the local-only fake-endpoint kill-switch smoke after P21.9 hot-reload fix; no real external provider connectivity and no source, frontend, or test edits

## 1. Preconditions

All requested preconditions were satisfied before the rerun:

1. execution happened on Windows test machine `Microsoft Windows NT 10.0.26200.0`
2. repository branch was `main`
3. `git pull origin main` returned up to date
4. current commit hash was `9db0c66c6755d65d2519ae7f1dfa851db6ba961f`
5. `git status --short --branch` was clean
6. no repo changes were made outside this receipt
7. no real external provider or real external network was used
8. only local fake endpoint `127.0.0.1:8765` was used for transport validation

## 2. Runtime Setup

The rerun used the validated Windows startup path from the prior operator receipt.

App command:

```powershell
$env:QWENPAW_WORKING_DIR = 'C:\ltclaw-data-backed'
$env:QWENPAW_CONSOLE_STATIC_DIR = 'E:\LTclaw2.0\console\dist'
$env:QWENPAW_RAG_API_KEY = '<placeholder only>'
E:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092
```

Local fake endpoint:

1. listener address: `127.0.0.1:8765`
2. route: `POST /v1/chat/completions`
3. stats route: `GET /stats`
4. captured fields per request:
   - cumulative `request_count`
   - whether `Authorization` header was present
   - `body.model`
   - whether request body contained `api_key`
   - whether request body contained `provider` or `provider_name`
   - request body keys

Placeholder-only environment rule preserved:

1. no real API key value was used
2. only `QWENPAW_RAG_API_KEY=<placeholder only>` was set for the smoke app process
3. persisted config stored only `env.api_key_env_var = QWENPAW_RAG_API_KEY`

## 3. Baseline Result

Baseline checks passed before any operator-only config write:

1. `GET /api/agent/health` returned `200`
2. `GET /api/agents/default/game/project/config` returned `200`
3. `GET /api/agents/default/game/knowledge/releases/status` returned `200`
4. current release existed as `win-op-r1-1778393517`
5. local project directory existed at `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
6. project data directory remained `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d`
7. baseline `external_provider_config` was `null`

## 4. Backend-Owned Config Saved

The rerun saved backend-owned `external_provider_config` through `PUT /api/agents/default/game/project/config` with this operator-only shape:

```json
{
  "external_provider_config": {
    "enabled": true,
    "transport_enabled": true,
    "provider_name": "future_external",
    "model_name": "backend-model",
    "allowed_providers": ["future_external"],
    "allowed_models": ["backend-model"],
    "base_url": "http://127.0.0.1:8765/v1/chat/completions",
    "env": {"api_key_env_var": "QWENPAW_RAG_API_KEY"}
  }
}
```

Immediate readback result:

1. `GET /api/agents/default/game/project/config` returned `200`
2. `external_provider_config` remained non-null
3. readback preserved:
   - `enabled=true`
   - `transport_enabled=true`
   - `provider_name=future_external`
   - `model_name=backend-model`
   - `allowed_providers=["future_external"]`
   - `allowed_models=["backend-model"]`
   - `base_url=http://127.0.0.1:8765/v1/chat/completions`
   - `env.api_key_env_var=QWENPAW_RAG_API_KEY`
4. readback did not echo any `api_key` value

## 5. Positive RAG Answer Result

The positive request reused the ordinary answer path and intentionally included request-owned negative-test fields:

```json
{
  "query": "What does DaShenScore contain in the current release?",
  "max_chunks": 8,
  "max_chars": 12000,
  "provider": "request-provider",
  "model": "request-model",
  "api_key": "<request-owned negative-test field>"
}
```

Observed result:

1. `POST /api/agents/default/game/knowledge/rag/answer` returned `200`
2. response returned `mode="answer"`
3. response answer was `Windows operator smoke grounded answer`
4. response citations included `citation-001`
5. fake endpoint `request_count` increased from `0` to `1`
6. fake endpoint logged `Authorization` present
7. fake endpoint logged `body.model = backend-model`
8. fake endpoint body keys were only `messages` and `model`
9. fake endpoint body did not contain `api_key`
10. fake endpoint body did not contain `provider` or `provider_name`

Boundary conclusion:

1. request-owned `provider` was ignored
2. request-owned `model` was ignored in favor of backend-owned `backend-model`
3. request-owned `api_key` was ignored

## 6. transport_enabled=false Immediate Hot-Reload Result

The rerun then persisted `transport_enabled=false` without restarting LTCLaw.

Observed result:

1. `PUT /api/agents/default/game/project/config` returned `200`
2. immediate `GET /api/agents/default/game/project/config` returned `transport_enabled=false`
3. the next immediate answer request returned `200`
4. response returned `mode="insufficient_context"`
5. response warnings included `External provider adapter skeleton transport is not connected.`
6. fake endpoint `request_count` remained `1`
7. fake endpoint received no additional HTTP request

Conclusion:

1. the P21.5 restart-only caveat no longer reproduced in this Windows rerun
2. saving `transport_enabled=false` immediately blocked the next ordinary RAG answer from reaching transport

## 7. enabled=false Result

To isolate the disabled branch, the rerun persisted:

1. `enabled=false`
2. `transport_enabled=true`
3. `allowed_models=["backend-model"]`

Observed result:

1. immediate `GET /api/agents/default/game/project/config` returned `enabled=false`
2. the next answer request returned `200`
3. response returned `mode="insufficient_context"`
4. response warnings included `External provider adapter skeleton is disabled.`
5. fake endpoint `request_count` remained `1`

Conclusion:

1. the disabled branch failed closed
2. no fake-endpoint traffic was emitted when `enabled=false`

## 8. allowed_models=[] Result

To isolate the allowlist branch, the rerun persisted:

1. `enabled=true`
2. `transport_enabled=true`
3. `allowed_models=[]`

Observed result:

1. immediate `GET /api/agents/default/game/project/config` returned `allowed_models=[]`
2. the next answer request returned `200`
3. response returned `mode="insufficient_context"`
4. response warnings included `External provider adapter skeleton model is not allowed.`
5. fake endpoint `request_count` remained `1`

Conclusion:

1. empty model allowlist failed closed
2. no fake-endpoint traffic was emitted when `allowed_models=[]`

## 9. Cleanup

Cleanup completed successfully:

1. operator-only `external_provider_config` was set back to `null`
2. fake endpoint process was stopped
3. smoke app process was stopped
4. baseline LTCLaw app was restarted without `QWENPAW_RAG_API_KEY`
5. post-cleanup `GET /api/agent/health` returned `200`
6. post-cleanup `GET /api/agents/default/game/project/config` returned `200`
7. post-cleanup `GET /api/agents/default/game/knowledge/releases/status` returned `200`
8. post-cleanup `external_provider_config` read back as `null`
9. current release still existed after cleanup

## 10. Boundaries Preserved

This rerun did not do any of the following:

1. production rollout
2. claim production ready status
3. Ask schema expansion
4. frontend provider selector work
5. `ProviderManager.active_model` integration
6. `SimpleModelRouter` integration
7. ordinary RAG writes
8. default-to-formal-knowledge test-plan behavior changes
9. any real external provider connection
10. any source, frontend, or test file modification

## 11. Final Result

Final disposition: passed

Required report values:

1. current commit hash: `9db0c66c6755d65d2519ae7f1dfa851db6ba961f`
2. fake endpoint `request_count` after positive request: `1`
3. fake endpoint `request_count` after `transport_enabled=false`: `1`
4. fake endpoint `request_count` after `enabled=false`: `1`
5. fake endpoint `request_count` after `allowed_models=[]`: `1`
6. `Authorization` header presence on positive transport request: present
7. fake endpoint model: `backend-model`
8. request-owned `provider`, `model`, and `api_key` were ignored at the fake boundary
9. cleanup restored baseline successfully

This rerun confirms that the next immediate Windows RAG answer no longer reaches the fake endpoint after saving `transport_enabled=false`.
