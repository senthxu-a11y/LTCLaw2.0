# Knowledge P3.7c-2 Formal Map Status Edit Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/mvp/knowledge-p3-7c-formal-map-review-ux-boundary-2026-05-08.md
2. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
3. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-permission-boundary-review-2026-05-08.md
5. docs/tasks/knowledge/mvp/knowledge-frontend-permission-ui-boundary-review-2026-05-08.md
6. docs/tasks/knowledge/mvp/knowledge-frontend-permission-copy-review-2026-05-08.md

## Review Goal

Define the minimum boundary for formal map status editing after `P3.7c-1`.

This review is documentation only. It does not add frontend UI, backend API, PATCH semantics, relationship editing, graph editing, LLM behavior, build or publish coupling, or SVN behavior.

## Current State

The current landed state before `P3.7c-2` is:

1. `P3.7c-1` can already review candidate map and saved formal map.
2. `PUT /game/knowledge/map` can already save a complete validated `KnowledgeMap`.
3. The backend already validates schema, `source_path`, `status`, and relationship endpoints.
4. The current frontend does not yet edit formal map content.
5. Save still does not build, does not set current release, and does not mutate release history.

## Minimum Status Edit Scope

The first status-edit slice should be intentionally narrow.

Recommended editable object types:

1. `systems`
2. `tables`
3. `docs`
4. `scripts`

Allowed status values:

1. `active`
2. `deprecated`
3. `ignored`

Not editable in the first slice:

1. `id` fields such as `system_id`, `table_id`, `doc_id`, and `script_id`
2. `title`
3. `source_path`
4. `source_hash`
5. `relationships`
6. `deprecated` list
7. `release_id`
8. `schema_version`

## Relationship Handling Rule

`P3.7c-2` must not turn into implicit relationship editing.

Chosen strategy:

1. Status edit does not automatically delete or rewrite relationships.
2. The UI should show a warning that an `ignored` or `deprecated` item may still be referenced by relationships.
3. The backend remains responsible for relationship endpoint existence validation on save.
4. Relationship cleanup is deferred to `P3.7c-3` or a later dedicated relationship-edit slice.
5. `P3.7c-2` must not auto-clean or auto-rewire relationships.

## Save Boundary

Status edit should continue to use the existing complete-map save boundary.

Required save rules:

1. The frontend edits a local editable formal-map draft only.
2. Save uses the existing `PUT /game/knowledge/map` API through the current `saveFormalMap` wrapper.
3. No new PATCH API is added.
4. Save success refreshes formal map from the existing `GET /game/knowledge/map` path.
5. Save does not build a release.
6. Save does not set current release.
7. Save does not modify release history.
8. Save does not read or write SVN.
9. The next safe build is still the point where saved formal map is snapshotted into a release.

## Permission Boundary

The status-edit slice must stay inside the existing capability model.

Required permission rules:

1. Viewing formal map review still requires `knowledge.map.read`.
2. Editing status and saving require `knowledge.map.edit`.
3. Without `knowledge.map.edit`, status controls must remain disabled.
4. Backend `403` still uses `You do not have permission to perform this action.`.
5. Local trusted fallback remains unchanged when no explicit capability context exists.

## UX Recommendation

The status-edit slice should extend the already-landed `P3.7c-1` surface rather than introducing a new editor.

Recommended UX direction:

1. Add status controls to the existing formal map review UI.
2. Use segmented control or select-style status inputs for supported object rows.
3. Candidate map remains advisory source state.
4. Saved formal map is the editable target.
5. If there is no saved formal map yet, the user should first use `Save as formal map` from `P3.7c-1`.
6. Do not use raw JSON as the main editing surface.
7. Do not add graph or drag-and-drop editing.

Recommended first edit target:

1. Prefer status editing on saved formal map only.
2. Do not make candidate map directly editable in `P3.7c-2`.
3. If candidate map and formal map are both visible, candidate map remains comparison or advisory context only.

## Recommended Drafting Model

The minimum frontend draft model should remain simple.

Recommended behavior:

1. Load saved formal map.
2. Clone it into a local editable draft.
3. Status changes update only the local draft until save.
4. Cancel or refresh discards unsaved local draft state.
5. Save writes the full draft through existing `saveFormalMap`.

## Error And Copy Rules

The status-edit slice should reuse the existing permission and error-copy baseline.

Required copy rules:

1. Missing `knowledge.map.edit` should use `Requires knowledge.map.edit permission.` for disabled-state explanation.
2. Backend `403` should use `You do not have permission to perform this action.`.
3. Missing project root or other local-project-directory problems must remain configuration errors, not permission errors.
4. Status edit must not introduce approval-language that implies ordinary NumericWorkbench testing requires administrator acceptance.

## Recommended Validation For Later Implementation

When `P3.7c-2` is implemented later, the expected focused validation should include:

1. `capabilities` undefined -> local trusted fallback still allows interaction.
2. `knowledge.map.read` only -> map review loads, status controls remain disabled.
3. `knowledge.map.read` plus `knowledge.map.edit` -> status controls are enabled.
4. Changing status updates local draft only until save.
5. Save uses the existing `saveFormalMap` wrapper.
6. Save success refreshes formal map.
7. No build or set-current call is triggered.
8. TypeScript passes.

## Final Review Result

Boundary approved:

1. `P3.7c-2` should be a minimal status-only edit slice.
2. The editable surface is limited to `systems`, `tables`, `docs`, and `scripts` status values.
3. Relationships are not edited automatically and are deferred to `P3.7c-3`.
4. Save continues to use the existing full-map `PUT /game/knowledge/map` boundary.
5. Permission rules remain `knowledge.map.read` for review and `knowledge.map.edit` for editing or save.
6. The next implementation slice should be minimal frontend status edit, not relationship editor or graph canvas.

## Implementation Status Update

Status as of 2026-05-08: the recommended `P3.7c-2` minimal frontend formal map status edit slice is now implemented.

Implemented scope:

1. The implementation files are `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/GameProject.module.less`.
2. Candidate map remains read-only.
3. Saved formal map is the only editable object in this slice.
4. Editable fields are limited to `systems`, `tables`, `docs`, and `scripts` status values.
5. Allowed status values remain limited to `active`, `deprecated`, and `ignored`.
6. This slice does not expose editing for ids, titles, `source_path`, `source_hash`, `relationships`, `deprecated`, `release_id`, or `schema_version`.
7. Save continues to use the existing `saveFormalMap` wrapper over `PUT /game/knowledge/map`.
8. No PATCH API was added.
9. Save does not build a release, does not set current release, does not modify release history, and does not read or write SVN.
10. Relationship handling remains warning-only and does not auto-clean or auto-rewrite relationships.
11. Relationship editor remains deferred to `P3.7c-3`.
12. The permission boundary is unchanged: `knowledge.map.read` for review and `knowledge.map.edit` for edit or save, with backend `403` still as the final boundary.

Validation summary:

1. TypeScript passed in the console workspace via `npm exec tsc -- -p tsconfig.app.json --noEmit --incremental false`.
2. `git diff --check` reported no patch-format errors and only CRLF/LF warnings.
3. There are no existing GameProject or formal-map frontend tests in this repository to run for this slice.
4. Code review is complete.
