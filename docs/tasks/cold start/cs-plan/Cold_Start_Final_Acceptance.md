# Cold Start Final Acceptance

## Scope

This record covers the accepted cold start chain from P0-00 through P2-00 only.

Accepted chain:

- Project Setup API and UI
- Source Discovery
- Rule-only Raw Index rebuild
- Rule-only Canonical Facts rebuild
- Candidate Map from canonical facts
- Rule-only smoke script
- Cold-start background job API
- Progress UI and one-click rule-only build entry
- Boundary tests and final acceptance

Out of scope and intentionally not added:

- LLM-backed cold start
- KB/retrieval integration
- SVN recovery or watcher flows
- Automatic Save Formal Map
- Automatic Build Release
- Automatic Publish / Set Current

## P0-00 to P0-05 Conclusions

### P0-00 Minimal Sample + Project Setup API

- `examples/minimal_project/Tables/HeroTable.csv` exists and remains the minimal verification sample.
- Project Setup API supports local project root save, tables source save, and setup-status readback.
- Project Setup defaults still return the expected default include/exclude/header_row/primary key candidate values when no project root is configured.

### P0-01 Source Discovery

- Source Discovery remains read-only.
- It discovers `HeroTable.csv` under the minimal sample project.
- It excludes `~$Temp.xlsx` and marks `.xls` as unsupported.
- P2 boundary tests additionally confirm case-insensitive include matching for uppercase `.CSV`, backslash-configured table roots, Chinese paths, and paths with spaces.

### P0-02 Raw Index Rebuild

- Rule-only raw rebuild remains CSV-only by design.
- UTF-8 and UTF-8 BOM CSV files are supported.
- Empty files, empty headers, and invalid `header_row` produce explicit per-file errors.
- Rule-only raw rebuild still does not call LLM.

### P0-03 Canonical Facts Rebuild

- Canonical rebuild still consumes the raw aggregate file only.
- It preserves partial-failure shape when one raw entry is broken.
- It still does not require or call LLM.

### P0-04 Build Readiness + Candidate Diagnostics

- Build readiness still reflects project root, discovery, raw, canonical, formal map, and current release status.
- Candidate-from-source still returns diagnostics when canonical facts are missing.
- Agent-scoped route semantics remain authoritative.

### P0-05 Smoke Script

- Smoke script still runs fully locally through:
  `save_project_tables_source_config -> discover_table_sources -> rebuild_raw_table_indexes -> CanonicalFactsCommitter.rebuild_tables -> build_map_candidate_from_canonical_facts`
- Real smoke execution still succeeds in rule-only mode on `examples/minimal_project`.

## P1-00 to P1-02 Conclusions

### P1-00 Project Setup UI

- The user can find Project Setup at the existing Game -> Project page.
- The page surfaces:
  - Local Project Root
  - Tables Source
  - Source Discovery
  - Build Pipeline Status
- The page shows `project_key`, `project_bundle_root`, discovery summary, available/excluded/unsupported/errors lists, and setup readiness state.

### P1-01 Cold-start Job API

- Cold-start job API supports:
  - create
  - get
  - cancel
- Job state persists under project runtime `build_jobs`.
- Refresh recovery works by reading persisted job JSON.
- Running-job dedupe is project-scoped within the current process.

### P1-02 Progress UI + Rule-only One-click Build

- Project Setup now exposes a `Rule-only 冷启动构建` button.
- The button is disabled unless local project root, tables source, and available discovered tables are present.
- UI consumes only agent-scoped cold-start job routes.
- UI shows progress, stage, message, current file, counts, warnings, errors, next action, candidate refs, and copyable diagnostics.
- UI supports cancel and retry.
- Success state only provides explicit navigation entries to Map Editor for Candidate Map / Diff Review / Save Formal Map.
- No automatic Save Formal Map, Build Release, or Publish action is triggered.

## P2 Boundary Test Conclusions

### Windows / Path Boundaries

Verified by unit tests:

- Equivalent Windows-style path parsing is normalized from `E:\test_project` to `E:/test_project` in project-root path handling.
- Local project root save accepts backslash-separated paths and normalizes them before persistence.
- Paths containing spaces are accepted.
- Paths containing Chinese characters are accepted.
- Backslash-configured table roots are normalized and still discover files.

Note:

- These checks were executed on macOS using equivalent path parsing logic, not on a native Windows runtime.

