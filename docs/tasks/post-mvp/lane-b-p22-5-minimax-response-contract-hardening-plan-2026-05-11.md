# Lane B P22.5 MiniMax Response Contract Hardening Plan

Date: 2026-05-11
Status: docs-only plan
Scope: freeze the MiniMax response contract hardening direction, freeze the redacted raw response shape evidence requirements, and define the smallest testable next slice without changing source, frontend, or tests and without calling the real provider again

## 1. Current Blocker

Current blocker state:

1. P22.3 remains blocked
2. no-write pass remains required and was reported as pass
3. cleanup pass remains required and was reported as pass
4. the blocker category remains provider response contract and grounding failure
5. redacted raw response shape evidence is still missing from the repo because the expected P22.3 receipt file is not present here

P22.5 does not change the blocked status.

P22.5 does not call the real provider.

## 2. Plan Goal

The goal of P22.5 is to freeze the next minimal, testable direction before any code change:

1. harden the outbound MiniMax instruction contract first
2. keep the current grounding and citation rules intact
3. define the exact evidence-only Windows collection required before any parser or normalizer work is justified
4. define P22.6 as the first possible implementation slice

## 3. Current Required Response Contract

Provider final content must be parseable as a JSON mapping in this shape:

```json
{
  "answer": "<grounded answer string>",
  "citation_ids": ["<allowed citation id>"],
  "warnings": []
}
```

Current contract facts preserved by code and tests:

1. the external client accepts only JSON mappings with answer and citation_ids present
2. the transport path may extract provider content from an OpenAI-compatible choices -> message -> content shape before parsing
3. the answer layer accepts the answer only when answer is non-empty and citation_ids validate against the provided context citations
4. empty answer degrades to insufficient_context
5. missing citation_ids degrades to insufficient_context
6. out-of-context citation_ids degrade to insufficient_context
7. invalid provider payload shape is rejected as invalid_response rather than trusted

## 4. Non-Negotiable Rules

The following rules are fixed and must not be relaxed in P22.5 or any immediate follow-up:

1. do not accept ungrounded answer
2. do not accept missing citation_ids
3. do not accept citation_ids outside provided context
4. do not trust raw provider output
5. do not expose raw provider error in product response or docs receipts
6. do not relax grounding validation
7. do not relax citation validation
8. do not write release state
9. do not write formal map state
10. do not write test plan state
11. do not write workbench draft state

## 5. Preferred Hardening Direction

Preferred hardening direction for MiniMax:

1. first harden the outbound instruction to be JSON-only
2. explicitly forbid markdown fences
3. explicitly forbid prose outside JSON
4. explicitly require citation_ids to be selected only from Allowed Citation IDs
5. explicitly require unsupported or weakly supported queries to return an empty answer with warnings rather than invented citation ids
6. keep the current single user message unless later code review and evidence prove a system or developer message is required
7. do not add a provider-specific parser yet
8. do not add a provider-specific normalizer yet

Reason for this order:

1. the current runtime already has a generic parser for the required JSON mapping
2. the current runtime already enforces grounding and citation validation after parsing
3. the missing evidence is the redacted raw MiniMax response shape, so immediate parser or normalizer changes would be speculative
4. prompt contract hardening is the smallest defensible next move

## 6. Proposed JSON-Only Instruction Text

Draft instruction text for a future outbound prompt hardening change:

```text
Use only the grounded release context below.
Output only valid JSON.
Do not wrap the output in markdown.
Do not add any prose before or after the JSON object.
Use only this schema:
{"answer":"<grounded answer string>","citation_ids":["<allowed citation id>"],"warnings":[]}
citation_ids must be selected only from Allowed Citation IDs.
Do not invent citation ids.
If no grounded answer exists, return exactly:
{"answer":"","citation_ids":[],"warnings":["insufficient grounded context"]}
```

Planning rules for this text:

1. this text is frozen here as a planning artifact only
2. this round does not implement it in source
3. future implementation may refine wording, but only if it preserves the same contract strength or stronger

