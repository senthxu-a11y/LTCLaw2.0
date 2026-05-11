# Lane B P22.2 Controlled Real Provider Smoke Operator Runbook

Date: 2026-05-11
Status: docs-only runbook
Scope: define the exact Windows operator procedure for one planned real-provider smoke without executing any real provider call in this document

## 1. Scope

This runbook is intentionally narrow:

1. backend-only
2. operator-only
3. single provider
4. single model
5. single Windows machine
6. manual env secret
7. no frontend selector
8. no Ask schema expansion
9. not production rollout
10. not production ready

This runbook does not authorize execution by itself. It freezes the operator procedure and receipt shape that P22.3 must follow after review and acceptance.

## 2. Preconditions And Entry Decision

P22.3 may start only after all of the following are true:

1. P22 checklist is accepted
2. P22.1 source/config review is accepted
3. this P22.2 runbook is reviewed and accepted
4. the target Windows machine has a known current release
5. the target Windows machine can restore external_provider_config=null
6. the target Windows machine can restart LTCLaw and return to health, project config, and release status 200
7. one approved provider account exists outside the repo
8. one approved backend-owned model exists outside the repo
9. one low-risk grounded prompt is selected before execution

Entry decision:

1. P22.3 is still blocked until this runbook is reviewed and accepted
2. after approval, P22.3 must remain backend-only and operator-only
3. after approval, P22.3 must stop at the first failure

## 3. Operator Variables

The operator must fill these placeholders on the Windows machine before execution:

```powershell
$RepoRoot = 'E:\LTclaw2.0'
$AppHost = '127.0.0.1'
$AppPort = 8092
$BaseApi = "http://${AppHost}:${AppPort}"
$ProjectConfigUrl = "$BaseApi/api/agents/default/game/project/config"
$HealthUrl = "$BaseApi/api/agent/health"
$ReleaseStatusUrl = "$BaseApi/api/agents/default/game/knowledge/releases/status"
$ReleaseListUrl = "$BaseApi/api/agents/default/game/knowledge/releases"
$FormalMapUrl = "$BaseApi/api/agents/default/game/knowledge/map"
$TestPlansUrl = "$BaseApi/api/agents/default/game/knowledge/test-plans"
$DraftProposalsUrl = "$BaseApi/api/agents/default/game/change/proposals?status=draft"
$RagAnswerUrl = "$BaseApi/api/agents/default/game/knowledge/rag/answer"

$WorkingDir = 'C:\ltclaw-data-backed'
$ConsoleStaticDir = 'E:\LTclaw2.0\console\dist'
$SecretEnvVarName = 'QWENPAW_RAG_API_KEY'

$ProviderName = 'future_external'
$BackendModel = '<single backend-owned model>'
$ProviderEndpoint = '<backend-owned provider endpoint>'
$TimeoutSeconds = 15.0
$MaxOutputTokens = 512
$MaxPromptChars = 12000
$MaxOutputChars = 2000

$LowRiskQuery = '<ask about one current-release indexed fact that is easy to verify from citation>'
```

Rules:

1. SecretEnvVarName may be written in the receipt
2. the secret value must never be written in the receipt
3. ProviderEndpoint may be written only in redacted form when needed
4. BackendModel must be one backend-owned model only
5. LowRiskQuery must satisfy the low-risk rules in this runbook
6. the no-write verification should prefer the known release, formal map, test plan, and draft proposal endpoints listed above

## 4. Preflight Checks

The operator must complete all of these checks before any provider config write:

1. confirm Windows OS version
2. confirm repo commit hash
3. confirm clean git status
4. confirm LTCLaw startup path
5. confirm QWENPAW_WORKING_DIR
6. confirm QWENPAW_CONSOLE_STATIC_DIR
7. confirm health returns 200
8. confirm project config GET returns 200
9. confirm release status returns 200
10. confirm current release id exists
11. confirm external_provider_config is null before run

Exact commands:

```powershell
Set-Location $RepoRoot

git rev-parse HEAD
git status --short --branch

[System.Environment]::OSVersion.VersionString

Test-Path "$RepoRoot\.venv\Scripts\ltclaw.exe"
Test-Path $WorkingDir
Test-Path $ConsoleStaticDir

Invoke-RestMethod -Uri $HealthUrl -Method Get
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get

$ProjectConfigBefore = Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
$ReleaseStatusBefore = Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get

$ProjectConfigBefore.external_provider_config
$ReleaseStatusBefore.current_release_id
```

