# P1-02 Admin Panel

## Goal

Validate Admin Panel status visibility and capability-gated operation entries.

## Required Checks

- [ ] Admin Panel shows project bundle path.
- [ ] Admin Panel shows source config path.
- [ ] Admin Panel shows current release id.
- [ ] Admin Panel shows previous release id.
- [ ] Admin Panel shows current map hash.
- [ ] Admin Panel shows formal map status.
- [ ] Admin Panel shows RAG status.
- [ ] No previous release shows `-` and warning.
- [ ] planner / viewer cannot see admin write actions.
- [ ] admin can see admin write actions.

## Preferred Tests

- `console/src/pages/Game/components/adminPanel.test.ts`
- Knowledge Release router tests for current/previous release payload.

## Receipt Requirements

Report displayed cards, action visibility matrix, and whether Build Release remains separate from Publish / Set Current.
