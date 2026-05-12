# Lane G Game Workspace Page Split Checklist

Date: 2026-05-12
Status: planning checklist
Scope: split the overloaded game workspace into clear frontend pages without changing backend or workflow semantics

## 1. Goal

Split the current game workspace into four primary pages:

1. Project
2. Knowledge
3. Map Editor
4. Advanced

Keep NumericWorkbench as an independent workspace route because real-data validation has shown it is a first-class draft-only editing surface.

This lane is an information-architecture and frontend routing split. It must not change backend behavior, API schema, release semantics, RAG semantics, NumericWorkbench write semantics, formal map save semantics, provider ownership, or SVN behavior.

## 2. Hard Boundaries

Do not change:

1. backend API
2. API schema
3. ordinary RAG no-write behavior
4. release build semantics
5. set-current semantics
6. rollback semantics
7. formal map save semantics
8. NumericWorkbench draft-only semantics
9. proposal or export semantics
10. provider selector
11. API key UI
12. provider or model selection for ordinary users
13. SVN capability
14. SVN sync, update, or commit behavior
15. map editor MVP internal logic
16. automatic formal map writes from chat
17. automatic NumericWorkbench draft creation from chat

Allowed:

1. add frontend routes
2. add frontend page containers
3. move existing UI sections between pages
4. extract presentational components from `GameProject.tsx`
5. add entry cards and navigation links
6. reduce `GameProject` to a pure Project page
7. move low-frequency SVN entry under Advanced

## 3. Target Pages

### 3.1 Project

Route:

1. `/game/project`

Purpose:

Project onboarding and base configuration.

Owns:

1. Project Summary
2. Project Config
3. local project directory
4. agent binding summary
5. storage snapshot summary
6. workspace entry cards

Must not own:

1. RAG Ask
2. current release main panel
3. formal map editor body
4. doc library main area
5. provider config
6. SVN primary operations

### 3.2 Knowledge

Route:

1. `/game/knowledge`

Purpose:

Knowledge runtime and daily knowledge workflow.

Owns:

1. Current Release
2. release list
3. build-from-current-indexes entry
4. set current entry
5. RAG Ask
6. citations
7. doc library status
8. empty doc context message
9. workbench entry
10. knowledge status summary

Must not own:

1. project directory config form
2. formal map editor body
3. provider or API key UI
4. SVN

### 3.3 Map Editor

Route:

1. `/game/map`

Purpose:

Formal knowledge structure review and editing.

Owns:

1. existing formal map review/editor MVP
2. candidate map review
3. Save as formal map
4. saved formal map status-only edit

Must not own:

1. ordinary RAG Ask
2. NumericWorkbench draft editing
3. project onboarding config
4. SVN

### 3.4 NumericWorkbench

Route:

1. `/game/numeric-workbench`
2. keep any existing compatible route if currently different

Purpose:

Draft-only table edit workspace.

Owns:

1. citation target state
2. dirty edit
3. save session
4. export draft dry-run
5. proposal handoff

Must not own:

1. formal map editing
2. release publishing
3. SVN write-back

### 3.5 Advanced

Routes:

1. `/game/advanced`
2. `/game/advanced/svn`

Purpose:

Low-frequency operator, admin, and legacy tools.

Owns:

1. SVN or legacy entry
2. diagnostics placeholders
3. operator-only placeholders

Must not own:

1. ordinary daily Knowledge workflow
2. Project onboarding
3. RAG main path

## 4. Existing Module Migration Table

| Existing area | Target |
| --- | --- |
| GameProject top config form | Project / Project Config |
| GameProject project summary | Project / Project Summary |
| GameProject storage summary | Project / Storage Snapshot |
| GameProject current release status | Knowledge / Current Release |
| GameProject release list | Knowledge / Current Release |
| GameProject set current and rollback controls | Knowledge / Current Release |
| GameProject build-from-current-indexes entry | Knowledge / Current Release |
| GameProject RAG Ask | Knowledge / Ask |
| GameProject citation list | Knowledge / Ask |
| GameProject Open in workbench | Knowledge / Workbench Entry |
| GameProject doc-context-empty hint | Knowledge / Ask |
| GameProject formal map status summary | Knowledge / Knowledge Status |
| GameProject formal map review/editor | Map Editor |
| GameProject Save as formal map | Map Editor |
| GameProject saved formal map status edit | Map Editor |
| NumericWorkbench page | Keep standalone |
| SvnSync page | Advanced / SVN |
| DeepSeek/operator config | Keep out of ordinary pages; future Advanced/Operator only |
| Provider/API key config | Do not expose in this lane |

