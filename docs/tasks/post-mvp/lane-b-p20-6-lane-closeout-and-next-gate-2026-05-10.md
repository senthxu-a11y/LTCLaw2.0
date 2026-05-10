# Lane B P20.6 Lane Closeout And Next Gate

Date: 2026-05-10
Status: completed lane closeout.

## Closeout Summary

1. P20 backend-only real HTTP transport lane has reached the minimum validated state.
2. The current implementation is backend-only, default-off, and not production rollout.
3. A real HTTP transport code path now exists for the RAG answer path, but it is not open to ordinary users.
4. The current product state remains pilot usable and not production ready.

## What Stayed Fixed

1. Ask request schema did not change.
2. Frontend did not gain a provider selector.
3. Router still does not choose provider.
4. ProviderManager.active_model is still outside the current RAG path.
5. SimpleModelRouter is still outside the current RAG path.
6. Credential source is still backend-owned env metadata with gate-controlled resolution.
7. API key still cannot come from request, frontend, or router.
8. Ordinary RAG Q&A remains no-write.
9. Test plans still do not enter formal knowledge by default.

## Review Findings

1. ExternalRagModelClient.generate_answer(...) still uses gate order: enabled, transport_enabled, payload normalization, allowlist, credential resolution, transport, response normalization.
2. enabled=False still returns before env lookup, resolver, transport, and httpx.
3. transport_enabled=False still returns before env lookup, resolver, transport, and httpx.
4. Allowlist failures still block before resolver and HTTP transport.
5. Missing credential, resolver exception, and missing endpoint still safe-fail without secret leakage.
6. Real HTTP transport is still triggered only by backend-owned config and default config still does not send network traffic.
7. httpx.Client still uses trust_env=False.
8. Endpoint, proxy, and API key redaction still hold.
9. Response still goes through provider parsing and _normalize_response(...).
10. Answer layer still enforces grounding and citation checks.
11. candidate_evidence still does not enter provider prompt and still does not grant citation authority.
12. Router still does not directly call provider registry.
13. Request body provider, model, and api_key still do not participate in selection.

## Minimal Cleanup Applied

1. transport_kind in outbound request contract and preview was renamed from http_skeleton to backend_http to reduce ambiguity.
2. The unreachable return None after successful credential resolution was removed.
3. No functional behavior was expanded.

## Next Gate

1. Do not go directly to production rollout.
2. Preferred next gate: P21 Controlled Backend Config Activation Plan.
3. Alternate next gate: Lane F production-hardening scope decision.
