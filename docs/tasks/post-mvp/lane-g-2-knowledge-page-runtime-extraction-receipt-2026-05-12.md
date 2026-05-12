# Lane G.2 Knowledge Page Runtime Extraction Receipt

Date: 2026-05-12
Status: implemented, not committed
Scope: move Knowledge runtime ownership from Project to /game/knowledge without entering G.3/G.4/G.5

## Changed Files

1. console/src/pages/Game/Knowledge/index.tsx
2. console/src/pages/Game/GameProject.tsx
3. docs/tasks/post-mvp/lane-g-2-knowledge-page-runtime-extraction-receipt-2026-05-12.md

## Migrated Knowledge Blocks

1. Current release summary
2. Release list
3. Set current action
4. Rollback to previous action
5. Build release entry and modal
6. RAG ask input, examples, recent questions, loading, warnings, result state
7. Structured query panel and readonly result rendering
8. Citation list, focus interaction, and Open in workbench action
9. doc_knowledge insufficient-context hint path
10. Readonly candidate map summary
11. Readonly saved formal map summary

## Project Retained Blocks

1. Project basic info form
2. SVN and local project directory fields
3. Watch configuration
4. Workflow configuration
5. Storage snapshot
6. Save / validate / reset actions
7. Create-project-agent wizard
8. Formal map review/editor body
9. Save as formal map and status-edit flow
10. Footer action bar

## Boundary Checks

1. Formal map editing stayed in Project: yes
2. NumericWorkbench deep-link contract unchanged: yes
3. Backend/API/schema untouched: yes
4. Packaged assets untouched: yes

## Validation

1. git diff --check: pass with line-ending warning on console/src/pages/Game/Knowledge/index.tsx about CRLF to LF normalization
2. console local TypeScript noEmit: pass
3. targeted ESLint on touched TSX files: pass

## Smoke

1. Not run in this lane. Scope for this step was extraction plus static validation only.

## Notes

1. Project page now renders a lightweight entry card to /game/knowledge where the migrated runtime lives.
2. Readonly map summaries are duplicated on Knowledge intentionally; mutable formal map draft/edit state remains Project-owned in this lane.