## 7. Redacted Raw Response Shape Collection

P22.5 freezes one Windows evidence-only run requirement.

Purpose:

1. collect only the raw MiniMax response shape needed to justify or reject later parser or normalizer work
2. do not reclassify P22.3 as pass
3. do not broaden into a new rollout or expanded smoke

Evidence-only run requirements:

1. use the same MiniMax provider and model configuration already used in the blocked run
2. use one low-risk query only
3. collect the HTTP status for the exact evaluated request
4. collect whether the response body uses an OpenAI-compatible choices -> message -> content envelope
5. collect content prefix and suffix only after redacting user data and never including any secret
6. collect whether the content starts with a JSON object
7. collect whether the content includes a markdown fence
8. collect whether the content includes citation_ids
9. collect whether the content includes warnings
10. do not write or preserve Authorization headers
11. do not write or preserve raw secret values
12. do not attempt to call this pass
13. final status for this evidence step must remain blocked or evidence-only

Evidence-only output checklist:

1. HTTP status observed
2. envelope shape observed or absent
3. content appears to start with left brace or not
4. markdown fence present or absent
5. citation_ids field present or absent
6. warnings field present or absent
7. redaction confirmation

## 8. Future Implementation Slice

P22.6 is the first possible code slice after P22.5 planning acceptance.

P22.6 scope should be limited to:

1. outbound prompt contract hardening
2. tests for the JSON-only instruction text or its approved equivalent
3. tests that ungrounded answer remains rejected
4. tests that missing citation_ids remain rejected
5. tests that out-of-context citation_ids remain rejected
6. tests for markdown-fenced JSON only if and only if P22.5 evidence later shows MiniMax actually returns that shape

P22.6 must not include:

1. frontend selector work
2. Ask schema provider or model or api_key expansion
3. API key UI
4. ProviderManager.active_model expansion into ordinary RAG
5. SimpleModelRouter expansion into ordinary RAG
6. parser or normalizer branching based only on guesswork rather than evidence

## 9. Smallest Testable Change Set

The smallest testable change set after this plan is accepted is:

1. change only the outbound user-message contract text
2. keep transport boundary behavior unchanged
3. keep answer-layer grounding logic unchanged
4. add tests that pin the strengthened instruction text
5. add tests that confirm markdown fences and prose outside JSON are still not accepted unless later evidence explicitly justifies additional normalization work

This keeps the next slice measurable:

1. if MiniMax then returns valid JSON with valid citation_ids, the current parser and answer layer may already be sufficient
2. if MiniMax still fails after prompt hardening, the stop conditions below force the work to halt before broader changes

## 10. Stop Conditions

Stop conditions after future prompt hardening or evidence collection remain strict:

1. if MiniMax still does not return valid JSON after prompt hardening, stop
2. if citation_ids are missing, stop
3. if citation_ids are invalid, stop
4. if raw response contains secret, stop
5. if no-write changes release state, stop
6. if no-write changes formal map state, stop
7. if no-write changes test plan state, stop
8. if no-write changes workbench draft state, stop

Stop means:

1. keep blocked status
2. do not widen rollout scope
3. do not accept ungrounded output as a temporary pass

## 11. Explicitly Not Allowed

The following remain explicitly not allowed:

1. no production rollout
2. no production ready claim
3. no frontend selector
4. no Ask schema provider or model or api_key support claim
5. no API key UI
6. no accepting ungrounded answers
7. no ordinary RAG writes
8. no direct parser or normalizer implementation in this planning round

## 12. Decision Summary

Decision summary:

1. P22.5 is a plan-only slice
2. MiniMax response contract hardening is planned
3. the preferred direction is stronger JSON-only outbound instruction, not immediate parser or normalizer changes
4. a Windows evidence-only redacted raw response shape collection is required
5. the next implementation candidate is P22.6 outbound prompt contract hardening with narrow tests only
6. P22.3 remains blocked
7. this is not production rollout
8. this is not production ready