# Lane B P22.3 Windows Agent Execution Prompt

Date: 2026-05-11
Status: handoff prompt only
Scope: provide a strict execution prompt for the Windows test machine operator agent; this document does not mean the real provider smoke has executed

## 1. Use This Prompt Only On The Windows Test Machine

Do not execute this prompt on macOS or any non-target machine.

Use this prompt only when all of the following are true:

1. the machine is the intended Windows test machine
2. the operator has the approved real provider secret outside the repo
3. the operator has reviewed the P22 checklist and P22.2 patched runbook
4. the operator understands that this is backend-only, operator-only, single provider, single model, manual env secret, and stop on first failure

## 2. Strict Execution Prompt

```text
接手 Windows 测试机，执行 P22.3 Controlled Real Provider Smoke。严格按 runbook 执行，backend-only、operator-only、single provider、single model、manual env secret，stop on first failure。

前置：
1. 确认在 Windows 测试机。
2. git checkout main
3. git pull origin main
4. git status --short --branch 必须干净。
5. 确认存在并阅读：
   - docs/tasks/post-mvp/lane-b-p22-controlled-real-provider-smoke-checklist-2026-05-11.md
   - docs/tasks/post-mvp/lane-b-p22-1-source-config-review-2026-05-11.md
   - docs/tasks/post-mvp/lane-b-p22-2-controlled-real-provider-smoke-runbook-2026-05-11.md
   - docs/tasks/post-mvp/lane-b-p22-2a-no-write-operator-check-patch-2026-05-11.md
   - docs/tasks/post-mvp/lane-b-p22-2-runbook-review-go-no-go-2026-05-11.md
6. 不改 src、console/src、tests。
7. 不改 Ask schema。
8. 不改 frontend provider UI。
9. 不接 ProviderManager.active_model。
10. 不接 SimpleModelRouter。
11. 不做 production rollout。
12. 不写真实 API key 到任何文件。

本轮目标：
执行一次真实 provider smoke，只验证 backend-owned config -> real provider -> grounded answer -> kill switch -> cleanup。
如果任一步失败，立即停止，写 blocked receipt，并清理。

执行边界：
1. single provider
2. single model
3. single Windows machine
4. one low-risk grounded prompt
5. manual env secret only
6. config only stores env var name
7. no API key UI
8. no frontend selector
9. no production ready claim

运行准备：
1. 设置真实 provider secret 只在当前进程环境变量中。
2. 启动 LTCLaw：
   QWENPAW_WORKING_DIR=C:\ltclaw-data-backed
   QWENPAW_CONSOLE_STATIC_DIR=E:\LTclaw2.0\console\dist
   <PROVIDER_SECRET_ENV_VAR>=<real secret value, do not print>
   ltclaw.exe app --host 127.0.0.1 --port 8092
3. 不要把真实 secret value 输出到终端、receipt、日志摘录或 git diff。

Baseline checks：
1. GET /api/agent/health -> 200
2. GET /api/agents/default/game/project/config -> 200
3. GET /api/agents/default/game/knowledge/releases/status -> 200
4. current release id exists
5. external_provider_config is null before run
6. record local project directory
7. record commit hash

No-write baseline snapshot：
在 real provider answer 前记录：
1. release status current release id
2. release list/history count
3. formal map summary/checksum or stable fields
4. test plans list/count
5. workbench drafts/proposals list/count
如果某个 endpoint 不存在，记录 endpoint absent，不要静默 pass。

Save backend-owned config：
通过 project config API 保存 external_provider_config：
enabled=true
transport_enabled=true
provider_name=future_external
model_name=<single backend-owned real model>
allowed_providers=["future_external"]
allowed_models=["<same backend-owned real model>"]
base_url=<backend-owned provider endpoint>
timeout_seconds=<bounded timeout>
max_output_tokens=<bounded output>
max_prompt_chars=<bounded prompt>
max_output_chars=<bounded response>
env.api_key_env_var=<PROVIDER_SECRET_ENV_VAR name only>

要求：
1. config 中不得出现真实 API key value。
2. GET readback 不得出现真实 API key value。
3. readback 必须保留 backend-owned fields。

Positive real provider smoke：
POST /api/agents/default/game/knowledge/rag/answer
使用一个低风险 grounded prompt：
- 必须基于 current release 已索引内容
- 不要求外部知识
- 不要求生成代码
- 不要求 secret
- 结果可由 citation 验证

同时发送 request-owned negative fields：
provider=request-provider
model=request-model
api_key=request-owned-negative-field

期望：
1. HTTP 200
2. answer is grounded
3. citation ids valid
4. warnings safe
5. request-owned provider/model/api_key ignored
6. no secret appears in response
7. no raw provider error appears in response

No-write after snapshot：
real provider answer 后再次记录：
1. release status current release id
2. release list/history count
3. formal map summary/checksum or stable fields
4. test plans list/count
5. workbench drafts/proposals list/count

No-write pass rule：
1. current release id unchanged
2. release list/history count unchanged
3. formal map unchanged
4. test plan count unchanged
5. workbench draft/proposal count unchanged
如果任一项变化，P22.3 blocked，立即 stop and cleanup。

Kill switch check：
1. PUT project config with transport_enabled=false
2. GET readback confirms transport_enabled=false
3. Immediately POST same RAG answer again without restart
4. Expected:
   - no real provider call should occur
   - response safe fallback / safe warning
   - no secret leak
如果 kill switch fails，P22.3 blocked，立即 cleanup。

Cleanup:
1. PUT external_provider_config=null
2. clear real provider env secret from process/session
3. restart LTCLaw without secret
4. verify:
   - health 200
   - project config 200
   - external_provider_config null
   - release status 200
   - current release id unchanged

Receipt:
新增：
docs/tasks/post-mvp/lane-b-p22-3-windows-real-provider-smoke-receipt-2026-05-11.md

Receipt 必须写：
1. final status: pass or blocked
2. Windows version
3. commit hash
4. app startup command with env var name only
5. local project directory
6. current release id before and after
7. provider name
8. model name
9. config readback result
10. whether any secret appeared anywhere
11. response mode
12. citation ids
13. warnings
14. request-owned provider/model/api_key ignored result
15. release no-write result
16. formal map no-write result
17. test plan no-write result
18. workbench draft no-write result
19. kill switch result
20. cleanup result
21. if blocked, exact failure step and redacted evidence

收尾验证：
1. git diff --check
2. receipt NUL check
3. keyword boundary review：
不得把 production rollout、production ready、frontend provider selector、Ask schema provider/model/api_key、ProviderManager.active_model、SimpleModelRouter、ordinary RAG writes release、test plans enter formal knowledge by default 写成已完成。
允许写 P22.3 real provider smoke pass/blocked，但必须同时写 not production rollout and not production ready。

完成后汇报：
1. P22.3 final status: pass or blocked
2. commit hash
3. provider/model name
4. response mode/citations/warnings
5. no-write 四类 state 是否全部 pass
6. kill switch 是否 pass
7. cleanup 是否 pass
8. receipt 路径
9. diff / NUL / keyword review 结果
```

## 3. Current Reality

This workspace session has not executed P22.3.

Current constraints:

1. current machine is not confirmed as the target Windows test machine
2. no real provider secret is available through this workspace session
3. no real provider smoke has been run from this session
4. no P22.3 receipt has been produced from this session

## 4. Handoff Decision

Handoff decision:

1. this document is ready to hand to the Windows operator agent
2. P22.3 must be executed only on the target Windows machine
3. any pass or blocked result must come from that Windows execution, not from this macOS workspace session
4. this does not mean production rollout
5. this does not mean production ready status