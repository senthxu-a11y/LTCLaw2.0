# P0-04 Workbench Suggest Validator

## Goal

Validate that LLM output cannot fabricate table, field, row, or evidence refs.

## Required Checks

- [ ] Legal suggestion passes.
- [ ] Unknown table is filtered.
- [ ] Unknown field is filtered.
- [ ] Unknown row id is filtered.
- [ ] evidence ref outside allowed refs is filtered.
- [ ] No formal context does not fabricate `source_release_id`.
- [ ] Runtime-only suggestions are marked `validated_runtime_only`.
- [ ] Draft Overlay is marked as draft and not formal evidence.
- [ ] Non-JSON LLM output does not generate changes.
- [ ] Empty LLM output returns explicit error.

## Preferred Tests

- `tests/unit/game/test_workbench_suggest_context.py`
- `tests/unit/routers/test_game_workbench_router.py`
- `console/src/pages/Game/components/workbenchSuggestEvidence.test.ts`

## Receipt Requirements

Report validator behavior, formal/runtime/draft distinction, model failure shape, and frontend evidence display coverage.
