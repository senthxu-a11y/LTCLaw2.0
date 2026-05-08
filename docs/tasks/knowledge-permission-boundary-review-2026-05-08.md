# Knowledge Capability / Permission Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
4. docs/tasks/knowledge-p1-boundary-audit-2026-05-07.md

## Review Goal

Define the backend capability boundary between ordinary workbench fast-test actions and knowledge-governance actions.

This review is preparatory only. It does not add permission code, new API surfaces, router changes, UI changes, RAG changes, or SVN behavior.

## Current Problem

The current backend already exposes governance-capable surfaces across P1, P2, and P3:

1. build release
2. set current or publish release
3. candidate inclusion during build
4. formal map save
5. future formal map review or edit actions

These are governance actions, not ordinary workbench test actions.

Current risks:

1. frontend button hiding is not a permission boundary
2. a caller that can reach backend routes can still invoke governance actions unless backend capability checks are added
3. safe-build formal-map consumption being complete increases the need to harden build, publish, and map-edit paths on the backend

This review does not change the already-approved product rule:

> Ordinary workbench fast testing does not require administrator acceptance. Governance applies only to whether project state becomes part of a formal knowledge release.

## Permission Principles

1. Workbench fast-test permission and knowledge-governance permission must remain separate.
2. Ordinary numeric fast testing must not require administrator acceptance.
3. Administrator governance applies only to whether state enters a formal knowledge release.
4. A release candidate is a build-time optional input, not an automatic publish action.
5. Formal map save is a project-level governance write, not a release publish action.
6. Build release and publish release are different actions and should not collapse into one permission.
7. Set current release is a publish or go-live action and should be stricter than build, or at minimum independently grantable.
8. Candidate inclusion remains governed by the build action; it does not create a second publish path.
9. Future formal map review UX must follow the same governance boundary and must not bypass backend checks.

## Recommended Capability Set

The minimum capability vocabulary should be:

1. `knowledge.read`
2. `knowledge.build`
3. `knowledge.publish`
4. `knowledge.map.read`
5. `knowledge.map.edit`
6. `knowledge.candidate.read`
7. `knowledge.candidate.write`
8. `workbench.read`
9. `workbench.test.write`
10. `workbench.test.export`

Recommended semantics:

1. `knowledge.read` covers release-owned read surfaces such as release listing, current release lookup, manifest read, knowledge query, and debug RAG read surfaces.
2. `knowledge.build` covers safe build of a new release and any build-time optional candidate inclusion.
3. `knowledge.publish` covers switching or publishing the current release.
4. `knowledge.map.read` covers governance-oriented map read surfaces, including saved formal map and candidate-map review.
5. `knowledge.map.edit` covers governance writes to formal map state and future formal-map review edits.
6. `knowledge.candidate.read` and `knowledge.candidate.write` keep release-candidate governance independent from ordinary workbench testing.
7. `workbench.read`, `workbench.test.write`, and `workbench.test.export` keep test-plan read, mutation, and export separated from knowledge governance.

## Route To Capability Mapping

### Read-Only Endpoints

1. `GET /game/knowledge/releases` -> `knowledge.read`
2. `GET /game/knowledge/releases/current` -> `knowledge.read`
3. `GET /game/knowledge/releases/{release_id}/manifest` -> `knowledge.read`
4. `POST /game/knowledge/query` -> `knowledge.read`
5. `POST /game/knowledge/rag/context` -> `knowledge.read`
6. `POST /game/knowledge/rag/answer` -> `knowledge.read`
7. `GET /game/knowledge/map/candidate` -> `knowledge.map.read`
8. `GET /game/knowledge/map` -> `knowledge.map.read`

Justification for candidate-map read:

1. candidate-map output is not a general release reader surface; it is a governance-oriented preview used to inspect or classify future formal map state
2. separating it under `knowledge.map.read` keeps map review narrower than broad `knowledge.read`
3. this leaves room to expose ordinary release reads to a wider audience without automatically exposing map-governance views

