# Lane B P22.4 Provider Response Contract Review

Date: 2026-05-11
Status: docs-only review
Scope: review the blocked P22.3 Windows real-provider smoke result, classify the real blocker, and define the next planning slice without changing source, frontend, or tests and without calling the real provider again

## 1. Final Decision

P22.3 final status remains blocked.

This review does not upgrade P22.3 to pass.

This review does not authorize production rollout.

This review does not mean production ready.

## 2. Evidence Reviewed

Evidence reviewed in this repo session:

1. docs/tasks/post-mvp/lane-b-p22-3-windows-agent-execution-prompt-2026-05-11.md
2. docs/tasks/post-mvp/lane-b-p22-2-controlled-real-provider-smoke-runbook-2026-05-11.md
3. docs/tasks/post-mvp/lane-b-p22-2a-no-write-operator-check-patch-2026-05-11.md
4. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
5. src/ltclaw_gy_x/game/knowledge_rag_answer.py
6. tests/unit/game/test_knowledge_rag_external_model_client.py
7. tests/unit/game/test_knowledge_rag_answer.py

Expected but not present in the repo at review time:

1. docs/tasks/post-mvp/lane-b-p22-3-windows-real-provider-smoke-receipt-2026-05-11.md

Review consequence:

1. this P22.4 review can confirm the current code contract and can classify the blocker only from the reported P22.3 result summary plus source and test evidence
2. this P22.4 review cannot claim raw-response facts that are not redacted and preserved in the repo receipt
3. receipt absence is a real evidence gap and must stay visible in the decision

## 3. P22.3 Receipt Recheck

Based on the reported Windows execution result supplied for this review:

1. provider name: future_external
2. model name: MiniMax-M2.7
3. a real provider request reached MiniMax at least once and an HTTP 200 was observed at that boundary
4. the final ordinary RAG response still degraded to mode=insufficient_context
5. the final ordinary RAG response had citation ids = []
6. the final warnings included External provider adapter skeleton HTTP error.
7. the final warnings included Model client output was not grounded in the provided context.
8. no-write verification passed for release state
9. no-write verification passed for formal map state
10. no-write verification passed for test plan state
11. no-write verification passed for workbench draft state
12. cleanup passed because external_provider_config returned to null and the app returned to health/config/release status 200 without the secret

P22.3 therefore remains blocked for response-contract reasons, not because the no-write or cleanup checks failed.

## 4. Current Runtime Contract

The current code requires provider content to end in this normalized shape:

```json
{"answer":"...","citation_ids":["..."],"warnings":[]}
```

Current code requirements that must remain unchanged:

1. grounding required
2. citation validation required
3. no raw provider output trusted
4. no ungrounded answer accepted
5. missing answer degrades to insufficient_context
6. missing citation_ids degrades to insufficient_context
7. out-of-context citation_ids degrade to insufficient_context
8. invalid provider payload shape is rejected rather than trusted

The outbound external-provider request currently uses one user-role message that includes all of the following:

1. use only grounded release context below
2. return a JSON object with keys answer and citation_ids
3. allowed citation ids
4. grounded chunks
5. policy hints when present

At review time, the transport contract in current code does not add a separate system-role or developer-role message. Any provider-specific stronger instruction would need to be planned deliberately rather than assumed to already exist.

## 5. Blocker Classification

### 5.1 Transport Connectivity

Decision:

1. not the primary blocker
2. not a full success signal either

Reason:

1. the reported Windows run reached the real provider boundary at least once and observed HTTP 200 there
2. that is enough to say the smoke was not blocked only by DNS, proxy, socket, or generic connectivity failure

### 5.2 Provider HTTP Error

Decision:

1. present in the final app-observed warning set
2. still part of the blocked result

Reason:

1. current code emits External provider adapter skeleton HTTP error. only when the http client receives a non-2xx status on the request it is evaluating
2. when that warning is returned to the answer layer, the answer layer then degrades the result to insufficient_context because answer is empty and citation_ids are empty

Limit:

1. without the redacted receipt and raw response evidence, this review cannot prove whether the observed HTTP 200 and the observed adapter HTTP error came from the same request, a retried request, or two separate attempts

### 5.3 Provider Response Parse Failure

Decision:

1. not proven from current evidence
2. cannot be promoted to the primary blocker yet

Reason:

1. current code would emit External provider adapter skeleton returned an invalid response. for parse failure
2. that warning was not part of the reported final warning set
3. the missing repo receipt means there is no preserved redacted raw response shape to inspect

### 5.4 Model Did Not Follow JSON Contract

Decision:

1. plausible
2. not yet proven

Reason:

1. the current outbound prompt requests JSON only in the user message
2. MiniMax may need a stricter contract than the current generic user-only prompt provides
3. but without redacted raw provider content, this review cannot say whether MiniMax returned non-JSON, partial JSON, wrapper text around JSON, or valid JSON with unusable citations

