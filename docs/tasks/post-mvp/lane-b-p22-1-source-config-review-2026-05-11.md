# Lane B P22.1 Source And Config Review

Date: 2026-05-11
Status: docs-only review
Scope: reconfirm the current backend-owned config, secret, provider-selection, transport, redaction, grounding, and no-write boundaries before any controlled real-provider smoke is planned further

## 1. Review Decision

Current decision:

1. current source state still satisfies the P22 source/config preconditions for a planned backend-only real provider smoke
2. current source state does not justify production rollout
3. current source state does not justify production ready status
4. P22.2 operator runbook should proceed next
5. P22.3 real provider smoke must remain blocked until the operator-side prerequisites in this review are written and available

This review is limited to source and config boundaries. It does not execute a real provider call.

## 2. Sources Reviewed

Reviewed docs:

1. docs/tasks/post-mvp/lane-b-p22-controlled-real-provider-smoke-checklist-2026-05-11.md
2. docs/tasks/post-mvp/lane-b-p21-11-lane-b-closeout-next-gate-decision-2026-05-11.md
3. docs/tasks/post-mvp/lane-b-p21-10-windows-kill-switch-rerun-receipt-2026-05-11.md
4. docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-checklist-2026-05-10.md

Reviewed source:

1. src/ltclaw_gy_x/game/config.py
2. src/ltclaw_gy_x/game/service.py
3. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
4. src/ltclaw_gy_x/game/knowledge_rag_answer.py
5. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
6. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
7. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
8. src/ltclaw_gy_x/app/routers/game_project.py

## 3. Source Findings

### 3.1 Backend-Owned Config Still Exists

Confirmed:

1. ProjectConfig.external_provider_config is still a backend-owned typed config field in src/ltclaw_gy_x/game/config.py at lines 145 through 156
2. the nested env metadata is still typed through ExternalProviderEnvProjectConfig in src/ltclaw_gy_x/game/config.py at lines 118 through 123
3. the persisted external provider shape is still typed through ExternalProviderProjectConfig in src/ltclaw_gy_x/game/config.py at lines 126 through 143
4. GameProject config read and write still use ProjectConfig as the typed API contract in src/ltclaw_gy_x/app/routers/game_project.py at lines 32 and 38

Conclusion:

1. the controlled real-provider shape remains backend-owned and typed
2. there is no new frontend-owned or request-owned config authority in the reviewed path

### 3.2 Config Still Stores Env Var Name, Not Secret Value

Confirmed:

1. the only external-provider secret metadata field in reviewed config is env.api_key_env_var in src/ltclaw_gy_x/game/config.py at lines 118 through 123
2. ExternalRagModelEnvCredentialResolver still resolves the API key by reading os.environ using that env var name in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 107 through 129
3. the external transport boundary still receives a resolved credentials object and does not persist that value back into project config

Conclusion:

1. config must continue to store only the env var name
2. config must not contain an API key value

### 3.3 GameService Config Bridge Still Returns Project Config

Confirmed:

1. GameService.project_config still returns the loaded project config in src/ltclaw_gy_x/game/service.py at lines 134 through 135
2. GameService.config still returns project_config in src/ltclaw_gy_x/game/service.py at lines 138 through 139

Conclusion:

1. the ordinary RAG path still reads backend-owned project config through the service bridge

### 3.4 Provider Selection Still Resolves From Backend-Owned Config

Confirmed:

1. build_rag_answer_with_provider resolves provider_name through resolve_rag_model_provider_name and resolves external_config through resolve_external_rag_model_client_config in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 124 through 128
2. provider selection walks only configured fields and nested config objects, including external_provider_config, in src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py at lines 14 through 20, 27 through 47, and 94 through 99
3. the model registry still allows future_external only through the backend-owned ExternalRagModelClientConfig object in src/ltclaw_gy_x/game/knowledge_rag_model_registry.py at lines 18 through 21 and 98 through 106
4. ExternalRagModelClient still validates provider_name and model_name against backend-owned allowed_providers and allowed_models in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 321 through 334

Conclusion:

1. provider and model selection are still backend-owned
2. the runtime path still depends on backend config, not on request or router ownership

### 3.5 Request-Owned Provider, Model, And Api Key Still Do Not Control Selection

Confirmed:

1. the public Ask schema in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 26 through 29 still exposes only query, max_chunks, and max_chars
2. the answer router calls build_rag_answer_with_service_config with body.query and the settled context only in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 136 through 145
3. no reviewed router field or answer-path argument passes request-owned provider, model, or api_key into provider selection

Conclusion:

1. request-owned provider, model, and api_key still do not participate in ordinary RAG provider selection
2. P22.2 may still include a negative test that sends extra request fields and confirms they are ignored by the backend path

### 3.6 External Client Still Uses Httpx, Trust Env False, Backend-Owned Base Url, And Backend-Owned Model

Confirmed:

1. the real transport implementation uses httpx.Client in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 233 through 242 and 723 through 729
2. the transport client is created with trust_env=False in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at line 726
3. the outbound request body uses config.model_name as the model field in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at line 524
4. the effective endpoint resolves from backend-owned credentials.endpoint or backend-owned config.base_url in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at line 720

Conclusion:

1. transport remains backend-owned and proxy inheritance from host env is disabled by default
2. model and endpoint are still backend-owned inputs

### 3.7 Authorization Still Exists Only At The Transport Boundary

Confirmed:

1. Authorization is assembled only inside ExternalRagModelHttpTransport.__call__ in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at line 229
2. the request preview explicitly reports includes_authorization_header=false in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at line 200
3. outbound request preview exposes only boolean credential presence metadata and redacted endpoint metadata in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 537 through 544

Conclusion:

1. Authorization remains transport-boundary-only
2. the reviewed path does not surface the raw secret or Authorization header in ordinary output

### 3.8 Endpoint, Proxy, Error, And Warning Redaction Still Holds

Confirmed:

1. endpoint and proxy previews pass through _redact_transport_locator in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 539 through 540 and 738 through 753
2. provider transport exceptions map to fixed safe warnings through _warning_for_error_code in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 699 through 712
3. ordinary warning output does not expose provider raw exception text in the reviewed transport path

Conclusion:

1. redaction and safe warning mapping still exist for the operator-visible ordinary RAG path

### 3.9 Response Still Goes Through Normalize, Grounding, And Citation Validation

Confirmed:

1. ExternalRagModelClient.generate_answer still normalizes the model response through _normalize_response in src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py at lines 304 through 305 and 410 through 434
2. grounded context is still collected before model usage in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 56 through 67 and 227 through 261
3. model citation ids are still validated against provided grounded citations in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 189 through 224 and 343 through 360

Conclusion:

1. the answer path still preserves normalization, grounding, and citation validation after transport returns

### 3.10 No Current Release And Insufficient Context Still Short-Circuit Before Provider Path

Confirmed:

1. build_rag_answer returns immediately on no_current_release in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 47 through 54
2. build_rag_answer_with_provider returns immediately on no_current_release in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 106 through 107
3. build_rag_answer_with_provider returns insufficient_context before provider selection when there are no grounded chunks in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 109 through 117
4. provider selection happens only after those guards in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 124 through 128

Conclusion:

1. no_current_release and insufficient_context still do not initialize the provider path

### 3.11 Generation Barrier And Kill Switch Coverage Still Exists For Hot Reload

Confirmed:

1. the RAG router settles config generation before answer execution in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 91 through 103 and 136 through 152
2. repeated config churn fails closed with a settling warning in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 21 through 22 and 106 through 113
3. build_rag_answer_with_provider asserts expected_generation before provider selection in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 119 through 123 and 156 through 166
4. GameService.reload_config still increments config_generation after reload in src/ltclaw_gy_x/game/service.py at lines 337 through 370

Conclusion:

1. the transport-sensitive generation barrier and hot-reload kill-switch protection remain present in the reviewed source path

### 3.12 Ordinary RAG Still No-Write

Confirmed:

1. the reviewed ordinary RAG router only builds current-release context and returns an answer payload in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 84 through 161
2. the reviewed ordinary RAG answer path only reads grounded context, selects a model client, and validates citations in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 97 through 224
3. no reviewed ordinary RAG path writes release, formal map, test plan, or workbench draft state

Conclusion:

1. ordinary RAG remains no-write in the reviewed path

### 3.13 ProviderManager.active_model And SimpleModelRouter Still Do Not Control Ordinary RAG Provider Selection

Confirmed:

