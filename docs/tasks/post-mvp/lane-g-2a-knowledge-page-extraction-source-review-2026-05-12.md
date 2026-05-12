# Lane G.2a Knowledge Page Extraction Source Review

Date: 2026-05-12
Status: source review
Scope: freeze the implementation boundary for moving Knowledge runtime blocks from GameProject to /game/knowledge without changing business semantics

## 1. Final Recommendation

Result: proceed

Reason:

1. The Knowledge slice inside `console/src/pages/Game/GameProject.tsx` is already coherent enough to migrate as one route-level page container.
2. The G.1 route skeleton is already in place, so G.2 can focus on moving release/RAG/citation runtime blocks into `console/src/pages/Game/Knowledge/index.tsx` without reopening route or navigation work.
3. The risky parts are known and local: permission gating, release pointer operations, structured query affordance, and citation deep-link query params.
4. Formal map editing, NumericWorkbench, SVN, provider selection, and backend/API/schema concerns can remain untouched.

## 2. Exact G.2 Implementation Scope

G.2 should move only the Knowledge runtime slice from `GameProject.tsx` into `/game/knowledge`.

Move into Knowledge page:

1. Current Release summary block.
2. Release list block.
3. Set current action.
4. Rollback to previous action.
5. Build-from-current-indexes entry and build modal.
6. RAG Ask input, loading/error/result state, example questions, recent questions.
7. Structured query side panel and readonly result rendering.
8. Citation list, Focus citation interaction, and Open in workbench entry.
9. `doc_knowledge=0` insufficient-context hint.
10. Knowledge Status summary only, derived from current candidate/saved formal map data.
11. Candidate/saved formal map readonly counts and metadata summary only.

Keep in Project page:

1. Project basic info form.
2. SVN/local project directory form fields.
3. Watch configuration.
4. Workflow configuration.
5. Storage snapshot / storage groups.
6. Path and config validation.
7. Save / reset actions.
8. Create-project-agent wizard.
9. Footer actions for reset / validate / save / create agent.

Recommended Project-side render change in G.2:

1. Remove the full Knowledge release/RAG section from `GameProject.tsx`.
2. Replace it with a minimal entry card or CTA pointing to `/game/knowledge`.
3. Keep the formal map review section in Project until G.4.

## 3. Exact Hard-No List

Do not move or change in G.2:

1. Formal map review/editor body.
2. Save as formal map.
3. Formal map status edit flow.
4. `formalMapDraft` editing logic.
5. `updateFormalMapDraftStatus`.
6. `handleSaveFormalMap`.
7. `handleSaveFormalMapDraft`.
8. NumericWorkbench page or route.
9. Citation deep-link destination route.
10. SVN page or SVN behavior.
11. Provider selector or API key UI.
12. Backend API.
13. API schema.
14. Release build semantics.
15. Set-current semantics.
16. Rollback semantics.
17. RAG semantics.
18. Structured query response semantics.
19. Packaged runtime assets.
20. Route structure from G.1.

## 4. Affected Files