### Governance Write Endpoints

1. `POST /game/knowledge/releases/build-from-current-indexes` -> `knowledge.build`
2. `POST /game/knowledge/releases/{release_id}/current` -> `knowledge.publish`
3. `PUT /game/knowledge/map` -> `knowledge.map.edit`
4. `POST /game/knowledge/releases/build` legacy full-payload build -> internal or test-only capability, or disabled outside dev or test

Governance notes:

1. candidate inclusion during build remains part of `knowledge.build`; it does not require a separate publish capability
2. `knowledge.publish` should remain independently grantable from `knowledge.build`
3. an implementation may choose to make publish roles also hold build, but the route boundary should still check publish explicitly

### Candidate And Test-Plan Endpoints

1. `GET /game/knowledge/test-plans` -> `workbench.read`
2. `POST /game/knowledge/test-plans` -> `workbench.test.write`
3. `GET /game/knowledge/release-candidates` -> `knowledge.candidate.read`
4. `POST /game/knowledge/release-candidates` -> `knowledge.candidate.write`

P3.permission-2 implementation status:

1. These candidate and test-plan route checks are now implemented in the backend.
2. Local trusted fallback remains unchanged: when no explicit capability context exists, the helper still allows the request.
3. Once explicit capability context exists, missing `workbench.read`, `workbench.test.write`, `knowledge.candidate.read`, or `knowledge.candidate.write` returns `403`.
4. Test-plan routes remain part of the fast-test or workbench boundary and do not require `knowledge.build` or `knowledge.publish`.
5. Release-candidate write remains release-eligibility state only; it does not imply build, does not imply publish, and does not automatically enter a release.
6. The implemented route checks do not change store or service semantics, do not auto-build, and do not set current release.

Justification for test-plan read:

1. test-plan listing is a read operation over workbench artifacts and should not require mutation permission
2. using `workbench.read` preserves a clean read-only workbench role for inspection or debugging
3. write-capable users may still transitively have read access, but the route boundary should stay read-shaped

### Future Map Review Or Edit Actions

Future formal map review or edit actions should check:

1. `knowledge.map.read` for review-only surfaces
2. `knowledge.map.edit` for classification, save, accept, ignore, or deprecate mutations

## Backend Enforcement Recommendation

1. Do not rely on frontend visibility as the permission boundary.
2. Add a small centralized capability helper or middleware later rather than repeating ad hoc role logic per route.
3. Keep router checks thin and centralized where possible.
4. Return `403` when required capability is missing.
5. Add focused tests that cover missing-capability `403` for build, publish, map edit, and legacy full-payload build.
6. Local or single-user development mode may keep a permissive default, but that permissive mode must be explicit and documented rather than accidental.
7. Legacy full-payload build should be treated as internal or test-only, or disabled by configuration outside dev or test.

## Sequencing Recommendation

Do not start formal map UI before backend permission checks are defined.

Recommended next implementation slice:

1. `P3.permission-1` backend capability helper plus route checks for build, publish, and map edit
2. then extend the same pattern to legacy full-payload build and adjacent candidate surfaces as needed
3. only after that should formal map review UX proceed

Current landing status after P3.permission-2:

1. `P3.permission-1` is implemented for build, publish, and formal-map edit routes.
2. `P3.permission-2` is implemented for test-plan and release-candidate routes.
3. Workbench fast-test and knowledge governance remain separate boundaries in the backend route layer.
4. Further follow-up, if needed, is now broader read-route hardening and later permission-aware UI behavior rather than re-opening the fast-test vs governance split.

Formal map review UX should wait until map-edit permission boundary is implemented or at least stubbed in backend checks.

## Final Review Result

Boundary approved:

1. fast-test workbench permissions remain separate from knowledge-governance permissions
2. build, publish, formal-map edit, and legacy full-payload build must not rely on frontend-only hiding
3. backend capability checks are now the recommended next implementation priority
4. P3.7c or later formal map UI should remain blocked until the permission boundary is implemented or stubbed
