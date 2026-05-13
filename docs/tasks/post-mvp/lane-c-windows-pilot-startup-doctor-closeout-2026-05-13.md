# Lane C Windows Pilot Startup Doctor Closeout

Date: 2026-05-13
Status: completed

## Scope

This slice hardens Windows pilot startup diagnosis with a focused doctor command and matching runbook.

Changed surfaces:

1. existing `ltclaw_gy_x doctor` CLI gained a focused `windows-startup` subcommand
2. a Windows pilot startup doctor runbook was added
3. focused CLI tests were added
4. the subcommand now accepts direct `--host` / `--port` overrides so the operator-facing runbook command works as written

## What The Slice Adds

The new startup doctor helps operators verify, before startup:

1. `QWENPAW_WORKING_DIR` is set and exists
2. `QWENPAW_CONSOLE_STATIC_DIR` is set and exists
3. resolved console static files are present
4. repo `console/dist` exists when running from source
5. the target port is free
6. the local project directory is configured and readable
7. first Knowledge release bootstrap still requires current table indexes

It also prints the minimal post-start HTTP diagnostics for:

1. health
2. project config
3. release status

## Boundary Confirmation

This slice does not:

1. change Knowledge release governance
2. change RAG provider ownership
3. add frontend provider/model/api_key UI
4. change Ask schema
5. touch SVN sync/update/commit
6. claim production rollout
7. claim production ready
8. change P24 conclusions

## MVP Behavior

MVP behavior is unchanged.

Reason:

1. the new doctor command is read-only
2. the runbook only documents operator-side startup diagnosis
3. the slice adds startup visibility, not product semantics