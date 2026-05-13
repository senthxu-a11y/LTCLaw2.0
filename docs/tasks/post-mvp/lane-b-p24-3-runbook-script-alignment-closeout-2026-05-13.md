# Lane B P24.3 Runbook And Script Alignment Closeout

Date: 2026-05-13
Status: docs-plus-tooling closeout
Scope: align the P24.1 runbook and minimal operator tooling with the P24.2 dry-run finding that project-config apply, disable, and cleanup must use full-config PUT bodies

## 1. Actual Changed Files

This slice changed the following files:

1. docs/tasks/post-mvp/lane-b-p24-1-windows-operator-startup-secret-runbook-2026-05-13.md
2. docs/tasks/post-mvp/lane-b-p24-2-windows-operator-dry-run-receipt-2026-05-13.md
3. docs/tasks/post-mvp/lane-b-p24-3-runbook-script-alignment-closeout-2026-05-13.md
4. scripts/operator_deepseek_pilot.ps1
5. src/ltclaw_gy_x/cli/operator_cmd.py
6. tests/unit/cli/test_operator_cmd.py

## 2. What P24.3 Fixed

P24.3 updates the operator guidance and helper surface so they no longer suggest partial-body PUT requests.

The aligned rule is now:

1. GET current project config
2. modify only external_provider_config in memory
3. PUT the full project config JSON back

This rule now appears in:

1. the P24.1 runbook apply, disable, and cleanup steps
2. the minimal script guidance printed by the PowerShell helper
3. a dedicated operator CLI command that safely generates the merged full-config payload without embedding secrets

## 3. Boundary Confirmation

This slice did not do any of the following:

1. record a real secret value
2. change Ask request schema
3. add frontend provider, model, or api_key UI
4. change RAG provider ownership
5. touch SVN sync, update, or commit paths
6. claim production rollout
7. claim production ready
8. execute any real DeepSeek answer request

## 4. Verification Intent

The expected verification for this slice is:

1. operator CLI help still loads
2. focused operator CLI tests pass
3. diff formatting and touched-doc hygiene remain clean

## 5. MVP Behavior

MVP behavior is unchanged.

Reason:

1. the slice only aligns operator-side runbook and helper behavior with the already observed project-config API contract
2. it does not change accepted backend ownership, request schema, or ordinary-user surfaces
3. the current state remains pilot usable and not production ready