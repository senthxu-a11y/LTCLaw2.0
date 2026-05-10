# Lane B P21.7 Windows File-Backed Config Loading Closeout

Date: 2026-05-10
Status: completed validation and regression hardening

## Scope

This round stayed within the Windows test-machine boundary and did not continue fake-endpoint transport smoke.

What this round did:

1. re-checked the Windows environment on the test machine
2. re-checked that commit `bf94e8d` contains the P21.6 typed backend-owned `external_provider_config` persistence surface
3. re-read the P21.5 runbook, P21.6 closeout, and the current `config.py`, `service.py`, `game_project.py`, and RAG bridge code
4. revalidated project config API persistence and secret stripping on Windows
5. revalidated current file-backed `project_config.yaml` loading on Windows
6. added regression coverage for serialization safety, file-backed service loading, and route health under file-backed `external_provider_config`

What this round did not do:

1. it did not connect to any real external provider or any real external network
2. it did not write any real API key value
3. it did not change Ask schema
4. it did not change frontend
5. it did not connect `ProviderManager.active_model`
6. it did not connect `SimpleModelRouter`
7. it did not continue P21.5 fake-endpoint smoke past file-backed loading validation

## Environment

1. Windows version: `Microsoft Windows NT 10.0.26200.0`
2. branch: `main`
3. commit: `bf94e8d`
4. Python: `3.12.3`
5. Node: `v24.15.0`
6. npm: `11.12.1`
7. Windows local project directory: `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
8. app-owned project config path: `C:\ltclaw-data-backed\game_data\projects\中小型游戏设计框架-25f012e7d33d\project\config\project_config.yaml`
9. current release id during runtime validation: `win-op-r1-1778393517`

## Historical Blocker

The carry-forward P21.5 and P21.6 blocker was:

1. project config API persistence had already been fixed by P21.6
2. but the Windows operator retest previously reported `HTTP 502` after restart on:
   - `GET /api/agents/default/game/project/config`
   - `GET /api/agents/default/game/knowledge/releases/status`

This P21.7 round was tasked with confirming whether that remaining blocker was a real file-backed loading, serialization, or route-response bug in the current repo.

## Root-Cause Review Result

No current code-level file-backed loading exception was reproduced on `bf94e8d`.

What current evidence showed:

1. `ProjectConfig.external_provider_config` is already a typed backend-owned model with `extra="ignore"`
2. request-owned `api_key` fields are stripped during model validation and do not survive dump or readback
3. the current Windows app-owned `project_config.yaml` containing `external_provider_config` loaded successfully in the running app
4. current Windows runtime returned `200` for both project config and release status with file-backed `external_provider_config` present
5. no traceback or redacted exception identifying a current `config.py`, `service.py`, or `game_project.py` failure was emitted in this round

Practical conclusion:

1. the earlier Windows `502` could not be confirmed as a current repo code defect
2. the current repo state falsifies the hypothesis that `bf94e8d` still has a persistent file-backed loading or serialization bug in the reviewed path
3. the historical `502` summary remains a prior operator observation, but it was not reproducible from the current Windows machine state during this round

## Actual Modified Files

1. `tests/unit/game/test_config.py`
2. `tests/unit/game/test_service.py`
3. `tests/unit/routers/test_game_project_router.py`
4. `docs/tasks/post-mvp/lane-b-p21-7-windows-file-backed-config-loading-closeout-2026-05-10.md`

No source files under `src/` were changed in this round.

## Regression Hardening

### 1. Serialization coverage

Added coverage that a typed backend-owned `external_provider_config`:

1. dumps to a JSON-safe dict
2. preserves backend-owned fields such as `provider_name`, `model_name`, `base_url`, and `env.api_key_env_var`
3. strips request-owned `api_key` fields from both the top-level external config and nested env config

### 2. File-backed service loading coverage

Strengthened file-backed `GameService.reload_config()` coverage so the saved YAML now includes:

1. `enabled`
2. `transport_enabled`
3. `provider_name`
4. `model_name`
5. `base_url`
6. limits fields
7. a request-owned `api_key` field that must be ignored

The regression asserts that reload succeeds and the loaded typed config still exposes:

1. `enabled=True`
2. `transport_enabled=True`
3. `provider_name="future_external"`
4. `model_name="backend-model"`
5. `base_url="http://127.0.0.1:8765/v1/chat/completions"`
6. `env.api_key_env_var="QWENPAW_RAG_API_KEY"`
7. no persisted `api_key` attribute

### 3. Route health coverage

Added coverage that when a file-backed `project_config.yaml` contains backend-owned `external_provider_config`:

1. `GET /api/game/project/config` returns `200`
2. the response contains the typed backend-owned config
3. the response does not include request-owned `api_key` fields
4. `GET /api/game/knowledge/releases/status` returns `200`

## Runtime Validation Result

Windows runtime validation passed for the file-backed loading slice.

Observed result on the current machine state:

1. the app-owned `project_config.yaml` currently contains backend-owned `external_provider_config`
2. `GET /api/agents/default/game/project/config` returned `200`
3. `GET /api/agents/default/game/knowledge/releases/status` returned `200`
4. `external_provider_config` read back as non-null
5. the readback preserved:
   - `enabled=true`
   - `transport_enabled=true`
   - `provider_name=future_external`
   - `model_name=backend-model`
   - `base_url=http://127.0.0.1:8765/v1/chat/completions`
   - `env.api_key_env_var=QWENPAW_RAG_API_KEY`

## Persistence Boundary Result

P21.6 persistence behavior remains intact.

Observed result:

1. `PUT /api/agents/default/game/project/config` still preserves `external_provider_config`
2. immediate `GET` still returns the backend-owned config instead of `null`
3. request-owned `api_key` does not echo back
4. `REQUEST_SECRET_SHOULD_BE_STRIPPED` does not echo back
5. `TEST_PLACEHOLDER_SECRET_DO_NOT_COMMIT` does not echo back

## Boundaries Preserved

1. Ask schema was not changed
2. frontend was not changed
3. no frontend provider selector was added
4. `ProviderManager.active_model` was not connected to the RAG path
5. `SimpleModelRouter` was not connected to the RAG path
6. no real external provider was connected
7. no real external network was called
8. ordinary RAG Q&A remains no-write in this round
9. this is not production ready and not production rollout

## Test Result

Requested pytest command:

`python -m pytest tests/unit/routers/test_game_project_router.py tests/unit/game/test_service.py tests/unit/game/test_config.py tests/unit/game/test_knowledge_rag_provider_selection.py -q`

Result on this Windows machine:

1. blocked for executable pytest validation because the configured venv does not have `pytest` installed
2. actual error: `No module named pytest`

Static validation result for edited test files:

1. no editor diagnostics were reported in the edited test files

## Final Assessment

P21.7 target outcome is satisfied for the current repo state.

What is now true:

1. current Windows file-backed loading with backend-owned `external_provider_config` is working in the reviewed runtime path
2. current Windows `GET /game/project/config` is `200`
3. current Windows `GET /game/knowledge/releases/status` is `200`
4. P21.6 API persistence and secret stripping remain intact
5. no source fix was required in `src/` for the currently reproducible path

Residual limit:

1. executable pytest confirmation could not be completed on this machine because `pytest` is missing from the venv
2. the earlier historical `502` could not be reproduced into a current traceback, so no new source-level exception site was available to patch

## Next Step

1. re-run P21.5 Windows fake-endpoint smoke on this machine
2. keep the same backend-owned config shape and the same local-only fake endpoint boundary
3. treat this as a follow-up validation only, not production rollout