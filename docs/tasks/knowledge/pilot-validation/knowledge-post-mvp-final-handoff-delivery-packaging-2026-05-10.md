# Post-MVP Final Handoff / Delivery Packaging Closeout

Date: 2026-05-10
Scope: docs-only final handoff and delivery packaging closeout for the accepted P0-P3 MVP mainline after the data-backed final regression receipt

## 1. Current Status

The current official state is:

1. MVP complete.
2. Data-backed pilot readiness pass.
3. Pilot usable.
4. Not production ready.

This closeout does not add new product functionality.

This closeout does not continue `P20`.

This closeout does not reopen real external-provider rollout, real HTTP transport, provider/model/API key UI, Ask request-schema widening, SVN commit/update integration, relationship editor, graph canvas, or `P3.9 table_facts.sqlite` implementation.

## 2. What Is Delivered

The accepted delivered surface is:

1. local-first knowledge indexing over a configured local project directory
2. app-owned current indexes under project-level storage
3. release build
4. build-from-current-indexes
5. current release pointer
6. rollback through current-pointer switch only
7. formal map save
8. current-release keyword query
9. RAG over current release
10. structured query for exact table/field lookup
11. NumericWorkbench fast test flow
12. NumericWorkbench draft export / dry-run
13. permission split across release/map/candidate/workbench boundaries
14. browser smoke over GameProject and NumericWorkbench

The current delivered behavior remains conservative:

1. RAG reads the current release only.
2. Structured query remains explicit-open and explicit-submit.
3. NumericWorkbench export remains draft-only.
4. Test plans do not enter formal knowledge by default.
5. Rollback does not rebuild or publish.

## 3. Pilot Environment

The real data-backed pilot validation environment used in the latest accepted receipt is:

1. local project directory: `/Users/Admin/CodeBuddy/20260501110222/test-data`
2. real source set: 8 Excel tables
3. isolated runtime root: `/tmp/ltclaw-data-backed`
4. app-owned project storage root: `/tmp/ltclaw-data-backed/game_data/projects/test-data-201b6e029661`
5. user role: `maintainer`
6. current release exists
7. no real SVN/Tortoise dependency is required for this pilot pass

The 8 validated real Excel tables are:

1. `Buff效果表.xlsx`
2. `元素表.xlsx`
3. `关卡掉落表.xlsx`
4. `怪物表.xlsx`
5. `技能伤害表.xlsx`
6. `等级成长表.xlsx`
7. `装备表.xlsx`
8. `角色属性表.xlsx`

Pilot source-of-truth remains the configured local project directory plus app-owned derived assets, not SVN working-copy metadata.

## 4. Startup And Configuration

Operator preparation must stay aligned with the current repository and the accepted QA receipts.

Required preparation steps:

1. configure a valid local project directory
2. start the backend using the repository's existing startup path or scripts
3. start or build the console using the repository's existing console scripts
4. confirm `user_config`, project storage, and index status through the same endpoints used in the accepted receipts
5. confirm that a current release exists before ordinary current-release query or RAG checks

Confirmed console entry points from the current repository:

1. `console/package.json` provides `dev`, `build`, `build:prod`, `build:test`, `lint`, and `preview` scripts
2. accepted pilot validation used the latest `console/dist` as the served static bundle

Backend startup instruction for operators:

1. if the target machine already has a known-good startup script or runbook, use that existing repository path
2. if no machine-specific runbook is confirmed yet, execute the repository's existing backend startup path and use the QA receipt endpoint checks below as the acceptance standard rather than inventing a new launch contract

Confirmation standard after startup:

1. confirm `user_config` resolves the intended local project directory
2. confirm project storage resolves under app-owned `game_data/projects/...`
3. confirm `GET /api/agents/default/game/index/status` is healthy for the configured directory
4. confirm a current release exists before validating current-release query or RAG
5. if the UI does not match the current repository state, rebuild `console/dist` and recheck the configured static dir

## 5. Pilot Operating Flow

Recommended operator flow on a target machine:

1. configure the local project directory
2. rebuild the index
3. check that indexed tables are visible
4. save the formal map
5. build a release from current indexes
6. set the new release as current
7. query the current release
8. ask RAG against the current release
9. run structured query for exact facts
10. open NumericWorkbench
11. create a draft export and run dry-run
12. rollback the current release if needed

The accepted real-data flow already validated the following concrete results:

1. rebuild indexed 8 real tables
2. project-level current indexes were written
3. formal map save succeeded
4. build-from-current-indexes succeeded
5. set current succeeded
6. rollback succeeded
7. current-release query succeeded
8. current-release RAG context and answer succeeded
9. structured query returned exact-field and exact-table results
10. NumericWorkbench draft proposal create and dry-run succeeded

## 6. Recovery And Rollback

Current recovery rules are intentionally narrow.

Rollback rules:

1. rollback only switches the current pointer
2. rollback does not rebuild
3. rollback does not publish
4. rollback does not modify release artifacts
5. rollback does not modify formal-map working state
6. rollback does not modify pending test plans or release candidates

Recovery guidance:

1. if the current release is bad, switch back to the previous release
2. if current indexes are stale or missing, rerun rebuild
3. if release build cannot see current indexes, inspect the app-owned project storage path rather than the source project root
4. if retrieval status errors, first verify local project directory path resolution
5. if the UI looks stale, rebuild `console/dist`, verify the configured static dir, and reload

Known path-specific checks:

1. release build from current indexes depends on project-level app-owned current-index artifacts
2. retrieval status depends on correct local project directory path resolution in the configured runtime
3. full rescan fallback remains acceptable when SVN/Tortoise is unavailable

## 7. Permission Matrix

The current MVP capability matrix is:

1. `knowledge.read`
2. `knowledge.build`
3. `knowledge.publish`
4. `knowledge.map.read`
5. `knowledge.map.edit`
6. `knowledge.candidate.read`
7. `knowledge.candidate.write`
8. `workbench.read`
9. `workbench.test.write`
10. `workbench.test.export`

Boundary meaning:

1. ordinary fast test does not require administrator acceptance
2. administrator acceptance is only about whether something enters formal knowledge
3. draft export does not equal publish
4. ordinary RAG Q&A does not write release state
5. test plans do not enter formal knowledge by default
6. build does not imply publish
7. publish does not imply build
8. map read does not imply map edit
9. workbench test write does not imply workbench export

## 8. SVN Position

Current SVN position is explicit:

1. SVN integration is deferred.
2. Pilot uses the local project directory as source of truth.
3. Knowledge releases are app-owned artifacts.
4. SVN commit/update is not required for MVP pilot readiness.
5. Missing SVN/Tortoise does not block full rescan fallback in the accepted pilot path.
6. This round does not enable SVN commit/update.
7. SVN Phase 0/1 split is not executed in this closeout.
8. If SVN work is reopened later, it must be a separate post-MVP slice.

Any future SVN slice must treat the following as first-order concerns:

1. working-copy status
2. diff boundaries
3. conflict handling
4. DLP and logging boundaries
5. rollback consistency against app-owned release artifacts

## 9. External Provider Position

Current external-provider position is explicit:

1. external-provider remains frozen at P19
2. P20 real HTTP transport is deferred
3. there is no real provider
4. there is no real LLM
5. there is no real HTTP transport
6. there is no provider/model/API key UI
7. Ask request schema remains unchanged

The current MVP handoff must not be interpreted as production provider readiness.

## 10. Known Limitations

The current known limitations include at least the following:

1. the accepted data-backed pilot covers 8 table files only
2. `doc_knowledge` is empty in the validated real environment
3. `script_evidence` is empty in the validated real environment
4. relationship editor is deferred
5. graph canvas is deferred
6. `P3.9 table_facts.sqlite` remains optional/deferred
7. SVN commit/update remains deferred
8. production deployment, audit, and monitoring are not complete
9. the system is not production ready

Additional framing:

1. the accepted pilot is local-first and app-owned
2. the accepted pilot is suitable for controlled operator-side validation
3. the accepted pilot is not a production rollout sign-off

## 11. QA Receipt Summary

The accepted latest receipt summary is:

1. backend focused regression: `179 passed`
2. frontend TypeScript no emit: passed
3. targeted ESLint: `0 errors / 10 existing warnings`
4. production build: passed
5. data-backed smoke: passed
6. `git diff --check`: clean
7. NUL check: clean
8. keyword boundary review: clean in meaning

The current overall disposition remains:

1. Data-backed pilot readiness pass.
2. Pilot usable.
3. Not production ready.

## 12. Operator Checklist

Operator checklist for target-machine pilot support:

1. local project directory configured
2. index rebuild success
3. 8 tables visible
4. formal map saved
5. release built
6. current release set
7. rollback tested
8. query works
9. RAG works
10. structured query works
11. NumericWorkbench opens
12. draft export / dry-run works
13. no provider/model/API key UI visible
14. no SVN commit/update required

## 13. Handoff For Next Agent

The next agent should start from the following rule set:

1. if the task is only pilot support, read this final handoff first and then read the data-backed final regression receipt
2. if the task is operator-side pilot support, run the Operator Checklist on the target machine before proposing any code change
3. if the task is production-capability enhancement, open a new scoped slice instead of extending this closeout
4. do not continue `P20` by default
5. do not mix production readiness language into MVP closeout language
6. treat SVN Phase 0/1 as a separate future slice, not as part of this handoff

Recommended next action after this closeout:

1. operator-side pilot on the target machine
2. then, only if needed, a separate scoped slice such as SVN Phase 0/1 review or another post-MVP scope decision

This handoff closes delivery packaging for the current MVP/pilot state.