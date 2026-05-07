# Knowledge P3.1 RAG Read Boundary Review

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p2-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p1-gate-status-2026-05-07.md
4. docs/plans/knowledge-architecture-handover-2026-05-06.md
5. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md

## Review Scope

This review defines the minimum read boundary for future P3 RAG work.

It does not:

1. implement RAG
2. change query behavior
3. add embedding or vector store work
4. add admin approval UI
5. read or write SVN
6. introduce new APIs

## Current Completed State

The current completed state before P3 work is:

1. P1 completed the knowledge release build, list, current-release pointer, and keyword-only current-release query baseline.
2. P2 completed test plan store, release candidate store and filter semantics, build-time candidate inclusion, frontend candidate selection UI, and the P2 final gate.
3. The current release query is still keyword-only; it is not RAG.
4. `candidate_evidence.jsonl` does not currently participate in query or RAG.

## Core Boundary Decision

The minimum P3 RAG read boundary is:

1. RAG may read only release-owned artifacts under the current release.
2. RAG must not read raw source files, pending app data, SVN working copy state, SVN remote state, or arbitrary external paths.
3. If no current release exists, the read path must return `no_current_release` or an equivalent explicit state rather than silently falling back to raw resources.

## Allowed Read Surface

For the first bounded RAG slice, the allowed read surface is intentionally small.

### Release-Owned Artifacts Allowed By Default

1. `manifest.json`
2. `map.json`
3. `indexes/table_schema.jsonl`
4. `indexes/doc_knowledge.jsonl`
5. `indexes/script_evidence.jsonl`

These are the minimum release-owned artifacts that may be assembled into bounded retrieval context.

### Metadata Allowed By Default

1. manifest metadata
2. map metadata
3. release id
4. artifact path
5. source path already recorded inside release-owned records

## Explicitly Disallowed Reads

The future RAG path must not read any of the following by default:

1. raw table source files
2. raw design document source files
3. raw script source files
4. `pending/test_plans.jsonl`
5. `pending/release_candidates.jsonl`
6. `indexes/candidate_evidence.jsonl`
7. SVN working copy metadata or file state
8. SVN remote resources
9. application-external paths outside the current release boundary

### Why `candidate_evidence.jsonl` Is Excluded By Default

`candidate_evidence.jsonl` is currently a build-time inclusion artifact, not an approved RAG input.

Default rule:

1. do not read `candidate_evidence.jsonl` in P3.2
2. only revisit it later under a dedicated evidence-usage review

This keeps P3.2 aligned with the P2 decision that candidate inclusion is build-time evidence only, not automatic query expansion.

## RAG Versus Precise Query Boundary

The responsibility split remains strict.

### RAG Should Handle

1. explanatory questions
2. structural questions
3. relationship summaries
4. evidence-location style answers

Examples:

1. "How is the combat skill system organized?"
2. "Which release-owned artifacts mention SkillTable?"
3. "Which docs or scripts in the current release provide evidence for this mechanic?"

### Structured Query Or Workbench Should Handle

1. precise numeric values
2. table row facts
3. direct modification requests
4. change recommendations that should become workbench or candidate actions

Examples:

1. "What is SkillTable 1029 damage?" -> structured query
2. "Change SkillTable 1029 damage to 120" -> workbench flow
3. "Should we publish this candidate?" -> not RAG, later governance/UI work

### Explicit Non-Goals For RAG

RAG must not:

1. mutate the formal map
2. mutate a release
3. create or accept a candidate
4. switch current release
5. read raw source as fallback

## Recommended P3.2 Direction

The next step after this review should be a bounded context assembly layer, not a full chat product surface.

Recommended P3.2 scope:

1. add a RAG service skeleton or retrieval context builder next to the existing keyword query service
2. accept `query + current release`
3. assemble bounded context chunks from release-owned artifacts only
4. return chunks plus citations
5. do not call an LLM yet
6. do not introduce vector store yet

### Minimum P3.2 Output Shape

Each returned citation should always include:

1. `release_id`
2. artifact type
3. artifact path or source path recorded in the release-owned artifact

This preserves auditability and keeps the read path bounded to release-owned data.

## Gate Conditions For Future P3.2 Work

P3.2 should not pass review unless all of these remain true:

1. no raw source read
2. no pending read
3. no SVN read or write
4. no automatic current-release switch
5. no release mutation
6. citations always include `release_id` plus artifact or source reference
7. no LLM call if P3.2 is still only a context builder

## Final Review Result

P3.1 is completed as a boundary-review phase.

The approved minimum direction is:

1. RAG reads only current-release, release-owned artifacts
2. `table_schema.jsonl`, `doc_knowledge.jsonl`, `script_evidence.jsonl`, and manifest/map metadata are the default allowed inputs
3. `candidate_evidence.jsonl` is excluded by default
4. raw source, pending files, SVN resources, and external paths are out of bounds
5. the next implementation step should be a bounded context assembly skeleton, not a full RAG or chat UI
