# Closure Criteria

## Architecture Baseline Closed If

- [ ] H1-H6 P0 tests pass.
- [ ] Source-write wrapper fixes and tests pass.
- [ ] Legacy KB UI is marked legacy.
- [ ] Release does not read KB.
- [ ] RAG does not read KB.
- [ ] RAG does not bypass Map.
- [ ] Workbench Suggest does not bypass Formal Context.
- [ ] Source write does not trigger knowledge update.
- [ ] Capability gate works on core routes.
- [ ] Unified Model Router is the formal Game model-call entry.
- [ ] SVN runtime remains frozen.

## Cannot Close If

- [ ] KB participates in Release / RAG / Workbench.
- [ ] RAG full-scans artifacts as the formal query path.
- [ ] source-write bypasses `workbench.source.write`.
- [ ] Workbench can `delete_row` or run schema ops through source-write.
- [ ] Source write auto Builds or Publishes.
- [ ] Important routes lack capability context.
- [ ] Formal Game model calls return to module-owned API config.
- [ ] SVN watcher returns to main flow.

## Final Output

When all blocking checks pass, mark:

```text
Architecture Baseline Closed
```

Then route future work to:

- Lane I: Canonical Schema / Map build quality.
- Lane J: Workbench Suggest interaction experience.
- Lane K: Admin Panel complete operation closure.
- Lane L: RAG recall quality.
