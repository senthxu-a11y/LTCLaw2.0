# Knowledge Read Permission Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/mvp/knowledge-permission-boundary-review-2026-05-08.md
2. docs/tasks/knowledge/mvp/knowledge-frontend-permission-ui-boundary-review-2026-05-08.md
3. docs/tasks/knowledge/mvp/knowledge-frontend-permission-copy-review-2026-05-08.md
4. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
5. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
6. docs/tasks/knowledge/mvp/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
7. docs/tasks/knowledge/mvp/knowledge-p1-boundary-audit-2026-05-07.md

## Review Goal

Decide whether broader read-only knowledge routes should receive backend capability checks, and if so which capability each route should require.

This review is documentation only. It does not add backend checks, router changes, new API surfaces, frontend UI, RAG expansion, LLM integration, or SVN behavior.

## Current State

1. Backend write routes already have capability checks for build, publish or set-current, formal-map save, test-plan read or write, and release-candidate read or write.
2. Frontend permission-aware handling already exists for the GameProject release-governance surface and for the current NumericWorkbench workbench read or export entry points.
3. Most broader read-only knowledge routes are still not forced through backend capability checks.
4. Local trusted fallback still exists: when no explicit capability context is present, backend capability helper behavior remains permissive.
5. Current read-only release, query, RAG, and map routes therefore remain acceptable in local trusted mode, but are not yet fully hardened for multi-user or non-trusted operation.

## Core Questions

The product decision to make here is:

1. Which read-only routes should require explicit capability when the deployment is multi-user or otherwise non-trusted?
2. Which read routes may continue to work through local trusted fallback when no explicit capability context exists?
3. Whether read permission should remain split across `knowledge.read`, `knowledge.map.read`, `workbench.read`, and `knowledge.candidate.read`, rather than collapsing everything under a single broad reader role.

## Review Principles

1. Read-only routes still reveal product-owned release assets or governance state, so they are not automatically safe for all callers in a multi-role deployment.
2. `knowledge.read` must remain narrower than build or publish. Reading a release must not imply ability to mutate it.
3. `knowledge.map.read` must remain narrower than `knowledge.map.edit`. Governance-oriented map inspection is not the same as map mutation.
4. `workbench.read` must remain narrower than `workbench.test.write`. Inspecting test-plan artifacts is not the same as changing them.
5. `knowledge.candidate.read` must remain narrower than `knowledge.candidate.write`, `knowledge.build`, and `knowledge.publish`.
6. Ordinary workbench fast testing still must not require administrator acceptance.
7. Query or RAG read remains constrained to release-owned artifacts only and must not widen to raw source, pending state, or `candidate_evidence.jsonl` unless a later dedicated review explicitly approves that change.

## Current Risk

The write boundary is now materially stronger than the read boundary.

Current risk in a multi-user or non-trusted setting:

1. A caller who cannot build or publish may still read release manifests, current release status, and query or RAG outputs unless broader read checks are added.
2. Candidate-map and saved-formal-map reads are governance-oriented review surfaces, but they are not yet clearly hardened in the same way as formal-map writes.
3. The current permissive behavior is acceptable for local trusted fallback, but it should not be mistaken for the intended long-term multi-role boundary.

## Recommended Capability Split

The current capability vocabulary should remain split rather than collapsed:

1. `knowledge.read` for release-owned release, query, and RAG reads.
2. `knowledge.map.read` for governance-oriented map inspection surfaces.
3. `workbench.read` for test-plan inspection surfaces.
4. `knowledge.candidate.read` for release-candidate inspection surfaces.

Recommended rationale:

1. A general release reader should not automatically gain candidate-review access.
2. A general release reader should not automatically gain map-governance review access.
3. Workbench read belongs to the fast-test boundary, not the formal knowledge-governance boundary.
4. This split keeps future product roles composable instead of forcing one over-broad read capability.

## Recommended Route Mapping

### General Release Read

1. `GET /game/knowledge/releases` -> `knowledge.read`
2. `GET /game/knowledge/releases/current` -> `knowledge.read`
3. `GET /game/knowledge/releases/{release_id}/manifest` -> `knowledge.read`

Reasoning:

1. These are release-owned formal knowledge read surfaces.
2. They do not mutate release state.
3. They should be grantable to readers who are not builders or publishers.

### Query And RAG Read

1. `POST /game/knowledge/query` -> `knowledge.read`
2. `POST /game/knowledge/rag/context` -> `knowledge.read`
3. `POST /game/knowledge/rag/answer` -> `knowledge.read`

Reasoning:

1. These routes read release-owned knowledge artifacts and return derived read output.
2. They remain part of the knowledge-read boundary, not workbench fast-test or governance write.
3. They must continue to respect the existing read boundary that excludes raw source files, pending files, and `candidate_evidence.jsonl` by default.

### Map Read

1. `GET /game/knowledge/map/candidate` -> `knowledge.map.read`
2. `GET /game/knowledge/map` -> `knowledge.map.read`

Reasoning:

