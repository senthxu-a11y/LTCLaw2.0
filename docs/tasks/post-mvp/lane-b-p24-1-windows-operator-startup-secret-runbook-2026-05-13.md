# Lane B P24.1 Windows Operator Startup And Secret Runbook

Date: 2026-05-13
Status: docs-only executable runbook
Scope: standardize the controlled Windows DeepSeek pilot startup, env-only secret handling, backend-owned provider config apply and disable, baseline checks, troubleshooting, and redacted receipt rules without changing source, frontend, or tests

## 1. Scope

This runbook is the executable P24.1 handoff for the current controlled DeepSeek pilot line.

What this runbook does:

1. standardizes Windows operator startup on the already-validated ltclaw.exe path
2. keeps the provider secret env-only under LTCLAW_RAG_API_KEY
3. uses only backend-owned external_provider_config apply, disable, and null cleanup steps
4. makes health, project config, and release baseline checks explicit
5. defines a redacted receipt shape that can be reviewed later
6. keeps the line pilot usable and not production ready

What this runbook does not do:

1. production rollout
2. production ready claim
3. Ask request schema expansion
4. frontend provider, model, or api_key UI
5. RAG provider ownership changes
6. SVN sync, update, or commit writes
7. ordinary RAG writes to release, formal map, test plan, or workbench draft

## 2. Preconditions

All of the following must already be true before execution:

1. the repo contains the accepted P23.2 Windows controlled pilot receipt
2. the local project directory is already configured and readable
3. a current release already exists
4. the operator has a DeepSeek key available outside the repo
5. the operator can start the app by running E:\LTclaw2.0\.venv\Scripts\ltclaw.exe app
6. console/dist already exists for the current checkout
7. the operator understands that this slice remains pilot usable and not production ready

## 3. Stable Endpoints And Variables

Use these stable values unless the local machine requires a different host or port:

```powershell
$RepoRoot = 'E:\LTclaw2.0'
$BaseUrl = 'http://127.0.0.1:8092'
$HealthUrl = "$BaseUrl/api/agent/health"
$ProjectConfigUrl = "$BaseUrl/api/agents/default/game/project/config"
$ReleaseStatusUrl = "$BaseUrl/api/agents/default/game/knowledge/releases/status"
$WorkingDir = 'C:\ltclaw-data-backed'
$ConsoleStaticDir = 'E:\LTclaw2.0\console\dist'
```

Rules:

1. only the env var name LTCLAW_RAG_API_KEY may appear in config, docs, logs, or receipts
2. never paste the secret value into PowerShell history, screenshots, docs, logs, or receipts
3. keep all provider config changes operator-only and local to the current machine
4. if a request body needs non-ASCII content later, prefer a Python UTF-8 helper instead of hand-editing PowerShell JSON

## 4. Startup Sequence

### Step 1. Confirm repo state

```powershell
Set-Location $RepoRoot
git status --short --branch
git rev-parse HEAD
```

Stop if the working tree contains unrelated local edits that the operator does not understand.

### Step 2. Set env vars in the current PowerShell process only

Use the current process only. Do not use setx.

```powershell
$secret = Read-Host 'Enter LTCLAW_RAG_API_KEY for this PowerShell process only' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
  $env:LTCLAW_RAG_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$env:QWENPAW_WORKING_DIR = $WorkingDir
$env:QWENPAW_CONSOLE_STATIC_DIR = $ConsoleStaticDir
```

### Step 3. Run secret shape check and print booleans only

```powershell
& 'E:\LTclaw2.0\.venv\Scripts\python.exe' -c "import json, os; v=os.environ.get('LTCLAW_RAG_API_KEY','').strip(); h='Bearer '+v; print(json.dumps({'exists': bool(v), 'length_gt_20': len(v) > 20, 'starts_with_sk': v.startswith('sk'), 'header_starts_with_bearer_sk': h.startswith('Bearer sk'), 'header_length_gt_env_length': len(h) > len(v)}, indent=2))"
```

Pass rule:

1. every field is true
2. no secret value is printed

### Step 4. Start LTCLAW

```powershell
& 'E:\LTclaw2.0\.venv\Scripts\ltclaw.exe' app --host 127.0.0.1 --port 8092
```

Keep this process in its own terminal.

### Step 5. Baseline health, project, and release checks

In a separate PowerShell terminal with the same three env vars set:

```powershell
Invoke-RestMethod -Uri $HealthUrl -Method Get
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get
```

Pass rule:

1. health returns 200 and a healthy payload
2. project config returns 200
3. release status returns 200
4. current release exists
5. baseline external_provider_config is null before apply

