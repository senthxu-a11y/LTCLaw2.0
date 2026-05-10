# Lane B P20.1 Real Transport Implementation Plan

Date: 2026-05-10
Status: docs-only implementation plan
Scope: freeze the next backend-only transport slices without changing accepted MVP behavior

## 1. Overall Result

This round is P20.1 docs-only implementation planning.

Implementation status in this round:

1. No source code changes.
2. No frontend changes.
3. No test changes.
4. P20 real HTTP transport is still not implemented.
5. Production provider rollout is still not implemented.
6. Current state remains MVP complete, data-backed pilot readiness pass, Mac and Windows operator-side pilot pass with known limitations, pilot usable, and not production ready.

Planning result:

1. The minimal provider identifier should remain future_external.
2. The preferred HTTP client for the first transport path should be the existing httpx dependency, not a new dependency.
3. The next recommended slice should be P20.2 Transport Contract Hardening before P20.3 Backend-Only Real HTTP Transport Implementation.

Reason for choosing P20.2 first:

1. The current external client already has a redacted preview helper and response normalization helper.
2. The current code still does not have a dedicated outbound request builder for real HTTP.
3. The current code still does not have a dedicated safe response parser for provider JSON.
4. The current code still does not have an explicit HTTP exception mapping layer for connect, DNS, TLS, and malformed provider body handling.
5. Freezing those helpers first reduces implementation ambiguity without widening router, request, or frontend scope.

## 2. Source Baseline From P20.0

P20.0 reconfirmed these source facts and this plan keeps them unchanged:

1. Gate order remains enabled gate, transport_enabled gate, payload normalization, allowlist validation, credential resolution, transport invocation, response normalization.
2. enabled=False and transport_enabled=False still short-circuit before payload normalization.
3. Allowlist failure still blocks before credential resolution and transport.
4. Env credential ownership remains backend-owned through ExternalRagModelEnvConfig.api_key_env_var plus backend env lookup.
5. The default transport remains a non-network safe-failure skeleton.
6. Router still does not own provider selection.
7. Ask request schema still remains query, max_chunks, and max_chars only.
8. Request body provider, model, and api_key fields still do not participate in provider selection.
9. Frontend still has no GameProject RAG provider or API-key UI in the reviewed path.
10. ProviderManager.active_model still does not control the current RAG provider path.
11. SimpleModelRouter still does not control the current RAG provider path.
12. no_current_release and insufficient_context still return before provider initialization.
13. candidate_evidence still does not automatically enter the provider prompt.

## 3. Proposed Provider Identifier

The next implementation slices should continue using future_external as the minimal backend-only external provider identifier.

Reasoning:

1. future_external is already the current backend-owned identifier on the RAG external-provider path.
2. future_external is already present in the registry supported provider set.
3. future_external already requires backend-owned external_provider_config before registry construction succeeds.
4. Reusing future_external avoids unnecessary registry churn in P20.2 or P20.3.

Rules for this identifier:

1. Do not add a new frontend provider option.
2. Do not add a request provider field.
3. Do not add a second runtime provider in P20.2 or P20.3.
4. Provider identifier must continue to come only from backend-owned config or the existing registry path.
5. Request-owned provider, model, or api_key fields must remain ignored.

## 4. Proposed Config Shape

P20.3 should keep the current backend-owned config object centered on ExternalRagModelClientConfig and extend it only where the real HTTP path truly needs more explicit metadata.

Recommended shape:

```python
ExternalRagModelClientConfig(
    provider_name='future_external',
    model_name='backend-owned-model-id',
    enabled=False,
    transport_enabled=False,
    allowed_providers=('future_external',),
    allowed_models=('backend-owned-model-id',),
    env=ExternalRagModelEnvConfig(api_key_env_var='QWENPAW_RAG_API_KEY'),
    base_url='https://provider.example/v1/chat/completions',
    timeout_seconds=15.0,
    max_output_tokens=512,
    max_prompt_chars=12000,
    max_output_chars=2000,
    proxy=None,
)
```

