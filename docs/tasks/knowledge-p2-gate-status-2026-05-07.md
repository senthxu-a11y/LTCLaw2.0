# Knowledge P2 Gate Status

Date: 2026-05-07

Authority:

1. docs/plans/knowledge-architecture-handover-2026-05-06.md
2. docs/plans/knowledge-p1-local-first-scope-2026-05-06.md
3. docs/tasks/knowledge-p0-p3-implementation-checklist.md
4. docs/tasks/knowledge-admin-vs-fast-test-boundary-review-2026-05-07.md

## Scope Snapshot

P2 is complete for the current MVP slice.

Completed in this gate:

1. P2.1 minimal test plan store.
2. P2.2 minimal release candidate store.
3. P2.3 candidate list/filter semantics.
4. P2.4 candidate-to-release inclusion boundary review.
5. P2.5 backend build-time candidate inclusion.
6. P2.6 frontend release candidate selection UI.

This gate covers app-owned pending persistence, backend-only build-time candidate inclusion, and the minimal frontend candidate selection UI on top of the existing safe build boundary. It still does not include admin approval UI, candidate-evidence query or RAG usage, or any P3 work.

Boundary clarification:

1. P2 does not add administrator acceptance to ordinary workbench fast testing.
2. Test plans can be created, tested, kept, or discarded without administrator acceptance.
3. Release candidates are optional future release-build inputs, not automatic formal knowledge changes.
4. Candidate `accepted` means release-eligible candidate state; it is not a required approval gate for fast numeric testing.

Final gate decision:

1. P2 passes the final gate.
2. The current MVP slice closes with P2.1-P2.6 complete.
3. No new features were added during final gate closeout; this step validated and repaired the existing slice only.

## Completed Scope

### P2.1 Completed Scope

1. Workbench test plans persist in app-owned pending storage at `pending/test_plans.jsonl`.
2. The current operations are minimal append/list/get semantics around the store layer.
3. Missing pending files return an empty list.
4. Relative local-project paths are normalized and validated; absolute and `..` escape paths are rejected.
5. Test plan state remains outside release directories and outside formal knowledge release assets.

### P2.2 Completed Scope

1. Release candidates persist in app-owned pending storage at `pending/release_candidates.jsonl`.
2. The current operations are minimal append/list semantics around the store layer.
3. Missing pending files return an empty list.
4. Relative local-project paths are normalized and validated; absolute and `..` escape paths are rejected.
5. Each release candidate links back to `test_plan_id` and remains separate from ordinary test plan state.

### P2.3 Completed Scope

1. Candidate list supports narrow `status`, `selected`, and `test_plan_id` filters.
2. Candidate query remains pending-state inspection only.
3. Candidate list does not mutate release assets, `current.json`, or source resources.

### P2.4 Completed Scope

1. Candidate eligibility is defined as `accepted + selected + explicitly requested in candidate_ids`.
2. Candidate inclusion is build-time only and stays behind the safe backend build endpoint.
3. `selected == false` fails clearly rather than being silently skipped.
4. Inclusion output may write only release-owned derived metadata or evidence, never raw source copies.

### P2.5 Completed Scope

1. The existing safe backend build path resolves requested `candidate_ids` from the release candidate store.
2. Every requested candidate must exist, be `accepted`, and have `selected == true`.
3. Validated inclusion is written as release-owned evidence in `indexes/candidate_evidence.jsonl` and `manifest.indexes.candidate_evidence`.
4. `candidate_evidence.jsonl` is release-owned metadata/evidence only; it does not copy raw source files.
5. Build success still does not set current release automatically.
6. Current release query does not read `candidate_evidence`.
7. The old full-payload build endpoint remains internal/test-only and is still not a normal frontend path.

### P2.6 Completed Scope

1. The existing build release modal now reads release candidates from `GET /game/knowledge/release-candidates?status=accepted&selected=true`.
2. The UI shows a compact checkbox list for candidate inclusion in the current build only.
3. All candidate checkboxes default to unchecked, so `candidate_ids=[]` keeps the previous safe build behavior.
4. The build request body remains narrow: `release_id`, `release_notes`, `candidate_ids`.
5. Candidate list loading failures are shown as lightweight warnings inside the modal and do not block the rest of the page.
6. This slice does not add admin approval UI, query expansion, RAG usage, or automatic set-current behavior.

