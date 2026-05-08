# Knowledge P3.7c Formal Map Review UX Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-7a-formal-map-read-save-boundary-review-2026-05-07.md
4. docs/tasks/knowledge-permission-boundary-review-2026-05-08.md
5. docs/tasks/knowledge-frontend-permission-ui-boundary-review-2026-05-08.md
6. docs/tasks/knowledge-frontend-permission-copy-review-2026-05-08.md
7. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md

## Review Goal

Define the minimum formal map review UX boundary and choose the first frontend implementation slice.

This review is documentation only. It does not add frontend UI, backend routes, API changes, RAG expansion, LLM integration, graph editing, or SVN behavior.

## Current Backend Capability

The current landed backend capability is already sufficient for a minimal formal map review UX.

Current backend state:

1. `GET /game/knowledge/map/candidate` can read the candidate map.
2. `GET /game/knowledge/map` can read the saved formal map or return `no_formal_map`.
3. `PUT /game/knowledge/map` can save validated formal map state.
4. Safe build snapshots `working/formal_map.json` into the next release when build is explicitly triggered.
5. Build does not automatically set current release.
6. Candidate inclusion during build does not mutate formal map.
7. Candidate map remains advisory read state until a user explicitly saves formal map or later builds a release.

## Permission Boundary

The UX must follow the already-landed backend capability split.

Required capability rules:

1. Viewing candidate map requires `knowledge.map.read`.
2. Viewing saved formal map requires `knowledge.map.read`.
3. Saving formal map requires `knowledge.map.edit`.
4. Building a release requires `knowledge.build`.
5. Setting current release or publish requires `knowledge.publish`.
6. Frontend disabled state is advisory only; backend `403` remains the final boundary.

Frontend behavior rules:

1. Governance actions should default to disabled-with-explanation rather than hidden when the surrounding section is visible.
2. Missing permission must use the fixed copy `You do not have permission to perform this action.` for backend `403`.
3. Disabled-state copy should remain action-scoped and permission-shaped, not SVN-shaped or project-root-shaped.
4. `no_formal_map`, `no current release`, and missing project root must not be collapsed into permission errors.
5. Ordinary NumericWorkbench fast-test flows must remain separate and must not be described as administrator approval flows.

## Recommended UI Placement

The first UX slice should not introduce a new governance console or standalone page.

Recommended placement:

1. Place formal map review inside the existing GameProject release or knowledge surface.
2. A section or modal is preferred over a new route.
3. The UX should stay close to release build and current-release status because formal map is governance state for later build, not a workbench experiment.
4. NumericWorkbench should remain unchanged in this slice.

Rejected placement for the first slice:

1. Do not create a new large map-governance page.
2. Do not place formal map review inside ordinary fast-test flows.
3. Do not make release-candidate or test-plan state look like mandatory approval steps for ordinary tests.

## Minimal UX Goal

The first formal map review UX should remain narrow and review-oriented.

Recommended first-version scope:

1. Add a `Map Review` section or modal inside the existing GameProject release or knowledge panel.
2. Load candidate map through `GET /game/knowledge/map/candidate`.
3. Load saved formal map through `GET /game/knowledge/map`.
4. When backend returns `no_formal_map`, show an explicit `no saved formal map` state.
5. Show `systems`, `tables`, `docs`, `scripts`, and `relationships` as scan-friendly lists.
6. Provide a `Save as formal map` action that saves the candidate map or current in-memory review copy through `PUT /game/knowledge/map`.
7. After save, do not build a release.
8. After save, do not set current release.
9. After save, show a small note that the saved formal map can be included the next time `Build knowledge release` is run.

This first slice is intentionally not a full editor.

## Explicit Non-Goals

The first formal map review UX must not turn into a graph editor or a complete governance workstation.

Not in scope for the first slice:

