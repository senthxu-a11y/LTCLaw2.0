# Lane H-B Test Matrix Plan

Lane H-B is a test, verification, and small-fix lane after Lane H-A hardening.

Goal:

```text
Architecture Baseline Closed
```

This lane must not expand features. It validates the architecture baseline through code review, focused tests, small fixes, and closure records.

## Execution Order

P0 must be completed before P1/manual closure:

1. [P0-01 Workbench Source Write](p0-01-workbench-source-write.md)
2. [P0-02 Capability Agent Profile](p0-02-capability-agent-profile.md)
3. [P0-03 Map-gated RAG](p0-03-map-gated-rag.md)
4. [P0-04 Workbench Suggest Validator](p0-04-workbench-suggest-validator.md)
5. [P0-05 Release Strict Bootstrap](p0-05-release-strict-bootstrap.md)
6. [P0-06 Unified Model Router](p0-06-unified-model-router.md)
7. [P0-07 SVN Freeze](p0-07-svn-freeze.md)
8. [P1-01 Legacy UI](p1-01-legacy-ui.md)
9. [P1-02 Admin Panel](p1-02-admin-panel.md)
10. [P1-03 Citation Deep-link](p1-03-citation-deeplink.md)
11. [Manual Acceptance](manual-acceptance.md)
12. [Closure Criteria](closure-criteria.md)

## Lane Rules

- Do not restore KB/retrieval as formal knowledge.
- Do not bypass Map-gated RAG.
- Do not let Workbench source write trigger rebuild, Release build, Publish, RAG rebuild, SVN update, SVN commit, or SVN revert.
- Do not add new capabilities.
- Do not add new product flows.
- Small fixes are allowed only when they close a listed test/checklist gap.
- Every agent must report files changed, tests run, uncovered items, and boundary impact.

## Baseline Closure Standard

Lane H-B can close only when:

- All P0 checks pass.
- P1 checks have no architecture-boundary blockers.
- Manual flows are either passed or have explicit non-blocking notes.
- Temporary files are absent.
- The final reviewer can state: `Architecture Baseline Closed`.
