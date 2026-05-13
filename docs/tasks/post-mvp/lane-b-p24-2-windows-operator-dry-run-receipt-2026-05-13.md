# Lane B P24.2 Windows Operator Dry-Run Receipt

Date: 2026-05-13
Status: pass
Scope: Windows pilot-machine dry run of the P24.1 operator startup and secret-management runbook; operator-only, backend-only, env-only secret handling; no frontend provider UI, no Ask schema expansion, no provider ownership change

## 1. Final Status

1. final status: pass
2. stop condition triggered: none
3. production rollout: no
4. production ready: no
5. MVP behavior changed: no

## 2. Environment And Preconditions

The following preconditions were checked successfully:

1. repository root: E:\LTclaw2.0
2. commit hash: a527eec0a28bc96c2622bc5d6569c1c05159a8c5
3. Windows version: Microsoft Windows 11 专业版 10.0.26200 build 26200
4. console/dist exists: yes
5. working directory C:\ltclaw-data-backed exists: yes
6. operator CLI surface is present in the current working tree

Execution note:

1. the first script launch attempt was blocked by PowerShell execution policy
2. rerunning with Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned resolved that local shell issue without changing repo files

## 3. Command Shapes Executed

The dry run executed the following redacted command shapes:

1. git status --short --branch
2. git rev-parse HEAD
3. Test-Path .\console\dist
4. Test-Path C:\ltclaw-data-backed
5. Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
6. LTCLAW_RAG_API_KEY injected into the app-start shell process only
7. .\scripts\operator_deepseek_pilot.ps1
8. GET /api/agent/health
9. GET /api/agents/default/game/project/config
10. GET /api/agents/default/game/knowledge/releases/status
11. GET current project config, modify only external_provider_config in memory, then PUT full project config back
12. repeat full-config PUT for transport_enabled=false
13. repeat full-config PUT for external_provider_config=null
14. restart LTCLAW in a fresh shell without LTCLAW_RAG_API_KEY
15. final GET /api/agent/health
16. final GET /api/agents/default/game/project/config
17. final GET /api/agents/default/game/knowledge/releases/status
18. Test-Path Env:\LTCLAW_RAG_API_KEY in a fresh validation shell

The dry run did not execute any RAG answer request, did not send provider traffic, and did not perform any SVN write-path action.

## 4. Redacted Evidence

Secret gate output was boolean-only and contained no secret value:

```json
{
  "exists": true,
  "header_length_gt_env_length": true,
  "header_starts_with_bearer_sk": true,
  "length_gt_20": true,
  "starts_with_sk": true
}
```

Preflight output confirmed all required startup paths were set and existed, and the provider metadata contained only LTCLAW_RAG_API_KEY as the env var name.

Config-template output confirmed the backend-owned DeepSeek config shape and did not include any secret value.

Interpretation:

1. LTCLAW_RAG_API_KEY was present only in the app-start shell process
2. the boolean-only check stayed within the redaction rule
3. no secret value, Authorization header, or standalone api_key field was written to docs or config readback

## 5. Baseline And Final State

Baseline checks executed successfully before config mutation:

1. health status before apply: 200 with healthy runner=ready
2. project config status before apply: 200
3. release status before apply: 200
4. baseline external_provider_config: null
5. current release id before apply: win-op-r1-1778393517
6. release history count before apply: 2

Config-flow validation result:

1. first partial-body PUT attempt failed because the project-config API requires the full config body including project and svn fields
2. rerunning with GET-modify-PUT full config succeeded and preserved the existing project config surface
3. apply readback returned 200 with enabled=true, transport_enabled=true, provider_name=future_external, model_name=deepseek-chat, base_url=https://api.deepseek.com/chat/completions, env.api_key_env_var=LTCLAW_RAG_API_KEY
4. apply readback did not contain a standalone api_key field
5. disable readback returned 200 with transport_enabled=false
6. cleanup readback returned 200 with external_provider_config restored to null

Required final-state statements:

1. current release unchanged: yes, current release id remained win-op-r1-1778393517 before cleanup and after restart without secret
2. external_provider_config finally restored to null: yes
3. LTCLAW_RAG_API_KEY cleared from current validation session: yes, a fresh validation shell returned Test-Path Env:\LTCLAW_RAG_API_KEY = False
4. post-cleanup health status after restart without secret: 200
5. post-cleanup project config status after restart without secret: 200
6. post-cleanup release status after restart without secret: 200
7. MVP behavior unchanged: yes

## 6. Boundary Confirmation

This dry run did not do any of the following:

1. expose or record a real secret value
2. change Ask request schema
3. add frontend provider, model, or api_key UI
4. change RAG provider ownership
5. touch SVN sync, update, or commit paths
6. claim production rollout
7. claim production ready
8. send any real DeepSeek answer request during this dry run

## 7. Dry-Run Conclusion

P24.2 succeeded as a Windows operator dry run.

It proved all of the following within the allowed operator-only boundary:

1. env-only secret handling can be performed without printing the secret
2. secret shape check, DeepSeek preflight, and config template all produce redacted-safe output
3. baseline health, project config, and release checks pass on the pilot machine
4. backend-owned provider config apply, disable, and null cleanup all succeed when the full project config body is preserved
5. current release remains unchanged
6. final external_provider_config returns to null
7. restart without LTCLAW_RAG_API_KEY returns the app to a healthy baseline state