### 5.5 Citation IDs Missing Or Invalid

Decision:

1. plausible and contract-relevant
2. not yet proven at raw provider boundary

Reason:

1. current answer code accepts only citation ids that exist in context.citations
2. empty citation_ids or out-of-context citation_ids both degrade to insufficient_context
3. the reported final RAG payload had citation ids=[] after degradation, but that does not prove what the raw provider payload contained before normalization and validation

### 5.6 Answer Not Grounded

Decision:

1. confirmed
2. this is the decisive product-level blocker

Reason:

1. the final warning set includes Model client output was not grounded in the provided context.
2. current answer code adds that warning whenever there is no usable grounded answer with valid citation ids from the provider response path
3. no citation answer is not acceptable and must remain blocked

## 6. Real Blocker Category

The most defensible current classification is:

1. P22.3 is blocked by a provider response contract and grounding failure
2. the run is not blocked by no-write behavior
3. the run is not blocked by cleanup behavior
4. the run is not classified as pure transport-connectivity failure because the provider boundary was reached
5. the run still includes an app-observed provider HTTP error signal that must be explained before any pass claim

Operational interpretation:

1. the current evidence is enough to say real provider reached plus no-write pass plus cleanup pass
2. the current evidence is not enough to claim parse failure
3. the current evidence is not enough to claim valid JSON contract followed
4. the current evidence is enough to keep P22.3 blocked

## 7. Direction Decision

Next direction:

1. choose P22.5 MiniMax response contract hardening plan
2. do not go directly to implementation in this slice
3. do not loosen grounding or citation enforcement
4. do not rerun a broader real-provider pass attempt before the contract plan is accepted

This direction is closer to prompt and contract hardening than to immediate parser or normalizer changes.

Reason:

1. the current transport already reached the provider boundary
2. the current parser already accepts the minimal valid JSON shape that the code requires
3. the missing evidence is the redacted raw provider response shape, so parser or normalizer changes would be premature without that shape
4. the smallest defensible next slice is therefore contract hardening plus evidence capture planning, not speculative parsing changes

## 8. Recommended P22.5 Scope

P22.5 should be named MiniMax response contract hardening plan.

Recommended scope:

1. define a stricter user prompt that requires JSON only and explicitly forbids wrapper prose
2. keep the required output keys fixed to answer, citation_ids, and warnings
3. explicitly require citation_ids to come only from the allowed citation id list already sent in the prompt
4. explicitly require an empty answer plus explicit warning rather than fabricated unsupported content when support is weak
5. review whether the transport should later support provider-specific system or developer instruction for MiniMax, but do not assume that support exists today
6. allow response normalizer work only after a redacted raw MiniMax response shape is collected and shown to be stable and safe
7. plan test additions only with redacted provider-like fixtures and no real secret

P22.5 must not do any of the following:

1. must not relax citation validation
2. must not treat no citation as pass
3. must not accept ungrounded output to make the smoke green
4. must not claim production rollout
5. must not claim production ready

## 9. Evidence Gap And Next Windows Collection Rule

Because the expected repo receipt is missing and no redacted raw provider payload is preserved here, the next Windows collection should be constrained.

Recommended next Windows evidence rule:

1. collect only the redacted raw provider response shape for the blocked MiniMax call path
2. do not broaden scope into a new pass attempt in the same step
3. do not write secrets
4. do not preserve authorization headers
5. do not preserve raw secret values
6. do not change the pass or blocked decision during that evidence-only collection step unless the existing blocked evidence is clearly disproved

Minimum evidence to collect next time:

1. provider HTTP status for the exact evaluated request
2. redacted raw response body shape
3. whether the body is JSON or wrapper text around JSON
4. whether answer exists
5. whether citation_ids exists and whether the ids are in the allowed list
6. whether warnings exists

Until that redacted evidence exists, parser or normalizer changes remain conditional rather than approved.

## 10. Explicit Prohibitions Preserved

This review explicitly preserves all of the following:

1. do not relax citation validation
2. do not mark a no-citation provider answer as pass
3. do not accept ungrounded output to pass the smoke
4. do not mark P22.3 as production rollout
5. do not mark P22.3 as production ready
6. do not claim real provider enabled for users

## 11. Review Outcome

Review outcome:

1. P22.3 final status remains blocked
2. real provider boundary was reached at least once
3. no-write verification passed across all four checked state classes
4. cleanup passed
5. the blocker is best classified as provider response contract and grounding failure with an unresolved provider HTTP error signal still present in the final warning set
6. MiniMax response contract hardening is needed
7. another Windows evidence-only collection step is needed if the team wants to justify any future parser or normalizer change
8. the next slice should be P22.5 MiniMax response contract hardening plan