## 5. Baseline Evidence To Record

Record the following before any provider config change:

1. commit hash
2. Windows version
3. local project directory
4. current release id
5. release history count or list count if readable
6. formal map hash or stable summary if readable
7. test plan count if readable
8. workbench draft count if readable
9. project config external_provider_config state
10. request count if a fake or proxy monitor is in use

If one of the optional counts is absent or unreadable, record that explicitly instead of inventing a value.

## 6. Provider Config Apply

Use only backend-owned external_provider_config. Do not add provider, model, or api_key to Ask requests.

Important interface rule verified by P24.2:

1. do not PUT only `{ "external_provider_config": ... }` to the project-config API
2. the project-config API expects the full current project config body, including existing project and svn fields
3. therefore apply must follow: GET current project config -> modify only external_provider_config -> PUT the full config JSON back

Reference payload:

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

Safe apply flow:

```powershell
$CurrentProjectConfigPath = Join-Path $RepoRoot 'current-project-config.json'
$ApplyProjectConfigPath = Join-Path $RepoRoot 'project-config-apply.json'

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get |
  ConvertTo-Json -Depth 8 |
  Set-Content -Path $CurrentProjectConfigPath -Encoding UTF8

& 'E:\LTclaw2.0\.venv\Scripts\ltclaw.exe' operator deepseek-project-config-payload \
  --mode apply \
  --input-file $CurrentProjectConfigPath |
  Set-Content -Path $ApplyProjectConfigPath -Encoding UTF8

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json; charset=utf-8' -InFile $ApplyProjectConfigPath
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
```

Apply pass rule:

1. PUT returns 200
2. immediate GET returns non-null external_provider_config
3. readback preserves enabled, transport_enabled, provider_name, model_name, base_url, and env.api_key_env_var
4. readback does not contain api_key, Authorization, or the secret value
5. the full-config PUT preserves the pre-existing project and svn fields

## 7. Disable And Null Cleanup

### Step 1. Kill switch validation

Persist transport_enabled=false without changing provider ownership:

```powershell
$CurrentProjectConfigPath = Join-Path $RepoRoot 'current-project-config.json'
$DisableProjectConfigPath = Join-Path $RepoRoot 'project-config-disable.json'

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get |
  ConvertTo-Json -Depth 8 |
  Set-Content -Path $CurrentProjectConfigPath -Encoding UTF8

& 'E:\LTclaw2.0\.venv\Scripts\ltclaw.exe' operator deepseek-project-config-payload \
  --mode disable \
  --input-file $CurrentProjectConfigPath |
  Set-Content -Path $DisableProjectConfigPath -Encoding UTF8

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json; charset=utf-8' -InFile $DisableProjectConfigPath
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
```

Disable pass rule:

1. immediate readback shows transport_enabled=false
2. the next pilot probe fails closed rather than using transport
3. if transport still appears active, stop the run and restore null config immediately

### Step 2. Full cleanup

```powershell
$CurrentProjectConfigPath = Join-Path $RepoRoot 'current-project-config.json'
$CleanupProjectConfigPath = Join-Path $RepoRoot 'project-config-cleanup.json'

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get |
  ConvertTo-Json -Depth 8 |
  Set-Content -Path $CurrentProjectConfigPath -Encoding UTF8

& 'E:\LTclaw2.0\.venv\Scripts\ltclaw.exe' operator deepseek-project-config-payload \
  --mode cleanup \
  --input-file $CurrentProjectConfigPath |
  Set-Content -Path $CleanupProjectConfigPath -Encoding UTF8

Invoke-RestMethod -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json; charset=utf-8' -InFile $CleanupProjectConfigPath
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
Remove-Item Env:\LTCLAW_RAG_API_KEY -ErrorAction SilentlyContinue
```

Then restart LTCLAW in a fresh PowerShell session without LTCLAW_RAG_API_KEY and rerun:

```powershell
Invoke-RestMethod -Uri $HealthUrl -Method Get
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get
```

Cleanup pass rule:

1. project config readback returns external_provider_config=null
2. health returns 200 after restart
3. project config returns 200 after restart
4. release status returns 200 after restart
5. current release id remains unchanged

## 8. Troubleshooting Matrix

### Secret shape check fails

1. likely cause: blank value, malformed paste, or wrong terminal session
2. action: clear the env var, re-enter the secret in the same PowerShell session, rerun the boolean-only check

### health returns 500

1. likely cause: startup dependency or runtime bootstrap failure
2. action: stop pilot steps, capture redacted logs only, restore baseline before retry

### project config returns 500 or 502

1. likely cause: unstable service bridge or startup order problem
2. action: stop, restart LTCLAW to baseline, and do not apply provider config again until GET project config returns 200

