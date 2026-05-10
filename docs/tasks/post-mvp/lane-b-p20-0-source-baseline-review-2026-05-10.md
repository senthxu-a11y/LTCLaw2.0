# Lane B P20.0 Source Baseline Review

Date: 2026-05-10
Status: docs-only source baseline review
Scope: current RAG external-provider backend path only

## 1. Overall Result

This review reconfirms the current source baseline before any P20 implementation work.

Current state remains:

1. MVP complete.
2. Data-backed pilot readiness pass remains valid.
3. Mac operator-side pilot pass with known limitations remains valid.
4. Windows operator-side pilot pass with known limitations remains valid.
5. Pilot usable.
6. Not production ready.
7. P20 is not implemented.
8. External-provider remains frozen at P3.external-provider-19.

Overall source conclusion:

1. The current external-provider path is still backend-owned and gated.
2. The current credential source is still backend-owned env metadata plus env value lookup.
3. The current default transport is still a non-network safe-failure skeleton.
4. No production real HTTP transport is connected on the current RAG external-provider path.
5. Router request schema, frontend ownership, ProviderManager.active_model, and SimpleModelRouter remain outside the current GameProject RAG provider path.

## 2. Source Baseline

Reviewed docs:

1. engineering roadmap, Lane B plan, Lane B checklist
2. P0-P3 implementation checklist
3. P19 governance plan
4. P18 env credential closeout
5. P13 transport skeleton closeout
6. P11 gate-order closeout
7. P10 allowlist closeout

Reviewed source surfaces:

1. knowledge_rag_external_model_client.py
2. knowledge_rag_answer.py
3. knowledge_rag_provider_selection.py
4. knowledge_rag_model_registry.py
5. game_knowledge_rag.py

Reviewed focused tests:

1. test_knowledge_rag_external_model_client.py
2. test_knowledge_rag_answer.py
3. test_knowledge_rag_provider_selection.py
4. test_knowledge_rag_model_registry.py
5. test_game_knowledge_rag_router.py

Reconfirmed source facts:

1. future_external is still the only external-provider identifier on the current RAG external path.
2. deterministic_mock, disabled, and future_external remain the only supported provider names in the registry.
3. future_external still requires backend-owned external_provider_config before registry construction succeeds.
4. The current Ask router still accepts only query, max_chunks, and max_chars.
5. The current router still forwards the service object into the answer layer rather than selecting a provider directly.

## 3. Gate Order

ExternalRagModelClient.generate_answer(...) still runs in this order:

1. enabled gate
2. transport_enabled gate
3. payload normalization
4. allowlist validation
5. credential resolution
6. transport invocation
7. response normalization

Confirmed runtime details:

1. enabled=False still short-circuits before payload normalization.
2. enabled=False still short-circuits before credential resolver invocation.
3. enabled=False still short-circuits before transport invocation.
4. transport_enabled=False still short-circuits before payload normalization.
5. transport_enabled=False still short-circuits before credential resolver invocation.
6. transport_enabled=False still short-circuits before transport invocation.
7. Payload normalization still happens only after both gates are open.
8. Allowlist validation still happens before credential resolution and transport.
9. Provider or transport output still goes through _normalize_response(...).

## 4. Allowlist And Credential Boundary

Allowlist behavior with transport_enabled=True remains hardened:

1. allowed_providers must normalize to a non-empty set.
2. provider_name must normalize to a non-empty value.
3. provider_name must be present in allowed_providers.
4. allowed_models must normalize to a non-empty set.
5. model_name must normalize to a non-empty value.
6. model_name must be present in allowed_models.
7. Provider allowlist failure returns the provider-not-allowed warning before credential resolution.
8. Model allowlist failure returns the model-not-allowed warning before credential resolution.
9. Allowlist failure occurs before transport invocation.

Credential boundary remains backend-owned:

1. The default resolver remains ExternalRagModelEnvCredentialResolver.
2. Env var metadata still comes only from ExternalRagModelEnvConfig.api_key_env_var in backend-owned config.
3. Env var value still comes only from os.environ lookup in the backend resolver.
4. Request body fields and router fields do not provide env var values.
5. Frontend does not provide credential values on this path.
6. Missing env metadata, blank env var name, missing env value, blank env value, and env read exception still safe-fail to not configured.
7. Missing credential still blocks transport invocation.
8. Resolver exceptions are still mapped to the safe not-configured warning and do not expose raw exception text to ordinary users.

Additional cleanup note from source review:

1. ExternalRagModelEnvCredentialResolver.__call__(...) still contains an unreachable trailing return None after the successful return path.
2. This is a cleanup item only and not changed in this docs-only review.

## 5. Transport Boundary

Current transport facts:

1. The default transport remains ExternalRagModelHttpTransportSkeleton.
2. The skeleton still builds a redacted request preview.
3. The skeleton still safe-fails by raising a skeleton error that the client maps to the request-failed warning.
4. The skeleton is still non-network by design.
5. The skeleton still does not perform real file I/O, env I/O, or socket I/O.
6. The current transport path still does not call requests.
7. The current transport path still does not call httpx.
8. The current transport path still does not call urllib HTTP clients.
9. The current transport path still does not call openai.
10. The current transport path still does not call anthropic.
11. The urllib usage currently present is limited to URL redaction helpers for preview shape, not real transport rollout.
12. There is still no production real HTTP transport on the current RAG external-provider path.
13. There is still no production provider rollout on the current RAG external-provider path.

