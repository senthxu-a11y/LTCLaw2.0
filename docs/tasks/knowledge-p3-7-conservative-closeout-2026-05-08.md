# Knowledge P3.7 Conservative Closeout

Date: 2026-05-08

Authority:

1. docs/tasks/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge-p3-7a-formal-map-read-save-boundary-review-2026-05-07.md
4. docs/tasks/knowledge-p3-7c-formal-map-review-ux-boundary-2026-05-08.md
5. docs/tasks/knowledge-p3-7c-2-formal-map-status-edit-boundary-2026-05-08.md
6. docs/tasks/knowledge-p3-7c-3-relationship-edit-boundary-2026-05-08.md

## Closeout Goal

Record whether P3.7 formal map work has reached a conservative, usable MVP closeout.

This closeout is documentation only. It does not add frontend UI, backend API, graph editing, relationship editing, LLM behavior, build or publish coupling, or SVN behavior.

## Landed P3.7 Facts

The following P3.7 facts are now treated as landed:

1. `P3.7a` formal map read/save boundary review is complete.
2. `P3.7b` backend formal map store plus `GET` or `PUT` API is complete.
3. `working/formal_map.json` is app-owned project working state.
4. `GET /game/knowledge/map` returns saved formal map or `no_formal_map`.
5. `PUT /game/knowledge/map` saves formal map.
6. Saving formal map does not build a release.
7. Saving formal map does not set current release.
8. Saving formal map does not read or write SVN.
9. `P3.7b+` safe build prefers a valid `working/formal_map.json` when it exists.
10. Safe build snapshots the effective formal map into `releases/<release_id>/map.json`.
11. `manifest.map_hash` corresponds to the final `release/map.json` snapshot.
12. `P3.7c-1` already provides candidate map and saved formal map review in GameProject.
13. Candidate map is read-only advisory state.
14. `Save as formal map` saves candidate map only and does not build or publish.
15. `P3.7c-2` already provides saved-formal-map status-only edit.
16. Status-only edit is limited to `systems`, `tables`, `docs`, and `scripts` status values.
17. Allowed status values remain limited to `active`, `deprecated`, and `ignored`.
18. Relationship handling is still warning-only and does not auto-clean or auto-rewrite relationships.

## MVP Loop Result

The conservative formal map MVP loop is now complete.

Closed loop:

1. Review candidate map.
2. Save formal map.
3. Apply status-only edits on saved formal map.
4. Run safe build and snapshot the effective formal map into the release.

## What Is Not Required For This Closeout

The following items are explicitly not blockers for conservative P3.7 completion:

1. Relationship editor.
2. Graph canvas.
3. LLM map generation.

These are broader governance UX or later product-surface decisions rather than MVP blockers.

## P3.7c-3 Decision

`P3.7c-3-alpha` is complete as a docs-only boundary decision.

Decision:

1. Relationship editor is deferred.
2. It does not enter the current conservative closeout.
3. If implemented later, it should remain saved-formal-map-only, form-based, and continue to use complete-map `PUT /game/knowledge/map` save.

## Conservative Closeout Decision

Decision: P3.7 is conservatively complete.

Meaning:

1. The formal map MVP is usable.
2. The current MVP already covers formal map working-state persistence and release snapshot consumption.
3. Broader governance editing UX can remain deferred without blocking P3.7 closeout.

## Next-Phase Recommendation

Recommended next direction:

1. Do not continue expanding P3.7 UI in the immediate next slice.
2. Prefer P3 gate consolidation or the P3 RAG or model-client boundary direction instead.
3. Keep later map-governance UX expansion optional and explicitly scoped if product needs it.

## Still Not Implemented

These items remain intentionally outside conservative P3.7 completion:

1. Relationship editor.
2. Graph canvas.
3. Real LLM integration.
4. Embedding or vector store.
5. Frontend RAG UI.
6. Candidate-evidence RAG usage.
7. Broader map governance UX if later needed.

## Final Result

Closeout approved:

1. P3.7 formal map MVP is conservatively complete.
2. The completed loop is candidate review -> save formal map -> status edit -> safe build snapshot.
3. Relationship editor is explicitly deferred and is not a blocker for P3.7 closeout.
4. The next phase should move to broader P3 consolidation or RAG or model-client boundary work rather than continuing P3.7 UI expansion.
