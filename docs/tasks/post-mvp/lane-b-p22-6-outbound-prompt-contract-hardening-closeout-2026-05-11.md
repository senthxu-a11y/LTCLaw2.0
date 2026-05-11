# Lane B P22.6 Outbound Prompt Contract Hardening Closeout

Date: 2026-05-11
Status: docs-only closeout for a code change that hardens the outbound prompt contract only
Scope: record the completed P22.6 outbound prompt contract hardening change without claiming a real-provider rerun, production rollout, or production ready status

## 1. What Changed

P22.6 hardens only the outbound user-message contract in the external RAG client.

Changed files:

1. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
2. tests/unit/game/test_knowledge_rag_external_model_client.py
3. docs/tasks/post-mvp/lane-b-p22-6-outbound-prompt-contract-hardening-closeout-2026-05-11.md

## 2. New Prompt Constraints

The outbound prompt now explicitly requires all of the following:

1. output only valid JSON
2. do not wrap the output in markdown fences
3. do not include prose before or after the JSON
4. use exactly the answer, citation_ids, warnings schema
5. select citation_ids only from Allowed Citation IDs
6. do not invent citation ids
7. if no grounded answer exists, return the fixed insufficient grounded context fallback JSON

## 3. Boundaries Preserved

P22.6 preserves all of the following:

1. single user message only
2. existing request body shape with model, messages, and max_tokens only
3. existing parser acceptance rules
4. existing grounding and citation validation rules
5. existing transport gate order
6. existing credential handling
7. existing no-write expectations for ordinary RAG

## 4. Explicit Non-Changes

P22.6 does not do any of the following:

1. does not change parser or normalizer acceptance rules
2. does not add markdown-fenced JSON parsing
3. does not relax grounding or citation validation
4. does not change Ask request schema
5. does not change frontend provider selector behavior
6. does not change ProviderManager.active_model behavior for ordinary RAG
7. does not change SimpleModelRouter behavior for ordinary RAG

## 5. Status After P22.6

Status after this slice:

1. P22.3 remains blocked until a controlled Windows rerun happens
2. MiniMax response contract hardening is now implemented at the outbound prompt layer
3. this is not production rollout
4. this is not production ready