1. No graph canvas.
2. No drag-and-drop relationship editor.
3. No LLM map generation.
4. No candidate-to-map auto merge.
5. No `candidate_evidence` to map patch pipeline.
6. No automatic build after save.
7. No automatic publish or set-current after save.
8. No SVN sync, update, commit, or any other SVN behavior.
9. No raw JSON as the primary UX.
10. If raw JSON appears later, it should be debug or advanced read-only only.

## Editing Boundary

The first slice should choose the narrowest possible editing boundary.

Recommended staged strategy:

1. `P3.7c-1`: read-only review plus `Save as formal map` using candidate map or current review copy, with no field-level editing.
2. `P3.7c-2`: status-only editing for `active`, `deprecated`, and `ignored`.
3. `P3.7c-3`: relationship review or edit.

Chosen first implementation slice:

1. Choose `P3.7c-1`.
2. Do not start with field-level editing.
3. Do not start with relationship editing.
4. Treat the initial save action as explicit formalization of the reviewed candidate or current review copy, not as a full governance editor.

Reasoning:

1. The backend API already supports review and save without needing new routes.
2. This keeps the first slice additive and low-risk.
3. It avoids prematurely introducing complex per-field mutation semantics.
4. It gives product users a visible formal-map state before build without coupling save to build or publish.

## API Usage Boundary

The first slice should use only existing APIs.

Allowed API usage:

1. `GET /game/knowledge/map/candidate`
2. `GET /game/knowledge/map`
3. `PUT /game/knowledge/map`

Not allowed in this slice:

1. No new backend API.
2. No new map review mutation API.
3. No new release build or publish API behavior.

Response-handling rules:

1. `403` should use the fixed message `You do not have permission to perform this action.`
2. `no_formal_map` should be rendered as explicit absence, not an error.
3. `No current knowledge release is set` for candidate map should not be relabeled as permission denial.
4. Missing or invalid local project directory should stay a configuration or environment error, not a permission error.

## UX Interaction Rules

The UX should keep governance actions visible but narrow.

Recommended interaction rules:

1. If `knowledge.map.read` is missing, the Map Review section may remain visible but should load no governance data and should show permission denial cleanly.
2. If `knowledge.map.edit` is missing, review remains read-only and `Save as formal map` stays disabled.
3. If `knowledge.build` is missing, do not enable release build from this review surface.
4. If `knowledge.publish` is missing, do not enable set-current or publish actions from this review surface.
5. Saving formal map should not imply release build, release candidate acceptance, or publish.

## Relationship To Fast-Test Boundary

Formal map review UX must not break the fast-test product rule.

Required product semantics:

1. Formal map review is governance UX, not ordinary fast-test UX.
2. Ordinary NumericWorkbench changes still do not require administrator acceptance.
3. Release candidates remain build-time optional inputs, not mandatory approvals for ordinary tests.
4. Formal map review must not reframe test plans or release candidates as the normal path for everyday workbench edits.

## Recommended First Implementation Slice

The next implementation slice should be small and frontend-only.

Recommended slice:

1. `P3.7c-1` minimal frontend formal map review section or modal.
2. Scope: `console/src` only.
3. Use only existing `GET /game/knowledge/map/candidate`, `GET /game/knowledge/map`, and `PUT /game/knowledge/map` APIs.
4. Do not add backend code.
5. Do not add new API.
6. Run TypeScript validation.
7. If there are no existing frontend tests for this area, state that clearly rather than inventing new backend validation work.

## Final Review Result

Boundary approved:

1. The current backend capability is sufficient for a minimal formal map review UX without adding new API.
2. The first UX slice should be a small GameProject-adjacent section or modal, not a new page or graph editor.
3. The first UX slice should choose `P3.7c-1`: review plus `Save as formal map`, with no field-level edit.
4. Save must remain decoupled from build and publish.
5. Permission-aware disabled state should be used in the frontend, while backend `403` remains the final boundary.
6. Formal map review must remain separate from ordinary NumericWorkbench fast-test semantics.
