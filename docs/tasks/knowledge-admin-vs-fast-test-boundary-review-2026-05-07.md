# Knowledge Admin Vs Fast-Test Boundary Review

Date: 2026-05-07

Authority:

1. docs/plans/knowledge-architecture-handover-2026-05-06.md
2. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md
3. docs/tasks/knowledge-p0-p3-implementation-checklist.md

## Core Decision

Do not use administrator acceptance for ordinary numeric workbench changes.

The boundary is:

1. Fast numeric testing is a workbench flow.
2. Formal knowledge publishing is an administrator release-build flow.
3. A workbench change affects formal knowledge only if it later becomes a selected release candidate and is explicitly included during a release build.

This means "accepted" must not become a generic approval step for every value edit.

## Three Separate Flows

### 1. Fast-Test Flow

Purpose: let designers change values quickly, preview, export, upload to engine test, keep, or discard.

Allowed without administrator acceptance:

1. edit values in the workbench
2. preview impact
3. save a test plan
4. export or upload a test patch for engine test
5. keep or discard the test plan

Output:

1. `pending/test_plans.jsonl`
2. optional exported patch or engine-test reference

This flow must not:

1. mutate a formal release
2. mutate `current.json`
3. mutate formal map
4. rebuild official indexes
5. rebuild vectors
6. require administrator acceptance before testing

### 2. Release-Candidate Flow

Purpose: mark a verified workbench result as eligible for a future knowledge release.

Allowed only as a separate step from fast testing:

1. convert or mark a kept/verified test plan as a release candidate
2. keep release-candidate state in app-owned pending storage
3. list candidates for a future release build

Output:

1. `pending/release_candidates.jsonl`

This flow must not:

1. automatically enter a release
2. automatically set current release
3. automatically change formal map
4. automatically trigger RAG/index rebuild

Terminology note:

1. Candidate `accepted` means release-eligible candidate state.
2. It does not mean ordinary workbench edits require administrator acceptance before testing.
3. UI copy should avoid making `accepted` sound like a required approval gate for fast tests.

### 3. Administrator Release-Build Flow

Purpose: produce formal knowledge assets.

Administrator-only choices:

1. confirm or edit formal map
2. build official indexes
3. optionally include selected verified release candidates
4. build a knowledge release
5. publish or switch current release

Output:

1. release `manifest.json`
2. release `map.json`
3. release `indexes/`
4. optional candidate evidence included during build
5. `current.json` only when explicitly switched

This flow is the only place where a release candidate may affect formal knowledge.

## Product Boundary Rule

The product must keep this rule visible in both backend and UX design:

> Workbench changes are immediate test artifacts. Formal knowledge changes happen only during administrator-controlled release build or publish.

Implications:

1. Ordinary users can test values without waiting for administrator acceptance.
2. Ordinary users cannot publish knowledge by saving a test plan.
3. Workbench write permission is not knowledge-governance permission.
4. Build/publish/map-edit permissions must be separate from workbench test permissions.

## Current Implementation Implications

Current P2 candidate selection is acceptable only if interpreted narrowly:

1. candidate inclusion is build-time only
2. candidates default to unchecked in the build modal
3. build success does not set current release
4. candidate evidence is release-owned metadata/evidence only

However, any future UX must avoid adding an "administrator accept" gate to the ordinary fast-test path.

## Required Follow-Up

1. Keep fast-test test plan states separate from release-candidate states.
2. Label release-candidate status as release eligibility, not test approval.
3. Enforce build/publish/map-edit as admin-only before multi-user usage.
4. Keep `candidate_evidence.jsonl` out of default query/RAG until a dedicated review widens that boundary.

## Final Review Result

Boundary approved:

1. Fast testing does not require administrator acceptance.
2. Administrator choices apply only to formal knowledge governance and release build.
3. Release candidates are optional build inputs, not automatic outputs of the workbench.
4. The next implementation work should harden permissions and copy, not merge the fast-test and release-governance flows.