Response normalization remains mandatory:

1. Transport output still flows through _normalize_response(...).
2. Non-mapping response still safe-fails through invalid-response handling.
3. Invalid citation_ids or warnings shape still safe-fail through invalid-response handling.

## 6. Router / Request / Frontend Boundary

Router and request schema facts:

1. RagRequest still contains only query, max_chunks, and max_chars.
2. Ask request body still does not declare provider.
3. Ask request body still does not declare model.
4. Ask request body still does not declare api_key.
5. Router still forwards body.query, body.max_chunks, and body.max_chars into current-release context building.
6. Router still passes the game service into build_rag_answer_with_service_config(...).
7. Router still does not call the provider registry directly.
8. Router still does not select a provider.
9. Request-injected provider, model, api_key, provider_hint, and service_config fields are still ignored by the router schema path.

Frontend boundary for this review:

1. This round did not review or modify frontend code.
2. No frontend finding in this review should be read as GameProject RAG provider rollout.
3. A shell-level or unrelated model selector elsewhere in the product does not count as GameProject RAG provider rollout.
4. Only GameProject RAG request ownership or GameProject RAG UI exposure of provider, model, or API key would count as boundary drift.
5. No such drift was found in the reviewed GameProject RAG backend path.

## 7. ProviderManager / SimpleModelRouter Boundary

Current RAG provider path still does not use ProviderManager.active_model or SimpleModelRouter.

Confirmed facts:

1. knowledge_rag_answer.py still resolves provider selection through resolve_rag_model_provider_name(...) and resolve_external_rag_model_client_config(...).
2. knowledge_rag_model_registry.py still constructs future_external only from backend-owned external_config.
3. ProviderManager.active_model is not read anywhere in the current RAG answer path.
4. SimpleModelRouter is not referenced anywhere in the current RAG answer path.
5. game/service.py still contains a separate SimpleModelRouter bridge that can call provider-managed models.
6. That bridge is a different model path and must not be described as already connected to the current GameProject RAG external-provider path.
7. That bridge remains a source risk for future architectural drift if later slices widen scope carelessly, but it is not current RAG path behavior.

## 8. Early Return And Grounding Boundary

Early return behavior remains intact:

1. build_rag_answer(...) still returns no_current_release before provider initialization.
2. build_rag_answer_with_provider(...) still returns through build_rag_answer(...) when context mode is no_current_release.
3. build_rag_answer_with_provider(...) still returns insufficient_context before provider selection when there are no grounded chunks.
4. insufficient_context still returns before provider initialization.

Grounding boundary remains intact:

1. Only grounded chunks with matching citation ids are passed into the prompt payload.
2. candidate_evidence is not added to the provider prompt payload by the reviewed answer path.
3. The prompt payload built for model_client.generate_answer(...) still includes query, release_id, built_at, grounded chunks, grounded citations, and policy_hints.
4. The prompt payload path reviewed here does not automatically include candidate_evidence artifacts.
5. Model output still goes through answer-layer citation validation.
6. Missing answer or empty valid citation_ids still degrades to insufficient_context.
7. Out-of-context citation ids still do not bypass grounding and instead add warnings.
8. Transport behavior still does not bypass answer-layer grounding and citation checks.

## 9. Current Gaps Before P20.1

Current gaps that remain explicitly open:

1. P20 real HTTP transport is not implemented.
2. Production provider rollout is not implemented.
3. UI provider selector is not implemented for GameProject RAG.
4. Ask schema is not expanded for provider, model, or api_key.
5. ProviderManager.active_model does not control RAG provider selection.
6. SimpleModelRouter is not connected to the current RAG provider path.
7. Production readiness is not reached.

## 10. Recommended Next Slice

Recommended next slice:

1. P20.1 Real Transport Implementation Plan.

Rationale:

1. The current source baseline is stable and still matches the intended P10, P11, P13, and P18 boundaries.
2. The next useful step is to convert this baseline into an exact transport contract and implementation plan before any code slice opens P20.3.
3. Jumping directly to P20.3 would widen risk before request, response, timeout, redaction, and safe-warning rules are frozen against current source reality.

## 11. Validation

This round is docs-only.

Implementation constraints respected:

1. No src changes.
2. No console/src changes.
3. No test changes.
4. No pytest run.
5. No TypeScript run.
6. No real HTTP.
7. No real provider.
8. No real LLM.
9. No Ask schema expansion.
10. No ProviderManager integration.
11. No SimpleModelRouter integration.
12. No production rollout claim.

Checklist sync result:

1. Lane B checklist remains consistent with the current reviewed source facts.
2. No checklist update was required in this round.

Post-edit validation required after this document write:

1. git diff --check
2. touched docs NUL check
3. keyword boundary review