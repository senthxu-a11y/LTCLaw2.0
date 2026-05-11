# Lane B P24 Operator Startup And Secret-Management Hardening Checklist

Date: 2026-05-11
Status: planning checklist only
Scope: standardize Windows operator startup, LTCLAW_RAG_API_KEY secret handling, provider config apply and cleanup, baseline monitoring, and troubleshooting for the controlled DeepSeek pilot line without changing source, frontend, or tests

## 1. Purpose

P24 exists to make the controlled DeepSeek pilot repeatable and reduce operator error.

The purpose of this checklist is to:

1. make the controlled DeepSeek pilot repeatable
2. reduce operator startup and cleanup mistakes
3. keep the line backend-only and operator-only
4. avoid any production rollout claim

## 2. Scope

P24 scope includes all of the following:

1. Windows operator startup
2. LTCLAW_RAG_API_KEY env-only secret handling
3. provider config apply and disable steps
4. external_provider_config=null cleanup
5. health, project config, and release baseline checks
6. request-count and cost note
7. troubleshooting guidance
8. no API key UI
9. no frontend selector
10. no Ask schema expansion

## 3. Preconditions

P24 may start only after all of the following are true:

1. P23.2 pass receipt exists
2. DeepSeek key is available outside the repo
3. LTCLAW_RAG_API_KEY is the chosen product env var name
4. QWENPAW_RAG_API_KEY is not used for the provider secret
5. Windows local project directory is configured
6. current release exists

## 4. Startup Checklist

Windows startup checklist:

1. confirm git status is clean
2. set LTCLAW_RAG_API_KEY in the current PowerShell process only
3. run secret shape check and print booleans only
4. set QWENPAW_WORKING_DIR
5. set QWENPAW_CONSOLE_STATIC_DIR
6. start ltclaw.exe app
7. GET health returns 200
8. GET project config returns 200
9. GET release status returns 200

Suggested command shape:

```powershell
Set-Location E:\LTclaw2.0
git status --short --branch

$env:LTCLAW_RAG_API_KEY = '<set manually here; do not echo>'
$env:QWENPAW_WORKING_DIR = 'C:\ltclaw-data-backed'
$env:QWENPAW_CONSOLE_STATIC_DIR = 'E:\LTclaw2.0\console\dist'

python - <<'PY'
import os
v = os.environ.get('LTCLAW_RAG_API_KEY', '')
print({
  'exists': bool(v.strip()),
  'length_gt_20': len(v) > 20,
  'starts_with_sk': v.startswith('sk'),
  'header_starts_with_bearer_sk': ('Bearer ' + v).startswith('Bearer sk'),
  'header_length_gt_env_length': len('Bearer ' + v) > len(v),
})
PY

& 'E:\LTclaw2.0\.venv\Scripts\ltclaw.exe' app --host 127.0.0.1 --port 8092
```

## 5. Secret Handling Checklist

Secret handling rules:

1. key exists only in env
2. key does not appear in config
3. key does not appear in docs
4. key does not appear in logs
5. key does not appear in receipts
6. key does not appear in screenshots
7. only the env var name LTCLAW_RAG_API_KEY may appear in config
8. shape check may print booleans only
9. cleanup must remove the env var

## 6. Provider Config Apply Checklist

Provider config apply checklist:

1. enabled=true
2. transport_enabled=true
3. provider_name=future_external
4. model_name=deepseek-chat
5. allowed_providers=["future_external"]
6. allowed_models=["deepseek-chat"]
7. base_url=https://api.deepseek.com/chat/completions
8. env.api_key_env_var=LTCLAW_RAG_API_KEY
9. GET readback confirms no secret value is present

Minimum config shape:

```json
{
  "external_provider_config": {
    "enabled": true,
    "transport_enabled": true,
    "provider_name": "future_external",
    "model_name": "deepseek-chat",
    "allowed_providers": ["future_external"],
    "allowed_models": ["deepseek-chat"],
    "base_url": "https://api.deepseek.com/chat/completions",
    "env": {
      "api_key_env_var": "LTCLAW_RAG_API_KEY"
    }
  }
}
```

## 7. Disable And Cleanup Checklist

Disable and cleanup checklist:

1. set transport_enabled=false for kill switch validation
2. set external_provider_config=null for full cleanup
3. run Remove-Item Env:\LTCLAW_RAG_API_KEY
4. restart LTCLaw without secret
5. confirm health, project config, and release status all return 200
6. confirm current release remains unchanged

## 8. Baseline Monitor Checklist

Baseline monitor checklist:

1. current release id
2. release list or history count
3. formal map hash or stable summary
4. test plan count
5. workbench draft or proposal count
6. external_provider_config state
7. request count if available

## 9. Troubleshooting Matrix

### env shape fails

1. likely cause: wrong env var, blank key, or malformed copy
2. operator action: clear env, re-enter key, rerun shape check booleans only

### direct provider 401

1. likely cause: invalid key, expired key, or account mismatch
2. operator action: stop, verify the key source outside the repo, do not continue broad pilot use

### provider HTTP error

1. likely cause: upstream provider issue, endpoint mismatch, or transient network issue
2. operator action: capture redacted receipt evidence, stop after repeated failures, do not broaden prompts

### mode=insufficient_context

1. likely cause: prompt not supported by current citations or provider returned unusable output
2. operator action: confirm the scenario is grounded in current-release citations and keep warnings redacted in receipts

### citation_count=0

1. likely cause: provider output not grounded or citation validation failed
2. operator action: treat as blocked for that scenario, do not accept as pass

### kill switch fails

1. likely cause: transport_enabled readback mismatch or provider still reachable after disable
2. operator action: stop immediately and restore external_provider_config=null

### cleanup fails

1. likely cause: external_provider_config not restored or env var still present in session
2. operator action: restore null config, remove env var, restart without secret, recheck baseline

### health 500

1. likely cause: startup or runtime dependency failure
2. operator action: stop pilot use, capture redacted logs, return to baseline before retry

### project config 502 or 500

1. likely cause: service bridge or startup instability
2. operator action: stop, restart to baseline, confirm project config before provider config changes

### release status 500

1. likely cause: runtime state inconsistency or release index issue
2. operator action: stop, do not proceed with pilot scenarios, restore baseline first

### no-write state changed

1. likely cause: unintended write path or operator-side workflow leak
2. operator action: treat as blocked, stop immediately, preserve redacted evidence, and restore baseline

## 10. Cost And Usage Guidance

Cost and usage guidance:

1. record approximate request count per controlled pilot session
2. keep the controlled pilot scenario set small
3. stop after unexpected repeated failures
4. do not run broad exploratory prompts by default

## 11. P24 Execution Split

Recommended split:

1. P24.1 docs checklist
2. P24.2 optional Windows operator dry run
3. P24.3 optional startup helper script plan
4. P24.4 next gate decision

## 12. Not Allowed

P24 must not include:

1. production rollout
2. production ready claim
3. API key UI
4. frontend provider selector
5. Ask request provider, model, or api_key fields
6. ordinary user provider choice
7. multi-provider routing
8. ordinary RAG writes release
9. ordinary RAG writes formal map
10. ordinary RAG writes test plan
11. ordinary RAG writes workbench draft