## 5. Route Plan

Add or normalize routes:

1. `/game/project`
2. `/game/knowledge`
3. `/game/map`
4. `/game/numeric-workbench`
5. `/game/advanced`
6. `/game/advanced/svn`

Compatibility:

1. keep old `game-project` route as an alias or redirect to `/game/project`
2. keep existing NumericWorkbench route working
3. keep existing deep links from citations working
4. do not break proposal or workbench routes
5. keep old map internals intact and only change page entry/container

## 6. Navigation Plan

Recommended sidebar order:

1. Project
2. Knowledge
3. Map Editor
4. NumericWorkbench
5. Advanced

Decision note:

Keep NumericWorkbench as first-level navigation for now because real-data validation proved it is a first-class daily workspace, not only a hidden downstream tool. Knowledge should still be the primary guided entry for citation-driven workbench usage.

## 7. Component Split Plan

Create page containers:

1. `ProjectPage`
2. `KnowledgePage`
3. `MapEditorPage`
4. `AdvancedPage`

Extract reusable modules:

1. `ProjectSummaryCard`
2. `ProjectConfigPanel`
3. `StorageSnapshotPanel`
4. `WorkspaceEntryCards`
5. `KnowledgeReleasePanel`
6. `KnowledgeAskPanel`
7. `KnowledgeCitationList`
8. `KnowledgeStatusPanel`
9. `KnowledgeDocLibraryStatusPanel`
10. `MapCandidatePanel`
11. `SavedFormalMapPanel`
12. `AdvancedToolsPanel`

Implementation rule:

Extract by existing UI blocks first. Do not redesign interactions while moving them.

## 8. Suggested File Layout

Preferred new structure:

```text
console/src/pages/Game/
  Project/
    ProjectPage.tsx
    ProjectPage.module.less
    components/
      ProjectSummaryCard.tsx
      ProjectConfigPanel.tsx
      StorageSnapshotPanel.tsx
      WorkspaceEntryCards.tsx

  Knowledge/
    KnowledgePage.tsx
    KnowledgePage.module.less
    components/
      KnowledgeReleasePanel.tsx
      KnowledgeAskPanel.tsx
      KnowledgeCitationList.tsx
      KnowledgeStatusPanel.tsx
      KnowledgeDocLibraryStatusPanel.tsx

  MapEditor/
    MapEditorPage.tsx
    MapEditorPage.module.less
    components/
      MapCandidatePanel.tsx
      SavedFormalMapPanel.tsx

  Advanced/
    AdvancedPage.tsx
    AdvancedPage.module.less
    AdvancedSvnPage.tsx
```

Temporary compatibility files may remain:

```text
console/src/pages/Game/GameProject.tsx
console/src/pages/Game/GameProject.module.less
```

During migration, `GameProject.tsx` can become a thin compatibility wrapper or the new Project page container.

## 9. Minimum Implementation Order

### G.0 Source Review And Freeze

1. Read `GameProject.tsx`.
2. Read route and nav config.
3. Read `NumericWorkbench.tsx`.
4. Read the existing `SvnSync` route/page.
5. Produce source review and exact impacted-file list.
6. Do not change code.

Output:

```text
docs/tasks/post-mvp/lane-g-game-workspace-page-split-source-review-2026-05-12.md
```

### G.1 Route Skeleton

1. Add page containers for Project, Knowledge, Map Editor, and Advanced.
2. Add routes.
3. Add nav entries.
4. Preserve old route compatibility.
5. Use placeholder panels only where needed.
6. Do not migrate behavior yet.

Validation:

1. Project route loads.
2. Knowledge route loads.
3. Map route loads.
4. Advanced route loads.
5. Old links still work.

### G.2 Move Knowledge Runtime Blocks

1. Move current release panel from GameProject to Knowledge.
2. Move RAG Ask to Knowledge.
3. Move citation list to Knowledge.
4. Move doc-context-empty hint to Knowledge.
5. Move workbench entry links to Knowledge.
6. Keep behavior identical.

