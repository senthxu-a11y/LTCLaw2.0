# Lane G.3 Project Page Contraction Receipt

Date: 2026-05-12
Status: implemented, not committed
Scope: contract Project page visuals and responsibility framing to project setup / storage / validation / save / workspace entries only, without entering G.4

## Changed Files

1. console/src/pages/Game/GameProject.tsx
2. console/src/pages/Game/GameProject.module.less
3. docs/tasks/post-mvp/lane-g-3-project-page-contraction-receipt-2026-05-12.md

## G.3 Contraction Applied

1. Replaced the single Knowledge CTA block with Project-focused top framing and three workspace entry cards.
2. Added workspace entries for Knowledge, Map Editor, and NumericWorkbench.
3. Reframed the Project top narrative around project setup, configuration ownership, storage inspection, validation, and save flows.
4. Moved formal map review lower in the page so it no longer presents as the Project page primary task.
5. Added transitional copy that explicitly says Map Editor migration is pending and that formal map ownership will move later.
6. Added a compact candidate-map / saved-formal-map summary ahead of the existing formal map body.
7. Kept all formal map handlers, fetch semantics, save-as-formal-map behavior, and status-edit behavior unchanged.

## Project Content Retained

1. Project basic info form
2. SVN and local project directory fields
3. Watch configuration
4. Workflow configuration
5. Storage snapshot
6. Save / validate / reset actions
7. Create-project-agent wizard

## Formal Map Status

1. Formal map editing remains in Project in this lane: yes
2. Formal map editing moved to /game/map in this lane: no
3. Save as formal map behavior changed: no
4. Saved formal map status edit behavior changed: no
5. Candidate/saved formal map data-fetch semantics changed: no

## Boundary Confirmation

1. Entered G.4: no
2. Backend/API/schema changed: no
3. Packaged runtime assets changed: no
4. NumericWorkbench business logic changed: no
5. Knowledge page business logic changed: no
6. SVN behavior changed: no

## Validation

1. File-level error check on GameProject.tsx: pass
2. File-level error check on GameProject.module.less: pass
3. git diff --check: pass
4. console local TypeScript noEmit via ./node_modules/.bin/tsc --noEmit: pass
5. targeted ESLint on GameProject.tsx via ./node_modules/.bin/eslint src/pages/Game/GameProject.tsx: pass

## Follow-up Fix Summary

1. Kept the entry-card copy and routing semantics intact.
2. Moved the tone badge onto its own line instead of sharing the title row width.
3. Added title-specific layout rules to prevent mid-word wrapping.
4. Renamed the third card title from NumericWorkbench to Numeric Workbench for cleaner first-screen reading while keeping the route and description semantics unchanged.
5. Tightened the desktop grid minimum width so the three-card row stays readable on the Project first screen.

## Smoke

1. Manual route smoke: pass
2. URL used for final smoke: http://127.0.0.1:8096/game-project
3. Card layout result:
	- Desktop first-screen entry card titles no longer break mid-word: pass
	- Tone badges no longer squeeze card titles into awkward wraps: pass
	- No obvious first-screen card overlap, text overflow, or layout collapse observed in the three-card row: pass
4. Project page contraction checks:
	- Project top no longer reads like the Knowledge main workbench: pass
	- Storage snapshot appears near the top and remains readable: pass
	- Project basic info / SVN / Watch / Workflow / Reset / Validate / Save remain visible: pass
	- Formal map still remains on Project with migration-pending copy and lower exposure: pass
5. Workspace entry card route checks:
	- Knowledge card -> /game/knowledge: pass; landed on Knowledge page with release and RAG sections visible
	- Map Editor card -> /game/map: pass; landed on Map Editor skeleton with G.4-pending placeholder wording and Project return entry
	- Numeric Workbench card -> /numeric-workbench: pass; landed on Numeric Workbench session entry page
6. Scope note:
	- Smoke used a temporary local workspace with no configured local project directory, so map/release unavailable alerts were expected and were not treated as a G.3 blocker.

## Final Checks

1. NUL check on touched files: pass
2. Keyword boundary review: pass
3. Recommendation before release step: commit and push are reasonable for G.3 after this follow-up smoke.

## Notes

1. A file named lane-g-3-project-contraction-source-review-2026-05-12.md was not present under docs/tasks/post-mvp during implementation. The lane-g source review used for boundary confirmation was lane-g-game-workspace-page-split-source-review-2026-05-12.md together with the checklist and G.2 receipt.
