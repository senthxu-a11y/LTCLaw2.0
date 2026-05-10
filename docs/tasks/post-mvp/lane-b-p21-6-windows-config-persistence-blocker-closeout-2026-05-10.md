# Lane B P21.6 Windows Config Persistence Blocker Closeout

Date: 2026-05-10
Status: completed blocker review and minimal fix.

## Windows P21.5 Blocked Symptoms

Windows P21.5 fake-endpoint operator smoke was reported blocked with these observed symptoms:

1. After saving backend-owned external_provider_config through the project config API, GET /api/agents/default/game/project/config read back null.
2. After switching to app-owned file-backed project_config.yaml injection, related LTCLaw endpoints returned HTTP 502.
3. The fake endpoint still did not receive the expected request, so Windows operator smoke could not prove backend-owned config activation through the operator path.

## Input Note

1. The requested Windows receipt file was not present in the current Mac development workspace at review time.
2. This closeout therefore uses the blocked symptoms provided by the operator report as the review input.

## Real Code Cause Located In This Round

The narrow review did not reproduce a hard backend drop of external_provider_config in the current project config API route.

What the review confirmed:

1. ProjectConfig already declared external_provider_config.
2. ProjectConfig YAML save and load already preserved the field in the recommended backend-owned shape.
3. The game_project router already accepted ProjectConfig directly for PUT and returned ProjectConfig directly for GET.
4. A local in-memory PUT then GET round-trip preserved external_provider_config.

The real persistence risk found in code was narrower and still worth fixing:

1. ProjectConfig.external_provider_config was typed as a raw dict[str, Any] rather than a constrained backend-owned config model.
2. That raw dict contract allowed unknown nested request-owned fields to pass through persistence unchecked.
3. The project config API had no dedicated regression coverage for external_provider_config persistence, readback, and file-backed reload.
4. Because of that gap, the Windows operator path had no protected contract ensuring backend-owned shape stability or secret-value stripping through API persistence.

Root-cause summary for the landed fix:

1. The persistence surface was under-specified and under-tested, not explicitly hardened for the backend-owned external_provider_config contract.
2. The minimum corrective action was to make external_provider_config a typed backend-owned project-config model and add router plus file-backed regression coverage.

## Actual Changed Files

1. src/ltclaw_gy_x/game/config.py
2. tests/unit/routers/test_game_project_router.py
3. tests/unit/game/test_service.py
4. tests/unit/game/test_knowledge_rag_provider_selection.py
5. docs/tasks/post-mvp/lane-b-p21-6-windows-config-persistence-blocker-closeout-2026-05-10.md

## What Changed

### 1. Project config persistence model hardening

1. external_provider_config is now persisted through a typed backend-owned project-config model instead of a raw dict[str, Any].
2. env is now persisted through a typed nested model that keeps only api_key_env_var.
3. Unknown fields are ignored rather than stored.
4. request-owned api_key-like fields are therefore not persisted into project config.

### 2. Project config API persistence coverage

1. Added a router regression that PUTs a project config containing external_provider_config.
2. The regression GETs the saved config back and verifies external_provider_config is still present.
3. The regression verifies api_key-like fields are not returned.
4. The regression verifies api_key-like fields are not written into the saved YAML file.

### 3. File-backed config loading coverage

1. Added a GameService reload_config regression using a saved project_config.yaml containing external_provider_config.
2. The regression verifies reload_config does not raise.
3. The regression verifies provider_name remains future_external.
4. The regression verifies env.api_key_env_var remains QWENPAW_RAG_API_KEY.

### 4. Provider-selection bridge coverage

1. Extended the existing provider-selection bridge regression.
2. The regression now verifies enabled, transport_enabled, provider_name, model_name, base_url, allowed_models, and env.api_key_env_var.

## Project Config API Result

After the landed fix and new regression coverage:

1. project config API can save external_provider_config.
2. GET /game/project/config can read the field back.
3. The persisted response shape includes backend-owned fields such as enabled, transport_enabled, provider_name, model_name, base_url, limits, and env.api_key_env_var.
4. request-owned api_key-like fields are not persisted or read back.

## File-Backed Config Result

After the landed fix and new regression coverage:

1. file-backed project_config.yaml with backend-owned external_provider_config loads successfully.
2. GameService.reload_config can load that config without exception in the tested path.
3. provider_name remains future_external.
4. env.api_key_env_var remains QWENPAW_RAG_API_KEY.

## Provider Selection Bridge Result

1. resolve_external_rag_model_client_config(game_service) continues to read from game_service.config.external_provider_config.
2. The parsed result now remains verified for enabled, transport_enabled, provider_name, model_name, base_url, allowed_models, and env.api_key_env_var.

## Secret Storage Boundary Result

1. Project config still stores only the env var name.
2. Project config still does not store a real API key value.
3. Added regression coverage that api_key-like request fields are not written into project config YAML.

## Boundaries Preserved

1. Ask schema was not changed.
2. Frontend was not changed.
3. ProviderManager.active_model was not connected to the RAG path.
4. SimpleModelRouter was not connected to the RAG path.
5. No real external provider was connected.
6. No real external network was called.
7. Ordinary RAG Q&A remains no-write.
8. Current state remains backend-only, not production rollout, and not production ready.

## Test Results

Executed validation:

1. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/routers/test_game_project_router.py tests/unit/game/test_service.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/routers/test_game_knowledge_rag_router.py -q -> 94 passed in 1.66s
2. /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest tests/unit/game/test_config.py -q -> 10 passed in 0.03s

## Next Step

1. Re-run P21.5 Windows fake-endpoint operator smoke with the current code.
2. Confirm the Windows operator path now persists and reads back external_provider_config through the project config API.
3. Confirm the Windows fake endpoint receives the request after backend-owned config activation.
4. This next step is still not production rollout.