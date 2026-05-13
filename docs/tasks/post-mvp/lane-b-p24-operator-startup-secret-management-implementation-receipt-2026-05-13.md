# Lane B P24 Operator Startup And Secret Management Implementation Receipt

Date: 2026-05-13
Status: current working-tree implementation verified locally
Scope: backend/CLI/script only; no frontend key UI, no ordinary user provider selector, no Ask schema expansion

## 1. Implemented

P24 now has a concrete operator-only CLI surface:

1. `ltclaw operator rag-secret-check`
2. `ltclaw operator deepseek-config-template`
3. `ltclaw operator deepseek-preflight`

The CLI is registered through the lazy command loader in `src/ltclaw_gy_x/cli/main.py`.

## 2. Secret Handling

`rag-secret-check` reads `LTCLAW_RAG_API_KEY` from the current process environment and prints booleans only:

1. `exists`
2. `length_gt_20`
3. `starts_with_sk`
4. `header_starts_with_bearer_sk`
5. `header_length_gt_env_length`

It does not print the secret value, the bearer header, a prefix sample, or a suffix sample.

## 3. Provider Config Template

`deepseek-config-template` emits the backend-owned controlled-pilot config shape:

1. `enabled=true`
2. `transport_enabled=true`
3. `provider_name=future_external`
4. `model_name=deepseek-chat`
5. `allowed_providers=["future_external"]`
6. `allowed_models=["deepseek-chat"]`
7. `base_url=https://api.deepseek.com/chat/completions`
8. `env.api_key_env_var=LTCLAW_RAG_API_KEY`

The template contains only the env var name, not the secret value.

## 4. Startup Script

Added `scripts/operator_deepseek_pilot.ps1` for Windows operator startup.

The script:

1. keeps the key in the current PowerShell process environment
2. prompts with `Read-Host -AsSecureString` when `LTCLAW_RAG_API_KEY` is not already set
3. sets `QWENPAW_WORKING_DIR`
4. sets `QWENPAW_CONSOLE_STATIC_DIR`
5. runs secret shape check
6. runs DeepSeek preflight
7. prints the provider config template
8. starts `ltclaw app`

The script was reviewed for secret handling but was not fully executed in this validation pass because it prompts for a secret and starts a long-running app process.

## 5. Tests Added

Added focused unit coverage in `tests/unit/cli/test_operator_cmd.py` for:

1. secret-shape report contains booleans only
2. CLI secret check does not echo a real-looking secret value
3. missing secret can fail closed with `--fail-on-missing`
4. DeepSeek config template contains only `LTCLAW_RAG_API_KEY`
5. preflight report does not include secret values

## 6. Validation

Local validation performed:

1. `.venv\Scripts\python.exe -m ltclaw_gy_x operator --help` succeeded after registering the lazy `operator` command
2. `.venv\Scripts\python.exe -m ltclaw_gy_x operator rag-secret-check` printed boolean-only output and did not print any secret value
3. `.venv\Scripts\python.exe -m ltclaw_gy_x operator deepseek-config-template` printed only backend-owned config plus `LTCLAW_RAG_API_KEY`
4. `.venv\Scripts\python.exe -m ltclaw_gy_x operator deepseek-preflight` printed secret/path readiness booleans plus provider metadata without any secret value
5. `.venv\Scripts\ltclaw.exe operator --help` succeeded, confirming the installed CLI entrypoint can load the new command group
6. `.venv\Scripts\python.exe -m pytest tests\unit\cli\test_operator_cmd.py` passed with `5 passed`

Observed default-output notes from the local validation environment:

1. `rag-secret-check` returned `exists=false`, `length_gt_20=false`, and `starts_with_sk=false` when `LTCLAW_RAG_API_KEY` was unset
2. `deepseek-preflight` returned `set=false` and `exists=false` for `QWENPAW_WORKING_DIR` and `QWENPAW_CONSOLE_STATIC_DIR` when those env vars were unset
3. these default local results were expected for a shell without pilot env setup and did not expose any secret material

## 7. Boundary

This is still controlled-pilot tooling. It does not claim production rollout readiness and does not add:

1. API key UI
2. frontend provider selector
3. multi-provider routing
4. Ask request provider/model/key fields
5. release writes from RAG
6. formal map writes from RAG
7. workbench draft writes from RAG