Preflight pass rules:

1. git status must be clean on the target Windows machine
2. Health, project config, and release status must each return 200
3. ReleaseStatusBefore.current_release_id must be non-empty
4. ProjectConfigBefore.external_provider_config must be null

## 5. Secret Handling Checklist

The operator must preserve all of the following rules:

1. env stores the secret value
2. config stores only the env var name
3. no secret in docs
4. no secret in tasks
5. no secret in tests
6. no secret in fixtures
7. no secret in logs
8. no secret in receipts
9. no secret in project_config.yaml
10. no secret in response body
11. no secret in warning text
12. no secret in error text
13. no secret in screenshots
14. there is no API key UI
15. the operator must redact terminal output before writing the receipt
16. provider raw error text must not be copied into the receipt
17. Authorization must remain transport-boundary-only

Operator handling rules:

1. set the secret only in the current PowerShell process
2. do not paste the secret into config JSON
3. do not save the secret in shell history notes or screenshots
4. if a secret appears anywhere, stop immediately and execute rollback

## 6. Minimal Backend-Owned Config Shape

P22.3 must save only this minimum backend-owned config shape, with placeholders replaced by approved operator values:

```json
{
  "external_provider_config": {
    "enabled": true,
    "transport_enabled": true,
    "provider_name": "future_external",
    "model_name": "<single backend-owned model>",
    "allowed_providers": ["future_external"],
    "allowed_models": ["<same backend-owned model>"],
    "base_url": "<backend-owned provider endpoint>",
    "timeout_seconds": 15.0,
    "max_output_tokens": 512,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {
      "api_key_env_var": "<env var name only>"
    }
  }
}
```

Required config rules:

1. enabled=true
2. transport_enabled=true
3. provider_name=future_external
4. model_name must be the single backend-owned model
5. allowed_providers must be ["future_external"]
6. allowed_models must be ["<same backend-owned model>"]
7. base_url must be the backend-owned provider endpoint
8. timeout_seconds must remain bounded
9. max_output_tokens must remain bounded
10. max_prompt_chars must remain bounded
11. max_output_chars must remain bounded
12. env.api_key_env_var must contain only the env var name
13. config must contain no api_key value

## 7. Low-Risk Prompt Requirements

The one real-provider smoke prompt must satisfy all of the following:

1. it asks about current-release indexed data
2. it does not ask for broad generation
3. it does not ask for secrets
4. it does not ask for source code
5. it does not ask for unsupported external knowledge
6. it is easy to verify from citation

Good prompt shape:

1. ask for one concrete current-release fact already present in indexed chunks
2. prefer one table, field, feature, or short factual summary tied to one citation
3. keep the question narrow enough that a grounded citation can clearly confirm or reject the answer

Bad prompt shape:

1. broad design generation
2. multi-step planning
3. requests for external facts outside indexed release content
4. source code requests
5. any request that invites secrets or credentials

## 8. Exact Operator Commands

### 8.1 Set Env Secret In Current Process Only

```powershell
$env:$SecretEnvVarName = '<set manually here; do not copy the value into the receipt>'
[string]::IsNullOrWhiteSpace($env:$SecretEnvVarName)
```

Pass rule:

1. the second command must return False

### 8.2 Start LTCLaw On 127.0.0.1:8092

Open a dedicated PowerShell window for the app process and run:

```powershell
Set-Location $RepoRoot
$env:QWENPAW_WORKING_DIR = $WorkingDir
$env:QWENPAW_CONSOLE_STATIC_DIR = $ConsoleStaticDir
$env:$SecretEnvVarName = '<set manually here; do not copy the value into the receipt>'
& "$RepoRoot\.venv\Scripts\ltclaw.exe" app --host 127.0.0.1 --port 8092
```

Receipt rule:

1. record the startup command shape with env var name only
2. do not record the secret value

### 8.3 GET Health

```powershell
$Health = Invoke-WebRequest -Uri $HealthUrl -Method Get
$Health.StatusCode
$Health.Content
```

Pass rule:

1. Health.StatusCode must be 200

### 8.4 GET Project Config

```powershell
$ProjectConfigBefore = Invoke-WebRequest -Uri $ProjectConfigUrl -Method Get
$ProjectConfigBefore.StatusCode
$ProjectConfigBefore.Content
```

Pass rule:

1. ProjectConfigBefore.StatusCode must be 200

### 8.5 GET Release Status

