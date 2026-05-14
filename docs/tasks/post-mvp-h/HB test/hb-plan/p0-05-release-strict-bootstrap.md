# P0-05 Release Strict / Bootstrap

## Goal

Validate that Release build cannot bypass Formal Map review, and bootstrap must be explicit.

## Required Checks

- [ ] Formal Map exists and strict build succeeds.
- [ ] No Formal Map with `bootstrap=false` fails.
- [ ] No Formal Map with `bootstrap=true` succeeds with warning.
- [ ] Build Release does not auto Publish.
- [ ] Publish Current requires a separate call.
- [ ] Publish Current requires `knowledge.publish`.
- [ ] Release does not read KB.
- [ ] Release does not read Draft / Proposal.
- [ ] Release artifacts include `map.json`.
- [ ] Release artifacts include `table_schema.jsonl`.
- [ ] Release artifacts include `doc_knowledge.jsonl`.
- [ ] Release artifacts include `script_evidence.jsonl`.

## Preferred Tests

- `tests/unit/game/test_knowledge_release_service.py`
- `tests/unit/game/test_knowledge_release_builders.py`
- `tests/unit/routers/test_game_knowledge_release_router.py`
- Optional split file: `tests/unit/game/test_knowledge_release_strict_bootstrap.py`

## Receipt Requirements

Report strict/bootstrap behavior, warning shape, current release pointer behavior, and proof that KB/Draft/Proposal are not Release inputs.