1. Candidate-map and saved-formal-map reads are governance-oriented review surfaces, not ordinary release listing.
2. Keeping them under `knowledge.map.read` preserves a narrower permission than broad `knowledge.read`.
3. This keeps room for a role that may inspect releases but not inspect governance map state.

### Candidate And Test-Plan Read

1. `GET /game/knowledge/release-candidates` is already implemented -> `knowledge.candidate.read`
2. `GET /game/knowledge/test-plans` is already implemented -> `workbench.read`

Reasoning:

1. Candidate read is release-eligibility inspection and must remain distinct from build or publish.
2. Test-plan read remains part of the fast-test boundary and must not be relabeled as a governance read.

## Local Trusted Fallback Recommendation

The recommended behavior is not route-specific permissiveness. It is capability-context-sensitive permissiveness.

Recommended rule:

1. In local trusted or single-user mode, when no explicit capability context exists, current local trusted fallback may continue for the broader read routes.
2. Once explicit capability context exists, the listed read routes should check capability strictly and return `403` when missing.
3. Do not create a second class of permanently unguarded multi-user read routes just because they are read-only.

This means the allowed fallback set is:

1. General release read may continue through local trusted fallback only when explicit capability context is absent.
2. Query and RAG read may continue through local trusted fallback only when explicit capability context is absent.
3. Map read may continue through local trusted fallback only when explicit capability context is absent.
4. Already-implemented candidate and test-plan read routes keep the same helper semantics: permissive only when explicit capability context is absent.

## Product Boundary

The following distinctions must remain explicit:

1. `knowledge.read` is not `knowledge.build` or `knowledge.publish`.
2. `knowledge.map.read` is not `knowledge.map.edit`.
3. `workbench.read` is not `workbench.test.write`.
4. `knowledge.candidate.read` is not `knowledge.candidate.write`, `knowledge.build`, or `knowledge.publish`.
5. Query and RAG read still must not read raw source, pending state, or `candidate_evidence.jsonl` unless a later review explicitly widens the boundary.
6. Ordinary workbench fast testing still does not require administrator acceptance.

## Rollout Strategy

Recommended strategy:

1. Keep local trusted fallback so single-machine usage does not break when no capability context is present.
2. Once capability context is present, read routes should enforce capability strictly just like the existing write routes.
3. Implement broader backend read checks before adding broader permission-aware UI.
4. Phase the backend rollout in this order: map read, release read, then query or RAG read.
5. Only after backend read checks exist should later frontend permission-aware empty states or disabled states expand to those surfaces.

Reasoning for this order:

1. Map read is the narrowest governance-facing read boundary and the closest match to already-hardened map edit.
2. Release read is broader but still a straightforward release-owned read surface.
3. Query and RAG read need the same `knowledge.read` capability, but product messaging must stay careful because these endpoints can be mistaken for a general assistant surface.

## Frontend Impact

If backend read checks are enabled later, frontend behavior should follow these rules:

1. Frontend must handle backend `403` for read routes even if the page currently shows the panel.
2. The `403` copy should continue to be `You do not have permission to perform this action.`
3. Read-route `403` must not be misreported as SVN configuration failure or local project directory failure.
4. Read-only panels may show an info or empty state when permission is missing.
5. Missing read capability should be explained as permission denial, not as feature absence or unsupported product state.

## Status Update

Status as of 2026-05-08: recommended implementation `P3.permission-3` is completed.

Implementation update:

1. The recommended read checks are now implemented for release read, query, RAG, and map read routes.
2. Local trusted fallback remains unchanged and still applies only when explicit capability context is absent.
3. Query and RAG read boundaries remain unchanged and still do not widen to raw source, pending state, or `candidate_evidence.jsonl`.
4. Candidate and test-plan read checks remain on their existing `knowledge.candidate.read` and `workbench.read` boundaries.

## Final Recommendation

Recommended direction:

1. Yes, broader read-only knowledge routes should receive backend capability checks for multi-user or non-trusted operation.
2. The capability mapping should be `knowledge.read` for general release, query, and RAG read; `knowledge.map.read` for candidate-map and saved-formal-map reads; `workbench.read` for test-plan reads; and `knowledge.candidate.read` for release-candidate reads.
3. The local trusted fallback should remain in place only as the existing no-capability-context escape hatch for single-user or trusted deployments.
4. That recommended backend slice has now been implemented; broader UI work remains separate follow-up.

## Next Step Recommendation

Recommended next slice:

1. Defer formal-map review UX until the landed backend read boundary is actually consumed by product-facing permission UX.
2. Expand frontend permission coverage only if later product review still needs those existing entry points hardened.
3. Preserve the current query or RAG read boundary unless a later dedicated review explicitly widens it.

If product review decides not to implement broader read checks now, the acceptable fallback direction would be formal-map review UX boundary or design only. That is not the recommended direction from this review.

## Final Review Result

Boundary approved:

1. Broader read capability checks are recommended and should not remain indefinitely implicit.
2. Read capability should stay split across `knowledge.read`, `knowledge.map.read`, `workbench.read`, and `knowledge.candidate.read`.
3. Local trusted fallback may remain, but only when explicit capability context is absent.
4. The recommended `P3.permission-3` backend read capability checks are now implemented.
