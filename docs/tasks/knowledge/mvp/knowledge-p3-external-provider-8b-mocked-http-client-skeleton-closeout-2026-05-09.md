# Knowledge P3.external-provider-8b Mocked HTTP Client Skeleton Closeout

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md
4. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8a-mocked-http-client-skeleton-implementation-plan-2026-05-09.md
5. docs/tasks/knowledge/mvp/knowledge-p3-external-provider-7-real-provider-rollout-boundary-2026-05-09.md
6. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
7. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
8. src/ltclaw_gy_x/game/knowledge_rag_answer.py
9. tests/unit/game/test_knowledge_rag_external_model_client.py
10. tests/unit/game/test_knowledge_rag_provider_selection.py
11. tests/unit/game/test_knowledge_rag_answer.py

## Closeout Goal

Close out the mocked HTTP client skeleton implementation promised by `P3.external-provider-8a`, without widening into real provider rollout.

This closeout records a narrow backend implementation.

It does not authorize real provider integration.

It does not connect a real LLM.

It does not perform real HTTP.

It does not connect real credential material.

It does not add API.

It does not change frontend UI.

It does not change the Ask request schema.

It does not change router provider-selection authority.

It does not change `ProviderManager.active_model` behavior.

## Implemented Result

The landed implementation is intentionally narrow.

Current result:

1. `ExternalRagModelClientConfig` now has a separate backend-owned `transport_enabled` gate.
2. `enabled=True` no longer implies that external transport may initialize.
3. when `transport_enabled=False`, the external client returns the existing `transport is not connected` warning before credential resolution.
4. when `transport_enabled=False`, the external client does not call the credential resolver.
5. when `transport_enabled=False`, the external client does not call the injected transport.
6. when `transport_enabled=True`, the existing mocked transport seam still remains injectable for focused tests.
7. allowlist checks, credential checks, response normalization, warning mapping, and answer grounding behavior remain intact.
8. backend-owned config coercion now preserves `transport_enabled` when it is explicitly set in `external_provider_config`.

## Code Path Outcome

The minimal code-path change is:

1. external client runtime gating still begins in `knowledge_rag_external_model_client.py`
2. `enabled` remains the outer adapter gate
3. `transport_enabled` is now the explicit backend-owned transport gate behind `enabled`
4. credential resolution now occurs only after transport has been explicitly enabled
5. transport invocation now occurs only after transport has been explicitly enabled and credentials have been resolved
6. backend-owned `external_provider_config` still remains the only external-config source
7. request-like provider/model/api_key fields still do not participate in provider selection or transport activation

The semantic implementation files for this slice are:

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`
3. `tests/unit/game/test_knowledge_rag_answer.py`
4. `tests/unit/game/test_knowledge_rag_provider_selection.py`

The boundary-anchor files for this slice remained unchanged but were revalidated by focused tests:

1. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`

## Boundary Preservation

The following boundaries remain preserved:

1. this slice is mocked transport skeleton implementation, not real provider integration
2. this slice adds no real HTTP
3. this slice adds no real credential integration
4. this slice adds no API
5. this slice adds no frontend change
6. this slice adds no Ask request-schema change
7. router/request/UI still have no provider-selection authority
8. `ProviderManager.active_model` remains out of scope
9. request-like provider/model/api_key fields remain ignored
10. missing credentials still degrade safely when transport has been explicitly enabled
11. disabled path still remains safe
12. mocked transport seam still is not a production provider

## Validation Result

Focused validation recorded for this slice:

1. focused pytest: `60 passed in 0.05s`
2. focused scope: `test_knowledge_rag_external_model_client.py`, `test_knowledge_rag_answer.py`, and `test_knowledge_rag_provider_selection.py`
3. focused regression confirmed that `transport_enabled=False` blocks both credential resolution and transport invocation
4. focused regression confirmed that backend-owned config coercion preserves `transport_enabled`

This closeout pass does not run frontend validation.

## Next Step

The next recommended step is a later real provider rollout implementation plan or later real transport design review, not direct production provider enablement in this slice.

Any later step must still keep transport enablement backend-owned and separate from request, router, frontend, and `ProviderManager.active_model`.

## Closeout Decision

1. `P3.external-provider-8b` mocked HTTP client skeleton implementation is complete.
2. external transport now requires an explicit backend-owned gate beyond the existing adapter enabled flag.
3. mocked transport remains injectable for focused tests but remains non-production.
4. real LLM, real HTTP, real credential integration, API expansion, frontend changes, and Ask request-schema changes all remain out of scope.
5. router, request body, frontend UI, and `ProviderManager.active_model` still do not choose provider or enable transport for this path.
6. allowlist, answer-grounding, and warning-mapping behavior remain preserved.