Required implementation files for G.2:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/Knowledge/index.tsx`

Likely additional files if extraction is done cleanly:

1. `console/src/pages/Game/Knowledge/components/KnowledgeReleasePanel.tsx`
2. `console/src/pages/Game/Knowledge/components/KnowledgeAskPanel.tsx`
3. `console/src/pages/Game/Knowledge/components/KnowledgeCitationList.tsx`
4. `console/src/pages/Game/Knowledge/components/KnowledgeStatusSummary.tsx`
5. `console/src/pages/Game/Knowledge/components/StructuredQueryPanel.tsx`

Optional only if needed:

1. `console/src/pages/Game/ragUiHelpers.ts`
2. `console/src/pages/Game/GameProject.module.less`

Files that should not need G.2 changes:

1. `console/src/layouts/MainLayout/index.tsx`
2. `console/src/layouts/Sidebar.tsx`
3. `console/src/pages/Game/NumericWorkbench.tsx`
4. `console/src/pages/Game/SvnSync.tsx`
5. backend/API/schema files

## 5. Migration Block Map From GameProject To Knowledge

### 5.1 State That Belongs To Knowledge

Move these state slices out of `GameProject.tsx` and into `Knowledge/index.tsx`:

1. `releaseLoading`
2. `releaseError`
3. `releases`
4. `currentRelease`
5. `previousRelease`
6. `settingCurrentId`
7. `buildModalOpen`
8. `buildingRelease`
9. `buildCandidatesLoading`
10. `buildCandidatesError`
11. `buildCandidates`
12. `selectedCandidateIds`
13. `ragQuery`
14. `ragLoading`
15. `ragError`
16. `ragAnswer`
17. `structuredQueryPanelOpen`
18. `structuredQueryDraft`
19. `structuredQueryLoading`
20. `structuredQueryResponse`
21. `recentRagQuestions`
22. `highlightedCitationId`
23. `citationsSectionRef`
24. `citationRefs`
25. `citationHighlightTimeoutRef`

Readonly Knowledge-status state that may also move if the compact summary is implemented in G.2:

1. `candidateMapLoading`
2. `candidateMapError`
3. `candidateMap`
4. `candidateMapReleaseId`
5. `formalMapLoading`
6. `formalMapError`
7. `formalMap`

Do not move map-editing state in G.2:

1. `formalMapDraft`
2. `savingFormalMap`
3. `savingFormalMapDraft`

### 5.2 Effects And Fetch Logic That Belong To Knowledge

Move or recreate these in `Knowledge/index.tsx`:

1. `fetchKnowledgeReleases`
2. `fetchBuildCandidates`
3. `handleAskRagQuestion`
4. `handleOpenStructuredQueryPanel`
5. `handleCloseStructuredQueryPanel`
6. `handleSubmitStructuredQuery`
7. `focusCitation`
8. `handleCopyRagAnswer`
9. `handleGoToWorkbench`
10. `handleOpenCitationInWorkbench`
11. selected-agent reset for structured query state
12. citation highlight timeout cleanup

If Knowledge Status summary is included in G.2, move or recreate readonly fetch only:

1. `fetchCandidateMap`
2. `fetchFormalMap`
3. `fetchMapReviewData`

Do not move `fetchConfig` as-is.

Reason:

1. `fetchConfig` currently couples project form loading, storage snapshot loading, release loading, and map loading.
2. G.2 should split this into a Knowledge-page fetch path and leave project form/storage fetch in Project.

### 5.3 Derived Values That Belong To Knowledge

Move these derived values to Knowledge page:

1. `buildDisabledReason`
2. `publishDisabledReason`
3. `knowledgeReadReason`
4. `workbenchReadReason`
5. `releaseCandidateReadReason`
6. `recordRecentRagQuestion`
7. `formatRagMode`
8. `getLocalizedRagWarning`
9. `ragExampleQuestions`
10. `ragDisplayState`
11. `shouldShowEmptyDocContextHint`
12. `ragNextStepHints`
13. `groupedRagCitations`
14. `canSubmitStructuredQuery`

Readonly Knowledge-status summary values that can move without bringing map editing:

1. `candidateSummary`
2. `savedFormalMap`
3. compact counts derived from `formalMap?.map`
4. readonly saved-formal-map metadata such as `updated_at`, `updated_by`, and `map_hash`

Do not move these map-editing derivations in G.2:

1. `formalSummary`
2. `formalMapDraftDirty`
3. `formalMapRelationshipWarnings`
4. `saveFormalMapFirstReason`
5. `saveFormalMapDisabledReason`
6. `canSaveFormalMap`
7. `statusEditDisabledReason`
8. `canEditFormalMapStatuses`
9. `canSaveFormalMapDraft`

### 5.4 Render Blocks That Belong To Knowledge

Move these render blocks from `GameProject.tsx`:

1. The `Knowledge Release Status` card release summary block.
2. The release list block.
3. The build-release entry and build-release modal.
4. The rollback block.
5. The full `ragSection` block.
6. The structured query panel.
7. The RAG result block.
8. The citations block.
9. A new compact Knowledge Status summary built from candidate/saved formal map data.

Do not move these render blocks in G.2:

1. The `Formal map review` section.
2. The storage card.
3. The basic info card.
4. The SVN configuration card.
5. The watch configuration card.
6. The workflow configuration card.
7. The footer action bar.
8. The create-agent modal.

## 6. What Should Still Stay In Project

The following state/handlers remain Project-owned after G.2:

1. `form`
2. `loading`
3. `saving`
4. `error`
5. `storageSummary`
6. `wizardOpen`
7. `wizardSaving`
8. `wizardForm`
9. `fetchConfig` reduced to Project-only loading
10. `handleSave`
11. `persistFormToAgent`
12. `handleCreateProjectAgent`
13. `handleValidate`
14. `handleReset`
15. `storageGroups`

## 7. Exact Hard Boundary For Formal Map Summary In G.2

G.2 may show readonly status summary only.

Allowed summary content:

1. candidate map available or unavailable
2. candidate release id
3. candidate counts for systems/tables/docs/scripts/relationships
4. saved formal map available or unavailable
5. saved formal map hash
6. saved formal map updated_at / updated_by
7. saved formal map readonly counts

Not allowed in G.2 summary:

1. full system/table/doc/script listing UI
2. relationship list UI
3. status select controls
4. save buttons
5. dirty draft messaging
6. relationship warning editor workflow

## 8. Recommendation On Extraction Strategy

Recommendation: do not try to make `Knowledge/index.tsx` a thin wrapper that reuses partial `GameProject` JSX through prop drilling.

Reason:

1. `GameProject.tsx` mixes project form, storage, release, RAG, structured query, citation focus, and map review logic in one component.
2. Reusing partial local sections from `GameProject` would keep G.2 coupled to Project state ownership and make G.3 harder.
3. The safer first cut is a route-level `Knowledge` page container with page-local state ownership and small presentational children.

Suggested implementation style:

1. Put Knowledge runtime state and handlers directly in `Knowledge/index.tsx` first.
2. Extract presentational children under `Knowledge/components/` only when the data boundary is already clear.
3. Reuse existing translation keys.
4. Reuse `ragUiHelpers.ts` as-is when possible.
5. Reuse `GameProject.module.less` classes temporarily if that avoids CSS churn; do not redesign styles in G.2.

## 9. Suggested Minimal Safe Construction Slice

### 9.1 Suggested Files

Minimal safe file set:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/Knowledge/index.tsx`