### CSV Encoding / Error Boundaries

Verified by router and table-indexer tests:

- UTF-8 CSV: pass
- UTF-8 BOM CSV: pass
- Empty file: explicit file-level error
- Empty header: explicit file-level error
- Invalid `header_row`: explicit file-level error
- Missing primary key column: explicit fallback to default primary key (`ID`) without LLM

### XLSX Boundaries

Verified by direct `TableIndexer` rule-only tests and discovery tests:

- Single-sheet XLSX: pass
- Multi-sheet XLSX: pass using the active sheet only
- Empty active sheet: explicit `文件为空` error
- `~$Temp.xlsx`: excluded during source discovery
- `.xls`: marked unsupported during source discovery

## Core Matrix Rerun

The following cold start matrix was rerun during final acceptance:

- Project Setup API: pass
- Source Discovery: pass
- Raw Index: pass
- Canonical Facts: pass
- Candidate from Source / Build Readiness: pass
- Smoke script: pass
- Project Setup UI helper/static tests: pass
- Cold-start Job: pass
- Progress UI helper/static tests: pass

Executed command groups and results:

- `tests/unit/routers/test_game_project_router.py`: 23 passed
- `tests/unit/routers/test_game_knowledge_raw_index_router.py`: 5 passed
- `tests/unit/routers/test_game_knowledge_canonical_router.py`: 6 passed
- `tests/unit/routers/test_game_knowledge_map_router.py`: 28 passed
- `tests/unit/scripts/test_run_map_cold_start_smoke.py`: 5 passed
- `tests/unit/game/test_cold_start_job.py`: 1 passed
- `tests/unit/routers/test_game_knowledge_map_cold_start_job_router.py`: 4 passed
- `tests/unit/routers/test_agent_scoped_knowledge_routes.py`: 3 passed
- `tests/unit/game/test_table_indexer.py`: 13 passed
- `console` typecheck + static/helper tests: pass

## Smoke Script Result

Real smoke execution:

```json
{
  "success": true,
  "discovered_table_count": 1,
  "raw_table_index_count": 1,
  "canonical_table_count": 1,
  "candidate_table_count": 1,
  "candidate_refs": ["table:HeroTable"],
  "llm_used": false
}
```

Conclusion:

- `examples/minimal_project` passes the rule-only smoke path in one run.
- The rule-only cold start path does not depend on LLM.

## UI Path Result

Accepted UI entry/result summary:

- User can find Project Setup from the existing Game -> Project page.
- User can set Local Project Root.
- User can set Tables Root and related include/exclude/header settings.
- Source Discovery can find `HeroTable.csv`.
- Build Pipeline Status can show blocking reason / next action.
- Rule-only one-click build entry is present and disabled when prerequisites are not met.
- Progress UI can recover the active job after route changes and page refresh by reloading the persisted job id and job state.
- Manual browser acceptance was executed on macOS using the local workspace runtime.
- During manual acceptance, the successful browser path was:
  - Game -> Project
  - set `Local Project Root=/Users/Admin/LTCLaw2.0/examples/minimal_project`
  - set `Tables Root=Tables`
  - run Source Discovery and find `Tables/HeroTable.csv`
  - run `Rule-only 冷启动构建`
  - observe `succeeded / done / review_candidate_map / 1/1/1/1`
  - switch routes and return to Project page
  - refresh the page and confirm the succeeded job state recovers
  - open Map Editor and confirm there is no automatic Save Formal Map / Build Release / Publish / Set Current
  - click `Build Candidate Review` manually and load the candidate review from canonical facts

## Final Acceptance Against Required Conditions

- User can find Project Setup: yes
- User can set Local Project Root: yes
- User can set Tables Root: yes
- Source Discovery finds `HeroTable.csv`: yes
- Raw Index generates 1: yes
- Canonical Facts generate 1: yes
- Candidate Map generates 1: yes
- Build has background job: yes
- Build has progress UI: yes
- Route change does not cancel the job: yes, via persisted `active_job_id` + GET recovery semantics
- Page refresh restores state: yes, via persisted `active_job_id` + GET recovery semantics
- Failure includes `stage/error/next_action`: yes, covered by the accepted test matrix and contract checks; the manual browser run did not inject a dedicated failure case
- Rule-only does not depend on LLM: yes
- Does not auto-save Formal Map: yes
- Does not auto-build Release: yes
- Does not auto-publish Current: yes
- Smoke script passes once: yes