## Current JSONL Shape Summary

### Test Plan JSONL

Each line is one `workbench-test-plan.v1` record. The current minimal shape includes:

1. `schema_version`
2. `id`
3. `status`
4. `title`
5. `project_key`
6. `release_scope`
7. `test_scope`
8. `source_refs`
9. `changes`
10. `created_at`
11. `created_by`
12. `engine_test_ref`

Each `changes[]` item currently records:

1. `operation`
2. `table`
3. `primary_key`
4. `field`
5. `before`
6. `after`
7. `source_path`

### Release Candidate JSONL

Each line is one `release-candidate.v1` record. The current minimal shape includes:

1. `schema_version`
2. `candidate_id`
3. `test_plan_id`
4. `status`
5. `title`
6. `project_key`
7. `source_refs`
8. `source_hash`
9. `selected`
10. `created_at`

## Boundary Notes

1. `pending/test_plans.jsonl` and `pending/release_candidates.jsonl` are app-owned pending data under the project store.
2. Test plans and release candidates do not automatically enter the formal knowledge release.
3. Test plans and release candidates do not automatically set current release.
4. The current P2.1/P2.2 slice does not read or write SVN.
5. The current P2.1/P2.2 slice does not copy raw source tables, docs, or scripts.
6. Candidate inclusion happens only at build-time through the safe backend build endpoint.
7. The normal frontend path still does not send full `KnowledgeMap`, `TableIndex`, `DocIndex`, or `CodeFileIndex` payloads.
8. Current release query remains keyword-only and does not consume `candidate_evidence`.
9. The normal frontend path still does not use the old full-payload build endpoint.

## Verified Items

The current verified summary is:

1. P2.1 test plan store append/list behavior: passed.
2. P2.1 missing-file empty-list behavior: passed.
3. P2.1 relative-path validation and escape rejection: passed.
4. P2.1 no release-dir writes and no `.svn` touch in the persistence slice: passed.
5. P2.2 release candidate store append/list behavior: passed.
6. P2.2 missing-file empty-list behavior: passed.
7. P2.2 relative-path validation and escape rejection: passed.
8. P2.2 no release-dir writes, no current-release mutation, and no `.svn` touch in the persistence slice: passed.
9. Focused regression across the new P2.2 slice plus adjacent P2.1 and P1 release slices: passed.
10. The final focused regression result for this closeout slice was `40 passed`.
11. P2.3 candidate list/filter semantics: passed.
12. P2.4 candidate inclusion boundary review: passed.
13. P2.5 focused build-time candidate inclusion service validation: `11 passed`.
14. P2.5 adjacent regression across release candidate store/router, test plan store/router, release build/store/service/router/query: `72 passed`.
15. P2.5 touched Python files were rechecked as `NUL=0` after recovery cleanup.
16. P2.6 TypeScript validation rerun with `npm exec tsc -- -p tsconfig.app.json --noEmit --incremental false`: passed.
17. No repository-local GameProject or release-candidate frontend test suite exists yet; only an unrelated frontend test file is present.
18. Final P2 regression across test plan store, release candidate store/filter, build-time inclusion, release store/service/router/query, and representative game index/workbench routes: `97 passed in 10.28s`.
19. P2-related Python source and test files were rechecked for DLP/NUL corruption: all targeted files are now `NUL=0`.
20. One corrupted test file, `tests/unit/game/test_knowledge_release_store.py`, required a no-BOM UTF-8 rewrite during final gate closeout before the final regression could pass.

## Still Not Implemented

1. Admin approval UI.
2. Candidate-evidence query or RAG usage.
3. Formal release merge beyond current build-time evidence inclusion.
4. SVN resource-pull adapter.
5. P3.

## Recommendation For Next Step

The next reasonable options are:

1. Start P3 only when the team is ready to open map governance and RAG integration explicitly.
2. If a pre-P3 step is needed, treat admin approval UI or SVN resource-pull adapter as separate optional tracks rather than extending the closed P2 scope.
