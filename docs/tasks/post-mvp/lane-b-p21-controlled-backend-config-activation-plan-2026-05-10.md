# Lane B P21 Controlled Backend Config Activation Plan

Date: 2026-05-10
Status: docs-only plan.
Scope: controlled backend configuration activation for the existing backend-only real HTTP transport path.

## Goal

1. Define how the existing real HTTP transport path can be activated through backend-owned configuration only.
2. Keep ordinary users, router, request body, and frontend outside provider selection and credential control.
3. Preserve default-off behavior, safe degradation, DLP boundaries, and no-write guarantees for ordinary RAG Q&A.

## 1. Current Source Baseline

1. P20 real HTTP transport already exists in the current RAG path.
2. ExternalRagModelClientConfig still defaults enabled=False and transport_enabled=False.
3. backend-owned external_provider_config is the only current path for future_external provider activation.
4. Env credential source still works only by reading an env var value through a backend-configured env var name.
5. Request, frontend, and router do not provide api_key, provider, or model to the current RAG path.
6. Ask request schema still accepts only query, max_chunks, and max_chars.
7. Frontend still has no provider selector.
8. ProviderManager.active_model still does not participate in the current RAG path.
9. SimpleModelRouter still does not participate in the current RAG path.
10. Answer path still requires grounded current-release context and still enforces citation validation before returning an answer.

## 2. P21 Intended Effect

1. Allow a real LLM to be activated only through backend-owned configuration under administrator or operator control.
2. Keep provider_name, model_name, base_url, allowlist, timeout, env var name, and transport gate owned only by backend configuration.
3. Keep ordinary Ask requests unchanged so users still send only query, max_chunks, and max_chars.
4. Let NumericWorkbench and GameProject benefit from better RAG answers only through the existing answer path, not through new provider-selection powers.
5. Preserve safe degradation so activation failures do not damage release, formal map, structured query, or workbench draft flows.

## 3. Recommended Config Source

Preferred minimum source for the next implementation:

1. Reuse an existing backend service or app config object that can carry external_provider_config.
2. If no stable object exists at the exact activation point, use a local backend config file that is loaded into the existing service or app config object before the RAG answer path runs.
3. Store only env var metadata in config, not real secret values.
4. Store API key value only in environment variables.
5. Do not read provider, model, base_url, or api_key from request body.
6. Do not read provider, model, base_url, or api_key from frontend state.
7. Do not read provider, model, base_url, or api_key from ProviderManager.active_model.
8. Do not read provider, model, base_url, or api_key from SimpleModelRouter.
9. Do not read any secret value from docs or task files.

Rationale:

1. This keeps activation aligned with the existing resolve_external_rag_model_client_config(...) and build_rag_answer_with_service_config(...) path.
2. This keeps router authority unchanged.
3. This avoids introducing a new secret ownership surface.

## 4. Recommended Config Shape

Use a backend-owned external_provider_config compatible with the current config coercion path:

```python
external_provider_config = {
    "enabled": True,
    "transport_enabled": True,
    "provider_name": "future_external",
    "model_name": "backend-model-name",
    "allowed_providers": ["future_external"],
    "allowed_models": ["backend-model-name"],
    "base_url": "https://provider.example/v1/chat/completions",
    "timeout_seconds": 15.0,
    "max_output_tokens": 512,
    "max_prompt_chars": 12000,
    "max_output_chars": 2000,
    "env": {
        "api_key_env_var": "QWENPAW_RAG_API_KEY"
    }
}
```

Shape rules:

1. Do not store a real API key value in config.
2. Keep provider_name fixed to future_external for the current lane.
3. Keep allowlist explicit even when only one provider and one model are allowed.
4. Keep timeout and max limits backend-owned.
5. Treat proxy as optional backend-only config if a later slice needs it.

## 5. Activation Gates

Real HTTP transport should activate only when all of the following are true:

1. enabled=True.
2. transport_enabled=True.
3. provider_name is present in allowed_providers.
4. model_name is present in allowed_models.
5. base_url exists or credential endpoint exists.
6. env.api_key_env_var exists and is non-empty.
7. The env var value exists and is non-empty.
8. Current release context produces grounded context.
9. Answer layer citation validation succeeds on the provider response.

If any gate fails:

1. Do not call real HTTP.
2. Return the existing safe warning or safe insufficient_context behavior.
3. Do not fall back to another real provider.
4. Do not silently switch providers.
5. Do not write release, formal map, test plan, or workbench draft.

## 6. DLP, Redaction, And Logging

The next implementation must preserve these boundaries:

1. API key value must never appear in docs, tasks, tests, fixtures, logs, warnings, error responses, prompt payloads, release artifacts, formal map, snapshot output, or export output.
2. Authorization header must never be recorded.
3. endpoint and proxy query strings must always be redacted.
4. Provider raw response should not be logged by default.
5. Resolver exception raw text must not be exposed to ordinary users.
6. Smoke tests must use placeholder secrets only.
7. Config examples must use env var names only and must not include real secrets.

## 7. Kill Switch And Rollback

1. enabled=False is the adapter kill switch.
2. transport_enabled=False is the credential plus HTTP kill switch.
3. Removing provider_name or model_name from allowlist must block activation.
4. Removing env var value must block activation.
5. Clearing base_url must block activation unless a credential endpoint is explicitly provided by the approved backend config path.
6. Rollback must require config change only, not code change.
7. Rollback must not require release rebuild.
8. Rollback must not require frontend deployment.
9. Any DLP issue, secret leak, unexpected network call, ordinary RAG write, or router authority drift must trigger immediate config rollback.

## 8. Validation Matrix For The Future Implementation Slice

At minimum, the implementation slice should run:

1. external client focused tests
2. answer focused tests
3. provider selection tests
4. model registry tests
5. RAG router tests
6. config activation smoke tests
7. fake local server or monkeypatched httpx validation for real HTTP behavior with no external network calls
8. optional Windows operator smoke in a controlled environment

Validation rules:

1. Do not call real external network during automated validation.
2. Keep secrets as placeholders in every smoke path.
3. Prove default-off and rollback still work after activation support is added.

## 9. Explicitly Forbidden In P21

1. No frontend provider selector.
2. No Ask schema expansion.
3. No ordinary-user provider, model, or api_key fields.
4. No ProviderManager.active_model integration.
5. No SimpleModelRouter integration.
6. No production rollout.
7. No billing or quota surface.
8. No admin UI.
9. No secret store.
10. No automatic test-plan ingestion into formal knowledge.
11. No ordinary RAG write path into release, formal map, or workbench draft.

## 10. Recommended Next Slice Breakdown

1. P21.1 source baseline review
2. P21.2 config source implementation plan
3. P21.3 backend config activation implementation
4. P21.4 config activation smoke validation
5. P21.5 Windows operator real-config smoke
6. P21.6 closeout and production gate decision

Intent of each step:

1. P21.1 rechecks the current code and config load points before implementation.
2. P21.2 freezes where external_provider_config should come from and how it is loaded.
3. P21.3 implements the minimum backend-owned activation path.
4. P21.4 validates kill switches, DLP, and fake-network success and failure behavior.
5. P21.5 validates operator-side controlled config on Windows without opening ordinary-user controls.
6. P21.6 records whether the lane is ready for a later production-hardening decision.

## Non-Goals

1. This plan does not make the product production ready.
2. This plan does not make the feature production rollout.
3. This plan does not enable real provider access for ordinary users.
4. This plan does not add router-side provider selection.
5. This plan does not add frontend-side provider selection.