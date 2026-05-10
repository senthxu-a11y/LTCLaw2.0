# Lane A: Controlled Windows Pilot Usage And Pilot Hardening

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Let real users operate the validated Windows pilot flow.
2. Collect actual pilot issues before broad engineering expansion.
3. Fix only pilot blockers and Windows-path stability issues.

## Why This Lane Matters

1. Windows operator-side pilot already passed with known limitations, so the next value comes from controlled real usage rather than reopening MVP architecture.
2. Windows path, encoding, startup, and local environment issues are the fastest way to block pilot usefulness even when product semantics are already accepted.
3. This lane keeps pilot execution moving without accidentally turning the current baseline into production-hardening or provider-rollout work.

## Entry Conditions

1. The accepted baseline remains MVP complete, pilot usable, and not production ready.
2. The Windows operator-side pilot validation record remains the controlling validation baseline.
3. Work is limited to controlled pilot hardening and does not reopen P0-P3 feature semantics.

## Allowed Scope

1. Windows startup failures.
2. `local project directory` configuration mistakes.
3. Chinese path, Chinese filename, and Windows path separator issues.
4. Excel file-lock detection or clearer error messages.
5. Port collision handling or operator instructions.
6. Windows Defender or enterprise security write-block diagnosis.
7. App-owned storage discovery or recovery copy.
8. Minimal docs updates for operator recovery.

## Forbidden Scope

1. No P20 or real-provider work.
2. No SVN commit or update integration.
3. No relationship editor or graph canvas.
4. No production deployment claim.
5. No broad UI redesign.

## Expected Effect

1. Planner users can run the MVP on Windows with fewer setup and file-system failures.
2. Issues are classified as blocker, hardening, polish, or deferred.
3. Controlled pilot can continue without reopening accepted MVP architecture.

## Minimum Validation

1. Reproduce the affected Windows pilot path on the target-machine setup or an equivalent validated Windows environment.
2. Re-run the narrow operator-side startup or recovery path touched by the change.
3. If docs-only, run `git diff --check`, touched-doc NUL check, and keyword boundary review.
4. If scripts or product code change, run only the smallest focused validation for the touched Windows startup or operator surface.

## Closeout Wording

1. Use `Lane A controlled Windows pilot hardening completed` only when the targeted Windows blocker or hardening slice is actually closed.
2. Keep the state as pilot usable on Windows target machine with known limitations when that remains true.
3. Do not write production ready or equivalent wording.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane A: Controlled Windows pilot usage and pilot hardening。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-a-controlled-windows-pilot-hardening-2026-05-10.md，以及 docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-windows-operator-side-pilot-validation-2026-05-10.md。
只修 Windows pilot blocker、startup、path、encoding、storage、doctor 或 operator recovery 相关的最小切片。
不要改 MVP 产品语义，不要继续 P20，不要做 SVN commit/update，不要把当前状态写成 production ready。
完成后只跑与触达 Windows operator path 对应的最小验证，并在 closeout 中明确是否改变了 MVP 行为。
```
