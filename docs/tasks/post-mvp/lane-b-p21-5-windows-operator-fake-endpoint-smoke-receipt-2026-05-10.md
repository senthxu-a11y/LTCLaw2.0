# Lane B P21.5 Windows Operator Fake-Endpoint Smoke Receipt

Date: 2026-05-10
Status: passed with one restart-only caveat
Scope: Windows test-machine rerun of the backend-owned fake-endpoint smoke, including positive transport, request-boundary checks, and kill-switch validation

## 1. Scope Result

This rerun executed on the Windows test machine and stayed within the requested local-only boundary.

What this rerun did:

1. confirmed the execution environment was Windows
2. reused the existing backend-owned `external_provider_config` API surface only
3. started a local fake endpoint on `127.0.0.1:8765`
4. set a placeholder-only environment variable for the operator smoke
5. restarted LTCLaw with the validated Windows app startup path
6. saved backend-owned `external_provider_config` through `PUT /api/agents/default/game/project/config`
7. verified immediate `GET /api/agents/default/game/project/config` preserved the field and stripped the request-owned `api_key`
8. executed a positive RAG answer call and confirmed the request hit the local fake endpoint
9. executed a negative request-boundary call with request-owned `provider`, `model`, and `api_key`
10. validated the kill switch by persisting `transport_enabled=false`, then rechecking behavior after a full app restart
11. cleaned up the operator-only config injection, fake endpoint, and placeholder env state

What this rerun did not do:

1. it did not connect to any real external provider or real external network
2. it did not write any real API key value
3. it did not modify `src`, `console/src`, or `tests` for this smoke rerun
4. it did not change Ask schema
5. it did not change frontend provider UI
6. it did not connect `ProviderManager.active_model`
7. it did not connect `SimpleModelRouter`
8. it did not perform production rollout

## 2. Environment Facts

1. Windows version: `Microsoft Windows NT 10.0.26200.0`
2. git branch: `main`
3. commit hash: `bf94e8d`
4. Python version: `3.12.3`
5. Node version: `v24.15.0`
6. npm version: `11.12.1`
7. app startup command used in the rerun:
   - `$env:QWENPAW_RAG_API_KEY = '<placeholder only>'`
   - `$env:QWENPAW_WORKING_DIR = 'C:\ltclaw-data-backed'`
   - `$env:QWENPAW_CONSOLE_STATIC_DIR = 'E:\LTclaw2.0\console\dist'`
   - `E:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092`
8. Windows local project directory: `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
9. app-owned project config path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\project\config\project_config.yaml`
10. release id exercised in the rerun: `win-op-r1-1778393517`

## 3. Backend-Owned Config Shape Used

The rerun used this backend-owned config shape through the project config API:

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
    "timeout_seconds": 15.0,
    "max_output_tokens": 256,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {"api_key_env_var": "QWENPAW_RAG_API_KEY"},
    "api_key": "<request-owned negative-test field>"
  }
}
```

Boundary rule preserved:

1. only the env var name was intended to persist in config
2. the request-owned `api_key` field was a negative test field and did not persist
3. no real secret value was written into config

## 4. Project Config Persistence Result

This part passed.

Observed result:

1. `PUT /api/agents/default/game/project/config` succeeded
2. immediate `GET /api/agents/default/game/project/config` returned `external_provider_config` as non-null
3. the returned shape preserved:
   - `provider_name = future_external`
   - `model_name = backend-model`
   - `base_url = http://127.0.0.1:8765/v1/chat/completions`
   - `env.api_key_env_var = QWENPAW_RAG_API_KEY`
4. the immediate `GET` did not echo the request-owned negative-test `api_key` field
5. the immediate `GET` did not echo the placeholder secret
6. the immediate `GET` response did not include a persisted request-owned `api_key` field

## 5. Fake Endpoint Positive Path Result

Local fake endpoint details:

1. listener address: `127.0.0.1:8765`
2. route: `POST /v1/chat/completions`
3. response body: fixed fake payload with `answer="Windows operator smoke grounded answer"`, `citation_ids=["citation-001"]`, `warnings=[]`
4. capture policy: log only redacted request summaries

Observed positive-path result:

1. the positive RAG answer call returned `mode="answer"`
2. the returned answer was `Windows operator smoke grounded answer`
3. the returned citations included `citation-001`
4. the returned warnings array was empty
5. the fake endpoint received the request at `/v1/chat/completions`
6. the fake endpoint logged `authorization="present"`
7. the fake endpoint logged `model="backend-model"`

## 6. Negative Request Boundary Result

This part passed.

The negative request body intentionally added request-owned fields:

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

Observed result at the fake boundary:

1. the fake endpoint still logged `model="backend-model"`
2. the fake endpoint logged `has_api_key=false`
3. the fake endpoint logged `has_provider_name=false`
4. the fake endpoint logged `has_request_owned_model=false`
5. the response still returned the fixed fake grounded answer

Conclusion:

1. request-owned `provider` did not cross the boundary
2. request-owned `model` did not override the backend-owned model
3. request-owned `api_key` did not cross the boundary

## 7. Kill Switch Result

Kill-switch validation passed, with one caveat.

Observed result:

1. after saving `transport_enabled=false` through the project config API, an immediate answer call still hit the fake endpoint once more
2. that extra hot-reload call was captured as request count `3`
3. after a full LTCLaw restart, `GET /api/agent/health`, `GET /api/agents/default/game/project/config`, and `GET /api/agents/default/game/knowledge/releases/status` all returned `200`
4. after that restart, the same answer request returned:
   - `mode="insufficient_context"`
   - empty `answer`
   - empty `citations`
   - warnings including `External provider adapter skeleton transport is not connected.`
5. the fake endpoint request count stayed at `3` after the post-restart kill-switch check

Conclusion:

1. the file-backed cold-start kill switch worked on Windows
2. the immediate hot-reload path did not suppress the very next call in this rerun
3. production-readiness for live reload behavior should still treat that hot-reload caveat as open until explicitly covered elsewhere

## 8. Boundary Checks

Boundaries preserved in this rerun:

1. Ask schema was not changed
2. frontend did not gain a provider selector in this rerun
3. `ProviderManager.active_model` was not connected by this rerun
4. `SimpleModelRouter` was not connected by this rerun
5. no real secret value was written into config, docs, git, or logs
6. no real external network was called
7. no repo source, frontend, or test files were modified for this smoke rerun

Secret exposure result:

1. no real secret value was used
2. no placeholder secret value was written into the receipt
3. no placeholder secret value was observed in persisted project config readback
4. no request-owned secret value crossed to the fake endpoint

## 9. Operator Harness Note

The first listener draft used `ConvertFrom-Json -Depth`, which PowerShell 5.1 does not support.

Observed effect:

1. the first fake-endpoint capture could confirm request arrival and Authorization presence
2. the first fake-endpoint capture could not decode `body.model`

Resolution used in this rerun:

1. the local listener was restarted without `-Depth`
2. subsequent positive and negative boundary captures decoded correctly
3. no repo code change was needed for this operator-side harness fix

## 10. Cleanup

Cleanup completed:

1. the operator-only `external_provider_config` block was removed from the app-owned `project_config.yaml`
2. the fake endpoint terminal was stopped
3. the smoke app process was stopped
4. `Remove-Item Env:\QWENPAW_RAG_API_KEY -ErrorAction SilentlyContinue` was executed
5. LTCLaw was restarted back into baseline mode without the operator-only smoke config
6. baseline `GET /api/agent/health` returned `200`
7. baseline `GET /api/agents/default/game/project/config` returned `200` with `external_provider_config = null`

## 11. Final Result

Final disposition: passed with one restart-only caveat

What passed:

1. execution happened on Windows at `bf94e8d`
2. backend-owned fake-endpoint transport was hit successfully
3. fake-endpoint request capture showed `Authorization` present
4. fake-endpoint request capture showed `model=backend-model`
5. request-owned `provider`, `model`, and `api_key` did not cross the boundary
6. file-backed cold-start kill switch prevented further fake-endpoint traffic
7. cleanup restored baseline local app state

Open caveat:

1. `transport_enabled=false` did not suppress the next immediate post-PUT call until the app was fully restarted

This rerun stayed within the requested local-only operator boundary and did not touch any real external provider.