Accepted final summary:

- Cold Start core flow is accepted.
- Manual browser acceptance executed.
- Accepted with non-blocking UI deviations recorded.

## Manual Browser Acceptance

- Manual browser acceptance executed: yes

Environment:

- macOS
- local workspace runtime

Observed environment deviation before the accepted browser run:

- The `5175` frontend initially connected to an older `8088` backend instance.
- The two top-level Project Setup save actions returned `405` during that mismatch.
- After aligning the current workspace frontend and backend instances, the save, discovery, and build path behaved normally.
- This is not recorded as a product defect in the accepted cold start scope.
- It is recorded as an operator note: confirm frontend/backend instance version alignment before local manual browser acceptance.

Observed accepted browser run:

- Project Setup was opened from Game -> Project.
- `Local Project Root` was set to `/Users/Admin/LTCLaw2.0/examples/minimal_project`.
- `Tables Root` was set to `Tables`.
- Source Discovery found `Tables/HeroTable.csv`.
- `Rule-only 冷启动构建` was started from the Project Setup page.
- The build reached `succeeded / done / review_candidate_map / 1/1/1/1`.
- After route change and return, the succeeded cold-start job state recovered.
- After full page refresh, the succeeded cold-start job state recovered.
- Map Editor did not auto-save Formal Map, did not auto-build Release, and did not auto-publish / set current.
- After clicking `Build Candidate Review` manually, the candidate review loaded from canonical facts.

Observed job id:

- `de2369417cb34e9c9ff8d6334cb91842`

Observed success contract:

- `status = succeeded`
- `stage = done`
- `mode = rule_only`
- `next_action = review_candidate_map`
- `discovered_table_count = 1`
- `raw_table_index_count = 1`
- `canonical_table_count = 1`
- `candidate_table_count = 1`
- `candidate_refs = ["table:HeroTable"]`

LLM usage statement:

- The manual browser path entered from the `Rule-only 冷启动构建` button.
- After manual `Build Candidate Review`, Map Editor showed `candidate_source: source_canonical`.
- No LLM participation signal was observed during manual acceptance.
- The current job readback payload does not explicitly display `llm_used`, so manual acceptance is only an indirect confirmation of `llm_used=false`.
- The smoke script already directly verifies `llm_used=false`.

Recorded non-blocking deviations:

- Non-blocking UI consistency issue:
  - After a successful rule-only cold-start build, route change return and full page refresh both restored the succeeded job state.
  - However, the Source Discovery block reset to `DISCOVERED 0 / AVAILABLE 0` and again showed that the next build stage could not continue.
  - This conflicts with the restored succeeded job state shown on the same page.
  - This did not block the accepted core flow.
- Non-blocking interaction semantics issue:
  - Clicking `查看 Candidate Map` from Project Setup navigated to Map Editor.
  - The page initially still showed `No map available`.
  - A second explicit `Build Candidate Review` click was required to load the `1 systems / 1 tables` candidate review from canonical facts.
  - This is recorded as an interaction semantics deviation, not as Candidate Map unavailability.

## Known Compatibility Boundaries

- Rule-only raw rebuild intentionally remains CSV-only. `.xlsx` may be discovered but is not promoted into raw rebuild support in this phase.
- `.xls` intentionally remains unsupported.
- Multi-sheet XLSX handling is limited to the active sheet in `TableIndexer`; no multi-sheet merge behavior is introduced.
- Running-job dedupe is current-process scoped, which is sufficient for the accepted local cold-start job flow but is not a distributed task system.
- Windows path behavior was verified through normalization logic on macOS, not through a native Windows runtime run.
- Backslash-to-slash normalization remains an accepted compatibility tradeoff for this phase.

## Remaining Risk

- Manual browser click acceptance has now been executed, but the accepted record includes the two non-blocking UI deviations above.
- Windows path coverage still comes from equivalent normalization tests on macOS, not a native Windows runtime run.
- Cross-process cold-start job dedupe is not implemented and remains outside the accepted scope.
- Cold-start background job handling remains intentionally limited to this cold-start flow and is not expanded into a general task system.
- If future work wants true `.xlsx` raw rebuild support, that should be a separate feature phase rather than being folded into the accepted rule-only CSV path.