### release status returns 500

1. likely cause: release index inconsistency or runtime startup issue
2. action: stop immediately and recover baseline before any pilot prompt

### apply readback shows missing or mutated fields

1. likely cause: malformed full-config payload, project-config API contract mismatch, or local config persistence issue
2. action: stop, preserve redacted evidence, confirm project and svn fields were preserved, do not continue to answer probes, restore external_provider_config=null

### PUT returns missing project or svn field errors

1. likely cause: operator attempted to PUT only a partial external_provider_config block
2. action: rerun with GET current project config -> deepseek-project-config-payload helper -> PUT full project config JSON

### provider returns 401 or repeated HTTP failures

1. likely cause: invalid secret, expired secret, account mismatch, or upstream outage
2. action: stop the run, verify the key source outside the repo, and do not broaden prompts

### insufficient_context with citation_count=0 on a grounded scenario

1. likely cause: unsupported scenario, provider output not grounded, or validation failed closed
2. action: mark the scenario blocked, keep warnings redacted in the receipt, and do not count it as a pass

### cleanup fails

1. likely cause: null restore was not saved or the restart reused a terminal that still had LTCLAW_RAG_API_KEY set
2. action: reapply external_provider_config=null, open a fresh terminal, confirm the env var is absent, and recheck health, project config, and release status

### no-write boundary changed

1. likely cause: operator workflow leak or unrelated concurrent action on the same project
2. action: stop immediately, preserve redacted evidence, and do not claim pass

## 9. Redacted Receipt Template

Use this template for every controlled pilot rerun:

```md
# Lane B P24.1 Windows Operator Startup And Secret Receipt

Date: <yyyy-mm-dd>
Status: <pass|blocked>
Scope: backend-only, operator-only, Windows single-machine DeepSeek pilot, env-only secret handling

## 1. Environment

1. commit hash: <value>
2. Windows version: <value>
3. app startup command shape: ltclaw.exe app --host 127.0.0.1 --port 8092
4. env var name only: LTCLAW_RAG_API_KEY
5. local project directory: <value>

## 2. Baseline

1. health status: <value>
2. project config status: <value>
3. release status: <value>
4. current release id before run: <value>
5. external_provider_config before run: <null|non-null>

## 3. Secret Gate

1. exists: <true|false>
2. length_gt_20: <true|false>
3. starts_with_sk: <true|false>
4. header_starts_with_bearer_sk: <true|false>
5. header_length_gt_env_length: <true|false>

## 4. Provider Config Apply

1. put status: <value>
2. readback enabled: <true|false>
3. readback transport_enabled: <true|false>
4. readback provider_name: <value>
5. readback model_name: <value>
6. readback env.api_key_env_var: LTCLAW_RAG_API_KEY
7. secret value appeared anywhere: <yes|no>

## 5. Pilot Probe

1. probe result: <pass|blocked>
2. response mode: <value>
3. citation count: <value>
4. warnings: <redacted list>

## 6. Kill Switch And Cleanup

1. readback transport_enabled after disable: <true|false>
2. external_provider_config after null cleanup: <null|non-null>
3. final health status: <value>
4. final project config status: <value>
5. final release status: <value>
6. current release unchanged: <yes|no>

## 7. Optional Baseline Counters

1. release count before and after: <value|unreadable>
2. formal map summary before and after: <value|unreadable>
3. test plan count before and after: <value|unreadable>
4. workbench draft count before and after: <value|unreadable>

## 8. Final Status

1. final status: <pass|blocked>
2. stop condition triggered: <none|value>
3. notes: <redacted operator notes only>
```

Receipt rules:

1. never include the secret value
2. never include Authorization headers
3. never include pasted raw provider payloads if they contain secrets or account data
4. keep warnings redacted to the minimum needed for review
5. if an endpoint is absent or unreadable, say so explicitly
6. do not claim production rollout or production ready

## 10. Minimal Script Plan

This P24.1 slice is docs-only. If later automation is approved, keep it as an operator wrapper only.

Minimum future script scope:

1. prompt for LTCLAW_RAG_API_KEY in-process only
2. run the boolean-only secret shape check
3. GET current project config and generate a full-config apply payload that changes only external_provider_config
4. run health, project config, and release status checks
5. generate a full-config disable payload that changes only transport_enabled=false inside external_provider_config
6. generate a full-config cleanup payload that restores external_provider_config=null and clear LTCLAW_RAG_API_KEY from the session
7. print a redacted receipt skeleton without any secret material

Any future script must remain operator-only, backend-only, pilot usable, and not production ready.