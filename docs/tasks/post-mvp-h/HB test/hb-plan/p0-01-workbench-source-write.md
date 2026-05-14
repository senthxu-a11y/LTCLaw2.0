# P0-01 Workbench Source Write

## Goal

Validate that real source-table writeback is fully wrapped, gated, audited, and isolated from knowledge updates.

## Required Checks

- [ ] `update_cell` modifies an existing field successfully.
- [ ] `update_cell` to an unknown field fails.
- [ ] `update_cell` to a primary key fails.
- [ ] `insert_row` with a legal row succeeds.
- [ ] `insert_row` with non-object `new_value` fails.
- [ ] `insert_row` with an unknown field fails.
- [ ] `insert_row` primary key mismatch with `row_id` fails.
- [ ] `delete_row` is rejected.
- [ ] Unknown op is rejected.
- [ ] `.xls` writeback is rejected.
- [ ] Unknown file format is rejected.
- [ ] Successful write creates audit.
- [ ] Failed write attempts failure audit.
- [ ] Response includes `svn_update_required=true`.
- [ ] Response includes `svn_update_warning`.
- [ ] Response includes `release_id_at_write`.
- [ ] Response includes `source_files`.
- [ ] Response includes `changes`.
- [ ] Successful write does not trigger Rebuild / Release / Publish.

## Audit Requirements

If audit path is not split by agent/session, audit records must at least include:

- [ ] `agent_id`
- [ ] `session_id`
- [ ] `time`
- [ ] `release_id_at_write`

## Must Not

- [ ] Do not only test `ChangeApplier.apply()`.
- [ ] Do not bypass `workbench.source.write`.
- [ ] Do not treat `delete_row` as a success path.

## Preferred Tests

- `tests/unit/game/test_workbench_source_write_service.py`
- `tests/unit/routers/test_game_workbench_router.py`
- `tests/unit/game/test_change_applier.py`

## Receipt Requirements

Report changed files, exact tests, source-write op coverage, audit result shape, and whether writeback triggers any knowledge/SVN side effect.
