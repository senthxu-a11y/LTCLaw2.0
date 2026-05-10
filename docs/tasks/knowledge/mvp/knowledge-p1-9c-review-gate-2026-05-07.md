# Knowledge P1.9c Review Gate

Date: 2026-05-07

## Scope

This review gate covers the safe backend release-build boundary introduced by:

1. `POST /game/knowledge/releases/build-from-current-indexes`
2. server-side release build composition from current formal map and current indexes
3. prerequisite failures for missing current release, missing current indexes, and missing approved docs

It does not review the legacy full-payload build endpoint as a frontend contract.

## Boundary Decision

P1.9c is approved.

The new backend entry is narrow enough for productized frontend use because the frontend no longer transports derived release payloads.

## Boundary Findings

### 1. Router remains thin

The release router only:

1. resolves workspace and local project directory
2. forwards `release_id`, `release_notes`, optional `candidate_ids`
3. maps service exceptions to HTTP errors

It does not assemble `KnowledgeMap`, `TableIndex`, `DocIndex`, `CodeFileIndex`, or `KnowledgeDocRef` from frontend input.

### 2. Server-side inputs are authoritative

The service resolves build inputs from server-owned state:

1. current release map from app-owned release storage
2. current table indexes from the project table index store
3. current code indexes from the code index store
4. approved docs from knowledge-base entries with `source == "doc_library"`

This matches the P1.9b boundary review.

### 3. Prerequisite failures are explicit

The safe build path now fails clearly when:

1. no current release is set
2. current table indexes are missing
3. current code indexes are missing for mapped scripts
4. approved docs are missing for mapped docs
5. provided `candidate_ids` are not members of the current formal map

This is the correct failure mode for a frontend-safe build action.

### 4. No SVN coupling

The safe build path does not add SVN write, commit, or publish behavior.

The flow remains strictly local-project plus app-owned derived-assets composition.

### 5. No raw source copying

The build still writes only release metadata and derived assets:

1. `manifest.json`
2. `map.json`
3. `indexes/`
4. `release_notes.md`

It does not copy raw tables, raw docs, or raw scripts into the release.

## Validation

Focused P1.9c validation:

1. `12 passed` via:
   - `tests/unit/game/test_knowledge_release_service.py`
   - `tests/unit/routers/test_game_knowledge_release_router.py`
2. frontend typecheck later confirmed that P1.9d binds only to this safe endpoint.

## Review Result

P1.9c can be treated as the approved backend contract for the normal frontend build button.

The old `POST /game/knowledge/releases/build` endpoint should remain internal/test-only.