```powershell
$ReleaseStatusBefore = Invoke-WebRequest -Uri $ReleaseStatusUrl -Method Get
$ReleaseStatusBefore.StatusCode
$ReleaseStatusBefore.Content
```

Pass rule:

1. ReleaseStatusBefore.StatusCode must be 200

### 8.6 PUT External Provider Config

```powershell
$ConfigBody = @{
  external_provider_config = @{
    enabled = $true
    transport_enabled = $true
    provider_name = $ProviderName
    model_name = $BackendModel
    allowed_providers = @($ProviderName)
    allowed_models = @($BackendModel)
    base_url = $ProviderEndpoint
    timeout_seconds = $TimeoutSeconds
    max_output_tokens = $MaxOutputTokens
    max_prompt_chars = $MaxPromptChars
    max_output_chars = $MaxOutputChars
    env = @{
      api_key_env_var = $SecretEnvVarName
    }
  }
} | ConvertTo-Json -Depth 6

Invoke-WebRequest -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json' -Body $ConfigBody
```

Pass rule:

1. the request must succeed
2. the request body must contain no api_key value

### 8.7 GET Project Config Readback

```powershell
$ProjectConfigReadback = Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
$ProjectConfigReadback.external_provider_config | ConvertTo-Json -Depth 6
```

Pass rules:

1. readback must preserve enabled=true
2. readback must preserve transport_enabled=true
3. readback must preserve provider_name=future_external
4. readback must preserve model_name=$BackendModel
5. readback must preserve allowed_providers=["future_external"]
6. readback must preserve allowed_models=[$BackendModel]
7. readback must preserve base_url in backend-owned form
8. readback must preserve env.api_key_env_var=$SecretEnvVarName
9. readback must not echo any api_key value

### 8.8 POST One Low-Risk RAG Answer

```powershell
$PositiveAnswerBody = @{
  query = $LowRiskQuery
  max_chunks = 8
  max_chars = 12000
} | ConvertTo-Json -Depth 4

$PositiveAnswer = Invoke-RestMethod -Uri $RagAnswerUrl -Method Post -ContentType 'application/json' -Body $PositiveAnswerBody
$PositiveAnswer | ConvertTo-Json -Depth 6
```

Pass rules:

1. the answer request must return 200
2. response mode must be answer
3. response citations must be non-empty
4. warnings must remain safe and redacted
5. response must contain no secret value

### 8.8A Capture No-Write Baseline Before The Real-Provider Answer

The operator must snapshot the ordinary RAG no-write surfaces before treating the positive answer as valid evidence.

Known endpoints for the no-write check:

1. release state: $ReleaseStatusUrl and $ReleaseListUrl
2. formal map state: $FormalMapUrl
3. test plan state: $TestPlansUrl
4. workbench draft state: $DraftProposalsUrl

Recommended Windows command shape:

```powershell
$ReleaseStatusNoWriteBefore = Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get
$ReleaseListNoWriteBefore = Invoke-RestMethod -Uri $ReleaseListUrl -Method Get

$ReleaseCurrentIdBefore = $ReleaseStatusNoWriteBefore.current_release_id
$ReleaseCountBefore = @($ReleaseListNoWriteBefore).Count
$ReleaseIdsBefore = @($ReleaseListNoWriteBefore | ForEach-Object { $_.release_id })

$FormalMapEndpointState = 'readable'
try {
  $FormalMapBefore = Invoke-RestMethod -Uri $FormalMapUrl -Method Get
  $FormalMapModeBefore = $FormalMapBefore.mode
  $FormalMapHashBefore = $FormalMapBefore.map_hash
  $FormalMapUpdatedAtBefore = $FormalMapBefore.updated_at
  $FormalMapUpdatedByBefore = $FormalMapBefore.updated_by
  $FormalMapTableCountBefore = @($FormalMapBefore.map.tables).Count
} catch {
  $FormalMapEndpointState = 'endpoint_absent_or_unreadable'
}

$TestPlansEndpointState = 'readable'
try {
  $TestPlansBefore = Invoke-RestMethod -Uri $TestPlansUrl -Method Get
  $TestPlanCountBefore = @($TestPlansBefore).Count
  $TestPlanIdsBefore = @($TestPlansBefore | ForEach-Object { $_.id })
} catch {
  $TestPlansEndpointState = 'endpoint_absent_or_unreadable'
}

$DraftsEndpointState = 'readable'
try {
  $DraftsBefore = Invoke-RestMethod -Uri $DraftProposalsUrl -Method Get
  $DraftCountBefore = @($DraftsBefore).Count
  $DraftIdsBefore = @($DraftsBefore | ForEach-Object { $_.id })
} catch {
  $DraftsEndpointState = 'endpoint_absent_or_unreadable'
}
```

