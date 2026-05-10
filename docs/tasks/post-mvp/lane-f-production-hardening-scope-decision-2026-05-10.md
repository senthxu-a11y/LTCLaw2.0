# Lane F: Production-Hardening Scope Decision

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Define what production readiness means after pilot usage generates real evidence.
2. Avoid mixing production claims into MVP or pilot closeouts.

## Why This Lane Matters

1. The current accepted baseline is pilot usable, not production ready.
2. Production readiness requires a separate decision frame so pilot closeouts do not accidentally become deployment claims.
3. This lane creates a production roadmap only after real pilot evidence exists.

## Entry Conditions

1. Controlled pilot has run long enough to reveal operator issues.
2. P20 backend-only real transport is either still deferred or has its own closeout.
3. Windows pilot blockers are classified.

## Allowed Scope

1. Deployment packaging scope decision.
2. Audit and operational logs scope decision.
3. Backup and restore scope decision.
4. Multi-user distribution and permission-model scope decision.
5. Provider rollout governance scope decision.
6. Source-control strategy scope decision.
7. Data retention and DLP-boundary scope decision.

## Forbidden Scope

1. Do not claim production readiness as already achieved.
2. Do not rewrite MVP or pilot acceptance semantics.
3. Do not implement production rollout work inside this planning slice.
4. Do not enable P20, real provider connection, or SVN commit or update as part of this decision document alone.

## Expected Effect

1. A separate production roadmap exists.
2. Production readiness is not claimed by accident in pilot documents.
3. Future production work can be discussed as explicit scope rather than implied upgrade.

## Minimum Validation

1. This lane is docs-only unless separately reopened.
2. Run `git diff --check`.
3. Run touched-doc NUL check.
4. Run keyword boundary review and confirm wording remains pilot usable, not production ready.

## Closeout Wording

1. Use `Lane F production-hardening scope decision completed` only for the decision record itself.
2. Do not write `production ready` or equivalent completion wording.
3. Keep the result framed as a roadmap or scope decision, not a production certificate.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane F: Production-hardening scope decision。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-f-production-hardening-scope-decision-2026-05-10.md，以及 docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md。
这轮只做 docs-only scope decision，不实现 production rollout，不改 MVP checklist 语义，不把当前状态写成 production ready。
重点是定义 production readiness 需要哪些后续路线、证据和非功能要求，并明确这些内容尚未完成。
完成后只跑 git diff --check、touched-doc NUL check、keyword boundary review。
```
