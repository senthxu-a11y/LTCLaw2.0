# Lane B P22 Closeout And Provider Decision

Date: 2026-05-11
Status: docs-only closeout and provider decision
Scope: close P22 as a controlled real-provider validation gate, record the current provider decision, and define the next recommended backend-only pilot gate without changing source, frontend, or tests

## 1. Final Provider Decision

P22 final provider decision:

1. DeepSeek is the current verified provider for the next controlled pilot.
2. DeepSeek is the current pass provider under the P22 backend-only and operator-only boundary.
3. MiniMax is not the current pass provider.
4. P22 does not authorize production rollout.
5. P22 does not mean production ready.

## 2. DeepSeek Evidence

The current DeepSeek evidence recorded for this closeout is:

1. direct DeepSeek probe passed with HTTP 200
2. LTCLaw positive real-provider smoke passed with mode=answer
3. citation grounding passed with citation_count=1
4. warnings were empty
5. request-owned provider, model, and api_key were ignored
6. ordinary RAG no-write passed for release state
7. ordinary RAG no-write passed for formal map state
8. ordinary RAG no-write passed for test plan state
9. ordinary RAG no-write passed for workbench draft state
10. kill switch passed
11. cleanup passed
12. LTCLAW_RAG_API_KEY was used as the product env var name
13. QWENPAW_RAG_API_KEY was not used as the provider secret env var name in the passing DeepSeek path

Receipt for the passing DeepSeek path is reported as:

1. docs/tasks/post-mvp/lane-b-p22-deepseek-real-provider-smoke-receipt-2026-05-11.md

## 3. MiniMax Evidence

The current MiniMax evidence recorded for this closeout is:

1. MiniMax path remains blocked
2. current blocker is key-type or auth or account or endpoint mismatch
3. MiniMax direct auth probe returned 401 on the current key path
4. MiniMax is not the current pass provider
5. MiniMax should not continue under P22 unless a correct pay-as-you-go key or a provider-specific adapter is prepared

Operational conclusion:

1. MiniMax remains outside the current P22 pass decision
2. MiniMax follow-up, if needed, should be opened as a separate provider-specific investigation or adapter line

## 4. Boundaries Preserved

The following boundaries remain fixed after P22 closeout:

1. not production rollout
2. not production ready
3. backend-only
4. operator-only
5. single provider and single model verified
6. no frontend provider selector
7. no Ask schema expansion for provider, model, or api_key
8. no ProviderManager.active_model ordinary RAG path
9. no SimpleModelRouter ordinary RAG path
10. no ordinary RAG writes

## 5. Recommended Next Step

Recommended next gate:

1. P23 Controlled Pilot With DeepSeek Backend Config

P23 scope should remain narrow:

1. still backend-only
2. still operator-only
3. Windows target machine
4. one provider and one model
5. manual env secret only
6. limited planner usage
7. enhanced receipt and monitoring
8. no production rollout

## 6. P23 Entry Conditions

P23 may start only when all of the following are true:

1. DeepSeek key remains available
2. LTCLAW_RAG_API_KEY remains env-only
3. rollback checklist is ready
4. no-write monitor is ready
5. kill switch runbook is ready
6. receipt template is ready

## 7. P23 Not Allowed

P23 must not include any of the following:

1. frontend provider selector
2. Ask schema provider, model, or api_key expansion
3. user-facing provider choice
4. production claim
5. API key UI
6. multi-provider routing
7. ordinary RAG writes release
8. ordinary RAG writes formal map
9. ordinary RAG writes test plan
10. ordinary RAG writes workbench draft

## 8. Closeout Decision

Closeout decision:

1. P22 is closed as a controlled provider-validation gate
2. DeepSeek is the current verified provider for the next controlled pilot
3. MiniMax remains blocked and is not the current pass provider
4. the next recommended gate is P23 Controlled Pilot With DeepSeek Backend Config
5. this closeout does not mean production rollout
6. this closeout does not mean production ready