Baseline capture rules:

1. release state must be readable
2. formal map state should be read through the known endpoint when available
3. test plan state should be read through the known endpoint when available
4. workbench draft state should be read through the known endpoint when available
5. if any non-release no-write endpoint is absent or unreadable, the operator must record endpoint absent or endpoint unreadable in the receipt
6. if any non-release no-write endpoint is absent or unreadable, ordinary RAG no-write must not be marked pass by default

### 8.9 POST Same Answer With Request-Owned Provider, Model, And Api Key Negative Fields

### 8.9 POST Same Answer With Request-Owned Provider, Model, And Api Key Negative Fields

```powershell
$NegativeAnswerBody = @{
  query = $LowRiskQuery
  max_chunks = 8
  max_chars = 12000
  provider = 'request-provider'
  model = 'request-model'
  api_key = '<request-owned negative-test field>'
} | ConvertTo-Json -Depth 4

$NegativeAnswer = Invoke-RestMethod -Uri $RagAnswerUrl -Method Post -ContentType 'application/json' -Body $NegativeAnswerBody
$NegativeAnswer | ConvertTo-Json -Depth 6
```

Pass rules:

1. the answer request must return 200
2. request-owned provider must not change backend provider selection
3. request-owned model must not change backend model selection
4. request-owned api_key must not be used
5. the response must remain grounded and safe

### 8.9A Capture No-Write State After The Real-Provider Answer

Immediately after the positive and negative answer requests, the operator must re-read the same no-write surfaces.

Recommended Windows command shape:

```powershell
$ReleaseStatusNoWriteAfter = Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get
$ReleaseListNoWriteAfter = Invoke-RestMethod -Uri $ReleaseListUrl -Method Get

$ReleaseCurrentIdAfter = $ReleaseStatusNoWriteAfter.current_release_id
$ReleaseCountAfter = @($ReleaseListNoWriteAfter).Count
$ReleaseIdsAfter = @($ReleaseListNoWriteAfter | ForEach-Object { $_.release_id })

$FormalMapEndpointStateAfter = 'readable'
try {
  $FormalMapAfter = Invoke-RestMethod -Uri $FormalMapUrl -Method Get
  $FormalMapModeAfter = $FormalMapAfter.mode
  $FormalMapHashAfter = $FormalMapAfter.map_hash
  $FormalMapUpdatedAtAfter = $FormalMapAfter.updated_at
  $FormalMapUpdatedByAfter = $FormalMapAfter.updated_by
  $FormalMapTableCountAfter = @($FormalMapAfter.map.tables).Count
} catch {
  $FormalMapEndpointStateAfter = 'endpoint_absent_or_unreadable'
}

$TestPlansEndpointStateAfter = 'readable'
try {
  $TestPlansAfter = Invoke-RestMethod -Uri $TestPlansUrl -Method Get
  $TestPlanCountAfter = @($TestPlansAfter).Count
  $TestPlanIdsAfter = @($TestPlansAfter | ForEach-Object { $_.id })
} catch {
  $TestPlansEndpointStateAfter = 'endpoint_absent_or_unreadable'
}

$DraftsEndpointStateAfter = 'readable'
try {
  $DraftsAfter = Invoke-RestMethod -Uri $DraftProposalsUrl -Method Get
  $DraftCountAfter = @($DraftsAfter).Count
  $DraftIdsAfter = @($DraftsAfter | ForEach-Object { $_.id })
} catch {
  $DraftsEndpointStateAfter = 'endpoint_absent_or_unreadable'
}
```

No-write pass rules:

1. release state passes only if current release id is unchanged, release count is unchanged, and no new release id appears
2. formal map state passes only if no new save, no status edit, no updated_by change, no updated_at change, no map_hash change, and no structure summary change are observed
3. test plan state passes only if test plan count is unchanged and no new test plan id appears
4. workbench draft state passes only if draft or proposal count is unchanged and no new proposal id appears
5. ordinary RAG no-write passes only if all four state classes pass

No-write blocked rules:

1. if any state increases, changes, or cannot be read, ordinary RAG no-write = blocked
2. if any endpoint is absent in the current product or absent on the target machine, the receipt must say endpoint absent and must explain whether any substitute evidence exists
3. endpoint absent or endpoint unreadable must never be silently recorded as pass
4. if ordinary RAG no-write is blocked, the operator must stop and must not continue toward production or rollout claims

