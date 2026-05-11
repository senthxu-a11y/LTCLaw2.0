# Lane B P23 Controlled Pilot With DeepSeek Backend Config Plan

Date: 2026-05-11
Status: planning checklist only
Scope: define a limited real-planner pilot using the verified DeepSeek backend-only provider path without opening production rollout, frontend provider selection, or Ask schema expansion

## 1. Purpose

P23 moves the work from technical provider smoke to a controlled planner workflow pilot.

The goal is to prove that a numerical designer can use the existing Knowledge/RAG and NumericWorkbench surfaces with a real backend LLM in a narrow, observable, reversible workflow.

P23 does not make the feature production ready. It does not expose provider choice to ordinary users. It does not add an API key UI.

## 2. Current Baseline

P23 starts from this baseline:

1. P0-P3 MVP is closed
2. data-backed pilot readiness passed
3. Windows operator-side pilot passed with known limitations
4. P20 backend-only real HTTP transport is complete
5. P21 backend-owned config activation and hot-reload kill switch are complete
6. P22 DeepSeek controlled real-provider smoke passed
7. DeepSeek is the current verified provider for the next controlled pilot
8. MiniMax remains blocked and is not the current pass provider
9. `LTCLAW_RAG_API_KEY` is the product env var name for the provider secret
10. `QWENPAW_RAG_API_KEY` must not be used for the provider secret in P23
11. current state remains backend-only, operator-only, not production rollout, and not production ready

## 3. Scope

P23 scope:

1. backend-only provider config
2. operator-only setup
3. DeepSeek only
4. one model only
5. Windows target machine only
6. manual env secret only
7. limited planner usage
8. enhanced receipt and monitoring
9. no production rollout
10. no production ready claim

## 4. Product Effect To Validate

P23 should validate these product effects:

1. a planner can ask grounded questions about real current-release table data
2. answers include citations and remain grounded
3. request-owned provider, model, and api_key remain ignored
4. NumericWorkbench remains draft-only
5. ordinary RAG Q&A does not write release state
6. ordinary RAG Q&A does not write formal map
7. ordinary RAG Q&A does not write test plans
8. ordinary RAG Q&A does not write workbench drafts or proposals
9. `transport_enabled=false` stops provider calls without app restart
10. `external_provider_config=null` restores baseline

## 5. Pilot Configuration