Field decisions:

1. provider_name: keep existing field and require future_external.
2. model_name: keep existing field and treat it as backend-owned model selection.
3. enabled: keep existing adapter kill switch.
4. transport_enabled: keep existing transport plus credential kill switch.
5. allowed_providers: keep existing allowlist gate.
6. allowed_models: keep existing allowlist gate.
7. env.api_key_env_var: keep existing backend-owned env var metadata source.
8. base_url: keep existing field and use it as the backend-owned HTTP endpoint.
9. timeout_seconds: keep existing field as the outbound request timeout.
10. max_output_chars: reuse the existing field as the effective response-size cap instead of adding a parallel max_response_chars field.
11. max_output_tokens: keep existing field for provider request shaping when the upstream contract supports it.
12. proxy: keep existing field but do not allow implicit environment-proxy ownership for this path.

Not recommended for the first implementation:

1. No request-owned config.
2. No frontend-owned config.
3. No config-file secret values in docs examples.
4. No secret-store integration.
5. No admin credential UI.
6. No custom outbound headers field in P20.3 unless P20.2 proves a provider contract cannot work without one.

Documentation and storage rules:

1. Config examples may contain env var name placeholders only.
2. API key values must not appear in docs examples.
3. This config must not be sourced from request body.
4. This config must not be sourced from frontend.
5. This config must not be copied into formal map, release, snapshot, export, docs fixtures, or task fixtures.

## 5. HTTP Client Choice

Recommended HTTP implementation for the first real transport path:

1. Use the existing httpx dependency.
2. Do not add requests.
3. Do not add a new SDK dependency.
4. Do not install dependencies in P20.1.

Repository evidence:

1. pyproject.toml already declares httpx>=0.27.0.
2. The repository already uses httpx in multiple Python modules.
3. Existing repository test surfaces already include httpx-based mocking patterns.

Why httpx is preferred over stdlib urllib.request here:

1. The dependency already exists, so there is no package-scope widening.
2. httpx gives explicit exception types for timeout, connect, protocol, and HTTP status handling.
3. httpx fits the current synchronous ExternalRagModelClient.generate_answer(...) call surface without introducing async plumbing.
4. httpx makes header, JSON body, timeout, and response handling easier to harden than stdlib urllib.request.

Recommended P20.3 usage shape:

1. Use synchronous httpx for this path.
2. Use trust_env=False so ambient proxy environment variables do not silently control the RAG path.
3. Use the backend-owned timeout_seconds field.
4. Build Authorization only inside the HTTP call helper.
5. Treat proxy as backend-owned config only if explicitly set.

## 6. Request Payload Contract

P20.2 should freeze a dedicated outbound request builder. P20.3 should then use only that helper.

Transport input contract into the HTTP helper:

1. Input remains the normalized RagAnswerPromptPayload produced after the existing gates.
2. Provider and model selection remain backend-owned config fields.
3. Credentials remain a separate backend-owned object and do not enter the payload body.

Outbound provider payload contract for the first implementation:

1. Build exactly one outbound user message from the normalized prompt payload.
2. Message content must be derived only from query, grounded chunks, grounded citations, release_id, built_at, and policy_hints.
3. The rendered prompt must instruct the provider to return JSON with answer and citation_ids only.
4. The outbound JSON body may include backend-owned model_name.
5. The outbound JSON body may include backend-owned max_output_tokens when configured.
6. The outbound JSON body must not include api_key.
7. The outbound JSON body must not include the credential object.
8. The outbound JSON body must not include Authorization header material.
9. The outbound JSON body must not include request body provider, model, or api_key fields.
10. The outbound JSON body must not include raw release artifacts.
11. The outbound JSON body must not include raw files.
12. The outbound JSON body must not include docs or tasks content.
13. The outbound JSON body must not include candidate_evidence unless a later independent review explicitly authorizes it.

