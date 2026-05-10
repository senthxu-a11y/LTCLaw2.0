# Lane E: NumericWorkbench Practical UX Hardening

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Make the validated workbench useful for real numeric-planning sessions.
2. Improve planner ergonomics without changing formal-knowledge governance.

## Why This Lane Matters

1. The current MVP already validates the workbench path, but practical daily use depends on search, preview, disabled-state clarity, and review ergonomics.
2. UX friction can block pilot usefulness even when the backend and governance boundaries are accepted.
3. This lane can increase real planner value without turning fast test into publish or changing governance.

## Entry Conditions

1. The current workbench semantics remain fast test, draft export, and non-default formal-knowledge inclusion.
2. The slice starts from actual pilot pain points or a narrow observed UX blocker.
3. The lane must preserve the current release-governance path.

## Allowed Scope

1. Table and field search refinements.
2. Diff preview clarity.
3. Draft proposal and dry-run result visibility.
4. Clearer disabled states for export and save actions.
5. Copy that distinguishes fast test, draft export, and formal knowledge release.
6. Small targeted fixes for known existing warnings only when they block maintainability.

## Forbidden Scope

1. Do not make draft export publish.
2. Do not require administrator acceptance for ordinary fast tests.
3. Do not make test plans enter formal knowledge by default.
4. Do not add provider, model, or API-key controls.
5. Do not replace the current release governance path.

## Expected Effect

1. Numeric planners can find, test, and review value changes faster.
2. The workbench becomes practical for daily pilot use while preserving release governance.

## Minimum Validation

1. Re-run the touched workbench UX path manually.
2. Run targeted frontend validation for the touched UI slice.
3. Run any necessary narrow backend validation only if the slice touches a backend support contract.
4. Run `git diff --check`, touched-doc NUL check, and keyword boundary review.

## Closeout Wording

1. Use `Lane E NumericWorkbench UX hardening completed` only for a scoped usability slice.
2. Do not write wording that turns draft export into publish or fast test into admin-gated flow.
3. State clearly whether MVP behavior remained unchanged.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane E: NumericWorkbench practical UX hardening。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-e-numeric-workbench-ux-hardening-2026-05-10.md，以及 docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md 中 NumericWorkbench 相关边界。
目标是改善真实数值策划使用效率，不改变 formal knowledge governance。
不要让 draft export 变 publish，不要让 fast test 需要管理员接受，不要让 test plan 默认进入 formal knowledge。
先从 pilot 问题或真实用户痛点里选一个小切片，完成后跑 targeted frontend validation 和必要的 narrow backend checks。
```