### 8.10 PUT transport_enabled=false

```powershell
$KillSwitchBody = @{
  external_provider_config = @{
    enabled = $true
    transport_enabled = $false
    provider_name = $ProviderName
    model_name = $BackendModel
    allowed_providers = @($ProviderName)
    allowed_models = @($BackendModel)
    base_url = $ProviderEndpoint
    timeout_seconds = $TimeoutSeconds
    max_output_tokens = $MaxOutputTokens
    max_prompt_chars = $MaxPromptChars
    max_output_chars = $MaxOutputChars
    env = @{
      api_key_env_var = $SecretEnvVarName
    }
  }
} | ConvertTo-Json -Depth 6

Invoke-WebRequest -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json' -Body $KillSwitchBody
```

### 8.11 POST Same Answer Again To Verify Kill Switch

```powershell
$KillSwitchAnswer = Invoke-RestMethod -Uri $RagAnswerUrl -Method Post -ContentType 'application/json' -Body $PositiveAnswerBody
$KillSwitchAnswer | ConvertTo-Json -Depth 6
```

Pass rules:

1. the answer request must return 200
2. the response must fail closed
3. the response must not show evidence that a real provider call succeeded after transport_enabled=false
4. the warnings must remain safe
5. the operator must stop immediately if the kill switch appears ineffective

### 8.12 PUT external_provider_config=null

```powershell
$CleanupBody = @{
  external_provider_config = $null
} | ConvertTo-Json -Depth 3

Invoke-WebRequest -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json' -Body $CleanupBody

$ProjectConfigAfterCleanup = Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
$ProjectConfigAfterCleanup.external_provider_config
```

Pass rule:

1. readback must show external_provider_config=null

### 8.13 Clear Env Secret

```powershell
Remove-Item Env:$SecretEnvVarName -ErrorAction SilentlyContinue
Test-Path Env:$SecretEnvVarName
```

Pass rule:

1. Test-Path must return False

### 8.14 Restart LTCLaw Without Secret

Stop the prior LTCLaw process, open a clean PowerShell window, and run:

```powershell
Set-Location $RepoRoot
$env:QWENPAW_WORKING_DIR = $WorkingDir
$env:QWENPAW_CONSOLE_STATIC_DIR = $ConsoleStaticDir
Remove-Item Env:$SecretEnvVarName -ErrorAction SilentlyContinue
& "$RepoRoot\.venv\Scripts\ltclaw.exe" app --host 127.0.0.1 --port 8092
```

Pass rule:

1. the restarted app process must not inherit the secret value

### 8.15 GET Health, Config, And Release Status Baseline After Restart

```powershell
$HealthAfter = Invoke-WebRequest -Uri $HealthUrl -Method Get
$ProjectConfigAfter = Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
$ReleaseStatusAfter = Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get

$HealthAfter.StatusCode
$ProjectConfigAfter.external_provider_config
$ReleaseStatusAfter.current_release_id
```

Pass rules:

1. HealthAfter.StatusCode must be 200
2. ProjectConfigAfter.external_provider_config must be null
3. ReleaseStatusAfter.current_release_id must still exist
4. release status must return 200

## 9. Pass Criteria

P22.3 passes only if all of the following are true:

1. one real provider answer returns 200
2. the answer is grounded by at least one valid citation
3. warnings are safe
4. request-owned provider is ignored
5. request-owned model is ignored
6. request-owned api_key is ignored
7. no secret leak is found
8. ordinary RAG no-write passes through release, formal map, test plan, and workbench draft comparisons
9. transport_enabled=false blocks the next call without restart
10. cleanup restores external_provider_config=null
11. restart without secret returns health 200
12. restart without secret returns project config 200
13. restart without secret returns release status 200

## 10. Stop Conditions

The operator must stop immediately if any of the following occurs:

1. a secret appears anywhere
2. the provider answer has no valid citation
3. provider raw error text appears in response output
4. request-owned provider affects behavior
5. request-owned model affects behavior
6. request-owned api_key affects behavior
7. kill switch fails
8. ordinary RAG no-write check is blocked
9. ordinary RAG writes release
10. ordinary RAG writes formal map
11. ordinary RAG writes test plan
12. ordinary RAG writes workbench draft
13. cleanup cannot restore null config
14. the app cannot return to baseline

