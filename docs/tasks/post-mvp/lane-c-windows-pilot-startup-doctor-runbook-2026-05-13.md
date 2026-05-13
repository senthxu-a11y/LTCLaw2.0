# Lane C Windows Pilot Startup Doctor Runbook

Date: 2026-05-13
Status: operator-facing runbook for pilot startup hardening

## Scope

This runbook covers only Windows pilot startup checks.

- No Knowledge release governance change.
- No RAG provider ownership change.
- No frontend provider/model/api_key UI change.
- No Ask schema change.
- No SVN sync/update/commit path.
- No production rollout or production-ready claim.
- No P24 conclusion change.

## Pre-start Doctor Command

Run the focused startup preflight before starting the app:

```powershell
python -m ltclaw_gy_x doctor windows-startup --host 127.0.0.1 --port 8092 --agent-id default
```

`windows-startup` accepts `--host` and `--port` directly. If top-level `ltclaw_gy_x --host/--port` is also present, the subcommand values win.

The command checks:

1. `QWENPAW_WORKING_DIR` is explicitly set and points to an existing directory.
2. `QWENPAW_CONSOLE_STATIC_DIR` is explicitly set and points to an existing directory.
3. Resolved console static directory has `index.html`.
4. Source-checkout `console/dist` exists when running from repo source.
5. The target host/port is free before startup.
6. Local project directory from game user config is configured and readable.
7. First Knowledge release bootstrap prerequisite: current table indexes already exist.
8. Post-start HTTP URLs for health, project config, and release status.

## How To Read The Result

1. `Required env paths` must pass before startup.
2. `Console static` must pass before startup.
3. `Target port` must be available before startup.
4. `Local project directory` must be configured and readable before startup.
5. `Knowledge first-release bootstrap` must pass if the operator expects first-release initialization to work without an existing saved formal map or current release.

## Post-start Minimal Diagnostics

After `ltclaw_gy_x app` starts, verify the URLs printed by the doctor command:

1. `/api/agent/health`
2. `/api/agents/default/game/project/config`
3. `/api/agents/default/game/knowledge/releases/status`

Interpretation:

1. Health should return HTTP 200.
2. Project config should confirm the current local project directory is loaded for the selected agent.
3. Release status may still show no current release on a fresh project; that is acceptable, but first-release bootstrap still requires current table indexes.

## Knowledge Bootstrap Note

This runbook does not change Knowledge release governance.

It only records the already-verified prerequisite:

1. saved formal map still wins first
2. current release map still wins second
3. first bootstrap is allowed only when current table indexes already exist