Recommended first transport body shape:

```json
{
  "model": "backend-owned-model-id",
  "messages": [
    {
      "role": "user",
      "content": "backend-rendered grounded prompt"
    }
  ],
  "temperature": 0,
  "max_tokens": 512
}
```

This keeps the first transport contract close to the current skeleton preview shape, which already assumes one outbound message.

## 7. Response Contract

P20.2 should freeze a dedicated safe response parser before any real HTTP call ships.

Internal mapping that the transport helper must produce before _normalize_response(...):

```python
{
    'answer': 'non-empty answer text or empty string',
    'citation_ids': ['citation-001', 'citation-002'],
    'warnings': [],
}
```

Supported minimum contract for the first implementation:

1. Provider HTTP response body must be valid JSON.
2. The adapter must extract one text completion from the provider response.
3. That extracted text must itself be parseable into a JSON object with answer and citation_ids.
4. warnings should default to an empty list unless the adapter itself adds a fixed safe warning.
5. usage metadata may be parsed internally for future debugging but must not enter the user response in P20.3.

Response safety rules:

1. Provider output must still pass through _normalize_response(...).
2. Malformed JSON must safe-fail before raw provider content reaches ordinary users.
3. Unsupported response shape must safe-fail before raw provider content reaches ordinary users.
4. Empty answer should not be treated as a successful user-facing answer.
5. Missing citation_ids should not bypass grounding.
6. Out-of-range citation ids should not bypass grounding.
7. Provider raw response must not be returned directly.

Recommended behavior split:

1. If the adapter cannot build the internal mapping at all, return the invalid-response warning path.
2. If the adapter builds the internal mapping but answer text is empty, P20.2 should harden this into the invalid-response warning path rather than silently passing a blank transport success.
3. If answer text exists but citation_ids are missing or out of range, allow the answer layer to downgrade through its existing grounding logic.

## 8. Error Mapping

P20.2 should freeze explicit error mapping helpers, and P20.3 should use only those helpers.

Recommended mapping rules:

1. timeout -> External provider adapter skeleton timed out.
2. connection error -> External provider adapter skeleton request failed.
3. DNS error -> External provider adapter skeleton request failed.
4. TLS error -> External provider adapter skeleton request failed.
5. proxy connection failure -> External provider adapter skeleton request failed.
6. non-2xx HTTP status -> External provider adapter skeleton HTTP error.
7. malformed JSON response body -> External provider adapter skeleton returned an invalid response.
8. unsupported response shape -> External provider adapter skeleton returned an invalid response.
9. empty answer after parse -> External provider adapter skeleton returned an invalid response.
10. missing credential -> External provider adapter skeleton is not configured.
11. disallowed provider -> External provider adapter skeleton provider is not allowed.
12. disallowed model -> External provider adapter skeleton model is not allowed.
13. missing allowed_providers -> External provider adapter skeleton provider is not allowed.
14. missing allowed_models -> External provider adapter skeleton model is not allowed.
15. resolver exception -> External provider adapter skeleton is not configured.

Additional rules:

1. Do not expose endpoint query strings.
2. Do not expose Authorization header values.
3. Do not expose API key values.
4. Do not expose raw provider error text to ordinary users.
5. Do not silently fall back to another real provider.
6. Do not silently fall back to ProviderManager, SimpleModelRouter, or secret_store.

## 9. Redaction / DLP Plan

P20.2 and P20.3 must preserve the existing DLP posture and extend it to the real HTTP path.

Required redaction rules:

1. API key value must never enter logs.
2. API key value must never enter warnings.
3. API key value must never enter errors.
4. API key value must never enter fixtures.
5. API key value must never enter docs.
6. API key value must never enter tasks.
7. API key value must never enter release artifacts.
8. API key value must never enter formal map.
9. API key value must never enter snapshot.
10. API key value must never enter export artifacts.
11. API key value must never enter prompt payload.
12. Authorization header must never be recorded.
13. endpoint query string must always be redacted.
14. proxy query string must always be redacted.
15. provider raw response should not be logged by default.
16. provider raw error should not be logged by default.
17. tests must use placeholder secrets only.
18. git diff must not contain any real secret.
19. touched-file NUL check remains mandatory.

