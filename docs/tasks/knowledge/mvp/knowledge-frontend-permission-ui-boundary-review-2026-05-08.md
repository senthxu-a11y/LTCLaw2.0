# Knowledge Frontend Permission UI Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/mvp/knowledge-permission-boundary-review-2026-05-08.md
2. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
3. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
5. docs/tasks/knowledge/mvp/knowledge-p1-boundary-audit-2026-05-07.md

## Review Goal

Define frontend permission-aware behavior after the backend capability boundary has already been enforced.

This review is documentation only. It does not add UI code, frontend state plumbing, new API surfaces, RAG changes, LLM integration, or SVN behavior.

## Current Backend Capability State

The backend capability boundary currently lands as follows:

1. `knowledge.build` protects `POST /game/knowledge/releases/build-from-current-indexes` and the legacy `POST /game/knowledge/releases/build` route.
2. `knowledge.publish` protects `POST /game/knowledge/releases/{release_id}/current`.
3. `knowledge.map.edit` protects `PUT /game/knowledge/map`.
4. `workbench.read` and `workbench.test.write` protect test-plan routes.
5. `knowledge.candidate.read` and `knowledge.candidate.write` protect release-candidate routes.
6. Local trusted fallback still exists: when no explicit capability context is present, backend helper checks intentionally allow the request.

## Core Frontend Principle

1. The frontend is not the permission boundary; backend `403` is the final enforcement point.
2. The frontend should still reduce user confusion by not presenting governance actions as if they were available when capability context says they are not.
3. Read-only status surfaces may still be shown to users who can inspect release state or to local trusted users.
4. Workbench fast-test UI must not be hidden merely because the user lacks `knowledge.build` or `knowledge.publish`.
5. Release-candidate eligibility UI and formal release governance UI must remain visibly separate concepts.

## Recommended UI Strategy

Chosen strategy: keep governance panels visible when the surrounding page is visible, but disable unavailable governance actions and show a short permission explanation.

Reasoning:

1. Disabled controls preserve feature discoverability and reduce the chance that users misread a hidden action as a product bug or missing data.
2. Disabled controls fit the existing rule that read-only status panels may still be visible even when mutation capability is missing.
3. This strategy keeps the workbench fast-test surface visible while still making formal governance actions clearly unavailable.
4. Backend `403` handling remains mandatory even when the control is disabled in normal UI paths.

This review does not require every unauthorized control to be rendered. If a later navigation design removes an entire governance-only section from a low-permission entry point, that is acceptable. But when a governance panel is shown, the default interaction rule should be disabled-with-explanation rather than silently hidden.

## UI Behavior Matrix

### `knowledge.build`

1. Show the release status panel if the page already exposes release status.
2. Enable the `Build knowledge release` action only when `knowledge.build` is present.
3. Without `knowledge.build`, show the build action in disabled state with a short permission note.
4. Do not let missing `knowledge.build` hide unrelated workbench fast-test flows.

### `knowledge.publish`

1. Enable `Set current release` or publish controls only when `knowledge.publish` is present.
2. Without `knowledge.publish`, show publish controls as disabled if the release governance panel is visible.
3. Publish remains a stricter governance action than candidate write or test-plan write.

### `knowledge.map.read`

1. Allow viewing formal-map or candidate-map UI when those review surfaces exist.
2. If the current frontend still has no map UI, treat this as a future-facing rule for later map review work.
3. Map read should not by itself expose save or publish actions.

### `knowledge.map.edit`

1. Allow formal-map save actions only when `knowledge.map.edit` is present.
2. Without `knowledge.map.edit`, map review surfaces should be read-only and save actions should be disabled.
3. `knowledge.map.edit` does not imply `knowledge.publish`.

### `workbench.read`

1. Allow viewing test plans.
2. This remains part of the fast-test or workbench boundary, not release governance.
3. Missing `workbench.read` should not be described as a build or publish problem.

### `workbench.test.write`

1. Allow saving test plans and the later export-oriented workbench actions that belong to test-plan mutation.
2. Do not require `knowledge.build` or `knowledge.publish` for ordinary fast-test write actions.
3. Missing `workbench.test.write` should disable test-plan mutation controls but should not imply administrator acceptance semantics.

### `knowledge.candidate.read`

1. Allow viewing release candidates.
2. Candidate read must not grant formal-map edit, build, or publish actions.

### `knowledge.candidate.write`

1. Allow creating or marking release candidates.
2. Candidate write remains release-eligibility state only.
3. Candidate write does not imply build, does not imply publish, and does not automatically place anything into a release.

## 403 Handling Rules

1. The frontend must handle backend `403` even if the UI normally hides or disables the action.
2. Preferred short message: `You do not have permission to perform this action.`
3. `403` responses must not be misreported as SVN or local project directory configuration errors.
4. The UI must not encourage the user to reconfigure SVN when the actual error is permission-related.
5. Permission errors should stay action-scoped and concise.

## Local Trusted Fallback

1. In local mode with no explicit capability context, current UI behavior may remain as-is.
2. Once frontend capability context exists, the UI should switch to the capability matrix above.
3. Capability context may later come from user, session, or bootstrap API state, but this review does not define that transport or implement it.
4. Until that plumbing exists, the frontend should treat missing capability context differently from explicit capability denial.

## Sequencing Guidance

1. Do not jump directly into formal map review UX implementation.
2. Formal map review UX should only proceed after frontend handling rules for `knowledge.map.read` and `knowledge.map.edit` are settled in code-facing UI plumbing.
3. The recommended next implementation slice is `P3.permission-ui-1`: frontend capability state plumbing and API type definition.
4. A valid alternative next slice is docs-only UI copy review for permission-sensitive labels and disabled-state text.
5. Formal map review UX remains sequenced after permission-aware frontend plumbing.

## Final Review Result

Boundary approved:

1. Frontend behavior should become permission-aware, but frontend visibility is still not the true permission boundary.
2. Governance controls should default to disabled-with-explanation when the surrounding panel is visible and capability is missing.
3. Workbench fast-test UI must remain separate from release governance UI.
4. The next frontend-facing work should be permission-aware state plumbing or copy review, not direct formal map review UX.
