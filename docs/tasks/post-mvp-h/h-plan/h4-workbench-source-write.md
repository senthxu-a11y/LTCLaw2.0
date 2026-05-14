# H4 Workbench Source Write Validation

## Goal

Confirm real source table writeback is capability-gated, allowlisted, auditable, and isolated from knowledge rebuild/publish.

## Source Focus

- `src/ltclaw_gy_x/game/workbench_source_write_service.py`
- `src/ltclaw_gy_x/app/routers/game_workbench.py`
- `src/ltclaw_gy_x/game/change_applier.py`
- `console/src/api/modules/gameWorkbench.ts`
- Frontend writeback button / confirmation surfaces

## Checklist

- [ ] `/game/workbench/source-write` requires `workbench.source.write`.
- [ ] Missing capability returns 403.
- [ ] `planner` does not have `workbench.source.write` by default.
- [ ] `source_writer` has `workbench.source.write`.
- [ ] `admin` has `*` or equivalent.
- [ ] Allowlist includes only `update_cell` and `insert_row`.
- [ ] `delete_row` is blocked.
- [ ] Schema ops are blocked.
- [ ] New field/table, deleted field/table, renamed table/path, and primary-key rewrite are blocked.
- [ ] `update_cell` requires field and existing header.
- [ ] `update_cell` cannot update primary key.
- [ ] `insert_row` `new_value` must be an object.
- [ ] `insert_row` fields must exist in headers.
- [ ] `insert_row` primary key and row id must match when provided.
- [ ] `.xlsx`, `.csv`, and `.txt` are supported.
- [ ] `.xls` and unknown formats are rejected.
- [ ] TXT metadata/header/BOM behavior is preserved.
- [ ] Frontend warns that SVN Update is manual.
- [ ] Response includes `svn_update_required=true` and `svn_update_warning`.
- [ ] Backend does not run SVN update, commit, revert, or watcher.
- [ ] Success and failure audit records are attempted.
- [ ] Audit includes event type, agent, session, time, release id at write, reason, source files, changes, old values, and new values.
- [ ] Audit failure after write returns explicit `write_applied=true` and `audit_recorded=false`.
- [ ] Writeback does not trigger index rebuild, Release build, Publish/Set Current, RAG rebuild, or SVN watcher.

## Tests To Prefer

- Viewer/planner source write returns 403.
- Source writer update cell succeeds.
- Source writer insert row succeeds.
- Delete row fails.
- Unknown field/new field fails.
- Primary key rewrite fails.
- `.xls` write fails with clear reason.
- Audit file generated on success.
- Current Release remains unchanged after source write.

## Pass Standard

Real source writes are controlled, traceable, and do not mutate the formal knowledge baseline.
