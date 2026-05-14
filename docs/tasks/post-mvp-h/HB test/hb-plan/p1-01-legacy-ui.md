# P1-01 Legacy UI

## Goal

Validate that legacy KB / Doc Library surfaces cannot be mistaken for formal knowledge entry points.

## Required Checks

- [ ] Navigation displays `Legacy Knowledge Base` or equivalent when reachable.
- [ ] Navigation displays `Legacy Doc Library` or equivalent when reachable.
- [ ] Knowledge Base page states it does not participate in formal Release / RAG / Chat / Workbench Suggest.
- [ ] Doc Library page states it is not part of the formal Current Release knowledge chain.
- [ ] Legacy pages do not provide Build Release / Publish operations.
- [ ] User cannot enter formal RAG query from Legacy KB as if it were formal evidence.

## Preferred Tests

- Frontend helper / route-label checks if available.
- Locale/static diagnostics.
- Backend KB / Doc Library router tests.

## Receipt Requirements

Report UI labels, direct-route behavior, formal-flow navigation status, and whether static assets need rebuild.