## 11. Rollback Checklist

If execution stops early or fails, perform rollback immediately in this order:

1. set external_provider_config=null
2. clear env secret
3. restart app
4. verify health 200
5. verify project config external_provider_config=null
6. verify release status 200
7. verify current release unchanged
8. record rollback result in receipt

Exact rollback commands:

```powershell
$RollbackBody = @{
  external_provider_config = $null
} | ConvertTo-Json -Depth 3

Invoke-WebRequest -Uri $ProjectConfigUrl -Method Put -ContentType 'application/json' -Body $RollbackBody
Remove-Item Env:$SecretEnvVarName -ErrorAction SilentlyContinue
```

Then restart LTCLaw without the secret and re-run:

```powershell
Invoke-WebRequest -Uri $HealthUrl -Method Get
Invoke-RestMethod -Uri $ProjectConfigUrl -Method Get
Invoke-RestMethod -Uri $ReleaseStatusUrl -Method Get
```

Rollback pass rules:

1. health must return 200
2. project config readback must show external_provider_config=null
3. release status must return 200
4. current release id must remain unchanged from baseline unless a pre-existing unrelated system action changed it outside this smoke

## 12. Receipt Template

P22.3 must write a redacted receipt using this template:

```md
# Lane B P22.3 Windows Real-Provider Smoke Receipt

Date: <yyyy-mm-dd>
Status: <pass|blocked>
Scope: backend-only, operator-only, single provider, single model, single Windows machine, manual env secret

## 1. Environment

1. Windows version: <value>
2. commit hash: <value>
3. app startup command: <redacted command shape only>
4. env var name only: <value>
5. local project directory: <value>
6. current release id before run: <value>

## 2. Backend-Owned Config

1. provider name: <value>
2. model name: <value>
3. config readback preserved backend-owned fields: <yes|no>
4. api_key value appeared anywhere: <yes|no>

## 3. Positive Answer Result

1. response mode: <value>
2. citation ids: <list>
3. warnings: <redacted list>

## 4. Boundary Checks

1. request-owned provider ignored result: <value>
2. request-owned model ignored result: <value>
3. request-owned api_key ignored result: <value>
4. ordinary RAG no-write result: <pass|blocked>

## 5. No-Write Evidence

1. release current id before and after: <value>
2. release count before and after: <value>
3. new release id observed: <yes|no>
4. formal map endpoint state: <readable|endpoint absent|endpoint unreadable>
5. formal map summary before and after: <mode/hash/updated_at/updated_by/table_count>
6. test plans endpoint state: <readable|endpoint absent|endpoint unreadable>
7. test plan count before and after: <value>
8. new test plan id observed: <yes|no>
9. draft proposals endpoint state: <readable|endpoint absent|endpoint unreadable>
10. draft proposal count before and after: <value>
11. new draft proposal id observed: <yes|no>
12. substitute evidence used for absent endpoint: <none|value>

## 6. Kill Switch Result

1. transport_enabled=false result: <value>
2. post-kill-switch response mode: <value>
3. post-kill-switch warnings: <redacted list>

## 7. Cleanup And Rollback

1. cleanup result: <value>
2. external_provider_config after cleanup: <null|non-null>
3. final health status: <value>
4. final project config status: <value>
5. final release status: <value>
6. current release unchanged: <yes|no>

## 8. Final Status

1. final status: <pass|blocked>
2. stop condition triggered: <none|value>
3. notes: <redacted operator notes only>
```

Receipt rules:

1. never include the secret value
2. never include Authorization
3. never include unredacted provider raw errors
4. never include screenshots containing secrets
5. if any no-write endpoint is absent or unreadable, say so explicitly in the receipt
6. do not mark ordinary RAG no-write as pass unless all four state classes remain unchanged

## 13. Boundary Reminders

This runbook does not mean any of the following are complete:

1. production rollout
2. production ready status
3. frontend provider selector
4. Ask request support for provider, model, or api_key
5. ProviderManager.active_model control of ordinary RAG
6. SimpleModelRouter control of ordinary RAG
7. ordinary RAG writes

## 14. Final Runbook Decision

Final decision:

1. this P22.2 runbook contains the required Windows operator command sequence
2. this P22.2 runbook contains the required rollback checklist
3. this P22.2 runbook contains the required secret handling checklist
4. this P22.2 runbook contains the required receipt template
5. P22.3 may start only after this runbook is reviewed and accepted
6. P22.3 must stop at first failure