Validation:

1. schema RAG answer still works.
2. `doc_knowledge=0` hint still appears.
3. citation Open in workbench still works.
4. no API/schema changes.

### G.3 Shrink Project Page

1. Keep project config form on Project.
2. Keep storage summary snapshot on Project.
3. Add entry cards to Knowledge, Map Editor, and NumericWorkbench.
4. Remove RAG and release runtime from Project.
5. Ensure save config still works.

Validation:

1. local project directory visible.
2. config save still works.
3. no SVN action triggered.
4. Knowledge entry works.

### G.4 Move Formal Map Body To Map Editor

1. Move candidate map review to Map Editor.
2. Move Save as formal map to Map Editor.
3. Move saved formal map status-only edit to Map Editor.
4. Knowledge keeps only formal map status summary and link.
5. Do not change save logic.

Validation:

1. candidate map visible.
2. saved formal map visible.
3. Save as formal map still works.
4. status-only controls still visible.
5. no build, set-current, or publish triggered.

### G.5 Move SVN To Advanced

1. Move existing SvnSync nav entry under Advanced.
2. Add `/game/advanced/svn`.
3. Keep existing SvnSync page behavior unchanged.
4. Do not add new SVN behavior.

Validation:

1. Advanced page loads.
2. Advanced SVN page loads.
3. no SVN command runs during page load.
4. old direct route either redirects or remains compatible.

### G.6 Runtime Build And Smoke

1. TypeScript noEmit.
2. targeted ESLint.
3. frontend build.
4. sync packaged runtime assets.
5. packaged JS syntax check.
6. browser smoke on packaged runtime.

Smoke checklist:

1. `/game/project`
2. `/game/knowledge`
3. `/game/map`
4. `/game/numeric-workbench`
5. `/game/advanced`
6. `/game/advanced/svn`
7. RAG schema answer
8. empty doc context hint
9. citation to NumericWorkbench
10. formal map review
11. project config display

### G.7 Closeout

1. Document final route map.
2. Document moved modules.
3. Document unchanged behaviors.
4. Document validation results.
5. Document deferred items.

Output:

```text
docs/tasks/post-mvp/lane-g-game-workspace-page-split-closeout-2026-05-12.md
```

## 10. Acceptance Criteria

A pass requires:

1. Project page no longer carries daily Knowledge workflow.
2. Knowledge page owns RAG, current release, and citations.
3. Map Editor owns formal map review/editing.
4. NumericWorkbench remains independent and deep-link compatible.
5. SVN is under Advanced or otherwise lower exposure.
6. real-data RAG still works.
7. citation to NumericWorkbench still works.
8. formal map review still works.
9. config save still works.
10. no backend/API/schema changes.
11. no provider/API key UI added.
12. no SVN behavior added.
13. packaged runtime smoke passes.

## 11. Deferred Items

Do not solve in Lane G:

1. provider selector
2. API key UI
3. ordinary user model selection
4. SVN capability changes
5. graph canvas
6. relationship editor
7. candidate map editing
8. doc parser expansion
9. automatic formal map write from chat
10. automatic NumericWorkbench draft from chat
11. production rollout

## 12. First Execution Prompt

```text
You are Lane G.0 game workspace page split source review agent. Only do source review and implementation planning. Do not change code.

Goal:
Freeze the Game workspace page split plan by mapping current GameProject sections to Project / Knowledge / Map Editor / Advanced, and produce the exact affected-file list plus implementation order.

Must read:
1. console/src/pages/Game/GameProject.tsx
2. console/src/pages/Game/GameProject.module.less
3. console/src/pages/Game/NumericWorkbench.tsx
4. the existing SvnSync page path
5. console/src/App.tsx or the current route definition
6. the current navigation definition file
7. docs/tasks/post-mvp/lane-e-real-data-full-closeout-2026-05-12.md
8. docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md

Output:
Create docs/tasks/post-mvp/lane-g-game-workspace-page-split-source-review-2026-05-12.md

The document must include:
1. current GameProject section inventory
2. target page responsibilities
3. section migration table
4. route change table
5. navigation change table
6. component split recommendations
7. affected file list
8. minimum implementation order
9. acceptance criteria
10. hard-no scope

Boundaries:
- do not change source
- do not run app
- do not run SVN
- do not execute commit
```
