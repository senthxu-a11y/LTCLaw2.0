# Knowledge P3.3 RAG Answer Adapter Boundary Review

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/mvp/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-p2-gate-status-2026-05-07.md
5. docs/tasks/knowledge/mvp/knowledge-p1-gate-status-2026-05-07.md

## Review Scope

This review defines the adapter boundary for any future RAG answer-generation step.

It does not:

1. implement answer generation
2. add a new API
3. connect a real LLM
4. add embedding or vector store work
5. add frontend UI
6. expand the existing query path
7. read or write SVN

## Current State

The current completed state before any answer service work is:

1. P3.1 read boundary review is complete.
2. P3.2 context assembly skeleton is complete.
3. P3.2b debug context endpoint is complete.
4. The current system still has no RAG answer generation.
5. The current system still has no LLM integration, embedding, vector store, or frontend RAG UI.

## Core Conclusion

The approved boundary for a future RAG answer adapter is:

1. The answer adapter may receive only the output of the P3.2 context builder.
2. The answer adapter must not directly read `manifest.json`, `map.json`, or release JSONL artifacts.
3. The answer adapter must not read raw source files.
4. The answer adapter must not read `pending/test_plans.jsonl` or `pending/release_candidates.jsonl`.
5. The answer adapter must not read `candidate_evidence.jsonl` unless a later context-builder review explicitly adds it to the provided context.
6. The answer adapter must not read or write SVN.
7. The answer adapter must not mutate a release, set current release, or create or accept candidates.

This keeps the retrieval boundary and the answer boundary separate.

The context builder remains the only component allowed to assemble release-owned evidence.

The answer adapter remains a pure consumer of already-bounded context.

## Input And Output Boundary

Recommended answer-adapter input:

```json
{
  "query": "...",
  "context": {
    "mode": "context",
    "release_id": "...",
    "built_at": "...",
    "chunks": [...],
    "citations": [...]
  }
}
```

Boundary notes:

1. `context` must be the already-built payload from P3.2 or the P3.2b debug endpoint shape.
2. The adapter must not reinterpret this input as permission to reread artifacts.
3. If `context.mode != "context"`, the adapter should preserve that state rather than falling back to its own reads.

Recommended output:

```json
{
  "mode": "answer" | "no_current_release" | "insufficient_context",
  "answer": "...",
  "release_id": "...",
  "citations": [...],
  "warnings": []
}
```

Boundary notes:

1. `mode = "answer"` is used only when the provided context is sufficient for a supported answer.
2. `mode = "no_current_release"` is propagated when the upstream context builder already reports that state.
3. `mode = "insufficient_context"` is used when the provided context is empty, weak, or not adequate for a grounded answer.
4. `warnings` is the place for explicit caveats such as "use structured query for precise numeric facts".

## Citation Rules

Citation handling must obey all of the following rules:

1. Every answer citation must come from `context.citations`.
2. The adapter must not invent citations that were not already present in `context.citations`.
3. Every returned citation must preserve `release_id`.
4. If the relevant support is missing from the provided context, the adapter must return `insufficient_context` rather than fabricate an answer or citation.

This means the adapter may filter, order, or subset context citations for presentation, but it may not synthesize new evidence locations.

## Prompt And LLM Constraints

If a prompt or model-backed adapter is later introduced, the system prompt must enforce all of the following constraints:

1. The model may answer only from the provided context.
2. The model must not claim to have read source files, release artifacts, pending files, or SVN resources.
3. The model must not provide precise table facts or exact numeric values unless they are explicitly present in the provided context.
4. Requests for exact numeric values, change recommendations, or modification operations should be redirected toward structured query or workbench flow.
5. The adapter layer must not execute tools, read files, or call retrieval code directly.

Required behavioral guidance:

1. "Only use the supplied context chunks and citations."
2. "Do not imply access to files, SVN, or hidden state."
3. "If support is insufficient, return insufficient_context."
4. "Do not invent exact values or citations not present in context."

## Relationship To Existing Boundaries

This review preserves the previously approved boundaries:

1. P1 current-release query remains keyword-only and is still not RAG.
2. P2 pending test plans and release candidates remain out of bounds for default RAG answer generation.
3. P3.1 keeps raw source, pending files, SVN, and external paths outside the read boundary.
4. P3.2 remains the only approved place where release-owned context is assembled.
5. P3.2b remains a thin debug surface for inspecting that context.

## Recommended P3.4 Direction

The next recommended step is a minimal answer-service skeleton.

Approved direction:

1. A backend-only answer-service skeleton may be implemented next.
2. The first skeleton may remain deterministic or use a mock/no-LLM adapter.
3. If a real LLM is later connected, it must be reached only through a single injected model client.
4. Tests must mock that model client rather than calling a real model.
5. Frontend UI should remain out of scope for this next step.
6. Embedding and vector store should remain out of scope for this next step.

This sequencing keeps the adapter boundary testable before any UI or retrieval-expansion work is introduced.

## Final Review Result

P3.3 is approved as a boundary-review phase.

The approved result is:

1. The answer adapter consumes only P3.2 context output.
2. The answer adapter does not directly read artifacts, project files, pending files, or SVN resources.
3. All answer citations must come from `context.citations`.
4. Unsupported or weakly supported requests return `insufficient_context` rather than fabricated answers.
5. The next implementation step should be a minimal backend answer-service skeleton, not UI or vector-store work.
