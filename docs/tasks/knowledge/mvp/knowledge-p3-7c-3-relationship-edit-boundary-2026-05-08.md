# Knowledge P3.7c-3 Relationship Edit Boundary Review

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/mvp/knowledge-p3-7c-formal-map-review-ux-boundary-2026-05-08.md
4. docs/tasks/knowledge/mvp/knowledge-p3-7c-2-formal-map-status-edit-boundary-2026-05-08.md

## Review Goal

Decide whether relationship editing should enter the current conservative P3.7 closeout.

This review is documentation only. It does not add frontend UI, backend routes, PATCH semantics, graph editing, drag-and-drop editing, LLM behavior, build or publish coupling, or SVN behavior.

## Current State

The current landed formal map MVP state is:

1. Candidate map review exists in the existing GameProject formal-map review surface.
2. Saved formal map read and save already exist.
3. Saved formal map status-only edit already exists for `systems`, `tables`, `docs`, and `scripts`.
4. Relationship handling is currently warning-only.
5. Deprecated or ignored items may still be referenced by relationships, and the frontend does not auto-clean or auto-rewrite those relationships.

## Conservative Decision

Decision: relationship editor is deferred and does not enter the current conservative P3.7 closeout.

Chosen status:

1. `P3.7c-3-alpha` is completed as a docs-only boundary decision.
2. `P3.7c-3` implementation is intentionally not started in this closeout.

## Reasoning

Relationship editing is not required to complete the conservative formal map MVP loop.

Reasons:

1. The current closed loop already exists: candidate review -> save formal map -> status edit -> safe build snapshot.
2. Relationship editing materially expands the governance UX beyond the current conservative slice.
3. Relationship editing increases invalid-reference and mutation-scope risk without being required for the minimal usable formal map workflow.
4. The current warning-only behavior is sufficient for the conservative MVP because backend validation still protects the saved map boundary.

## If Implemented Later

If relationship editing is implemented in a future slice, the first version should remain narrow.

Allowed future-first-slice boundary:

1. Edit relationships only on saved formal map.
2. Candidate map remains non-editable.
3. Use a simple form-based add or remove interaction only.
4. `from_ref` and `to_ref` must be selected from refs that already exist in saved formal map.
5. The UI must not allow hand-entering a ref that does not already exist.
6. Save must still use the complete `PUT /game/knowledge/map` boundary through the existing full-map save path.
7. No PATCH API is added.
8. No backend API is added.
9. Save still must not build, must not set current release, must not modify release history, and must not read or write SVN.

## Explicit Non-Goals

Not part of the future-first relationship edit slice:

1. No graph canvas.
2. No drag-and-drop relationship editor.
3. No LLM relationship generation.
4. No automatic relationship cleanup.
5. No candidate-to-map auto merge.

## Final Review Result

Boundary approved:

1. Relationship editor is deferred and does not enter the current conservative P3.7 closeout.
2. `P3.7c-3-alpha` is complete as a docs-only boundary decision.
3. A future relationship edit slice, if needed, should remain simple, saved-formal-map-only, and form-based.
4. The current P3.7 MVP remains valid without relationship editor, graph canvas, or LLM-driven map editing.
