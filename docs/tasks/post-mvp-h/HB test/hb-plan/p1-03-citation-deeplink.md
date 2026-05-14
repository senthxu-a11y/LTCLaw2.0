# P1-03 Citation Deep-link

## Goal

Validate that RAG citations preserve Workbench deep-link context without causing side effects.

## Required Checks

- [ ] RAG citation can carry table.
- [ ] RAG citation can carry row.
- [ ] RAG citation can carry field.
- [ ] Workbench can read citation route context.
- [ ] Workbench does not create draft from citation automatically.
- [ ] Workbench does not write source from citation automatically.
- [ ] Workbench does not publish knowledge from citation automatically.

## Preferred Tests

- RAG context citation tests.
- Workbench route/highlight tests if available.
- Manual route smoke if no UI test harness exists.

## Receipt Requirements

Report citation payload shape, route parsing behavior, and proof of no draft/write/publish side effects.
