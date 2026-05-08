# Knowledge Frontend Permission Copy Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-frontend-permission-ui-boundary-review-2026-05-08.md
2. docs/tasks/knowledge-permission-boundary-review-2026-05-08.md
3. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md
4. docs/tasks/knowledge-p0-p3-implementation-checklist.md
5. docs/tasks/knowledge-p3-gate-status-2026-05-07.md

## Review Goal

Unify frontend permission-aware UI copy rules so permission problems are not misreported as SVN, local project directory, administrator-approval, or feature-absence problems.

This review is documentation only. It does not add UI code, frontend state plumbing, new API surfaces, RAG changes, LLM integration, or SVN behavior.

## Current State

1. Backend capability checks now cover build, publish, map-edit, test-plan, and release-candidate routes.
2. `P3.permission-ui-1` has already wired the GameProject release panel and build modal for permission-aware build, publish, and candidate-read disabled behavior.
3. Backend `403` remains the final permission boundary.
4. Local trusted fallback still exists: when capability context is absent, current local behavior remains permissive.

## Copy Principles

1. Permission errors must not mention SVN unless the actual failure is an SVN problem.
2. Permission errors must not mention `local project directory` unless the actual failure is missing or invalid project root configuration.
3. Permission errors must not say or imply that the feature does not exist.
4. Permission errors must not imply that ordinary fast-test work requires administrator acceptance.
5. When a governance action lacks permission, copy should say the user cannot perform that action, not that the project is misconfigured.
6. Permission copy should stay action-scoped, short, and recoverable.
7. Disabled-state copy and backend-`403` copy should describe the same permission boundary, not two different product stories.

## Recommended Fixed English Copy

Recommended defaultValue strings:

1. Generic `403`: `You do not have permission to perform this action.`
2. Build disabled: `Requires knowledge.build permission.`
3. Publish or set-current disabled: `Requires knowledge.publish permission.`
4. Candidate read disabled: `Requires knowledge.candidate.read permission.`
5. Candidate selection unavailable: `Candidate selection is unavailable without release-candidate read permission.`
6. Map save disabled: `Requires knowledge.map.edit permission.`
7. Workbench test write disabled: `Requires workbench.test.write permission.`
8. Test plan read disabled: `Requires workbench.read permission.`

## Chinese And Product-Semantics Guidance

If later translated to Chinese, the intended semantics should remain:

1. `You do not have permission to perform this action.` -> `你没有执行此操作的权限。`
2. `Requires knowledge.build permission.` -> `需要 knowledge.build 权限。`
3. `Requires knowledge.publish permission.` -> `需要 knowledge.publish 权限。`
4. Do not translate permission copy into `需要管理员批准测试` or any wording that suggests ordinary fast testing is approval-gated.
5. Release-candidate `accepted` must be described as release eligibility, not ordinary test approval.
6. Candidate status copy must not imply that a designer needs administrator approval before saving or trying a normal workbench test.

## UI Usage Rules

1. Disabled-button reasons may be shown as tooltip copy or short inline reason copy.
2. API `403` responses should use warning or message presentation with the generic `403` text.
3. Disabled governance controls must not block surrounding read-only status panels.
4. When candidate list read permission is missing, the UI should not request the candidate list endpoint and should show an info or empty state instead.
5. Build permission and candidate-read permission are independent: a user with build permission but without candidate-read permission may still build with `candidate_ids=[]`.
6. Missing test-plan permission should be described as workbench permission, not as release-build or publish permission.
7. Missing map-edit permission should be described as map-governance permission, not as release publish failure.

## Error-Avoidance Rules

Avoid these permission-copy mistakes:

1. Do not say `SVN not configured` when the real result is missing capability.
2. Do not say `local project directory not configured` when the real result is missing capability.
3. Do not say `feature unavailable` or `feature not supported` when the real result is missing capability.
4. Do not say `administrator approval required` for ordinary fast-test save, preview, export, or test-plan actions.
5. Do not describe candidate `accepted` as a mandatory approval step for all workbench changes.

## Reuse Guidance For Later Slices

1. `P3.permission-ui-2` should extend candidate, test-plan, and formal-map entry points by reusing these same permission-copy rules.
2. Do not introduce a new set of inconsistent permission strings for each page or modal.
3. If i18n keys are added later, prefer reusing existing GameProject permission keys or adopt a single consistent permission-key naming scheme.
4. Later copy review or implementation slices should treat this document as the baseline for permission-aware frontend wording.

## Final Review Result

Copy boundary approved:

1. Permission copy must stay action-scoped and must not be reinterpreted as SVN, local-directory, admin-approval, or feature-existence copy.
2. Backend `403` remains the final boundary and should use one stable generic permission message.
3. Future permission-aware frontend work should reuse the fixed English strings and the semantics defined here.
4. This review does not add UI implementation, backend changes, API changes, or formal map review UX.