Implementation guidance:

1. Reuse the existing URL redaction pattern already present in the skeleton preview helper.
2. Keep Authorization header creation inside the HTTP helper only.
3. Keep secret-like values out of assertion text and fixture payloads.
4. If a failure path needs diagnostics, log only redacted endpoint shape plus safe warning class.

## 10. Gate And Kill Switch Plan

The current gate model should remain the only authority for opening or closing the real transport path.

Required behavior:

1. enabled=False remains the adapter kill switch.
2. transport_enabled=False remains the transport plus credential kill switch.
3. payload normalization still occurs only when both gates are open.
4. missing allowlist still blocks before resolver.
5. allowlist failure still blocks before resolver.
6. allowlist failure still blocks before HTTP.
7. missing env credential still blocks before HTTP.
8. blank env credential still blocks before HTTP.
9. resolver exception still blocks before HTTP.
10. config rollback by setting enabled=False or transport_enabled=False must immediately disable real transport.
11. no_current_release must still avoid provider initialization.
12. insufficient_context must still avoid provider initialization.

## 11. Minimal Implementation Surface For P20.3

Allowed files for the next code slices:

1. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_external_model_client.py
3. Only if required for boundary regression:
4. tests/unit/game/test_knowledge_rag_answer.py
5. tests/unit/game/test_knowledge_rag_provider_selection.py
6. tests/unit/game/test_knowledge_rag_model_registry.py
7. tests/unit/routers/test_game_knowledge_rag_router.py
8. docs/tasks/post-mvp/lane-b-p20-2-transport-contract-hardening-closeout-2026-05-10.md
9. docs/tasks/post-mvp/lane-b-p20-3-real-http-transport-closeout-2026-05-10.md

Explicitly forbidden:

1. console/src/**
2. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py schema changes
3. ProviderManager
4. SimpleModelRouter
5. secret_store
6. admin UI
7. frontend provider selector
8. Ask request schema expansion
9. production rollout work

## 12. Test Matrix

P20.2 and P20.3 together must cover at least the following focused tests:

1. default config does not send HTTP.
2. enabled=False does not normalize, does not resolve credentials, and does not transport.
3. transport_enabled=False does not normalize, does not resolve credentials, and does not transport.
4. missing allowed_providers blocks before resolver and HTTP.
5. missing allowed_models blocks before resolver and HTTP.
6. disallowed provider blocks before resolver and HTTP.
7. disallowed model blocks before resolver and HTTP.
8. missing credential blocks before HTTP.
9. resolver exception safe-fails without raw exception leak.
10. fake HTTP success returns normalized mapping.
11. fake HTTP timeout maps to the timed-out warning.
12. fake HTTP non-2xx maps to the HTTP-error warning.
13. malformed JSON maps to the invalid-response warning.
14. unsupported response shape maps to the invalid-response warning.
15. empty answer maps to the invalid-response warning after P20.2 hardening.
16. secret-like values do not appear in warnings, errors, preview output, fixture text, or assertion text.
17. request-like provider, model, and api_key fields remain ignored.
18. router Ask schema remains unchanged.
19. no_current_release does not initialize provider.
20. insufficient_context does not initialize provider.
21. deterministic_mock regression still passes.
22. disabled regression still passes.

Focused files to keep as the main validation suite:

1. tests/unit/game/test_knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_answer.py
3. tests/unit/game/test_knowledge_rag_provider_selection.py
4. tests/unit/game/test_knowledge_rag_model_registry.py
5. tests/unit/routers/test_game_knowledge_rag_router.py

## 13. P20.2 vs P20.3 Decision

Decision:

1. The next slice should be P20.2 Transport Contract Hardening.

Why P20.2 is needed first:

1. The current build_request_preview(...) helper is useful for redaction preview but is not yet the actual outbound request builder.
2. The current code has no dedicated helper that renders the normalized prompt payload into a fixed outbound provider message contract.
3. The current code has no dedicated helper that parses provider HTTP JSON into the internal answer and citation_ids mapping.
4. The current code has no explicit helper that maps connect, DNS, TLS, malformed body, and unsupported shape into the fixed safe warning set.
5. The current code currently treats transport TypeError as invalid response, but that is not yet explicit enough for real provider body parsing.
6. Hardening those seams first keeps P20.3 smaller, more testable, and less likely to blur transport failure with answer-layer grounding failure.

P20.3 should follow immediately after P20.2 if P20.2 lands cleanly.

## 14. Prompt Seed For Next Agent

Recommended next-agent prompt for P20.2:

```text
接手当前仓库，只执行 Lane B / P20.2 Transport Contract Hardening。

先阅读：
1. docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md
2. docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-2026-05-10.md
3. docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-checklist-2026-05-10.md
4. docs/tasks/post-mvp/lane-b-p20-0-source-baseline-review-2026-05-10.md
5. docs/tasks/post-mvp/lane-b-p20-1-real-transport-implementation-plan-2026-05-10.md
6. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-19-real-http-transport-governance-implementation-plan-2026-05-09.md

只允许修改：
1. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_external_model_client.py
3. 如确有必要才窄改：
   - tests/unit/game/test_knowledge_rag_answer.py
   - tests/unit/game/test_knowledge_rag_provider_selection.py
   - tests/unit/game/test_knowledge_rag_model_registry.py
   - tests/unit/routers/test_game_knowledge_rag_router.py
4. docs/tasks/post-mvp/lane-b-p20-2-transport-contract-hardening-closeout-2026-05-10.md

目标：
1. 不接真实 HTTP。
2. 不接真实 provider。
3. 新增或固化 dedicated request builder、redacted endpoint helper、safe response parser、explicit warning mapper。
4. 继续保持 gate order、allowlist、backend-owned env credential、router/request/frontend 边界不变。
5. 继续保持 no_current_release / insufficient_context 不初始化 provider。

必须保持：
1. 不改 Ask schema。
2. 不改 frontend provider UI。
3. 不让 router 选择 provider。
4. 不接 ProviderManager.active_model。
5. 不接 SimpleModelRouter。
6. 不接 secret_store。
7. 不做 production rollout。

测试至少覆盖：
1. disabled / not-connected 仍在 normalize 前短路。
2. allowlist failure 仍在 resolver / transport 前阻断。
3. request preview / request builder 不含 api_key / Authorization / request-owned provider/model/api_key。
4. endpoint query string redaction。
5. malformed provider body -> invalid response warning。
6. unsupported response shape -> invalid response warning。
7. empty answer -> invalid response warning。
8. timeout / HTTP error / generic request failure warning mapping。
9. focused five-file RAG suite regression。

完成后执行：
1. focused pytest
2. git diff --check
3. touched Python/docs NUL check
4. keyword boundary review

closeout 必须明确：
1. 这是 contract hardening，不是 real provider rollout。
2. Ask schema、frontend、router authority、ProviderManager、SimpleModelRouter 仍未变化。
3. 当前仍 not production ready。
```

## Validation

This round is docs-only planning.

This round does not:

1. change source code
2. change frontend
3. change tests
4. run pytest
5. run TypeScript
6. connect real HTTP
7. connect a real provider
8. connect a real LLM
9. expand Ask schema
10. connect ProviderManager.active_model
11. connect SimpleModelRouter
12. claim production rollout

Checklist sync result:

1. The existing Lane B checklist already has the needed P20.2 and P20.3 separation.
2. No checklist update is required from this planning round.