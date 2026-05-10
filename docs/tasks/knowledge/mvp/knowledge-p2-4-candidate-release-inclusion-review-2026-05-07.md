# Knowledge P2.4 Candidate Release Inclusion Review

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/mvp/knowledge-p2-gate-status-2026-05-07.md
3. docs/tasks/knowledge/mvp/knowledge-p1-gate-status-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-p1-9c-review-gate-2026-05-07.md
5. docs/plans/knowledge-architecture-handover-2026-05-06.md
6. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md

## Review Scope

This review covers one narrow question only:

1. How release candidates may enter the formal knowledge release.
2. What build-time validation boundary should exist before implementation.
3. How the existing safe backend build endpoint should remain the only normal inclusion path.

This review does not implement candidate merge, frontend UI, RAG, P3 work, SVN behavior, or any new API.

## Current Completed State

The current completed state before P2.5 is:

1. P2.1 test plan store is complete.
2. P2.2 release candidate store is complete.
3. P2.3 candidate list/filter semantics are complete.
4. Test plans and release candidates are still app-owned pending data under `pending/test_plans.jsonl` and `pending/release_candidates.jsonl`.
5. Release candidates do not automatically enter the formal knowledge release.
6. Release candidates do not automatically set the current knowledge release.
7. The current P2 slice still does not read or write SVN and does not copy raw source files.

## Core Conclusion

The boundary decision for P2.4 is:

1. A release candidate must not automatically enter a knowledge release.
2. Candidate inclusion may happen only at build-time.
3. Build-time inclusion must be executed only by the safe backend release-build endpoint and service path.
4. The frontend must not submit a full derived release payload.
5. `rejected` and `pending` candidates must not enter the release by default.
6. Even an `accepted` candidate must not enter the release automatically; it still requires an explicit build request with `candidate_ids`.
7. A successful build that includes candidates must not automatically set the current release.

## Recommended Rules

### 1. Candidate Eligibility

Only candidates that satisfy all of these conditions are eligible for build-time inclusion:

1. `status == "accepted"`
2. `selected == true`
3. the candidate id is explicitly present in the build request `candidate_ids`

This is intentionally stricter than either field alone.

Reason:

1. `accepted` means the candidate is reviewable for release use.
2. `selected` means it is explicitly marked as eligible or intended for release-time consideration.
3. `candidate_ids` in the request means the current build still makes an explicit inclusion choice.

### 2. Explicit Build Request Required

The build request must continue to use narrow intent fields only:

1. `release_id`
2. `release_notes`
3. `candidate_ids`

The frontend must not send full `KnowledgeMap`, `TableIndex`, `DocIndex`, `CodeFileIndex`, or raw source payloads as the normal candidate inclusion path.

### 3. Validation Failures Must Be Clear

P2.5 should fail clearly in these cases:

1. candidate id does not exist in the release candidate store
2. candidate status is not `accepted`
3. candidate `selected` is `false`
4. candidate source refs are invalid

For `selected == false`, this review chooses one explicit strategy:

1. return a clear validation error
2. do not silently skip

Reason:

1. silent skipping would hide operator intent mistakes
2. explicit failure keeps build inputs auditable and easier to reason about
3. it matches the existing safe-endpoint style of prerequisite validation

### 4. Source Path Boundary Remains Strict

Candidate `source_refs` must continue to obey the existing local-project path rules:

1. only relative paths under the local project directory are allowed
2. absolute paths are rejected
3. `..` escape paths are rejected

This rule should remain enforced at both persistence time and build-time validation.

### 5. Inclusion Output Must Stay Derived

Candidate inclusion results may be written only as release-owned derived metadata or evidence, for example:

1. manifest metadata
2. release-owned evidence records
3. release-owned candidate inclusion summaries

Candidate inclusion must not:

1. copy raw source tables
2. copy raw source documents
3. copy raw source scripts
4. mutate project source files

## Relationship To P1.9c Safe Build Endpoint

P1.9c already established the correct backend boundary:

1. the normal frontend path uses only `release_id`, `release_notes`, and `candidate_ids`
2. router remains thin
3. server-side state remains authoritative
4. the old full-payload build endpoint is not restored as a normal frontend path

This means P2.5 should be implemented by extending the existing safe endpoint and service path, not by inventing a second ordinary build contract.

The recommended interpretation is:

1. P1.9c already solved the transport boundary
2. P2.4 now defines the candidate validation boundary
3. P2.5 can implement candidate inclusion inside the existing safe backend build path

## What Must Still Not Enter The Release Automatically

The following non-goals remain in force:

1. a test plan does not directly become a formal knowledge document
2. a release candidate is not an automatic map patch
3. a release candidate does not automatically modify `current.json`
4. a release candidate does not trigger extra behavior outside release build and normal derived release output generation
5. a release candidate does not add SVN read/write or commit behavior
6. this review does not add RAG behavior or semantic retrieval work

## Recommended P2.5 Direction

P2.5 should be a backend-only build-time inclusion slice.

Recommended implementation direction:

1. read release candidates in the service layer from the release candidate store
2. validate requested `candidate_ids`
3. require every requested candidate to exist, be `accepted`, and be `selected == true`
4. include only validated candidate evidence or metadata in the derived release outputs
5. keep the router thin and continue forwarding narrow request intent only

Recommended narrow tests for P2.5:

1. `accepted + selected` candidate inclusion succeeds
2. `pending` candidate inclusion fails clearly
3. `rejected` candidate inclusion fails clearly
4. `selected == false` candidate inclusion fails clearly
5. non-existent candidate id fails clearly
6. build after candidate inclusion does not set current release automatically
7. build path does not read or write SVN
8. build path does not copy raw source files

## Final Review Result

P2.4 is approved as a boundary-review phase.

The approved direction is:

1. candidate inclusion is build-time only
2. inclusion stays behind the existing safe backend endpoint
3. inclusion requires explicit `candidate_ids`
4. only `accepted + selected` candidates are eligible
5. `selected == false` must fail clearly, not be silently skipped
6. build success still does not imply set-current

P2.5 should therefore be treated as backend build-time inclusion work, not frontend UI work and not RAG work.