1. SimpleModelRouter remains defined in src/ltclaw_gy_x/game/service.py at lines 37 through 102 and is still built through ProviderManager only inside GameService._model_router at lines 214 through 221
2. the ordinary RAG router uses build_rag_answer_with_service_config, not SimpleModelRouter, in src/ltclaw_gy_x/app/routers/game_knowledge_rag.py at lines 136 through 145
3. the ordinary RAG answer path resolves provider selection through resolve_rag_model_provider_name and resolve_external_rag_model_client_config, not through ProviderManager.active_model or SimpleModelRouter, in src/ltclaw_gy_x/game/knowledge_rag_answer.py at lines 124 through 128

Conclusion:

1. ProviderManager.active_model still does not control ordinary RAG provider selection
2. SimpleModelRouter is still not connected to the ordinary RAG provider path

## 4. P22.2 Recommended Minimal Config Shape

P22.2 should use the smallest backend-owned shape that matches current source:

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

Rules:

1. enabled must be true only for the planned smoke window
2. transport_enabled must be true only for the planned smoke window
3. provider_name must stay future_external for the reviewed path
4. model_name must be one backend-owned model only
5. allowed_providers must contain only future_external
6. allowed_models must contain only the same backend-owned model
7. base_url must be backend-owned and operator-set through project config
8. timeout_seconds must stay bounded
9. max_output_tokens must stay bounded
10. max_prompt_chars must stay bounded
11. max_output_chars must stay bounded
12. env.api_key_env_var must contain only the env var name
13. config must not contain any API key value

## 5. Explicit Prohibitions To Preserve In P22.2

P22.2 must explicitly preserve all of the following:

1. do not write API key value into config
2. do not write API key value into docs, receipts, tasks, tests, fixtures, logs, or outputs
3. do not let request, frontend, or router control provider
4. do not let request, frontend, or router control model
5. do not let request, frontend, or router control api_key
6. do not let ProviderManager.active_model control ordinary RAG provider selection
7. do not let SimpleModelRouter control ordinary RAG provider selection
8. do not add Ask request fields for provider, model, or api_key
9. do not add API key UI
10. do not treat this work as production rollout
11. do not treat this work as production ready

## 6. Blocking Conditions Before Any Real Provider Smoke

The following must exist before P22.3 can start:

1. rollback checklist
2. secret handling checklist
3. low-risk grounded prompt that is already supported by indexed current-release content
4. baseline current release confirmation on the exact Windows target machine
5. cleanup path that restores external_provider_config=null
6. health check confirmation after cleanup
7. project config readback confirmation after cleanup
8. release status confirmation after cleanup
9. approved provider account and approved single model outside the repo
10. manual env secret handling steps that do not persist the secret into repo state

Current status from this review:

1. source/config boundaries are ready for P22.2 planning
2. operator execution prerequisites are not yet fully codified in a single runbook document
3. real provider smoke should remain blocked until P22.2 fills those operator gaps

## 7. Exact Command Gaps P22.2 Must Fill

P22.2 should define exact Windows commands for all of the following:

1. repository baseline commands
2. app startup command with manual env secret for the smoke process only
3. health check command
4. project config readback command
5. release status readback command
6. current release id check command
7. PUT command that saves the minimal external_provider_config shape
8. GET command that confirms readback preserves shape and does not echo secret
9. POST answer command for one low-risk grounded prompt
10. negative-test POST answer command that includes request-owned provider, model, and api_key fields and confirms they are ignored
11. PUT command that flips transport_enabled=false without restart
12. verification command that confirms no subsequent real-provider traffic
13. PUT command that restores external_provider_config=null
14. secret cleanup command that clears the env var from the session or process scope
15. restart command without secret present
16. final health, config, and release status confirmation commands

P22.2 should also define exact redacted receipt fields for:

1. commit hash
2. Windows OS version
3. startup command shape without secret value
4. config readback without secret value
5. response mode and citation outcome
6. kill-switch result
7. cleanup result

## 8. Recommendation

Recommendation:

1. proceed to P22.2 operator runbook now
2. do not execute P22.3 real provider smoke yet
3. keep the next step backend-only, operator-only, single provider, single model, single Windows machine, and manual env secret only

## 9. Final Conclusion

Final conclusion in one sentence:

1. the current reviewed source still preserves the backend-owned config and provider boundary required by the P22 checklist, so P22.2 should begin as docs-only runbook work, while any real provider smoke remains blocked pending explicit rollback, secret-handling, low-risk prompt, baseline, and cleanup execution steps