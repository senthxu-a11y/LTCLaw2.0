# Lane B P23.3 UX And Operations Gap Review

Date: 2026-05-11
Status: docs-only review based on synchronized Windows P23.2 execution receipt
Scope: review the controlled DeepSeek planner pilot result, identify UX and operations gaps, and recommend the next post-P23 gate without changing source, frontend, tests, or provider configuration

## 1. Evidence Basis

This review is based on the synchronized Windows P23.2 execution receipt:

1. final status: pass
2. commit hash: `05d72b4fdd11d45d210c48de14a4e4abdd462d04`
3. provider/model: `future_external` / `deepseek-chat`
4. env var name: `LTCLAW_RAG_API_KEY`
5. Windows controlled pilot scenario set completed
6. no-write checks passed
7. kill switch passed
8. cleanup passed

Receipt:

1. `docs/tasks/post-mvp/lane-b-p23-2-windows-controlled-pilot-deepseek-receipt-2026-05-11.md`
2. the receipt is now synchronized in this working copy
3. P23.2 is archived in-repo for the controlled pilot evidence it records

## 2. P23.2 Reported Scenario Result

The reported scenario results were:

1. Scenario 1: `mode=answer`, `citation_count=1`, `warnings=[]`
2. Scenario 2: `mode=answer`, `citation_count=1`, `warnings=[]`
3. Scenario 3: `mode=answer`, `citation_count=1`, `warnings=[]`
4. Scenario 4: `mode=answer`, `citation_count=2`, `warnings=[]`
5. Scenario 5: `mode=insufficient_context`, `citation_count=0`, warnings included:
   - `External provider adapter skeleton returned an invalid response.`
   - `Model client output was not grounded in the provided context.`

Interpretation:

1. planner scenarios 1 through 4 met the grounded-answer expectation
2. insufficient-context scenario 5 failed closed instead of fabricating an unsupported answer
3. Scenario 5 warnings are technically correct but too implementation-oriented for a planner-facing workflow

## 3. Boundary Result

The reported P23.2 boundary result was:

1. release no-write passed
2. formal map no-write passed
3. test plan no-write passed
4. workbench draft no-write passed
5. `transport_enabled=false` kill switch passed
6. cleanup restored `external_provider_config=null`
7. LTCLaw restarted without secret
8. health, project config, and release status returned to `200`
9. current release id stayed stable

This keeps P23 backend-only, operator-only, not production rollout, and not production ready.

## 4. Product Readiness Assessment

P23.2 is enough to say:

1. DeepSeek can support controlled planner Q&A against current-release data
2. the answer path can produce grounded citations for real planner questions
3. the no-write boundary remained intact during real planner usage
4. the kill switch and cleanup path remained operational

P23.2 is not enough to say:

1. production rollout is ready
2. ordinary users can manage providers
3. API key UI is acceptable
4. provider/model choice should be exposed in GameProject
5. warnings are planner-friendly
6. cost and usage guardrails are complete
7. operator startup is ergonomic enough for repeated daily use

## 5. UX Gaps

### 5.1 Planner-Facing Warning Copy

Current issue:

1. Scenario 5 returned safe fallback
2. warning text included internal phrases such as `External provider adapter skeleton returned an invalid response`
3. this is accurate for engineering but not suitable as planner-facing copy

Recommended follow-up:

1. map insufficient-context provider warnings to planner-friendly copy
2. keep raw technical warning available only in receipt/debug context
3. do not weaken grounding or citation validation

### 5.2 Citation Review Ergonomics

Current issue:

1. scenario pass criteria rely on citation ids
2. actual planner workflow needs quick inspection of cited rows/tables

Recommended follow-up:

1. improve citation display in GameProject RAG results if current UI is hard to inspect
2. make cited table/file/row context easier to open
3. do not change answer schema or provider selection while doing citation UX work

### 5.3 Workbench Handoff

Current issue:

1. Scenario 4 validated planning guidance without writes
2. the workflow from RAG guidance to NumericWorkbench draft action still needs usability review

Recommended follow-up:

1. observe one real planner session moving from cited answer to NumericWorkbench draft
2. identify whether users need explicit "open related table" or "start draft from cited row" affordances
3. keep NumericWorkbench export draft-only

## 6. Operations Gaps

### 6.1 Secret Startup Ergonomics

Current issue:

1. `LTCLAW_RAG_API_KEY` is set manually in the launch terminal
2. this is safe for controlled pilot but easy to misconfigure

Recommended follow-up:

1. create an operator startup script or runbook for Windows
2. print only secret shape booleans
3. never echo the secret
4. keep config storing only `LTCLAW_RAG_API_KEY`
5. do not add API key UI in this slice

### 6.2 Provider Config Toggle

Current issue:

1. operator config is currently managed through project config calls
2. this is acceptable for controlled pilot but not ergonomic

Recommended follow-up:

1. keep backend-owned config
2. consider an admin/operator-only config surface later
3. do not expose provider/model/api_key to ordinary GameProject Ask users

### 6.3 Cost And Usage Guard

Current issue:

1. P23.2 proved functionality but did not establish cost monitoring
2. repeated planner usage can accumulate provider cost

Recommended follow-up:

1. record request count per controlled pilot session
2. record approximate prompt/answer size if available
3. add operator guidance for daily usage limits
4. do not block MVP usage on a full billing dashboard

### 6.4 Receipt Discipline

Current result:

1. the Windows P23.2 receipt is present in this Mac working copy
2. the review conclusion matches the synchronized receipt summary

Recommended follow-up:

1. keep future pilot receipts in-repo before closing the matching review
2. keep receipt content redacted and free of provider secret values

## 7. Recommended Next Gate

Recommended next gate:

1. P24 Operator Startup And Secret-Management Hardening

Reason:

1. the real provider path and planner scenario pass are already established
2. the main operational risk is now repeatable startup, secret handling, cleanup, and supportability
3. production-hardening should wait until at least one repeated controlled pilot usage cycle

P24 should remain:

1. backend-only
2. operator-only
3. DeepSeek-focused
4. `LTCLAW_RAG_API_KEY` env-only
5. not production rollout
6. not production ready

## 8. P24 Suggested Scope

P24 should cover:

1. Windows startup runbook or script
2. secret shape check that does not reveal the secret
3. provider config apply/disable checklist
4. `external_provider_config=null` restore checklist
5. health/config/release status baseline checks
6. controlled usage receipt template
7. cost and request-count guidance
8. troubleshooting for invalid key, provider HTTP errors, and insufficient context

P24 should not include:

1. API key UI
2. frontend provider selector
3. Ask schema provider/model/api_key fields
4. production rollout
5. production ready claim
6. multi-provider routing
7. ordinary RAG writes

## 9. Optional Parallel Follow-Up

Lane E NumericWorkbench UX hardening may open after one real planner workbench session identifies concrete UI friction.

Lane F production-hardening scope decision should wait until P24 or one repeated controlled pilot usage cycle, whichever comes first.

MiniMax follow-up should remain outside the main DeepSeek path unless a compatible key or provider-specific adapter is prepared.

## 10. Current Decision

Current decision:

1. P23.2 reported pass is sufficient to move the main line out of provider transport work
2. P23 is not production rollout
3. P23 is not production ready
4. next recommended main-line gate is P24 Operator Startup And Secret-Management Hardening
5. P23.2 Windows receipt is synchronized for controlled pilot archival
