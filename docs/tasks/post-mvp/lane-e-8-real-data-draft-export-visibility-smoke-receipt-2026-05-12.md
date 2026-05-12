# Lane E.8 Real-Data Draft Export Visibility Smoke Receipt (2026-05-12)

## Scope

- Goal: verify that a draft exported from NumericWorkbench on the real local data project can be rediscovered and reviewed from an expected UI entry.
- Boundaries respected:
  - no SVN command run
  - no SVN sync/update/commit click
  - no publish
  - no formal knowledge release write
  - no backend/API/schema change
  - no source edit
  - no commit
  - no new real production writeback

## Runtime

- App startup command:
  - `.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8100`
- App port:
  - `8100`
- Startup log:
  - `e:\LTclaw2.0\logs\lane-e-8-runtime-smoke-8100-20260512.log`
- Packaged static dir confirmed from startup log:
  - `E:\LTclaw2.0\src\ltclaw_gy_x\console`
- Packaged frontend render result:
  - pass
  - `http://127.0.0.1:8100/chat` and `http://127.0.0.1:8100/numeric-workbench` both rendered successfully

## Real-Data Context Reuse

- Real dataset remained:
  - `E:\工作\资料\腾讯内部资料\中小型游戏设计框架`
- Current release/config were reused from prior real-data setup.
- E.7 draft state was still present and reusable.
- No E.7 precondition replay was needed.

## Reused Draft

- Reused draft from E.7 export, not regenerated in E.8.
- Original E.7 change being checked:
  - table: `EquipEnhance`
  - row: `5`
  - field: `强化所需金钱`
  - old value: `71`
  - new value: `72`

## Draft / Proposal Entry Location

- Entry location found in Chat page top action area:
  - `策划改动提案` button with badge count `1`
- Clicking that button opened a proposal drawer.
- Drawer list contained one visible draft row:
  - title: `数值改动: EquipEnhance (1 项)`
  - status: `草稿`

## Visibility Result

- Draft visibility result: `pass`
- The exported draft was rediscoverable from a stable UI entry on a fresh packaged runtime and new port.
- The draft/proposal card row was visible without needing to recreate the draft.

## Review Result

### Proposal detail

- Opening the visible draft row showed proposal detail inline in the drawer.
- Visible detail included:
  - title: `数值改动: EquipEnhance (1 项)`
  - status: `草稿`
  - operations row:
    - `update_cell`
    - table `EquipEnhance`
    - row_id `5`
    - field `强化所需金钱`
    - new_value `72`

### Dry-run preview

- To verify full change summary including before/after values, the proposal `预演` action was executed.
- This remained within smoke boundaries because it is a dry-run preview only.
- Dry-run result showed:
  - `table = EquipEnhance`
  - `row_id = 5`
  - `field = 强化所需金钱`
  - `before = 71`
  - `after = 72`
  - `ok = true`

## Required Change Summary Check

- Contains `EquipEnhance`: yes
- Contains `5`: yes
- Contains `强化所需金钱`: yes
- Contains `71 -> 72`: yes, via proposal dry-run preview (`before: 71`, `after: 72`)

## Boundary Evidence

- Draft boundary evidence:
  - proposal status visible as `草稿`
- Dry-run boundary evidence:
  - proposal action menu exposed `预演`
  - dry-run preview executed successfully
- No auto-publish / no formal knowledge release write evidence:
  - NumericWorkbench home view displayed:
    - `仅用于 draft 和 dry-run，不会自动发布，也不会写入 formal knowledge release。`
- No publish action taken.
- No formal release write action taken.

## Browser / API / Log Notes

- No browser-side error toast was observed during draft discovery, detail open, or dry-run preview.
- No proposal API failure message was observed.
- Startup log contained environment warnings/errors unrelated to this smoke result:
  - `Nacos SDK ... is not available`
  - `TortoiseSVN not installed`
- These were pre-existing environment/runtime warnings and did not block proposal visibility.

## SVN Statement

- no SVN command run
- no SVN sync/update/commit click

## Final Result

- final result: `pass`
- summary: on a fresh packaged runtime at port `8100`, the E.7 exported draft was still discoverable from the Chat `策划改动提案` entry, its title/status were visible, its detail could be reopened, and the required real-data change summary for `EquipEnhance / 5 / 强化所需金钱 / 71 -> 72` was recoverable via proposal detail plus dry-run preview, with no SVN, publish, or formal release writes performed.