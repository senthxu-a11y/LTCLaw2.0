# Knowledge P3.7a Formal Map Read/Save Boundary Review

Date: 2026-05-07

Authority:

1. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
2. docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md
3. docs/tasks/knowledge/mvp/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md
4. docs/tasks/knowledge/mvp/knowledge-p2-gate-status-2026-05-07.md
5. docs/tasks/knowledge/mvp/knowledge-p1-gate-status-2026-05-07.md

## Review Scope

This review defines the boundary for future formal `KnowledgeMap` read/save work.

It does not:

1. add a new backend API
2. add frontend UI
3. save a formal map
4. modify release assets
5. set current release
6. read or write SVN
7. connect an LLM, embedding, or vector store

## Current State

The current completed state before P3.7b is:

1. P3.5 completed a deterministic map candidate builder.
2. P3.6 completed a read-only candidate-map endpoint at `/api/agents/{agentId}/game/knowledge/map/candidate`.
3. The current system exposes candidate map inspection only.
4. There is no formal map edit/save API yet.
5. The current release build path still relies on server-side existing/formal map logic and must not be overridden by arbitrary frontend full-payload map submission.

## Core Boundary Decision

The formal map boundary should remain strict.

1. Formal `KnowledgeMap` is app-owned project-level state.
2. Formal map is not raw source.
3. Formal map is not pending test-plan state.
4. Formal map is not release-candidate state.
5. Saving formal map must not modify an existing release.
6. Saving formal map must not trigger release build.
7. Saving formal map must not set current release automatically.
8. Saving formal map must not read or write SVN.
9. Formal map should affect release output only on a later safe build.
10. Frontend must not be allowed to overwrite map state with unvalidated arbitrary large JSON payloads.
11. Backend must validate schema, source refs, status, and relationships before any future save succeeds.

## Recommended Storage Location

Formal map should live in app-owned project storage, not inside release history.

Recommended location:

1. `working/formal_map.json`

Acceptable alternative if naming consistency is preferred:

1. `working/map.json`

Storage rules:

1. Do not store formal map under `releases/<release_id>/map.json` because that would mutate historical release assets.
2. Do not store formal map under `pending/test_plans.jsonl`.
3. Do not store formal map under `pending/release_candidates.jsonl`.
4. The path must remain under the app-owned project store.
5. Future implementation may reuse existing knowledge path helpers or add a dedicated helper, but it must stay inside the same app-owned project storage boundary.

## API Boundary Recommendation

P3.7b should be backend-only.

Recommended future API surface:

1. `GET /game/knowledge/map`
2. `PUT /game/knowledge/map`
3. Keep `GET /game/knowledge/map/candidate` as the existing P3.6 read-only candidate endpoint.

### Recommended GET Strategy

Recommended behavior for `GET /game/knowledge/map` when no saved formal map exists:

1. Return explicit `no_formal_map`.
2. Do not silently fall back to current release map.

Reasoning:

1. Silent fallback would blur the boundary between saved project-level formal state and release snapshot state.
2. Candidate-map and current-release-map inspection already have separate roles.
3. Explicit absence keeps later save/build rules auditable.

### Recommended PUT Strategy

Future `PUT /game/knowledge/map` should:

1. save validated formal map only
2. not build release
3. not set current release
4. not mutate any historical release directory
5. stay behind thin router plus validated store/service logic

## Validation Rules

Future formal-map save must reject invalid payloads early.

Required validation rules:

1. `schema_version` must match the expected `KnowledgeMap` schema.
2. `systems`, `tables`, `docs`, `scripts`, `relationships`, and `deprecated` must validate against the `KnowledgeMap` model.
3. Every `source_path` must be relative to the local project directory.
4. Absolute paths must be rejected.
5. `..` path escape must be rejected.
6. Relationship endpoints must reference objects that exist inside the submitted map, or the API must return a clear validation error.
7. `status` values must be limited to `active`, `deprecated`, or `ignored`.
8. Save logic must produce a deterministic `map_hash` before write.

Optional minimal metadata:

1. `previous_hash`
2. `updated_at`
3. `updated_by`

These should remain minimal and app-owned if added later.

## Relationship To Release Build

Formal map save and release build must remain decoupled.

1. Safe build may read the saved formal map on the next build.
2. Build should snapshot the current formal map into the new release's `map.json`.
3. Saving formal map must not rewrite any old `release/<release_id>/map.json`.
4. Saving formal map must not modify `current.json`.
5. Candidate map remains advisory only and must not automatically become formal map.

## Recommended P3.7b Direction

The next implementation step should be backend-only formal map persistence, not UI.

1. Add backend formal map store.
2. Add backend `GET /game/knowledge/map`.
3. Add backend `PUT /game/knowledge/map`.
4. Keep router thin.
5. Put validation and atomic app-owned write logic in store/service.
6. Add narrow tests for save/load, path guard, relationship validation, no release mutation, no set-current behavior, and no SVN access.
7. Do not add frontend UI in P3.7b.

## Final Review Result

P3.7a is completed as a formal map read/save boundary-review phase.

The approved direction is:

1. formal map is app-owned project-level state
2. formal map save must not modify releases or set current release
3. formal map should be stored under app-owned working state, not release history or pending JSONL files
4. future `GET /game/knowledge/map` should return explicit `no_formal_map` when no saved formal map exists
5. future `PUT /game/knowledge/map` must validate schema, refs, status, and relationships before save
6. future release build may consume saved formal map only when a later safe build is explicitly triggered
7. the next implementation step is backend formal map store plus GET/PUT API, not frontend UI