The P23 provider config should remain:

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
    "timeout_seconds": 30,
    "max_output_tokens": 512,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {
      "api_key_env_var": "LTCLAW_RAG_API_KEY"
    }
  }
}
```

Rules:

1. config stores only the env var name
2. the env var stores the secret value
3. no secret value in repo files
4. no secret value in receipts
5. no secret value in logs or screenshots
6. no `QWENPAW_RAG_API_KEY` provider-secret fallback in P23

## 6. Pilot Questions

P23 should use a small fixed scenario set. The operator may replace table or field names only if the target current release does not contain the listed item.

### Scenario 1: Table Purpose

Question:

```text
在当前 release 的知识库中，DaShenScore 表主要包含什么内容？请只根据引用片段回答，并返回 citation。
```

Pass criteria:

1. response mode is `answer`
2. at least one citation id is returned
3. answer references only current-release context
4. no secret appears

### Scenario 2: Field Meaning

Question:

```text
在当前 release 的知识库中，折算群分数 这个字段表示什么？请只根据引用片段回答，并返回 citation。
```

Pass criteria:

1. response mode is `answer`
2. at least one citation id is returned
3. answer is tied to the cited table or field
4. no unsupported external knowledge is introduced

### Scenario 3: Planner Comparison

Question:

```text
请根据当前 release 的引用片段，比较 DaShenScore 表中可见字段之间的用途差异。只回答能从 citation 支持的内容。
```

Pass criteria:

1. answer stays within cited fields
2. answer does not infer hidden formulas unless cited
3. citation ids are valid

### Scenario 4: Workbench Safety Boundary

Question:

```text
请根据当前 release 的引用片段，说明如果策划想调整一个数值字段，应该先检查哪些引用信息。不要生成发布操作。
```

Pass criteria:

1. answer gives planning guidance only
2. answer does not claim to publish or save
3. NumericWorkbench remains draft-only
4. no release, formal map, test plan, or workbench draft write occurs

### Scenario 5: Unknown Or Insufficient Context

Question:

```text
请回答当前 release 中没有引用片段支持的问题，并在没有依据时明确说明无法从当前 citation 得出结论。
```

Pass criteria:

1. answer refuses or safely limits itself when context is insufficient
2. no fabricated citation id is accepted
3. no ungrounded answer is accepted as pass

## 7. Required Monitors

Every P23 execution must record these before and after the scenario set:

1. current release id
2. release history or release list count
3. formal map stable summary or checksum
4. test plan list or count
5. workbench draft or proposal list or count
6. project config `external_provider_config`
7. kill-switch state
8. app health

If a monitoring endpoint is absent, the receipt must write `endpoint absent` and describe the substitute evidence. It must not silently mark that check as pass.

## 8. No-Write Pass Rules

No-write passes only if all of these remain unchanged after the planner scenario set:

1. current release id
2. release list or history count
3. formal map stable summary
4. test plan count
5. workbench draft or proposal count

Any unexplained change is blocked.

## 9. Kill-Switch Pass Rules

Kill switch passes only if all of these are true:

1. `transport_enabled=false` is persisted
2. GET readback confirms `transport_enabled=false`
3. next immediate ordinary RAG answer does not return a real provider success answer
4. response fails closed with safe mode and safe warnings
5. no secret appears
6. cleanup can restore `external_provider_config=null`

## 10. Stop Conditions

Stop P23 immediately if any of these occur:

1. secret appears in response
2. secret appears in receipt
3. secret appears in logs or screenshots
4. answer has no valid citation
5. answer includes invalid citation ids
6. answer uses unsupported external knowledge as if it were current-release fact
7. ordinary RAG writes release state
8. ordinary RAG writes formal map
9. ordinary RAG writes test plan
10. ordinary RAG writes workbench draft or proposal
11. kill switch fails
12. cleanup cannot restore `external_provider_config=null`
13. app cannot return to health, project config, and release status baseline

## 11. P23 Execution Slices

Recommended split:

1. P23.1 controlled pilot scenario plan and checklist
2. P23.2 Windows controlled pilot execution receipt
3. P23.3 UX and operations gap review
4. P23.4 next gate decision

## 12. P23.1 Output

This document is the P23.1 plan and checklist.

Expected follow-up:

1. Windows operator uses this checklist to run P23.2
2. P23.2 records a pass or blocked receipt
3. no production rollout happens as part of P23.2

## 13. P23.2 Receipt Template

The P23.2 receipt must include:

1. final status: pass or blocked
2. commit hash
3. Windows version
4. local project directory
5. current release id before and after
6. provider and model
7. env var name `LTCLAW_RAG_API_KEY`
8. confirmation that `QWENPAW_RAG_API_KEY` was not used for provider secret
9. scenario-by-scenario response mode
10. scenario-by-scenario citation count
11. scenario-by-scenario warnings
12. request-owned provider, model, and api_key ignored result
13. no-write result for release
14. no-write result for formal map
15. no-write result for test plans
16. no-write result for workbench drafts
17. kill-switch result
18. cleanup result
19. if blocked, exact failure step and redacted evidence
20. not production rollout
21. not production ready

## 14. P23 Not Allowed

P23 must not do any of the following:

1. production rollout
2. production ready claim
3. frontend provider selector
4. Ask schema provider, model, or api_key fields
5. API key UI
6. user-facing provider choice
7. multi-provider routing
8. `ProviderManager.active_model` ordinary RAG control
9. `SimpleModelRouter` ordinary RAG control
10. ordinary RAG writes release
11. ordinary RAG writes formal map
12. ordinary RAG writes test plan
13. ordinary RAG writes workbench draft

## 15. Next Decision After P23

If P23 passes, the next decision should be one of:

1. P24 operator startup and secret-management hardening
2. Lane E NumericWorkbench UX hardening based on planner feedback
3. Lane F production-hardening scope decision

If P23 is blocked, the next slice must address the exact blocked condition and must not broaden into production rollout.