Safer structured file set:

1. `console/src/pages/Game/GameProject.tsx`
2. `console/src/pages/Game/Knowledge/index.tsx`
3. `console/src/pages/Game/Knowledge/components/KnowledgeReleasePanel.tsx`
4. `console/src/pages/Game/Knowledge/components/KnowledgeAskPanel.tsx`
5. `console/src/pages/Game/Knowledge/components/KnowledgeCitationList.tsx`
6. `console/src/pages/Game/Knowledge/components/KnowledgeStatusSummary.tsx`
7. `console/src/pages/Game/Knowledge/components/StructuredQueryPanel.tsx`

### 9.2 Suggested Component / Helper Names

1. `KnowledgeReleasePanel`
2. `KnowledgeBuildReleaseModal`
3. `KnowledgeAskPanel`
4. `KnowledgeCitationList`
5. `KnowledgeStatusSummary`
6. `StructuredQueryPanel`
7. `useKnowledgeRuntimeState` only if the page becomes too large
8. `buildCitationWorkbenchTarget` may remain local or be extracted to `ragUiHelpers.ts` only if both pages need it

### 9.3 Suggested Migration Order

1. Replace `Knowledge/index.tsx` placeholder with a real page container.
2. Move release status, release list, build modal, set current, and rollback logic into Knowledge page.
3. Move RAG Ask, structured query, citation focus, and workbench deep-link logic into Knowledge page.
4. Add readonly Knowledge Status summary using candidate/saved formal map counts and metadata only.
5. Remove the migrated Knowledge release/RAG block from `GameProject.tsx`.
6. Replace removed Project-area content with a minimal entry link to `/game/knowledge` if needed.
7. Leave formal map review section untouched in Project.

## 10. Risks And Required Guardrails

### 10.1 selectedAgent / permissions

Risk:

1. Capability-gated buttons and permission messages are currently derived inside `GameProject.tsx` from `selectedAgentSummary?.capabilities`.

Guardrail:

1. Preserve `canBuildRelease`, `canPublishRelease`, `canReadKnowledge`, `canReadWorkbench`, `canReadReleaseCandidates`, and `permissionDeniedMessage` behavior exactly.

### 10.2 release status loading

Risk:

1. `fetchConfig` currently triggers `fetchKnowledgeReleases` and map loading as side effects.

Guardrail:

1. Do not carry `fetchConfig` into Knowledge page.
2. Split release loading into Knowledge-owned fetch.

### 10.3 RAG answer state

Risk:

1. `ragDisplayState`, warnings, next-step hints, and answer rendering are tightly coupled.

Guardrail:

1. Preserve `getRagDisplayState`, `getRagNextStepHintKeys`, warning localization, and recent-question recording behavior.

### 10.4 citation deep-link query contract

Risk:

1. `handleOpenCitationInWorkbench` builds query params for `/numeric-workbench`.

Guardrail:

1. Preserve the exact params contract: `table`, `row`, `field`, `from=rag-citation`, `citationId`, `citationTitle`, `citationSource`.
2. Do not rename route or query keys.

### 10.5 current release and formal map shared state

Risk:

1. G.2 wants readonly Knowledge Status summary, while full formal map review stays in Project until G.4.

Guardrail:

1. Readonly summary may duplicate fetches temporarily.
2. Do not introduce shared mutable draft state between Project and Knowledge in G.2.

### 10.6 i18n key reuse

Risk:

1. The migrated UI already uses many `gameProject.*` keys.

Guardrail:

1. Reuse existing keys in G.2.
2. Do not start a broad i18n rename during extraction.

### 10.7 CSS class reuse

Risk:

1. Knowledge UI classes currently live inside `GameProject.module.less` alongside project form and map-review styles.

Guardrail:

1. Prefer temporary reuse of the existing CSS module over a style redesign.
2. If style extraction is needed later, do it after the behavior move is stable.

## 11. Suggested Acceptance Checks

G.2 should pass only if all of the following remain true:

1. `/game/knowledge` shows Current Release summary, release list, build-release entry, RAG Ask, citations, and readonly Knowledge Status summary.
2. `/game/project` no longer renders the migrated Knowledge release/RAG body.
3. Build release still uses the same server-side endpoint and does not auto-set current.
4. Set current still updates only the current release pointer.
5. Rollback still routes through the same set-current behavior.
6. `doc_knowledge=0` insufficient-context hint still appears only in the same condition.
7. Structured query panel still behaves as readonly exact lookup.
8. Citation Focus still scrolls and highlights within the returned citation list.
9. Open in workbench still lands on `/numeric-workbench` with the same query contract.
10. Project config save/validate/reset still works.
11. Formal map review and save/status-edit UI still stays on Project and remains unchanged.
12. No backend/API/schema changes occur.

## 12. Suggested Next-Agent Implementation Prompt Draft

```text
You are Lane G.2 implementation agent. Only move the Knowledge runtime slice from GameProject to /game/knowledge. Do not enter G.3 or G.4.

Repository: e:/LTclaw2.0

Must read first:
1. docs/tasks/post-mvp/lane-g-game-workspace-page-split-checklist-2026-05-12.md
2. docs/tasks/post-mvp/lane-g-game-workspace-page-split-source-review-2026-05-12.md
3. docs/tasks/post-mvp/lane-g-1-game-workspace-route-skeleton-receipt-2026-05-12.md
4. docs/tasks/post-mvp/lane-g-2a-knowledge-page-extraction-source-review-2026-05-12.md
5. console/src/pages/Game/GameProject.tsx
6. console/src/pages/Game/GameProject.module.less
7. console/src/pages/Game/ragUiHelpers.ts
8. console/src/pages/Game/Knowledge/index.tsx

Goal:
1. Implement /game/knowledge as the real Knowledge runtime page.
2. Move Current Release, release list, build-release entry/modal, set current, rollback, RAG Ask, structured query, citations, Open in workbench, Focus citation, insufficient-context hint, and readonly Knowledge Status summary to /game/knowledge.
3. Remove the migrated Knowledge runtime body from /game/project.
4. Keep Project config, storage snapshot, validation, save/reset, and create-agent wizard on /game/project.

Hard no:
1. Do not move formal map review/editor body.
2. Do not move Save as formal map.
3. Do not move formal map status edit flow.
4. Do not change NumericWorkbench route or behavior.
5. Do not change SVN behavior.
6. Do not change provider selector or API key UI.
7. Do not change backend/API/schema.
8. Do not change packaged runtime assets.
9. Do not commit.

Validation required:
1. git diff --check
2. console local tsc noEmit
3. targeted eslint on touched TS/TSX files

Closeout must report:
1. changed files
2. migrated Knowledge blocks
3. what remained in Project
4. confirmation that formal map editing stayed out of G.2
5. confirmation that NumericWorkbench deep-link contract stayed unchanged
6. validation results
```

## 13. Validation Result

Validation command for this review step:

1. `Set-Location 'e:/LTclaw2.0'; git diff --check`

Expected review-step result:

1. pass

## 14. Review Conclusion

G.2 is ready to start as a narrow extraction lane.

Recommended implementation boundary:

1. move release/RAG/citation/structured-query runtime into Knowledge page
2. keep Project config/storage/wizard in Project
3. keep formal map editing entirely out of G.2
4. keep NumericWorkbench contract unchanged
5. prefer route-level Knowledge container with small presentational children over partial reuse of GameProject