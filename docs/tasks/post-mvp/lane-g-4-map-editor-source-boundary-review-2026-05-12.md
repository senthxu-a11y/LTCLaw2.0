# Lane G.4 Map Editor Source-Boundary Review

Date: 2026-05-12
Status: source-boundary review
Scope: define the smallest safe migration from Project-page formal map transition area to the dedicated Map Editor page

## 1. Final Recommendation

Proceed to G.4 implementation, but keep the first slice narrow.

The dedicated Map Editor should own the existing formal map review and editing surface. It should not become a new backend capability, a new release publisher, or a replacement for Project configuration.

The first implementation slice should move the existing formal map UI semantics to `/game/map` by extracting or reusing the current Project-page logic, while leaving Project with only a compact saved/candidate summary and an "Open Map Editor" entry.

## 2. Current Source Boundary

Current formal map implementation still lives inside:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/GameProject.module.less`
3. `console/src/api/modules/gameKnowledgeRelease.ts`

The API surface already exists:

1. `getMapCandidate(agentId)`
2. `getFormalMap(agentId)`
3. `saveFormalMap(agentId, map, updatedBy)`

No backend API change is needed for G.4.

## 3. Current Formal Map Ownership In GameProject

`GameProject.tsx` owns these formal map states:

1. `candidateMapLoading`
2. `candidateMapError`
3. `candidateMap`
4. `candidateMapReleaseId`
5. `formalMapLoading`
6. `formalMapError`
7. `formalMap`
8. `formalMapDraft`
9. `savingFormalMap`
10. `savingFormalMapDraft`

It also owns these formal map actions:

1. `fetchCandidateMap`
2. `fetchFormalMap`
3. `fetchMapReviewData`
4. `handleSaveFormalMap`
5. `handleSaveFormalMapDraft`
6. `updateFormalMapDraftStatus`

And these render helpers:

1. `renderStatusControl`
2. `renderSystemList`
3. `renderTableList`
4. `renderDocList`
5. `renderScriptList`
6. `renderRelationshipList`

These are all Map Editor concerns.

## 4. What Should Move To Map Editor

Move these to `/game/map`:

1. Candidate map review panel
2. Saved formal map review panel
3. Save as formal map
4. Saved formal map status-only edit
5. Save status changes
6. Relationship warning display
7. Candidate/saved counts
8. `no_current_release` and `no_saved_formal_map` handling
9. permission copy for `knowledge.map.read` and `knowledge.map.edit`

The save semantics must remain unchanged:

1. Save as formal map saves the current candidate map.
2. Status edit saves the local draft of the saved formal map.
3. Neither action builds a release.
4. Neither action publishes a release.
5. Relationship warnings remain advisory and do not mutate the map by themselves.

## 5. What Must Stay On Project

Keep these in Project:

1. Project basic info
2. local project directory
3. SVN and storage configuration
4. Watch configuration
5. Workflow configuration
6. Save / validate / reset project config
7. Create-agent wizard
8. Storage snapshot
9. Workspace entry cards

Project may keep a compact map summary and an "Open Map Editor" action, but it should not continue to expose the full candidate/saved formal map editor after G.4.

## 6. Existing `/game/map` Caveat

The current `/game/map` implementation appears to be `IndexMap.tsx`, which is a table index/dependency browser. It is not the formal map editor described by Lane G.

G.4 should not pretend this existing table index page is the final Map Editor. The first implementation should either:

1. replace the `/game/map` route body with the formal map editor surface, or
2. add a clear Map Editor shell that owns formal map review first and demotes the table index view to a secondary tab or later lane.

The safest first slice is to put formal map review/edit first on `/game/map`, because that is the behavior currently stranded on Project.

## 7. Recommended Minimal Implementation Slice

Recommended G.4 slice:

1. Extract a small `FormalMapWorkspace` component from `GameProject.tsx`, or create an equivalent dedicated component using the existing API calls.
2. Use it as the main body of `/game/map`.
3. Keep candidate map and saved formal map side by side.
4. Preserve `Save as formal map`.
5. Preserve saved formal map status-only edit.
6. Preserve relationship warnings.
7. Keep Project with compact candidate/saved counts and an "Open Map Editor" button.
8. Keep Project's config form, storage, save, validate, reset, and create-agent wizard unchanged.

Do not split the backend or introduce new API calls in this slice.

## 8. Implementation Risk

Primary risk:

1. duplicated formal map logic between Project and Map Editor

Preferred mitigation:

1. extract a presentational/workspace component rather than copy large render blocks
2. keep the component close to existing Game page modules
3. preserve existing API calls and permission checks

Secondary risk:

1. Project page still needs a low-exposure summary while Map Editor owns the full editor

Preferred mitigation:

1. leave Project's compact summary only
2. remove full candidate/saved map panels from Project after `/game/map` owns them

## 9. Explicit Non-Goals

Do not do any of the following in G.4:

1. change backend APIs
2. change formal map save semantics
3. build or publish knowledge releases
4. add automatic formal map writes from RAG or chat
5. add provider selector
6. add API key UI
7. change Ask schema
8. change NumericWorkbench draft semantics
9. make `/game/map` a production-ready claim
10. perform production rollout

## 10. Suggested Smoke For G.4 Implementation

After implementation, smoke should verify:

1. `/game/project` still shows Project configuration and storage snapshot.
2. `/game/project` still shows only compact formal map summary plus "Open Map Editor".
3. `/game/map` loads candidate map and saved formal map states.
4. `/game/map` shows `no current release` safely when candidate map is unavailable.
5. `/game/map` can save candidate map as formal map where permissions allow.
6. `/game/map` can edit saved formal map statuses and save status changes where permissions allow.
7. Saving formal map does not build or publish a release.
8. Project save / validate / reset behavior is unchanged.
9. Existing Knowledge and NumericWorkbench routes are unchanged.

## 11. Go / No-Go

Go for G.4 implementation.

The next agent should implement the narrow migration slice above. If the extraction gets large or begins changing API semantics, stop and report instead of widening the lane.

