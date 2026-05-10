# Knowledge P1.9b Build UX Boundary Review

Date: 2026-05-07

Authority:

1. docs/plans/knowledge-architecture-handover-2026-05-06.md
2. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md
3. docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md
4. docs/tasks/knowledge/mvp/knowledge-p1-gate-status-2026-05-07.md

## Review Scope

This review covers one narrow decision only:

1. Whether a normal frontend build release button should be added on top of the current backend build endpoint.
2. If not, what backend boundary should exist first.

This review does not change product code, API behavior, or current P1 scope.

## Current State

P1.1-P1.9a are complete.

Current frontend scope stops at P1.9a:

1. View current knowledge release.
2. View release list.
3. Set current release.

Current backend already has a build endpoint, but it is still an internal skeleton. Its input shape accepts full derived payloads such as:

1. knowledge_map
2. table_indexes
3. doc_indexes
4. code_indexes
5. knowledge_docs

That shape is acceptable for backend tests and internal orchestration, but it is not a safe ordinary frontend build contract.

## 1. Current Build Endpoint Risk

The current build endpoint should not be exposed as a normal frontend button for these reasons.

Its current positioning should remain:

1. internal entry
2. test entry
3. backend orchestration entry

It should not be treated as a normal frontend build release button contract.

### 1.1 Full Derived Payload Risk

The endpoint accepts already-derived structures rather than a narrow build intent.

That means a frontend caller would need to assemble or transport:

1. map payload
2. table index payload
3. doc index payload
4. code index payload
5. approved knowledge doc payload

This is too much responsibility for a normal UI action.

### 1.2 Frontend Assembly Risk

If the frontend builds these payloads directly, it implicitly takes on responsibilities that should remain server-side:

1. Selecting which server-side assets are authoritative.
2. Deciding which map/index snapshot is used.
3. Serializing large derived structures correctly.
4. Keeping payload schema aligned with backend internals.

This increases coupling between UI and internal release composition logic.

### 1.3 Server-Side Source Of Truth Risk

The current local-first design assumes the application owns the derived assets and the release store.

If the frontend can push full derived payloads directly into release build, the system becomes easier to misuse:

1. Build inputs may drift away from the server-side current index stores.
2. Build inputs may bypass the formal map or any later map confirmation flow.
3. The UI may become an accidental second source of truth for release composition.

That would be opposite to the intended architecture.

### 1.4 Product Boundary Risk

The authoritative design documents place map confirmation, release candidate inclusion, and release build under explicit admin-only release-time choices.

A direct frontend button bound to the current full-payload endpoint would blur these boundaries:

1. map confirmation boundary
2. release candidate inclusion boundary
3. release build boundary

This is especially risky because P1.9a intentionally did not ship map review UX or candidate selection UX.

## 2. Current Risk Of Adding A Build Button Directly

If a normal frontend build button is added now on top of the current endpoint, the main risks are:

1. The frontend would need to pass large TableIndex, DocIndex, and CodeFileIndex payloads.
2. The frontend could pass data inconsistent with the current local project directory.
3. The frontend could bypass formal map, approved docs, or existing index stores as server-side inputs.
4. P2 release candidate inclusion would become harder to connect cleanly, because build input semantics would already be coupled to large frontend payload assembly.
5. Security boundaries and product semantics would both become blurred, because a normal button would implicitly expose an internal composition contract.

## 3. Recommended Build UX Layering

The recommended layering is:

1. P1.9a: read-only release status/list/set-current UI. Completed.
2. P1.9b: build UX boundary review. This document.
3. P1.9c: backend safe build-from-current-indexes endpoint. Optional but required before a normal button.
4. P1.9d: frontend build button that calls only the safe endpoint.

This layering keeps the product moving without exposing internal composition contracts too early.

### P1.9a

Already complete:

1. Read current knowledge release.
2. Read release list.
3. Set current release.

No build button was added here by design.

### P1.9b

This review confirms:

1. The current build endpoint is not a normal UI contract.
2. A safe frontend build button needs a narrower backend boundary first.

### P1.9c

If productization continues, the next backend step should be a server-side build-from-current-indexes endpoint.

Its job would be:

1. Read the local project directory from server-side configuration.
2. Read existing formal map from server-owned storage.
3. Read existing index stores from server-owned storage.
4. Optionally read selected candidate ids from server-owned pending storage.
5. Build the app-owned release store entry.

The frontend should not be responsible for composing these internals.

### P1.9d

Only after P1.9c exists should a normal frontend build button be considered.

That button should send only narrow build intent, not the full derived asset payload.

## 4. Preconditions For A Formal Build Button

Before any normal build release button is added, these conditions should hold.

### 3.1 Server-Side Inputs Must Be Authoritative

The backend must be able to resolve build inputs from server-side state:

1. local project directory
2. existing index stores
3. formal map
4. optional selected release candidates

The frontend should not transport full TableIndex, DocIndex, or CodeFileIndex payloads.

### 3.2 Frontend Input Must Stay Narrow

The frontend should send only small intent fields such as:

1. release_id
2. release_notes
3. optional candidate_ids

The frontend should not send:

1. TableIndex arrays
2. DocIndex arrays
3. CodeFileIndex arrays
4. full knowledge_map payload
5. full knowledge_docs payload

### 3.3 Release Output Must Stay App-Owned

The result of a build should still be written only to the app-owned release store.

That means:

1. manifest.json
2. map.json
3. indexes/
4. release_notes.md
5. current.json only when explicitly switched

After a successful build, the resulting release should be immediately usable by the existing release surfaces:

1. it can be listed
2. it can be set current
3. it can be queried through current-release query after set-current

### 3.4 No SVN Coupling

The build flow should not read or write SVN operations as part of the normal frontend button path.

Specifically:

1. no SVN write
2. no SVN commit
3. no SVN publish semantics

The UX should remain framed as knowledge release over local project resources.

### 3.5 No Raw Source File Copying

The build path must preserve the existing P1 rule:

1. do not copy raw source tables
2. do not copy raw design docs
3. do not copy raw scripts

Releases should continue to contain only derived assets and release metadata.

## 5. Minimal Safe Build API Draft

If P1.9c is approved, the safer contract shape would be something like:

POST /game/knowledge/releases/build-from-current-indexes

Request:

```json
{
  "release_id": "v2026.05.07.001",
  "release_notes": "Build from current local indexes",
  "candidate_ids": []
}
```

Response:

```json
{
  "release_dir": "...",
  "manifest": {},
  "artifacts": {}
}
```

This draft is intentionally narrow.

Its purpose is:

1. express build intent
2. keep composition server-side
3. avoid large frontend payloads
4. preserve server-side source of truth

This document does not propose implementing that endpoint now. It only defines the boundary that should exist before a normal build button is considered.

## 6. P1 Phase Recommendation

For P1, the recommendation is:

1. Do not add a build release button yet.
2. Do not bind the frontend directly to the current full-payload build endpoint.
3. If build UX continues, do P1.9c first as a backend safe endpoint.
4. Only after that, consider P1.9d frontend build button.
5. If the team decides not to do build UX immediately, it is acceptable to move to P2 test plan store, but the recommended sequencing is to finish the P1 build UX boundary through P1.9c first.

If build UX is not the immediate priority, it is also reasonable to stop here and move to P2 test plan store work instead.

That sequencing is safer than exposing a misleading button too early.

## 7. Risk Conclusion

Current conclusion:

"当前 build endpoint 可保留为内部/测试入口，但不应直接暴露为普通前端 build release 按钮。正式 build 按钮必须等待 server-side build-from-current-indexes endpoint。"
