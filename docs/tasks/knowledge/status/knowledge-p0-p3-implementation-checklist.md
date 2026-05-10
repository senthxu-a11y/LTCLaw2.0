# Knowledge Workbench P0-P3 Implementation Checklist

> Date: 2026-05-06
> Scope: Game planner knowledge workbench, local-first knowledge releases, numeric workbench test plans

Source plans:

- `docs/plans/knowledge-architecture-handover-2026-05-06.md`
- `docs/plans/knowledge-p1-local-first-scope-2026-05-06.md`

Status as of 2026-05-10:

1. the P0-P3 MVP mainline remains closed
2. post-MVP data-backed final regression receipt completed in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-data-backed-final-regression-receipt-2026-05-10.md`
3. post-MVP final handoff / delivery packaging completed in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-final-handoff-delivery-packaging-2026-05-10.md`
4. post-MVP operator-side pilot validation completed in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-operator-side-pilot-validation-2026-05-10.md`
5. post-MVP Windows operator-side pilot validation completed in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-windows-operator-side-pilot-validation-2026-05-10.md`
6. current pilot disposition is `Operator-side pilot pass with known limitations.` on the validated Mac and Windows target machines, while the underlying mainline status remains `Data-backed pilot readiness pass.` and pilot usable
7. the current state remains not production ready
8. SVN integration remains deferred, and SVN Phase 0/1 remains deferred to a separate slice
9. external-provider remains frozen at `P3.external-provider-19`, and `P20` remains deferred
10. the next recommended action is controlled pilot usage on the validated target machines while post-MVP engineering lines are opened only as separate scoped slices with explicit non-regression checks against the accepted MVP
11. the Windows validation doc now also records the final touched-doc NUL check `all touched docs NUL=0` and keyword boundary review `clean in meaning`
12. that Windows doc keeps the Windows-side status as `Windows operator-side pilot pass with known limitations.`, pilot usable on Windows target machine, and not production ready
13. that Windows doc also keeps backend pytest waived on Windows because `pytest` is missing from that venv, not because tests failed
14. post-MVP engineering can now proceed in parallel only where write surfaces are independent: backend-only real LLM transport, Windows pilot hardening, delivery or operations hardening, SVN legacy boundary work, and NumericWorkbench practical UX
15. the highest-value next implementation line for planner-workbench usefulness is backend-only real LLM transport, but it must start as a gated P20 slice and must not become production rollout, UI provider selection, or Ask-schema expansion

---

## 0. Execution Rules

### 0.0 Model And Execution Constraints

This checklist is intended to be executed by GPT-5.4 or an equivalent coding model.

Use this execution style:

1. Do not ask the model to implement P0-P3 in one pass.
2. Execute by review gates: P0 first, then P1, then P2, then P3.
3. At each review gate, stop and verify acceptance criteria before continuing.
4. Prefer small additive modules over large rewrites.
5. Keep old APIs compatible unless a task explicitly says otherwise.
6. Do not let the model invent new product semantics outside this checklist and the two source plans.
7. If a checklist item conflicts with existing code reality, inspect the code and update the checklist or ask for review before changing architecture.
8. If implementation touches frontend UX, keep copy consistent with "local project directory", "knowledge release", "test plan", and "release candidate".
9. If implementation touches backend `.py` files, follow the DLP avoidance rules in this document.
10. Use GPT-5.5 or a senior review pass only for architecture conflicts, broad refactors, or persistent test failures.

Recommended prompt for implementation sessions:

```text
Follow docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md exactly.
Implement only the requested phase or task range.
Preserve existing /game/index, /game/workbench, and /game-knowledge-base compatibility.
Do not add SVN credential, commit, login, password, or URL handling.
Prefer additive modules and avoid SVN hot-path files unless necessary.
Run relevant checks and stop at the review gate with a concise status report.
```

Recommended first prompt for GPT-5.4:

```text
请先完整阅读 docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md，以及它引用的两份 source plans。
这轮只执行 P0，不要做 P1-P3。
严格保持旧 API 兼容，遵守 DLP Avoidance Rules。
完成 P0 后停在 P0 Review Gate，汇报改动、验证结果和下一步建议。
```

### 0.1 Product Rules That Must Not Change

1. P1 is local-first.
2. SVN is not part of the core architecture.
3. The app reads local project resources and writes app-owned derived assets.
4. Raw source tables, docs, and scripts are not copied into knowledge releases.
5. Numeric workbench edits are fast-test actions.
6. Numeric workbench tests do not require administrator acceptance.
7. Test plans do not enter the formal knowledge release by default.
8. Only release build can turn selected verified candidates into formal knowledge assets.
9. RAG reads the current knowledge release only.
10. Precise values and modifications use structured query or structured patch paths, not RAG.

### 0.2 Compatibility Rules

1. Do not delete existing SVN classes or endpoints in P0-P1.
2. Do not break existing `/game/index/*`, `/game/workbench/*`, or `/game-knowledge-base/*` callers.
3. Old config fields such as `svn.root` and `svn_local_root` may remain internally during migration, but user-facing copy should say "local project directory".
4. New release APIs should be additive first.
5. Existing table indexer and workbench logic should be reused where safe.

### 0.3 DLP Avoidance Rules

The local-first architecture reduces DLP risk because P0-P3 should not add SVN credential, commit, login, password, or remote URL flows. Still, DLP can be triggered by unsafe `.py` edits or sensitive string combinations, so implementation must follow these rules.

1. Do not add new SVN credential handling in P0-P3.
2. Do not add `.py` string literals containing real SVN URLs, usernames, passwords, token values, or command examples with credential flags.
3. Do not build release assets under the source project root.
4. Do not copy raw source tables, docs, scripts, or credential-bearing config into releases.
5. Release manifest should store hashes, counts, relative paths, and selected candidate ids only.
6. Test plans should store before/after values and relative source paths, not credentials or raw file copies.
7. New code should prefer neutral names such as `project_root`, `source_snapshot`, `release_store`, and `test_plan`, not new SVN-centered names.
8. If editing `.py` in a DLP-scanned Windows environment, follow `docs/memory/dlp-incident.md`: write via safe command-line patch/stdin workflow and verify the file has zero NUL bytes after write.
9. Avoid touching known historical DLP hot files unless necessary: `src/ltclaw_gy_x/game/service.py`, `src/ltclaw_gy_x/game/svn_client.py`, `src/ltclaw_gy_x/app/routers/game_svn.py`.
10. Prefer additive new modules for release/test-plan work over modifying SVN hot-path modules.

### 0.4 Parallel Markers

- `[S]` Sequential: do after its dependencies.
- `[P]` Parallel: can be implemented in parallel once listed dependencies are complete.
- `[R]` Review gate: stop and verify before continuing.

---

## P0. Stabilize Boundaries And Names

Goal: make the product line unambiguous before touching deeper release logic.

Status as of 2026-05-07:

1. Completed.
2. Review gate P0.4 passed.

### P0.1 [S] Freeze Terminology

Depends on: none

Tasks:

1. Use "local project directory" in user-facing UX and API descriptions.
2. Use "knowledge release" for generated formal assets.
3. Use "test plan" for numeric workbench experiments.
4. Use "release candidate" for verified test plans that may be included in a release.
5. Avoid exposing "SVN sync", "pending approval", or "accepted patch" in new knowledge UX.

Likely files:

1. `console/src/api/types/game.ts`
2. `console/src/api/modules/game.ts`
3. `console/src/pages/**/GameProject*`
4. `console/src/pages/**/NumericWorkbench*`
5. Backend router response messages under `src/ltclaw_gy_x/app/routers/game_*.py`

Acceptance:

1. New UX copy does not describe P1 as SVN-based.
2. New workbench copy does not imply administrator approval is required for testing.

### P0.2 [S] Add Knowledge Release Path Helpers

Depends on: P0.1

Tasks:

1. Add path helpers for app-owned knowledge assets.
2. Keep old helpers intact.
3. Use the existing project store convention based on local project root hash.

Target shape:

```text
<game_data>/projects/<project-key>/project/
  working/
  releases/
    current.json
    <release_id>/
      manifest.json
      map.json
      indexes/
      vectors/
      release_notes.md
  pending/
    test_plans.jsonl
    release_candidates.jsonl
```

Likely files:

1. `src/ltclaw_gy_x/game/paths.py`

Suggested helper names:

1. `get_knowledge_working_dir(project_root: Path) -> Path`
2. `get_knowledge_releases_dir(project_root: Path) -> Path`
3. `get_current_release_path(project_root: Path) -> Path`
4. `get_release_dir(project_root: Path, release_id: str) -> Path`
5. `get_pending_test_plans_path(project_root: Path) -> Path`
6. `get_release_candidates_path(project_root: Path) -> Path`

Acceptance:

1. Helpers create no files by themselves.
2. Returned paths are under app-owned `game_data/projects/...`, not under the source project root.
3. Existing path helper tests or callers remain compatible.

### P0.3 [P] Add Minimal Release Models

Depends on: P0.1

Tasks:

1. Add Pydantic models for manifest, map, release pointer, test plan, release candidate.
2. Keep models small; avoid full enterprise audit fields.

Likely files:

1. `src/ltclaw_gy_x/game/models.py`, or new `src/ltclaw_gy_x/game/knowledge_models.py`

Minimum models:

```text
KnowledgeManifest
KnowledgeMap
KnowledgeSystem
KnowledgeTableRef
KnowledgeDocRef
KnowledgeScriptRef
KnowledgeRelationship
KnowledgeReleasePointer
WorkbenchTestPlan
ReleaseCandidate
```

Acceptance:

1. Models serialize to stable JSON.
2. Schema version fields exist.
3. `source_path` means relative to local project root, not SVN root.
4. `source_hash` is present for derived indexes.

### P0.4 [R] P0 Review Gate

Checklist:

1. New names are consistent.
2. New paths are app-owned.
3. No existing SVN code was removed.
4. No workbench flow was changed yet.

---

## P1. Local Knowledge Release MVP

Goal: prove `local project resources -> release assets -> current release query`.

### P1.1 [S] Implement Release Store

Status as of 2026-05-07: completed.

Depends on: P0.2, P0.3

Tasks:

1. Create a small service for reading/writing releases.
2. Write files atomically.
3. Maintain `releases/current.json`.
4. List releases.
5. Load current release.

Likely new file:

1. `src/ltclaw_gy_x/game/knowledge_release_store.py`

Core methods:

```text
create_release(project_root, manifest, map, indexes, release_notes)
list_releases(project_root)
get_current_release(project_root)
set_current_release(project_root, release_id)
load_manifest(project_root, release_id)
```

Acceptance:

1. Creating a release writes `manifest.json`, `map.json`, `indexes/`, `release_notes.md`.
2. Setting current release updates `current.json` atomically.
3. Loading current release fails clearly when none exists.
4. Raw source files are never copied.

### P1.2 [P] Build Minimal `manifest.json`

Status as of 2026-05-07: completed.

Depends on: P0.3, P1.1

Fields:

```json
{
  "schema_version": "knowledge-manifest.v1",
  "release_id": "v2026.05.06.001",
  "created_at": "2026-05-06T00:00:00Z",
  "created_by": "admin",
  "project_root_hash": "sha256:...",
  "source_snapshot_hash": "sha256:...",
  "map_hash": "sha256:...",
  "indexes": {
    "table_schema": {
      "path": "indexes/table_schema.jsonl",
      "hash": "sha256:...",
      "count": 0
    },
    "doc_knowledge": {
      "path": "indexes/doc_knowledge.jsonl",
      "hash": "sha256:...",
      "count": 0
    },
    "script_evidence": {
      "path": "indexes/script_evidence.jsonl",
      "hash": "sha256:...",
      "count": 0
    },
    "table_facts": {
      "path": "indexes/table_facts.sqlite",
      "hash": null,
      "count": 0
    }
  }
}
```

Acceptance:

1. Manifest can validate before release is set current.
2. Hashes are deterministic for unchanged generated files.
3. Missing optional indexes are represented explicitly.

### P1.3 [P] Build Minimal `map.json`

Status as of 2026-05-07: completed.

Depends on: P0.3, P1.1

Minimum shape:

```json
{
  "schema_version": "knowledge-map.v1",
  "systems": [],
  "tables": [],
  "docs": [],
  "scripts": [],
  "relationships": [],
  "deprecated": []
}
```

Acceptance:

1. Map can represent system -> table, system -> doc, table -> script, doc -> table.
2. Objects can be marked `active`, `deprecated`, or `ignored`.
3. Map is independent from raw source file contents.

### P1.4 [S] Export `table_schema.jsonl`

Status as of 2026-05-07: completed.

Depends on: P1.1, existing table indexer

Tasks:

1. Reuse `TableIndexer` to scan configured table paths.
2. Convert `TableIndex` to release-friendly JSONL records.
3. Use `source_path` relative to local project root.
4. Keep `svn_revision` out of new release schema, or map it to optional `source_revision`.

Likely files:

1. `src/ltclaw_gy_x/game/table_indexer.py`
2. New `src/ltclaw_gy_x/game/knowledge_builders.py`

Acceptance:

1. Each table produces one JSONL record.
2. Fields include name, type, description, confidence, primary key, row count, source path, source hash.
3. The release query API can list tables from this file without reading old index directories.

### P1.5 [P] Export Stub `doc_knowledge.jsonl`

Status as of 2026-05-07: completed as adapter-only export.

Depends on: P1.1

Tasks:

1. Start with confirmed document knowledge entries only.
2. Reuse `KnowledgeBaseStore` or doc library metadata where available.
3. Export approved entries into release JSONL.
4. Do not copy raw documents.

Likely files:

1. `src/ltclaw_gy_x/knowledge_base/kb_store.py`
2. `src/ltclaw_gy_x/game/retrieval.py`
3. New `src/ltclaw_gy_x/game/knowledge_builders.py`

Acceptance:

1. Export file exists even when empty.
2. Each record has title, summary, category, tags, source_path, related tables, source hash if available.

### P1.6 [P] Export Stub `script_evidence.jsonl`

Status as of 2026-05-07: completed as adapter-only export.

Depends on: P1.1

Tasks:

1. Reuse existing code indexer if available.
2. Export empty JSONL safely when code index is unavailable.
3. Keep this optional for P1.

Likely files:

1. `src/ltclaw_gy_x/game/code_indexer.py`
2. New `src/ltclaw_gy_x/game/knowledge_builders.py`

Acceptance:

1. Release build does not fail if scripts are absent.
2. Manifest records count `0` for empty script evidence.

### P1.7 [S] Add Release Build API

Status as of 2026-05-07: completed for backend/internal use.

Depends on: P1.1, P1.2, P1.3, P1.4

Tasks:

1. Add API to build a local release from configured project resources.
2. Add API to list releases.
3. Add API to set current release.
4. Keep old `/game/index/rebuild` unchanged.

Suggested endpoint prefix:

```text
/game/knowledge/releases
```

Likely new file:

1. `src/ltclaw_gy_x/app/routers/game_knowledge_release.py`

Router registration:

1. Add import and `router.include_router(...)` in `src/ltclaw_gy_x/app/routers/agent_scoped.py`.

Endpoints:

```text
POST /game/knowledge/releases/build
GET  /game/knowledge/releases
GET  /game/knowledge/releases/current
POST /game/knowledge/releases/{release_id}/current
GET  /game/knowledge/releases/{release_id}/manifest
```

Acceptance:

1. Build endpoint creates a release without SVN.
2. Set-current endpoint switches `current.json`.
3. Failure messages distinguish missing config, missing project root, and build failure.
4. The build endpoint currently accepts a full derived payload and remains an internal skeleton; do not expose it as an ordinary frontend build button without a dedicated UX boundary review.

### P1.8 [S] Add Current Release Query API

Status as of 2026-05-07: completed.

Depends on: P1.7

Tasks:

1. Query only current release files.
2. Support simple table/schema search.
3. Support simple doc knowledge search.
4. Return source path and release id in every item.

Endpoint:

```text
POST /game/knowledge/query
```

Request:

```json
{
  "query": "skill damage",
  "top_k": 10,
  "mode": "hybrid"
}
```

Acceptance:

1. If no current release exists, returns clear `not_configured` or `no_current_release`.
2. Results never read raw source tables for RAG-style query.
3. Every result includes `source_type`, `source_path`, `release_id`, and `updated_at` or `built_at`.
4. Current implementation is keyword-only current-release search, not RAG.

### P1.9a [P] Frontend Minimal Release Status UX

Depends on: P1.7 API shape

Status as of 2026-05-07: completed.

Tasks:

1. Add or adapt page section for release status.
2. Show current release id, build time, counts.
3. Show release list.
4. Provide set-current action if multiple releases exist.
5. Keep copy aligned with "knowledge release" and "local project directory".

Likely files:

1. `console/src/api/modules/gameKnowledgeRelease.ts`
2. `console/src/api/types/game.ts`
3. Existing game project or knowledge pages under `console/src/pages/**`

Acceptance:

1. UI can read release list and current release from existing release APIs.
2. UI can switch current release from release list.
3. UI copy says "knowledge release", not "SVN sync".
4. No build release button is exposed in P1.9a.

Implemented scope note:

1. The completed UI is a minimal Release Status/list/set-current panel in the existing GameProject page.
2. It is read-mostly and only writes via `POST /game/knowledge/releases/{release_id}/current`.
3. It does not call `POST /game/knowledge/releases/build`.
4. It does not add map review UX, release candidate selection, RAG entry, or expanded query semantics.

### P1.9b [S] Frontend Build Release UX Boundary Review And Design

Depends on: P1.7, P1.9a

Status as of 2026-05-07: completed.

Tasks:

1. Review what frontend input shape is safe for a build action.
2. Decide whether the current build endpoint should stay internal or gain a narrower frontend-facing contract.
3. Define the boundary between map confirmation, release candidate inclusion, and release build.
4. Only after that review, consider a normal frontend build button.

Acceptance:

1. No ordinary build button is added before the boundary review is complete.
2. Frontend does not directly expose the current full-payload build endpoint as a general user action.

Implemented scope note:

1. The boundary review is recorded in `docs/tasks/knowledge/mvp/knowledge-p1-9b-build-ux-boundary-review-2026-05-07.md`.
2. It explicitly keeps `POST /game/knowledge/releases/build` as an internal/test-only endpoint.
3. It requires a server-side safe endpoint before any normal frontend build button.

### P1.9c [P] Backend Safe Build-From-Current-Indexes Endpoint

Depends on: P1.7, P1.9b

Status as of 2026-05-07: completed.

Tasks:

1. Add a server-side `POST /game/knowledge/releases/build-from-current-indexes` endpoint.
2. Resolve build inputs from server-owned state rather than frontend-composed payloads.
3. Reuse the app-owned release store and existing release manifest/map builders.
4. Fail with explicit prerequisite errors when current formal map, current indexes, or approved docs are missing.

Acceptance:

1. The endpoint reads local project directory, current release map, current table/code indexes, and approved docs on the server side.
2. The frontend-facing request shape stays narrow: `release_id`, `release_notes`, optional `candidate_ids`.
3. The build path does not perform SVN write/commit operations.
4. The release output remains app-owned derived assets only.

Implemented scope note:

1. The router remains thin and forwards only project root, workspace dir, and narrow request intent.
2. The service now validates current formal-map membership for `candidate_ids`.
3. Missing current release is normalized to a prerequisite error for frontend-safe handling.
4. This boundary is reviewed in `docs/tasks/knowledge/mvp/knowledge-p1-9c-review-gate-2026-05-07.md`.

### P1.9d [P] Frontend Safe Build Release Button

Depends on: P1.9c

Status as of 2026-05-07: completed.

Tasks:

1. Add a normal build button in the existing GameProject release panel.
2. Use only the safe backend endpoint from P1.9c.
3. Keep frontend input narrow and avoid derived payload transport.
4. Refresh release status/list after a successful build.

Acceptance:

1. The button does not call `POST /game/knowledge/releases/build`.
2. The modal submits only `release_id`, `release_notes`, and empty or optional `candidate_ids`.
3. Existing read/list/set-current behavior continues to work.
4. Build success does not implicitly set current release.

Implemented scope note:

1. The GameProject release panel now exposes a minimal build modal.
2. The frontend API wrapper calls only `POST /game/knowledge/releases/build-from-current-indexes`.
3. Success refreshes the release list/current status, but set-current remains an explicit separate action.

### P1.10 [R] P1 Review Gate

Status as of 2026-05-07: final P1 gate passed for a local-first MVP loop, including safe build endpoint and safe frontend build UX.

Boundary qualifier:

1. P1 is complete for trusted or single-user local-first MVP usage.
2. P1 is not yet a hardened multi-role governance surface.
3. Build, set-current, full-payload build, and future map-edit routes still require backend capability checks before multi-user use.

Checklist:

1. A local project directory can produce a release.
2. `current.json` points to that release.
3. Query reads current release.
4. Raw source resources are not copied into release.
5. Existing `/game/index/*` still works as before.
6. Current release query does not perform SVN write/commit operations.
7. Representative existing `/game/workbench/*` behavior still works as before.

Current verified result (2026-05-07):

1. Build release: passed.
2. Set current: passed.
3. Query current release: passed.
4. No raw source read in release query path: passed.
5. No SVN write/commit in new release query path: passed.
6. Old index/workbench representative regression: passed.
7. Safe build-from-current-indexes endpoint: passed.
8. Frontend build button bound only to safe endpoint: passed.
9. Backend regression `18 passed` across release build/current/query service and router slices: passed.
10. Frontend typecheck for release build UI: passed.

Current non-goal at this gate:

1. Direct ordinary-user exposure of `POST /game/knowledge/releases/build`.
2. Release candidate selection UX beyond empty/default `candidate_ids`.
3. RAG or semantic retrieval beyond current keyword-only release query.
4. Full permission hardening for build/publish/map-edit.

---

## P2. Numeric Workbench Test Plans And Release Candidates

Goal: separate fast numeric testing from formal knowledge release.

Current scope note as of 2026-05-07:

1. `pending/test_plans.jsonl` and `pending/release_candidates.jsonl` are app-owned pending data under the project store.
2. Test plans and release candidates do not automatically enter the formal knowledge release.
3. Test plans and release candidates do not automatically set the current knowledge release.
4. Ordinary workbench fast testing does not require administrator acceptance.
5. Candidate `accepted` is release-eligibility state, not a required approval gate for fast numeric testing.
6. The current P2.1/P2.2 slice does not read or write SVN and does not copy raw source files.

### P2.1 [S] Add Test Plan Store

Status as of 2026-05-07: completed as a minimal app-owned pending JSONL persistence layer.

Depends on: P0.2, P0.3

Tasks:

1. Store workbench test plans in app-owned pending storage.
2. Use JSONL for P2.
3. Do not require administrator acceptance.
4. Keep pending test-plan state separate from formal knowledge release assets.

Likely new file:

1. `src/ltclaw_gy_x/game/knowledge_test_plan_store.py`
2. `src/ltclaw_gy_x/app/routers/game_knowledge_test_plans.py`

Minimum operations:

```text
append_test_plan
list_test_plans
get_test_plan
```

Acceptance:

1. Users can save test plans without touching release assets.
2. Test plan statuses are `draft`, `testing`, `kept`, `discarded`.
3. Release candidate is separate from ordinary test plan state.
4. Test plans persist only in app-owned pending storage at `pending/test_plans.jsonl`.
5. Test plans do not automatically enter the formal knowledge release.
6. Test plans do not automatically set current release.
7. Test plan persistence does not read or write SVN and does not copy raw source files.

Implemented scope note:

1. The current store layer is append/list-first and returns an empty list when the pending file is missing.
2. Stored paths must remain relative to the local project directory; absolute and `..` escape paths are rejected.
3. The current P2.1 slice is a persistence/router boundary only, not the full workbench save UX.

### P2.2 [S] Add Release Candidate Store

Status as of 2026-05-07: completed as a minimal app-owned pending JSONL persistence layer.

Depends on: P2.1

Tasks:

1. Store verified or proposed release candidates in app-owned pending storage.
2. Use JSONL for P2.
3. Keep release candidates separate from ordinary test plan state.
4. Keep the status model minimal: `pending`, `accepted`, `rejected`.
5. Require linkage to a source test plan and relative local-project source refs.

Likely files:

1. `src/ltclaw_gy_x/game/knowledge_release_candidate_store.py`
2. `src/ltclaw_gy_x/app/routers/game_knowledge_release_candidates.py`

Acceptance:

1. Release candidates persist only in app-owned pending storage at `pending/release_candidates.jsonl`.
2. Release candidate state remains separate from ordinary test plan state.
3. Release candidates do not automatically enter the formal knowledge release.
4. Release candidates do not automatically set current release.
5. Release candidate persistence does not read or write SVN and does not copy raw source files.

Implemented scope note:

1. The current store layer is append/list-first and returns an empty list when the pending file is missing.
2. Each candidate references `test_plan_id` and normalized relative `source_refs` only.
3. Stored paths must remain relative to the local project directory; absolute and `..` escape paths are rejected.
4. The current P2.2 slice does not yet implement candidate filtering, build-time selection review, or formal release merge.

### P2.3 [S] Candidate List And Filter Semantics

Status as of 2026-05-07: completed.

Depends on: P2.2

Tasks:

1. Add minimal read/list semantics for release candidates.
2. Support narrow filters for `status`, `selected`, and `test_plan_id`.
3. Keep candidate query as pending-state inspection only.
4. Do not merge candidates into the formal knowledge release.

Likely files:

1. `src/ltclaw_gy_x/game/knowledge_release_candidate_store.py`
2. `src/ltclaw_gy_x/app/routers/game_knowledge_release_candidates.py`

Acceptance:

1. Candidate list returns an empty list when the pending file is missing.
2. Candidate list supports `status`, `selected`, and `test_plan_id` filters.
3. Invalid filter values fail clearly.
4. Querying candidates does not mutate release assets, `current.json`, or source resources.

Implemented scope note:

1. The current list path is still read-only pending-state inspection.
2. Candidate query does not perform formal release merge.
3. Candidate query does not set current release.
4. Candidate query does not read or write SVN and does not copy raw source files.

### P2.4 [S] Candidate-To-Release Inclusion Boundary Review

Status as of 2026-05-07: completed.

Depends on: P1.9c, P2.2, P2.3

Tasks:

1. Define when a release candidate is eligible for formal release inclusion.
2. Define whether inclusion is automatic or build-time only.
3. Define which backend boundary should execute inclusion.
4. Define validation rules for `candidate_ids`, status, and selected state.
5. Define what inclusion may write into release-owned derived artifacts.

Acceptance:

1. Release candidates do not automatically enter the formal knowledge release.
2. Inclusion is build-time only and stays behind the safe backend build endpoint.
3. Frontend continues to send narrow intent only, not full derived payloads.
4. `pending` and `rejected` candidates are excluded by rule.
5. `accepted` candidates still require explicit `candidate_ids` selection.
6. Build success still does not imply set-current.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p2-4-candidate-release-inclusion-review-2026-05-07.md`.
2. Candidate eligibility is defined as `accepted + selected + explicitly requested in candidate_ids`.
3. `selected == false` should fail clearly rather than be silently skipped.
4. Inclusion output may write only release-owned derived metadata or evidence, never raw source copies.

### P2.5 [S] Backend Build-Time Candidate Inclusion

Depends on: P1.9c, P2.4

Status as of 2026-05-07: completed.

Tasks:

1. Extend the existing safe backend build path to resolve requested `candidate_ids` from the release candidate store.
2. Validate that every requested candidate exists, is `accepted`, and is `selected == true`.
3. Record validated candidate inclusion in release-owned derived metadata or evidence.
4. Keep router input narrow and router behavior thin.
5. Do not copy raw source files and do not set current release automatically.

Important rule:

```text
No candidate_ids -> release is built from current local project resources only.
```

Acceptance:

1. Admin can build release with zero candidates.
2. Admin can build release with explicit validated candidates.
3. Non-existent, pending, rejected, or unselected candidates fail clearly.
4. Inclusion is implemented in the backend service path, not as frontend UI work.
5. Inclusion does not add RAG work and does not restore the old full-payload build endpoint as a normal frontend path.
6. Current release query does not read `candidate_evidence`.

Implemented scope note:

1. Candidate inclusion happens only at build-time through `POST /game/knowledge/releases/build-from-current-indexes`.
2. A candidate enters the release only when it is explicitly listed in `candidate_ids`, `status == accepted`, and `selected == true`.
3. Validated inclusion is written as release-owned metadata or evidence in `indexes/candidate_evidence.jsonl` and `manifest.indexes.candidate_evidence`.
4. `candidate_evidence.jsonl` does not copy raw source tables, docs, or scripts.
5. Build success still does not set the current release automatically.
6. The current query path does not read `candidate_evidence`; no RAG or candidate-evidence retrieval work is added here.
7. Frontend candidate selection UI is still deferred to P2.6; this slice is backend-only.

### P2.6 [P] Frontend Release Candidate Selection UX

Depends on: P2.5 API shape

Status as of 2026-05-07: completed.

Tasks:

1. On release build page, show verified release candidates.
2. Default all candidates unchecked.
3. Show table, primary key, field, before/after, test note.
4. Let admin choose candidates for this release.

Acceptance:

1. Build page makes it clear candidates are optional.
2. Normal users do not see release build controls.

Implemented scope note:

1. The build release modal now reads only `accepted + selected=true` candidates from `GET /game/knowledge/release-candidates`.
2. The frontend still sends only narrow intent fields: `release_id`, `release_notes`, and `candidate_ids`.
3. All candidates are unchecked by default, so `candidate_ids=[]` preserves the existing safe build behavior.
4. The modal does not add admin approval actions, candidate status mutation, or selected toggles.
5. Build success still does not set the current release automatically.
6. This slice does not add RAG work, query expansion, or the old full-payload build endpoint.

### P2.7 [R] P2 Review Gate

Status as of 2026-05-07: completed.

Checklist:

1. Numeric workbench fast-test loop does not require admin.
2. Test plans persist outside release directories.
3. Release build can optionally include selected candidates.
4. Existing workbench preview and query still work.
5. Candidate inclusion is build-time only and does not automatically set current release.
6. Candidate evidence is release-owned metadata/evidence only and does not copy raw source files.

Current verified result (2026-05-07):

1. P2.1 test plan store: passed.
2. P2.2 release candidate store: passed.
3. P2.3 candidate list and filter semantics: passed.
4. P2.4 inclusion boundary review: passed.
5. P2.5 backend build-time candidate inclusion: passed.
6. Focused P2.5 service validation: `11 passed`.
7. Adjacent regression across release candidate store/router, test plan store/router, release build/store/service/router/query: `72 passed`.
8. Current release query remains keyword-only and does not read `candidate_evidence`.
9. P2.6 frontend candidate selection UI: passed.
10. TypeScript validation rerun: `npm exec tsc -- -p tsconfig.app.json --noEmit --incremental false` passed.
11. No repository-local GameProject or release-candidate frontend test suite exists yet; no related frontend tests were available to run.
12. Final P2 regression across test plan store, release candidate store/filter, build-time inclusion, release store/service/router/query, and representative game index/workbench routes: `97 passed`.
13. P2-related Python source and test files rechecked for DLP/NUL corruption: all `NUL=0` after targeted repair of `tests/unit/game/test_knowledge_release_store.py`.

Final gate result:

1. P2 is closed for the current MVP slice.
2. No new backend or frontend functionality was added during the final gate.
3. The current release query remains keyword-only and does not read `candidate_evidence`.
4. Build success still does not set current release automatically.
5. No SVN read/write or commit behavior was added in the P2 slice.

Remaining items after P2 close:

1. P3 RAG integration: not started.
2. Admin approval UI: not started.
3. Candidate-evidence query or RAG usage: not started.
4. SVN resource-pull adapter: not started and not part of the current mainline.

---

## P3. Map Governance, RAG Routing, And Hardening

Goal: make releases useful and safer without changing the P1/P2 boundaries.

### P3.1 [S] RAG Read Boundary Review

Depends on: P1.8, P2.7

Status as of 2026-05-07: completed.

Tasks:

1. Define the minimum read boundary for future RAG work.
2. Define which release-owned artifacts are allowed as default RAG inputs.
3. Define which paths remain out of bounds: raw source, pending files, SVN, and external paths.
4. Define the split between explanatory RAG reads and precise structured query or workbench flows.
5. Define the next implementation step without introducing full RAG, vector store, or chat UI.

Acceptance:

1. RAG is bounded to current-release, release-owned artifacts only.
2. Raw source files, pending data, SVN resources, and app-external paths are explicitly forbidden.
3. `candidate_evidence.jsonl` is excluded from default RAG reads.
4. No current release yields `no_current_release` or an equivalent explicit status.
5. P3.2 is defined as context assembly skeleton work, not full RAG productization.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md`.
2. The default allowed artifacts are `table_schema.jsonl`, `doc_knowledge.jsonl`, `script_evidence.jsonl`, plus manifest and map metadata.
3. The current release query remains keyword-only and is still not RAG.
4. `candidate_evidence.jsonl` does not currently participate in query or RAG.

### P3.2 [P] RAG Context Assembly Skeleton

Depends on: P3.1

Status as of 2026-05-07: completed as a read-only context assembly skeleton.

Tasks:

1. Add a bounded retrieval context builder next to the current keyword query service.
2. Input only `query + current release`.
3. Output bounded context chunks plus citations.
4. Use current-release, release-owned artifacts only.
5. Do not call an LLM yet.
6. Do not introduce vector store yet.

Acceptance:

1. Context assembly reads no raw source files.
2. Every citation includes `release_id` plus artifact or source reference.
3. The skeleton does not mutate releases or switch current release.
4. This is still not a full RAG chat UI.

Implemented scope note:

1. The current P3.2 slice builds bounded context from current-release, release-owned artifacts only.
2. The allowed read surface remains `manifest.json`, `map.json`, `indexes/table_schema.jsonl`, `indexes/doc_knowledge.jsonl`, and `indexes/script_evidence.jsonl`.
3. `indexes/candidate_evidence.jsonl` remains excluded from default RAG/context reads.
4. The output is context-only: `mode`, `query`, `release_id`, `built_at`, `chunks`, and `citations`.
5. This slice does not generate answers, does not call an LLM, does not add embedding or vector-store work, and does not add frontend UI.
6. The builder remains read-only and does not mutate releases or auto-set current release.

### P3.2b [S] Read-Only Debug Context Endpoint

Depends on: P3.2

Status as of 2026-05-07: completed.

Tasks:

1. Expose the existing P3.2 context builder through a thin debug router only.
2. Keep request shape narrow: `query`, `max_chunks`, `max_chars`.
3. Return the context-builder payload directly without answer generation.
4. Mount the endpoint under the agent-scoped router.
5. Keep the router read-only and avoid direct artifact reads in the router layer.

Acceptance:

1. The endpoint is available at `/api/agents/{agentId}/game/knowledge/rag/context`.
2. The response returns context chunks and citations only; it does not generate an answer.
3. The endpoint remains bounded to current-release, release-owned artifacts only.
4. The endpoint does not read raw source files, pending data, or `candidate_evidence.jsonl` by default.
5. The endpoint does not read or write SVN, does not mutate releases, and does not auto-set current release.
6. This slice does not add LLM integration, embedding, vector store, or frontend UI.

Implemented scope note:

1. The current request shape is `query`, `max_chunks`, and `max_chars`.
2. The current response shape is `mode`, `query`, `release_id`, `built_at`, `chunks`, and `citations`.
3. The router is a thin forwarding layer over the existing context builder; it does not assemble prompts, do retrieval policy expansion, or read artifacts directly.

### P3.3 [S] RAG Answer Adapter Boundary Review

Depends on: P3.2, P3.2b

Status as of 2026-05-07: completed as a boundary review.

Tasks:

1. Define the boundary between P3.2 context assembly and any future answer-generation step.
2. Require any future answer adapter to consume only the P3.2/P3.2b context payload.
3. Forbid answer generation code from directly reading release artifacts, project files, pending files, or SVN.
4. Define citation rules so every answer citation comes only from provided context citations.
5. Define the next implementation step as a backend answer-service skeleton, not UI or vector-store work.

Acceptance:

1. The next P3 slice does not start with frontend UI.
2. Any future answer service consumes only the P3.2/P3.2b context payload, not raw artifacts or project files.
3. The boundary remains compatible with no-LLM or stubbed-answer modes during early implementation.
4. Candidate evidence remains excluded unless a later dedicated review explicitly widens the read boundary.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-3-rag-answer-adapter-boundary-review-2026-05-07.md`.
2. The approved adapter input is `query + context`, where `context` is the existing P3.2 context-builder payload.
3. The adapter must not directly read `manifest.json`, `map.json`, release JSONL artifacts, raw source files, pending JSONL files, or SVN resources.
4. The adapter must not mutate releases, set current release, or create candidates.
5. The adapter must return `insufficient_context` rather than inventing unsupported facts or citations.

### P3.4 [S] Minimal Answer Service Skeleton

Depends on: P3.3

Status as of 2026-05-07: completed as a backend-only minimal answer service skeleton.

Tasks:

1. Add a backend-only answer-service skeleton that accepts only `query + context`.
2. Keep the first implementation compatible with deterministic or mock/no-LLM answer generation.
3. If a real model is later connected, inject it through a single model-client boundary and mock it in tests.
4. Preserve citation forwarding from provided context only.
5. Do not add frontend UI, vector store, embedding, tool calls, or direct artifact reads in this slice.

Acceptance:

1. The next code slice is a backend-only answer-service skeleton, not UI work.
2. The skeleton can run without a real LLM.
3. Any later real LLM integration stays behind a single injected model client.
4. The service consumes only P3.2/P3.2b context output and never rereads artifacts directly.

Implemented scope note:

1. The current backend-only minimal answer service skeleton is implemented in `src/ltclaw_gy_x/game/knowledge_rag_answer.py`.
2. The input boundary is `query + P3.2/P3.2b context payload` only.
3. The output shape is `mode`, `answer`, `release_id`, `citations`, and `warnings`.
4. The current implementation is deterministic/no-LLM and does not connect a real model client.
5. The service does not directly read release artifacts, raw source files, pending JSONL files, or SVN resources.
6. Returned citations may come only from `context.citations`; the service does not synthesize new citations.
7. When grounded support is missing, the service returns `insufficient_context` rather than inventing unsupported facts.
8. This slice does not add a new router and does not add frontend changes.

### P3.4b [S] Backend-Only RAG Answer Debug Endpoint

Depends on: P3.2b, P3.4

Status as of 2026-05-07: completed as a backend-only debug answer endpoint.

Tasks:

1. Add a thin backend-only debug answer endpoint over the existing context builder and deterministic answer service.
2. Keep the router thin: resolve workspace, game service, project root, and request fields only.
3. Reuse the existing `query`, `max_chunks`, and `max_chars` request shape.
4. Forward context builder output directly into the deterministic answer service.
5. Do not add frontend UI, real LLM, embedding, vector store, direct artifact reads, or retrieval-policy expansion in this slice.

Acceptance:

1. The new endpoint is exposed at `/api/agents/{agentId}/game/knowledge/rag/answer`.
2. The endpoint remains backend-only and debug-oriented.
3. The router only chains `context builder -> deterministic answer service`.
4. Artifact reads occur only inside the existing context builder, not in the router.
5. Blank-query requests return `insufficient_context` rather than triggering new retrieval behavior.
6. The slice still does not connect a real LLM and does not add frontend work.

Implemented scope note:

1. The current debug answer endpoint is exposed at `/api/agents/{agentId}/game/knowledge/rag/answer`.
2. It is a backend-only debug answer endpoint, not a frontend or chat UI surface.
3. The request body is `query`, `max_chunks`, and `max_chars`.
4. The response shape is `mode`, `answer`, `release_id`, `citations`, and `warnings`.
5. Blank `query` after trim returns `insufficient_context`.
6. The router only chains the existing context builder to the deterministic answer service.
7. Artifact reads occur only in the context builder; the router does not directly read artifacts.
8. This slice still does not connect a real LLM, add embedding or vector store work, or add frontend changes.

### P3.5 [S] Map Candidate Builder

Depends on: P1.3, P1.4

Status as of 2026-05-07: completed as a backend-only deterministic map candidate builder.

Tasks:

1. Generate a deterministic candidate map from current or explicit release-owned artifacts only.
2. Reuse manifest/map metadata plus release-owned table, doc, and script indexes as the only default inputs.
3. Preserve existing map hints when available, but keep generation deterministic and backend-only.
4. Generate relationships only when release-owned evidence explicitly supports them.
5. Do not save the formal map, mutate a release, or set current release in this slice.

Likely files:

1. `src/ltclaw_gy_x/game/knowledge_map_candidate.py`
2. `tests/unit/game/test_knowledge_map_candidate.py`

Acceptance:

1. The builder reads only the current release or an explicit release id.
2. Default inputs are limited to `manifest.json`, `map.json`, `indexes/table_schema.jsonl`, `indexes/doc_knowledge.jsonl`, and `indexes/script_evidence.jsonl`.
3. The builder does not read raw source files, pending JSONL files, `indexes/candidate_evidence.jsonl`, or SVN resources.
4. The builder produces a deterministic candidate map containing `tables`, `docs`, `scripts`, `systems`, and `relationships`.
5. Relationships are generated only when evidence exists in release-owned artifacts; the builder must not guess unsupported links.
6. The slice does not save the formal map, mutate release assets, or call `set_current_release`.

Implemented scope note:

1. The current deterministic map candidate builder is implemented in `src/ltclaw_gy_x/game/knowledge_map_candidate.py`.
2. Focused coverage is implemented in `tests/unit/game/test_knowledge_map_candidate.py`.
3. The builder reads only the current release or an explicit `release_id` through the existing release-store boundary.
4. Default inputs are limited to manifest/map metadata plus `table_schema.jsonl`, `doc_knowledge.jsonl`, and `script_evidence.jsonl` from the selected release.
5. The builder does not read raw source files, `pending/test_plans.jsonl`, `pending/release_candidates.jsonl`, `indexes/candidate_evidence.jsonl`, or SVN resources.
6. The builder generates a deterministic candidate `KnowledgeMap` with `tables`, `docs`, `scripts`, `systems`, and evidence-backed `relationships`.
7. Relationship generation is evidence-only; unsupported links are not guessed.
8. The builder is read-only with respect to formal map and release state: it does not save a formal map, modify release artifacts, or set current release.

### P3.6 [P] Map Review API

Depends on: P3.5

Status as of 2026-05-07: completed as a read-only map candidate API skeleton.

Tasks:

1. Expose the deterministic candidate map through a thin read-only backend debug/review API.
2. Keep the router thin: resolve workspace, game service, project root, and optional `release_id` only.
3. Return candidate-map payload only; do not save or edit the formal map in this slice.
4. Do not add frontend UI in this slice.

Endpoints:

```text
GET  /api/agents/{agentId}/game/knowledge/map/candidate
```

Acceptance:

1. The endpoint is read-only and exposes candidate-map inspection only.
2. The only query parameter is optional `release_id`.
3. When `release_id` is omitted, the endpoint uses the current release.
4. The response shape is `mode`, `release_id`, and `map`, where `map` is the candidate `KnowledgeMap`.
5. When no current release exists, the fixed behavior is HTTP 404 with detail `No current knowledge release is set`.
6. The router remains thin and only forwards to the P3.5 builder; it does not read artifacts directly and does not construct map content.
7. The API does not save or edit the formal map.
8. The API does not provide `PUT map`, does not mutate release assets, does not call `set_current_release`, and does not add frontend work.

Implemented scope note:

1. The current read-only endpoint is exposed at `/api/agents/{agentId}/game/knowledge/map/candidate`.
2. The only query parameter is optional `release_id`.
3. When `release_id` is omitted, the endpoint uses the current release.
4. The response shape is:

```json
{
  "mode": "candidate",
  "release_id": "...",
  "map": {"...": "KnowledgeMap"}
}
```

1. When no current release exists, the fixed behavior is HTTP 404 with detail `No current knowledge release is set`.
2. The router only resolves workspace, game service, project root, and query params, then forwards to `build_map_candidate_from_release(project_root, release_id=...)`.
3. The router does not read release artifacts directly and does not construct map content itself.
4. This slice does not save the formal map, does not provide `PUT map`, does not modify release state, does not call `set_current_release`, and does not add frontend UI.

### P3.7a [S] Formal Map Read/Save Boundary Review

Depends on: P3.6

Status as of 2026-05-07: completed as a formal map read/save boundary review.

Tasks:

1. Define the boundary between candidate map, saved formal map, and release snapshot map.
2. Define where saved formal map should live inside app-owned project storage.
3. Define future read/save API behavior before implementing backend write paths.
4. Define validation and release-build interaction rules before any frontend work.

Acceptance:

1. Formal map is defined as app-owned project-level state.
2. Saving formal map is explicitly separated from release build and current-release pointer updates.
3. Recommended storage stays in app-owned working state, not release history or pending JSONL files.
4. The next implementation step is backend formal map store plus GET/PUT API, not frontend UI.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-7a-formal-map-read-save-boundary-review-2026-05-07.md`.
2. It defines formal map as app-owned project-level state rather than raw source, pending test-plan state, or release-candidate state.
3. It recommends storing formal map under app-owned `working/` state rather than `releases/<release_id>/map.json`.
4. It recommends explicit `no_formal_map` for future `GET /game/knowledge/map` when no saved formal map exists.
5. It keeps future save behavior decoupled from release mutation, build trigger, and current-release switching.

### P3.7b [P] Backend Formal Map Store And API

Depends on: P3.7a

Status as of 2026-05-07: backend store/API validation landed; not productized.

Tasks:

1. Add backend formal map store under app-owned project state.
2. Add backend `GET /game/knowledge/map`.
3. Add backend `PUT /game/knowledge/map`.
4. Keep router thin and place validation plus atomic write logic in store/service.
5. Do not add frontend UI in this slice.

Acceptance:

1. `GET /game/knowledge/map` returns saved formal map or explicit `no_formal_map`.
2. `PUT /game/knowledge/map` validates schema, paths, status, and relationships before save.
3. Save does not mutate release history.
4. Save does not set current release.
5. Save does not read or write SVN.
6. The next code slice remains backend-only and does not add frontend UI.

Implemented scope note:

1. The current P3.7b implementation updates these files: `src/ltclaw_gy_x/game/paths.py`, `src/ltclaw_gy_x/game/local_project_paths.py`, `src/ltclaw_gy_x/game/knowledge_formal_map_store.py`, `src/ltclaw_gy_x/game/knowledge_release_builders.py`, `src/ltclaw_gy_x/app/routers/game_knowledge_map.py`, `src/ltclaw_gy_x/app/routers/agent_scoped.py`, `tests/unit/game/test_knowledge_formal_map_store.py`, and `tests/unit/routers/test_game_knowledge_map_router.py`.
2. The saved formal map lives under the app-owned project store at `working/formal_map.json`.
3. `GET /game/knowledge/map` now returns `mode=formal_map` plus `map`, `map_hash`, `updated_at`, and `updated_by` when a saved formal map exists.
4. `GET /game/knowledge/map` returns HTTP 200 with `mode=no_formal_map` and null `map`, `map_hash`, `updated_at`, and `updated_by` when no saved formal map exists.
5. `PUT /game/knowledge/map` accepts `map` plus optional `updated_by`, then returns `mode=formal_map_saved`, `map_hash`, `updated_at`, and `updated_by`.
6. Save-time validation currently covers `KnowledgeMap` schema validation, allowed enum `status` values through model validation, tables/docs/scripts `source_path` guards, relationship endpoint reference validation, relationship `source_hash` prefix validation, deprecated-ref validation, and deterministic `map_hash` generation.
7. The formal-map save path uses app-owned storage only and does not modify any historical release, does not auto-build a release, does not auto-set current release, and does not read or write SVN.
8. The current validation scope remains backend-only; no frontend UI or map-review UX is added in this slice.

Open product gaps:

1. Safe-build formal-map consumption is implemented in the backend safe-build path, and minimal frontend formal map review is now landed.
2. Candidate map is now exposed as a frontend read-only review surface, while editing remains limited to saved formal map.
3. Any later broader governance UX remains optional and should stay separate from the conservative P3.7 MVP closeout.

### P3.7b+ [P] Safe-Build Formal Map Consumption Boundary

Depends on: P3.7b backend store/API validation

Status as of 2026-05-08: completed.

Purpose:

1. Decide and implement how `working/formal_map.json` is consumed during the next safe release build.
2. Keep formal-map save separate from release build; saving a formal map must still not mutate releases, set current release, or touch SVN.
3. Make release build the only point where a saved formal map may be snapshotted into `releases/<release_id>/map.json`.

Tasks:

1. Add a boundary review or implementation note for formal-map build consumption.
2. Decide whether `build-from-current-indexes` should prefer `working/formal_map.json` when present.
3. If preferred, validate the saved formal map again at build time before snapshotting.
4. Ensure the manifest `map_hash` matches the final release `map.json`.
5. Add tests for these cases:
   - no saved formal map: build keeps deterministic generated map behavior
   - valid saved formal map: build snapshots it into the new release
   - invalid saved formal map: build fails clearly and does not create a partial release
   - saved formal map release id mismatch: build either rewrites through a deliberate rule or rejects clearly
6. Do not add frontend UI in this slice.

Acceptance:

1. The build-consumption rule is explicit and tested.
2. Saving formal map remains a non-release mutation.
3. Release build remains the only release-history mutation point.
4. Current-release pointer is not changed unless the existing build endpoint explicitly does that by contract.
5. No SVN read/write is introduced by formal-map consumption.

Implemented scope note:

1. The P3.7b+ implementation files are `src/ltclaw_gy_x/game/knowledge_release_service.py` and `tests/unit/game/test_knowledge_release_service.py`.
2. When `working/formal_map.json` exists and is valid, safe build prefers it over the current release map.
3. When `working/formal_map.json` exists and is valid, safe build can proceed without depending on a current release map.
4. The saved formal map is reloaded and revalidated at build time before snapshotting.
5. The build-time in-memory map copy rewrites `map.release_id` to the new `release_id`.
6. The final `release/map.json` is a build-time snapshot, and `manifest.map_hash` corresponds to that final `release/map.json`.
7. When `working/formal_map.json` does not exist, safe build falls back to the current release map and preserves the prior behavior.
8. When `working/formal_map.json` does not exist and there is also no current release, safe build fails clearly.
9. When `working/formal_map.json` exists but is invalid, safe build fails clearly, does not create a partial release, and does not set current release.
10. Saving formal map itself still does not build, does not set current release, and does not read or write SVN.
11. Candidate inclusion remains a build-time `candidate_evidence` write only and does not mutate the formal map snapshot.
12. P3.7c-1 minimal frontend formal map review is complete, P3.7c-2 status-only edit is complete, and P3.7c-3 relationship editor is explicitly deferred.

### P3.permission-0 [S] Knowledge Capability / Permission Boundary Review

Depends on: P1 boundary audit, P3.7b+, knowledge admin vs fast-test boundary review

Status as of 2026-05-08: completed.

Purpose:

1. Define the backend capability boundary between workbench fast-test permissions and knowledge-governance permissions.
2. Ensure build, publish, formal-map edit, and legacy full-payload build are not treated as frontend-only protected actions.
3. Keep fast-test policy unchanged: ordinary workbench testing still does not require administrator acceptance.

Acceptance:

1. The capability split is explicit.
2. Route-to-capability mapping is explicit for release read, build, publish, map read, map edit, candidate read or write, and workbench test-plan routes.
3. The next implementation slice is backend capability enforcement, not formal map UI.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-permission-boundary-review-2026-05-08.md`.
2. It defines the capability set `knowledge.read`, `knowledge.build`, `knowledge.publish`, `knowledge.map.read`, `knowledge.map.edit`, `knowledge.candidate.read`, `knowledge.candidate.write`, `workbench.read`, `workbench.test.write`, and `workbench.test.export`.
3. It states that frontend button visibility is not a permission boundary.
4. It keeps fast-test workbench permissions separate from formal knowledge governance permissions.

### P3.permission-1 [S] Backend Capability Helper And Route Checks

Depends on: P3.permission-0

Status as of 2026-05-08: completed.

Tasks:

1. Add a small backend capability helper or middleware.
2. Add route checks for `knowledge.build`, `knowledge.publish`, and `knowledge.map.edit` first.
3. Gate legacy full-payload build behind internal or test-only capability, or disable it outside dev or test.
4. Add focused `403` tests for missing capability.
5. Keep local or single-user development mode permissive only through an explicit documented default.

Acceptance:

1. Build no longer relies on frontend-only visibility.
2. Publish or set-current no longer relies on frontend-only visibility.
3. Formal-map writes no longer rely on frontend-only visibility.
4. Legacy full-payload build is either explicitly gated or disabled outside dev or test.

Implemented scope note:

1. The capability helper is implemented in `src/ltclaw_gy_x/app/capabilities.py`.
2. The helper resolves explicit capability context in this priority order: `request.state.capabilities`, then `request.state.user.capabilities`, then `app.state.capabilities`.
3. The helper accepts capability collections from list, set, mapping, string, and user-dict forms.
4. Mapping form is normalized by truthy values only, for example `{"knowledge.build": true, "knowledge.publish": false}` grants only `knowledge.build`.
5. The `*` wildcard is treated as allow-all within an explicit capability context.
6. When no capability context exists at any of those levels, the helper intentionally allows the request as the documented local trusted fallback for single-user or local-dev mode.
7. The following route checks are now enforced without changing their semantics: `POST /game/knowledge/releases/build` -> `knowledge.build`, `POST /game/knowledge/releases/build-from-current-indexes` -> `knowledge.build`, `POST /game/knowledge/releases/{release_id}/current` -> `knowledge.publish`, and `PUT /game/knowledge/map` -> `knowledge.map.edit`.
8. Read-only routes are not forced through capability checks in this slice.
9. Workbench fast-test permissions remain separate from knowledge-governance permissions; ordinary fast testing still does not require administrator acceptance.

### P3.permission-2 [S] Candidate And Test-Plan Route Capability Checks

Depends on: P3.permission-1

Status as of 2026-05-08: completed.

Purpose:

1. Add the minimum backend capability checks for test-plan and release-candidate routes.
2. Preserve the boundary between workbench fast-test artifacts and knowledge-governance state.
3. Keep local trusted fallback unchanged when no explicit capability context exists.

Acceptance:

1. Test-plan read and write routes no longer rely on frontend-only visibility.
2. Release-candidate read and write routes no longer rely on frontend-only visibility.
3. Test-plan fast testing still does not require `knowledge.build` or `knowledge.publish`.
4. Release-candidate write remains separate from build and publish, and does not auto-enter a release.

Implemented scope note:

1. The route checks are implemented in `src/ltclaw_gy_x/app/routers/game_knowledge_test_plans.py` and `src/ltclaw_gy_x/app/routers/game_knowledge_release_candidates.py`.
2. The following test-plan route checks are now enforced: `GET /game/knowledge/test-plans` -> `workbench.read`, `POST /game/knowledge/test-plans` -> `workbench.test.write`.
3. The following release-candidate route checks are now enforced: `GET /game/knowledge/release-candidates` -> `knowledge.candidate.read`, `POST /game/knowledge/release-candidates` -> `knowledge.candidate.write`.
4. Local trusted fallback is unchanged: when no capability context exists, the helper still allows the request.
5. Test-plan fast-test flow still does not require `knowledge.build` or `knowledge.publish`.
6. Release-candidate write still does not imply build or publish, and does not automatically enter a release.
7. This slice did not change store or service semantics, did not auto-build, and did not set current release.
8. This slice did not change the P2 candidate or test-plan storage model.

### P3.permission-ui-0 [S] Frontend Permission-Aware UI Boundary Review

Depends on: P3.permission-1, P3.permission-2

Status as of 2026-05-08: completed.

Purpose:

1. Define how the frontend should present governance controls once backend capability checks already exist.
2. Reduce user confusion without treating frontend visibility as the real permission boundary.
3. Keep workbench fast-test UI separate from release governance UI.

Acceptance:

1. The frontend rule is explicit that backend `403` remains the final boundary.
2. UI behavior is defined for build, publish, map read or edit, test-plan read or write, and candidate read or write.
3. The next recommended slice is permission-aware frontend plumbing or copy review, not direct formal map review UX.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-frontend-permission-ui-boundary-review-2026-05-08.md`.
2. It records the current backend capability state after `P3.permission-1` and `P3.permission-2`.
3. It keeps the rule that frontend is not the permission boundary and backend `403` remains authoritative.
4. It chooses disabled-with-explanation as the default behavior for governance controls when the surrounding panel is visible but required capability is missing.
5. It states that workbench fast-test UI should not be hidden just because `knowledge.build` or `knowledge.publish` is absent.
6. It keeps release-candidate eligibility UI separate from formal release build and publish UI.
7. It records that permission-aware frontend plumbing or docs-only copy review should come before formal map review UX.

### P3.permission-ui-1 [S] Frontend Capability State Plumbing And API Type Definition

Depends on: P3.permission-ui-0

Status as of 2026-05-08: completed.

Purpose:

1. Wire the minimum frontend capability state needed for release-governance controls.
2. Keep local trusted fallback unchanged when no explicit capability context exists.
3. Reduce duplicate permission noise in the existing release build modal without widening product scope.

Acceptance:

1. When `capabilities` is `undefined` or `null`, build and set-current remain usable by local trusted fallback.
2. When `capabilities=[]`, build and set-current are disabled by frontend state.
3. `knowledge.build` enables build, `knowledge.publish` enables set-current, and `knowledge.candidate.read` controls release-candidate list loading in the build modal.
4. Backend `403` remains the final permission boundary.
5. This slice does not add formal map review UX.

Implemented scope note:

1. Frontend capability types and helpers were added in `console/src/api/types/permissions.ts` and `console/src/utils/permissions.ts`.
2. `AgentSummary` and `AgentProfileConfig` now accept optional `capabilities` fields so existing agent data can carry explicit frontend capability context without a new API.
3. `console/src/pages/Game/GameProject.tsx` now uses permission-aware disabled behavior for release build, set-current, and candidate-read handling in the release panel and build modal.
4. Local trusted fallback is preserved: missing capability context still behaves permissively.
5. The build modal no longer requests the release-candidate list when `knowledge.candidate.read` is missing, and it shows only info or empty-state guidance instead of a duplicate warning path.
6. Frontend permission errors continue to collapse to `You do not have permission to perform this action.` for governance actions.
7. Backend route checks remain authoritative even when frontend capability state is present.
8. This slice does not add formal map review UX, RAG UI, real LLM wiring, SVN behavior changes, or workbench fast-test permission changes.

### P3.permission-ui-copy-review [S] Frontend Permission Copy Review

Depends on: P3.permission-ui-0, P3.permission-ui-1

Status as of 2026-05-08: completed.

Purpose:

1. Unify frontend permission-aware UI copy so permission errors are not misreported as SVN, local-directory, administrator-approval, or feature-missing problems.
2. Freeze a small set of reusable permission strings before broader frontend permission coverage expands.
3. Keep fast-test copy separate from formal release-governance copy.

Acceptance:

1. Recommended fixed English permission strings are documented.
2. The review explicitly says permission copy must not imply SVN or local project directory misconfiguration when the real error is missing capability.
3. The review explicitly says ordinary fast-test work does not require administrator acceptance.
4. The next frontend implementation slice must reuse these copy rules.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-frontend-permission-copy-review-2026-05-08.md`.
2. It documents the current backend capability coverage and the current `P3.permission-ui-1` GameProject release-panel behavior.
3. It fixes the recommended default permission strings for build, publish, candidate read, map edit, workbench write, and workbench read cases.
4. It records Chinese and product-semantics guidance so permission copy is not mistranslated into administrator-approval language.
5. It records UI usage rules for tooltip or inline disabled reasons, generic `403` message usage, and no-request behavior for candidate-list read denial.
6. It requires later permission-aware frontend slices to reuse these rules instead of inventing divergent strings.
7. This slice is docs-only and adds no UI implementation, no backend changes, no API changes, no SVN behavior changes, and no formal map review UX.

### P3.permission-ui-2 [S] Broader Frontend Permission Coverage On Existing Entry Points

Depends on: P3.permission-ui-1, P3.permission-ui-copy-review

Status as of 2026-05-08: completed as a narrow existing-entry-point slice.

Purpose:

1. Reuse the existing frontend capability helper on already-existing non-SVN entry points outside GameProject.
2. Extend fixed permission copy only where a concrete current entry point already exists.
3. Explicitly avoid inventing new test-plan or formal-map UI.

Acceptance:

1. Existing workbench entry points reuse the same capability semantics and fixed permission copy from the earlier review.
2. Missing `workbench.read` disables current workbench read surfaces without removing backend authority.
3. Missing `workbench.test.write` disables current workbench export or draft-write actions with the fixed permission string.
4. Backend `403` remains the final permission boundary.
5. If no current formal-map or knowledge test-plan entry point exists, the slice records that absence rather than creating one.

Implemented scope note:

1. `console/src/pages/Game/NumericWorkbench.tsx` now consumes existing agent capability context and applies permission-aware disabled behavior for workbench read and draft export actions.
2. Existing workbench read paths now stop requesting table, row, and AI panel data when explicit capability context is present and `workbench.read` is missing.
3. Existing workbench chat send and draft export flows now collapse frontend permission failures to `You do not have permission to perform this action.`.
4. `console/src/pages/Game/components/DirtyList.tsx` now reuses the fixed tooltip-style disabled reason for export when `workbench.test.write` is missing.
5. This slice intentionally does not modify `SvnSync`, proposal action semantics, backend APIs, or SVN logic.
6. No current dedicated frontend caller for `/game/knowledge/test-plans` was found, so no separate test-plan page wiring was added in this slice.
7. No current frontend formal-map review or candidate-map review entry point was found, so formal-map permission UI remains unimplemented.
8. This slice adds no backend `src` changes, no new API, no formal map review UX, no RAG UI, and no real LLM wiring.

### P3.read-permission-boundary-review [S] Broader Read Capability Checks Boundary Review

Depends on: P3.permission-2, P3.permission-ui-2

Status as of 2026-05-08: completed as a docs-only boundary review.

Purpose:

1. Decide whether broader read-only knowledge routes should receive backend capability checks.
2. Keep local trusted fallback semantics explicit rather than accidental.
3. Prevent broader read hardening from collapsing workbench, candidate, map, and release-reader roles into one over-broad permission.

Acceptance:

1. The route-to-capability recommendation is explicit for release read, query or RAG read, and map read routes.
2. The review states whether broader backend read checks are recommended or deferred.
3. The review keeps fast-test principles unchanged and does not widen RAG read boundaries.
4. The review states whether the next recommended slice is backend read checks or later formal-map UI boundary work.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-read-permission-boundary-review-2026-05-08.md`.
2. It recommends `knowledge.read` for release read and query or RAG read routes, and `knowledge.map.read` for candidate-map and saved-formal-map reads.
3. It keeps `GET /game/knowledge/test-plans` under `workbench.read` and `GET /game/knowledge/release-candidates` under `knowledge.candidate.read`.
4. It recommends preserving local trusted fallback only when explicit capability context is absent.
5. It recommends `P3.permission-3` backend read capability checks as the next implementation slice.
6. This slice is docs-only and adds no backend changes, no frontend changes, no new API, no RAG expansion, and no SVN behavior change.

### P3.permission-3 [S] Backend Read Capability Checks

Depends on: P3.permission-1, P3.permission-2

Status as of 2026-05-08: completed.

Purpose:

1. Harden broader read-only knowledge routes when explicit capability context exists.
2. Preserve the narrower split between release read, map read, candidate read, and workbench read.
3. Keep local trusted fallback unchanged when explicit capability context is absent.
4. Preserve the existing query or RAG release-owned read boundary without widening artifact access.

Acceptance:

1. `GET /game/knowledge/releases`, `GET /game/knowledge/releases/current`, and `GET /game/knowledge/releases/{release_id}/manifest` require `knowledge.read` when explicit capability context exists.
2. `POST /game/knowledge/query`, `POST /game/knowledge/rag/context`, and `POST /game/knowledge/rag/answer` require `knowledge.read` when explicit capability context exists.
3. `GET /game/knowledge/map/candidate` and `GET /game/knowledge/map` require `knowledge.map.read` when explicit capability context exists.
4. Existing write gates from `P3.permission-1` remain intact for build, publish, and formal-map edit routes.
5. Existing candidate and test-plan route checks from `P3.permission-2` remain intact.
6. Query or RAG read still does not widen to raw source, pending state, or `candidate_evidence.jsonl`.
7. Local trusted fallback remains unchanged when no explicit capability context is present.

Implemented scope note:

1. Backend read checks are now landed for `GET /game/knowledge/releases` -> `knowledge.read`.
2. Backend read checks are now landed for `GET /game/knowledge/releases/current` -> `knowledge.read`.
3. Backend read checks are now landed for `GET /game/knowledge/releases/{release_id}/manifest` -> `knowledge.read`.
4. Backend read checks are now landed for `POST /game/knowledge/query` -> `knowledge.read`.
5. Backend read checks are now landed for `POST /game/knowledge/rag/context` -> `knowledge.read`.
6. Backend read checks are now landed for `POST /game/knowledge/rag/answer` -> `knowledge.read`.
7. Backend read checks are now landed for `GET /game/knowledge/map/candidate` -> `knowledge.map.read`.
8. Backend read checks are now landed for `GET /game/knowledge/map` -> `knowledge.map.read`.
9. `P3.permission-1` write gates remain in place: release build -> `knowledge.build`, build-from-current-indexes -> `knowledge.build`, set current -> `knowledge.publish`, and `PUT /game/knowledge/map` -> `knowledge.map.edit`.
10. `P3.permission-2` candidate and test-plan checks remain in place and unchanged.
11. Local trusted fallback remains in place only when explicit capability context is absent.
12. Query and RAG read remain bounded to release-owned artifacts and still do not read raw source, pending state, or `candidate_evidence.jsonl`.
13. This slice is backend-only and does not add UI, new API, RAG expansion, LLM integration, or SVN behavior change.

### P3.7c-alpha [S] Formal Map Review UX Boundary Review

Depends on: P3.7b API shape, P3.7b+ safe-build consumption rule, P3.permission-1, P3.permission-3, P3.permission-ui-1, P3.permission-ui-copy-review

Status as of 2026-05-08: completed as a docs-only boundary review.

Purpose:

1. Define the minimum frontend formal map review UX boundary now that backend map read, save, and build-consumption rules already exist.
2. Avoid jumping directly to a graph editor, governance console, or field-level map editor.
3. Choose the first frontend implementation slice without changing backend APIs or fast-test semantics.

Acceptance:

1. The review records the current backend capability: candidate-map read, saved-formal-map read, formal-map save, and safe-build formal-map snapshot behavior.
2. The review records the required capability split for map read, map edit, build, and publish.
3. The review defines the minimum first UX slice and explicitly lists the major non-goals.
4. The review chooses the first implementation slice between review-only save, status editing, and relationship editing.
5. The review keeps ordinary workbench fast-test semantics unchanged.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-7c-formal-map-review-ux-boundary-2026-05-08.md`.
2. It confirms the current backend is already sufficient for a minimal frontend formal map review section or modal using the existing `GET /game/knowledge/map/candidate`, `GET /game/knowledge/map`, and `PUT /game/knowledge/map` APIs.
3. It recommends placing the first UX inside the existing GameProject release or knowledge surface rather than creating a new page.
4. It recommends `P3.7c-1` as the first implementation slice: read-only review plus `Save as formal map`, with no field-level editing.
5. It explicitly defers graph canvas, drag-and-drop relationship editing, LLM map generation, candidate-to-map auto merge, and automatic build or publish coupling.
6. It keeps disabled-with-explanation frontend behavior and backend `403` as the final permission boundary.
7. This slice is docs-only and adds no frontend implementation, no backend change, no new API, no RAG expansion, and no SVN behavior change.

### P3.7c [P] Map Review UX

Depends on: P3.7b API shape, P3.7b+ safe-build consumption rule, P3.permission-1 backend capability checks

Status as of 2026-05-08: planned; first implementation slice is `P3.7c-1` minimal frontend formal map review.

### P3.7c-1 [S] Minimal Frontend Formal Map Review

Depends on: P3.7c-alpha, P3.permission-3, P3.permission-ui-1, P3.permission-ui-copy-review

Status as of 2026-05-08: completed.

Purpose:

1. Add the narrowest possible formal map review surface to the existing GameProject governance area.
2. Reuse only the already-landed map APIs and capability plumbing.
3. Keep save decoupled from build and publish.

Acceptance:

1. The UI lives inside the existing GameProject `Knowledge Release Status` or governance surface.
2. The UI loads candidate map and saved formal map through existing frontend API wrappers only.
3. `no_formal_map` and `no current release` are shown as distinct states, not permission failures.
4. `Save as formal map` saves candidate map only and does not build or set current.
5. `knowledge.map.read` controls read behavior and `knowledge.map.edit` controls save behavior.
6. Backend `403` still uses `You do not have permission to perform this action.`.

Implemented scope note:

1. The changed frontend files are `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/GameProject.module.less`, `console/src/api/modules/gameKnowledgeRelease.ts`, and `console/src/api/types/game.ts`.
2. The reused or added frontend API wrappers are `getMapCandidate`, `getFormalMap`, and `saveFormalMap`.
3. The UI is placed inside the existing GameProject `Knowledge Release Status` or governance surface.
4. The first slice loads candidate map.
5. The first slice loads saved formal map.
6. The first slice shows `no_formal_map` as `no saved formal map`.
7. The first slice shows `No current knowledge release is set` as a separate candidate-map state.
8. `Save as formal map` saves candidate map only.
9. Save success does not build a release and does not set current release.
10. `knowledge.map.read` controls map reads.
11. `knowledge.map.edit` controls save.
12. Backend `403` continues to use `You do not have permission to perform this action.`.
13. This slice does not add graph canvas, relationship editor, field-level edit, LLM map generation, candidate-to-map auto merge, build or publish coupling, SVN behavior, or frontend RAG UI.

### P3.7c-2-alpha [S] Formal Map Status Edit Boundary Review

Depends on: P3.7c-1, P3.permission-3, P3.permission-ui-copy-review

Status as of 2026-05-08: completed as a docs-only boundary review.

Purpose:

1. Define the minimum boundary for status-only formal map editing after the `P3.7c-1` review-plus-save slice.
2. Keep the next map-edit slice smaller than relationship editing or graph editing.
3. Reuse the current complete-map save boundary without introducing PATCH semantics.

Acceptance:

1. The review defines which object types are editable in the first status-edit slice.
2. The review defines which fields remain non-editable.
3. The review explicitly states how relationships are handled when status changes.
4. The review preserves existing save, permission, and local trusted fallback semantics.
5. The review makes `P3.7c-2` the next recommended implementation slice instead of relationship editing.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-7c-2-formal-map-status-edit-boundary-2026-05-08.md`.
2. It recommends allowing status edit only for `systems`, `tables`, `docs`, and `scripts`.
3. It limits allowed statuses to `active`, `deprecated`, and `ignored`.
4. It explicitly defers editing of ids, titles, `source_path`, `source_hash`, `relationships`, `deprecated`, `release_id`, and `schema_version`.
5. It keeps relationship cleanup out of `P3.7c-2` and defers that work to `P3.7c-3`.
6. It keeps save on the existing `PUT /game/knowledge/map` path through the current full-map save boundary.
7. This slice is docs-only and adds no frontend implementation, no backend change, no new API, no relationship editor, no graph canvas, and no SVN behavior.

### P3.7c-2 [S] Minimal Frontend Formal Map Status Edit

Depends on: P3.7c-2-alpha, P3.permission-3, P3.permission-ui-copy-review

Status as of 2026-05-08: completed.

Purpose:

1. Add the minimum status-only edit surface on top of the landed formal map review UI.
2. Keep candidate map read-only and restrict editing to saved formal map only.
3. Reuse the existing full-map save boundary without adding PATCH or field-level editing.

Acceptance:

1. Candidate map remains read-only.
2. Saved formal map is the only editable object in this slice.
3. Editable fields are limited to `systems`, `tables`, `docs`, and `scripts` status values.
4. Allowed status values are limited to `active`, `deprecated`, and `ignored`.
5. Save continues to use the existing `saveFormalMap` wrapper over `PUT /game/knowledge/map`.
6. Save does not build, does not set current release, and does not modify release history.
7. Relationship handling stays warning-only in this slice and does not auto-clean or auto-rewrite relationships.
8. This slice adds no new backend API and does not alter NumericWorkbench fast-test permission semantics.

Implemented scope note:

1. The implementation files are `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/GameProject.module.less`.
2. Candidate map remains read-only and continues to render as a review-only list.
3. Saved formal map is cloned into a local draft for status-only editing.
4. Dirty state is tracked on the local formal-map draft before save.
5. The editable controls exist only on `systems`, `tables`, `docs`, and `scripts` rows.
6. The status controls allow only `active`, `deprecated`, and `ignored`.
7. This slice does not expose editing for ids, titles, `source_path`, `source_hash`, `relationships`, `deprecated`, `release_id`, or `schema_version`.
8. Save continues to use the existing `saveFormalMap` wrapper over `PUT /game/knowledge/map`.
9. No PATCH API was added.
10. Save success refreshes saved formal map and uses the short message `Saved formal map. It will be used by the next safe build.`.
11. Save does not build a release, does not set current release, does not modify release history, and does not read or write SVN.
12. Relationship handling remains warning-only: deprecated or ignored items may still be referenced, but the frontend does not auto-clean or auto-rewrite relationships.
13. `knowledge.map.read` still governs review visibility and `knowledge.map.edit` still governs status edit or save, with backend `403` remaining the final boundary.
14. This slice does not add graph canvas, relationship editor, field-level edit, LLM, frontend RAG UI, build or publish auto-coupling, or SVN behavior changes.

### P3.7c-3-alpha [S] Relationship Edit Boundary Decision

Depends on: P3.7c-2, P3.permission-3, P3.permission-ui-copy-review

Status as of 2026-05-08: completed as a docs-only boundary decision.

Purpose:

1. Decide whether relationship editor should enter the current conservative P3.7 closeout.
2. Record the narrowest possible future relationship-edit boundary if product later needs it.
3. Keep the current P3.7 MVP from expanding into graph or LLM-driven governance UX.

Implemented scope note:

1. The decision is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-7c-3-relationship-edit-boundary-2026-05-08.md`.
2. It explicitly defers relationship editor from the current conservative closeout.
3. It records that any future first slice should be saved-formal-map-only and simple form-based add or remove over existing refs.
4. It explicitly rejects graph canvas, drag-and-drop relationship editor, LLM relationship generation, automatic relationship cleanup, and candidate-to-map auto merge in that first future slice.
5. It preserves the existing complete-map `PUT /game/knowledge/map` save boundary and adds no new backend API, no PATCH API, and no SVN behavior.

Tasks:

1. Start with `P3.7c-1` minimal formal map review section or modal inside the existing GameProject release or knowledge surface.
2. Load candidate map and saved formal map through the existing map APIs.
3. Show explicit `no saved formal map` state when backend returns `no_formal_map`.
4. Allow `Save as formal map` without coupling save to build or publish.
5. Defer status editing, relationship editing, and graph editing to later slices.

Acceptance:

1. The first slice does not require a graph editor or field-level editor.
2. Formal map changes are visible before release build.
3. The first slice uses no new backend API.
4. The first slice does not alter NumericWorkbench fast-test behavior.

Next-step note:

1. Do not continue expanding P3.7 UI beyond the landed conservative MVP.
2. `P3.permission-1` backend capability helper and initial route checks are now complete.
3. `P3.permission-2` candidate and test-plan route capability checks are now complete.
4. `P3.permission-3` backend read capability checks are now complete.
5. `P3.permission-ui-0` frontend permission-aware UI boundary review is now complete.
6. `P3.permission-ui-1` frontend capability state plumbing and API type definition is now complete.
7. `P3.permission-ui-copy-review` frontend permission copy review is now complete.
8. `P3.permission-ui-2` broader frontend permission coverage is now complete as a narrow NumericWorkbench existing-entry-point slice.
9. `P3.read-permission-boundary-review` broader read capability checks boundary review is now complete as a docs-only slice.
10. `P3.7c-alpha` formal map review UX boundary review is now complete as a docs-only slice.
11. `P3.7c-1` minimal frontend formal map review is now complete.
12. `P3.7c-2-alpha` formal map status edit boundary review is now complete as a docs-only slice.
13. `P3.7c-2` minimal frontend formal map status edit is now complete.
14. `P3.7c-3-alpha` relationship edit boundary decision is now complete as a docs-only slice and explicitly defers relationship editor.
15. P3.7 formal map MVP is now conservatively complete.
16. Prefer broader P3 consolidation or RAG or model-client boundary work before any later relationship editor or graph canvas work.
17. Start with a docs-only P3 gate consolidation pass before any deeper RAG or model-client implementation slice.
18. Graph editor, relationship editor, and other broader governance UI remain intentionally deferred.

### P3.gate [S] P3 Gate Consolidation

Depends on: P3.7c-3-alpha

Status as of 2026-05-08: completed as a docs-only consolidation record.

Tasks:

1. Summarize landed P3 capabilities in one docs-only consolidation record.
2. Mark P3.7 formal map MVP as conservatively complete.
3. State explicitly that the product is still not a full RAG product.
4. Recommend RAG or model-client boundary work before more P3.7 UI.

### P3.rag-model-boundary [S] RAG / Model-Client Boundary Review

Depends on: P3.gate, P3.4b

Status as of 2026-05-08: completed as a docs-only boundary review.

Tasks:

1. Define how the answer path may move from deterministic or no-LLM behavior to an injected model-client boundary.
2. Preserve the existing RAG read boundary and keep context assembly as the only artifact-reading path.
3. Keep citations bounded to `context.citations` and require validation on model output.
4. Recommend a backend-only next slice using a protocol or interface plus deterministic or mock adapter.

Acceptance:

1. Router code still must not call a model directly.
2. Answer service still must not bypass the context builder to read release artifacts.
3. The review keeps raw source, pending state, SVN, `candidate_evidence.jsonl`, embedding, vector store, and frontend RAG UI out of scope.
4. The next implementation slice is explicitly `P3.rag-model-1` backend model-client protocol plus deterministic or mock adapter.

### P3.rag-model-1 [S] Backend Model-Client Protocol + Deterministic Or Mock Adapter

Depends on: P3.rag-model-boundary

Status as of 2026-05-08: completed.

Tasks:

1. Add a backend model-client protocol or interface for grounded answer generation.
2. Keep the input boundary bounded to `query + context` only.
3. Add a deterministic or mock adapter that uses only the provided payload and does not call a real model.
4. Preserve the existing deterministic or no-LLM answer path when no model client is injected.
5. Validate returned `citation_ids` against `context.citations` before producing the final answer payload.

Implemented scope note:

1. The implementation files for this slice are `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` and `src/ltclaw_gy_x/game/knowledge_rag_answer.py`.
2. The focused test files for this slice are `tests/unit/game/test_knowledge_rag_model_client.py` and `tests/unit/game/test_knowledge_rag_answer.py`.
3. The model-client prompt payload is bounded to `query`, `release_id`, `built_at`, `chunks`, `citations`, and `policy_hints`.
4. The model-client response is bounded to `answer`, `citation_ids`, and optional `warnings`.
5. `DeterministicMockRagModelClient` uses only the provided payload and does not read files or call a real model.
6. `build_rag_answer` now accepts an optional `model_client` while preserving the prior deterministic or no-LLM behavior when none is provided.
7. When a `model_client` is provided, the answer service only converts `query + context` into the bounded payload and does not reread artifacts.
8. Router behavior remains unchanged and still does not call any model directly.
9. `citation_ids` must exist in `context.citations`; out-of-context ids are dropped and added to warnings.
10. If all returned citations are invalid or the answer is not grounded, the result degrades to `insufficient_context`.
11. `no_current_release` still returns directly without calling the model client.
12. Empty or insufficient grounded context still returns `insufficient_context` without trusting model output.

Acceptance:

1. No real LLM is connected in this slice.
2. No provider registry or provider selection is added in this slice.
3. No embedding, vector store, frontend RAG UI, or API expansion is added in this slice.
4. The context builder read boundary remains unchanged and still excludes raw source, pending state, `candidate_evidence.jsonl`, and SVN.
5. Tests cover valid citations, invalid citations, no-current-release, insufficient-context, and default deterministic fallback behavior.

Validation note:

1. Focused pytest result: `15 passed`.
2. NUL check result: the 4 touched Python files were rechecked as `NUL=0`.
3. `git diff --check` reported no patch-format errors and only existing CRLF or LF warnings outside this slice.
4. Local pytest may still emit environment-specific `.pytest_cache` permission warnings, but the focused tests passed.

Next-step note:

1. Do not connect a real external model yet.
2. The next recommended slice is `P3.rag-model-2` backend provider registry or provider selection boundary review as a docs-only step.

### P3.rag-model-2 [S] Backend Provider Registry / Provider Selection Boundary Review

Depends on: P3.rag-model-1

Status as of 2026-05-08: completed as a docs-only boundary review.

Tasks:

1. Define how provider registry and provider selection may choose among backend model-client implementations.
2. Keep provider selection downstream of the existing `query + context` boundary.
3. Require every provider to implement the existing model-client protocol and pass through the same citation validation path.
4. Define a safe default provider strategy and a separate initialization-failure fallback strategy.
5. Recommend the next backend-only slice as a registry skeleton without any real external model integration.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-provider-selection-boundary-review-2026-05-08.md`.
2. Provider registry may choose only model-client implementations and must not widen retrieval or context-builder read boundaries.
3. Provider selection must not let router code call any model directly.
4. Provider selection must not let the answer service reread artifacts directly.
5. Every provider must implement the `P3.rag-model-1` model-client protocol.
6. Every provider output must pass the same citation validation already enforced against `context.citations`.
7. Providers must not read raw source, pending state, SVN, or `candidate_evidence.jsonl`.
8. Providers must not add embedding, vector store, frontend RAG UI, or API expansion in this slice.
9. Recommended provider types are `deterministic_mock`, `disabled`, and `future_external`, with `future_external` kept as documentation-only placeholder.
10. Recommended selection order is explicit backend function argument or dependency injection, then app or service config, then environment variable only if a later review explicitly allows it.
11. Provider choice must never come directly from user query body and must never accept arbitrary frontend provider names without backend allowlist.
12. The recommended default provider is `deterministic_mock`, while initialization failure should fall back to `disabled` with a clear warning rather than silently attempting any external connection.

Acceptance:

1. The review does not implement a registry, provider selection runtime, or real external model.
2. The review keeps permission checks, retrieval bounds, citation validation, and trusted-local fallback rules unchanged.
3. The review records that any future request-level provider hint must still be validated by backend allowlist.
4. The next implementation slice is explicitly `P3.rag-model-2a` backend provider registry skeleton.

### P3.rag-model-2a [S] Backend Provider Registry Skeleton

Depends on: P3.rag-model-2

Status as of 2026-05-08: completed.

Tasks:

1. Add a backend registry skeleton for model-client provider lookup.
2. Keep runtime providers limited to `deterministic_mock` and `disabled`.
3. Keep `future_external` as documentation-only placeholder rather than runtime provider.
4. Keep provider lookup bounded to backend model-client selection only.
5. Avoid any real external model connection, router change, frontend change, or API expansion.

Implemented scope note:

1. The implementation files are `src/ltclaw_gy_x/game/knowledge_rag_model_client.py` and `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`.
2. `src/ltclaw_gy_x/game/knowledge_rag_answer.py` was compatibility-checked only and did not gain new router semantics.
3. The focused test files are `tests/unit/game/test_knowledge_rag_model_client.py`, `tests/unit/game/test_knowledge_rag_model_registry.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
4. The registry API is `get_rag_model_client(provider_name=None, *, factories=None)` and `ResolvedRagModelClient(provider_name, client, warnings)`.
5. Runtime providers are limited to `deterministic_mock` and `disabled`.
6. `future_external` remains documentation-only and is not included in `SUPPORTED_RAG_MODEL_PROVIDERS`.
7. The default provider is `deterministic_mock`.
8. `None`, empty string, and whitespace provider names normalize to `deterministic_mock`.
9. Unknown provider names fail clearly with `ValueError` and do not fall back.
10. Provider factory initialization failure falls back to `disabled` and returns a clear warning.
11. `DisabledRagModelClient` returns empty `answer`, empty `citation_ids`, and `Model provider is disabled.` warning.
12. The registry does not read files, does not read environment variables, and does not connect any real external model.
13. Retrieval, context assembly, and citation validation boundaries remain unchanged.
14. Router was not modified.
15. Frontend was not modified.
16. No new API was added.
17. This slice experienced DLP/NUL corruption during editing and then received a clean repair before final validation.

Validation note:

1. NUL check result after clean repair: `knowledge_rag_model_client.py NUL=0`.
2. NUL check result after clean repair: `knowledge_rag_answer.py NUL=0`.
3. NUL check result after clean repair: `knowledge_rag_model_registry.py NUL=0`.
4. NUL check result after clean repair: `test_knowledge_rag_model_client.py NUL=0`.
5. NUL check result after clean repair: `test_knowledge_rag_model_registry.py NUL=0`.
6. NUL check result after clean repair: `test_knowledge_rag_answer.py NUL=0`.
7. Focused pytest result: `27 passed`.
8. Local pytest may emit `.pytest_cache` permission warnings, but they do not affect the passing result.
9. `git diff --check` reported no patch-format or whitespace errors and only existing CRLF/LF warnings.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2b` service-layer provider selection boundary review or implementation planning.

### P3.rag-model-2b [S] Service-Layer Provider Selection Skeleton

Depends on: P3.rag-model-2a

Status as of 2026-05-08: completed.

Tasks:

1. Wire service-layer provider selection through the existing registry entry point only.
2. Keep provider choice in backend service/config/DI boundaries only.
3. Keep router thin and prevent request-body or arbitrary frontend provider selection.
4. Preserve answer-service early-return and citation-validation boundaries.
5. Keep real external model integration out of scope.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-service-selection-boundary-review-2026-05-08.md`.
2. This slice is closed out in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2b-closeout-2026-05-08.md`.
3. The implementation files are `src/ltclaw_gy_x/game/knowledge_rag_answer.py` and `tests/unit/game/test_knowledge_rag_answer.py`.
4. Provider selection remains limited to backend service layer, app/service config, or dependency injection boundaries.
5. The service layer may call only `get_rag_model_client(...)`.
6. Router code still must not call models directly and still must not choose arbitrary providers.
7. Query body is not allowed to carry provider name in this slice.
8. Frontend is not allowed to choose arbitrary provider name in this slice.
9. Any future request-level provider hint requires a later dedicated boundary review plus backend allowlist validation.
10. The default provider remains `deterministic_mock`.
11. `disabled` remains explicit provider state rather than silent failure, and provider initialization failure may fall back only to `disabled` with clear warning.
12. Registry warnings are now merged into answer warnings in the service layer.
13. `no_current_release` and `insufficient_context` still must not call model client.
14. Citation validation remains centralized in the existing `P3.rag-model-1` answer path and still accepts only `context.citations` as citation authority.
15. The answer service still consumes only the P3.2 context payload and does not read artifacts, raw source, pending state, or SVN.
16. This slice adds no new API, no request-body provider control, no frontend change, no real LLM, no embedding/vector store, and no `candidate_evidence` expansion.

Validation note from implementation round:

1. Mainline reference: `5355e39 Implement knowledge permission gates and RAG provider skeleton`.
2. Python NUL scan result: `ALL_PY_NUL=0`.
3. RAG model focused tests: `32 passed`.
4. TypeScript validation: passed.
5. `git diff --check`: clean.
6. Local router pytest on one Windows machine hit `tmp_path` permission issues; this was an environment problem rather than an assertion failure and is not treated as a code failure for this slice.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2c` app/service config injection boundary review.

### P3.rag-model-2c [S] App/Service Config Injection Boundary Review

Depends on: P3.rag-model-2b

Status as of 2026-05-08: completed as a docs-only boundary review.

Tasks:

1. Define where RAG provider configuration may enter the backend service layer after the 2b skeleton is landed.
2. Decide whether app config, service config, project config, or dependency injection should own provider selection input.
3. Keep router thin and forbid request-body or frontend provider selection.
4. Keep environment-variable-driven provider selection out of scope in this slice.
5. Preserve allowlist, clear-fail, fallback-disabled, warning-merge, early-return, retrieval, context, and citation-validation boundaries.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2c-config-injection-boundary-review-2026-05-08.md`.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The reviewed code baseline is `src/ltclaw_gy_x/game/knowledge_rag_model_client.py`, `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`, `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`, `src/ltclaw_gy_x/game/config.py`, `src/ltclaw_gy_x/game/service.py`, and `src/ltclaw_gy_x/providers/provider_manager.py`.
4. The review keeps provider choice as a backend-only service/config/dependency-injection concern.
5. The recommended config entry points are explicit backend dependency injection first, then server-side app or service config.
6. `ProjectConfig.models` and `UserGameConfig` are not selected as direct `P3.rag-model-2c` provider-control surfaces.
7. Router must not choose provider, and request body must not carry provider name.
8. Frontend must not choose arbitrary provider name.
9. Environment-variable-driven selection is explicitly out of scope in this slice.
10. `ProviderManager.active_model` is not adopted as the `P3.rag-model-2c` source of truth in this slice; any bridge to broader provider runtime requires a later dedicated review.
11. Provider allowlist remains the existing registry allowlist, so config-injected names must still resolve only through `get_rag_model_client(...)` and the current supported runtime providers.
12. Unknown provider names must still clear-fail and must not silently degrade to `disabled`.
13. Provider initialization failure may still fall back only to `disabled` with clear warning.
14. Registry warnings must continue to merge into answer warnings rather than being dropped.
15. `no_current_release` and `insufficient_context` must still return before provider selection or provider call.
16. Retrieval, context assembly, and citation validation remain unchanged and still do not widen to raw source, pending state, `candidate_evidence.jsonl`, or SVN.

Acceptance:

1. The review does not implement config injection, runtime provider expansion, or real external model wiring.
2. The review does not allow request-body, frontend, router, or environment-variable provider control.
3. The review keeps unknown provider handling as clear-fail and provider initialization failure as fallback-to-disabled only.
4. The review records `P3.rag-model-2d` as the next possible implementation slice, still limited to `deterministic_mock` and `disabled`.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to `git diff --check`.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2d` app/service config injection implementation, still limited to `deterministic_mock` and `disabled`.

### P3.rag-model-2d [S] Minimal App/Service Config Injection Implementation

Depends on: P3.rag-model-2c

Status as of 2026-05-08: completed.

Tasks:

1. Add a very small service-layer resolver helper for provider-name selection.
2. Keep provider-name resolution limited to backend DI or passed service or config objects.
3. Keep runtime providers limited to `deterministic_mock` and `disabled` only.
4. Preserve router, request-body, frontend, retrieval, context, and citation-validation boundaries.
5. Keep real external models out of scope.

Implemented scope note:

1. The plan is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2d-implementation-plan-2026-05-08.md`.
2. This slice is closed out in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2d-closeout-2026-05-08.md`.
3. The implementation files are `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, `src/ltclaw_gy_x/game/knowledge_rag_answer.py`, `tests/unit/game/test_knowledge_rag_provider_selection.py`, and `tests/unit/game/test_knowledge_rag_answer.py`.
4. The new helper is limited to service-layer provider-name resolution.
5. The helper does not perform I/O, does not read environment variables, and does not access `ProviderManager`.
6. The helper accepts only explicit backend-passed object or mapping fields and currently supports direct or nested `config`-style resolution for `rag_model_provider` and `knowledge_rag_model_provider`.
7. `build_rag_answer_with_provider(...)` now resolves provider name only after the existing `no_current_release` and grounded-context early returns.
8. Provider selection still occurs only through `get_rag_model_client(...)`.
9. Router was not modified, request body was not modified, and frontend was not modified.
10. Runtime providers remain limited to `deterministic_mock` and `disabled`.
11. Unknown provider remains clear-fail.
12. Provider factory initialization failure still falls back only to `disabled`.
13. Citation validation still trusts only `context.citations`.
14. Retrieval and context boundaries remain unchanged and were not widened.

Acceptance:

1. This slice adds only a minimal service-layer resolver path and does not add new runtime providers, real external model wiring, API changes, request-schema changes, or frontend changes.
2. Runtime providers remain limited to `deterministic_mock` and `disabled`.
3. Request-level provider hint, frontend provider control, and `ProviderManager.active_model` are still not allowed in this slice.

Validation note from implementation round:

1. Focused pytest result: `38 passed`.
2. `git diff --check`: clean.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2e` boundary review or implementation planning for whether and how backend app/service config should be injected into the live RAG answer path, still without direct real external model integration.

### P3.rag-model-2e [S] Live Backend App/Service Config Injection Boundary Review

Depends on: P3.rag-model-2d

Status as of 2026-05-08: completed as a docs-only boundary review.

Tasks:

1. Define whether and how backend app or service config may enter the live RAG answer path after the 2d resolver helper landed.
2. Define the allowed handoff layer for server-owned config.
3. Keep router, request body, frontend, and global provider runtime state out of scope.
4. Preserve provider allowlist, clear-fail, fallback-disabled, early-return, retrieval, context, and citation-validation boundaries.
5. Keep real external model integration out of scope.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2e-live-config-injection-boundary-review-2026-05-08.md`.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The review records that live config injection should happen only through explicit server-side handoff of app or service config into the existing backend answer path.
4. The review keeps `build_rag_answer_with_provider(...)` as the service-layer provider-selection entry point and `get_rag_model_client(...)` as the only registry entry point.
5. The review does not allow request-body provider hint, frontend provider control, router provider selection, environment-variable-driven selection, `ProjectConfig.models`, `UserGameConfig`, or `ProviderManager.active_model` as the live source of truth.
6. The review keeps runtime providers limited to `deterministic_mock` and `disabled` only.
7. The review keeps unknown provider as clear-fail and provider factory initialization failure as fallback-to-disabled only.
8. The review keeps `no_current_release` and `insufficient_context` ahead of provider resolution and provider lookup.
9. The review keeps retrieval, context assembly, and citation validation boundaries unchanged.

Acceptance:

1. The review does not add code, runtime providers, real external model wiring, API changes, request-schema changes, or frontend changes.
2. The review records explicit backend config handoff as the only allowed live injection shape in this slice.
3. The review keeps request-level provider hint and frontend provider control disallowed.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to `git diff --check`.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2f` implementation planning for a minimal live backend app/service config handoff into the existing RAG answer path.

### P3.rag-model-2f [S] Minimal Live Config Handoff Implementation Plan

Depends on: P3.rag-model-2e

Status as of 2026-05-08: completed as a docs-only implementation plan.

Tasks:

1. Define the minimal code shape for handing backend-owned app or service config into the live RAG answer path.
2. Decide whether the next slice should add one small service-layer helper for live config handoff.
3. Define where that helper should live.
4. Define the smallest allowed router touch, if any, without allowing router provider selection.
5. Define focused tests and acceptance criteria for the next implementation slice.

Implemented scope note:

1. The plan is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2f-live-config-handoff-implementation-plan-2026-05-08.md`.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The plan recommends keeping `build_rag_answer_with_provider(...)` as the service-layer provider-selection entry point and `get_rag_model_client(...)` as the only registry entry point.
4. The plan recommends either a very small `build_rag_answer_with_service_config(...)` helper in `src/ltclaw_gy_x/game/knowledge_rag_answer.py` or a narrowly named resolver helper extension in `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`, with preference for the answer-layer wrapper because it keeps router logic thin.
5. The plan allows a minimal router change only if needed to hand off backend-owned service config into the existing answer path.
6. The plan does not allow router to call `get_rag_model_client(...)` directly, does not allow request-body provider hint, and does not allow frontend provider control.
7. The plan keeps runtime providers limited to `deterministic_mock` and `disabled` only.
8. The plan keeps unknown provider as clear-fail and provider factory initialization failure as fallback-to-disabled only.
9. The plan keeps `no_current_release`, `insufficient_context`, citation validation, retrieval, and context boundaries unchanged.

Acceptance:

1. The plan is implementation planning only and does not add code, new runtime providers, real external model wiring, API changes, request-schema changes, or frontend changes.
2. The plan can directly guide the next minimal backend code slice.
3. The plan keeps request-level provider hint, frontend provider control, and router provider selection out of scope.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to `git diff --check`.

Next-step note:

1. Do not connect any real external model in the next slice.
2. The next recommended slice is `P3.rag-model-2g` minimal live config handoff implementation.

### P3.rag-model-2g [S] Minimal Live Config Handoff Implementation

Depends on: P3.rag-model-2f

Status as of 2026-05-08: completed.

Tasks:

1. Add the smallest answer-layer wrapper needed to hand backend-owned app or service config into the live RAG answer path.
2. Keep router limited to backend-owned config handoff only.
3. Keep provider resolution and provider instantiation inside the existing service-layer and registry boundaries.
4. Preserve all request, frontend, retrieval, context, and citation-validation boundaries.
5. Keep real external models out of scope.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-model-2g-closeout-2026-05-08.md.
2. The implementation files are src/ltclaw_gy_x/game/knowledge_rag_answer.py, src/ltclaw_gy_x/app/routers/game_knowledge_rag.py, tests/unit/game/test_knowledge_rag_answer.py, and tests/unit/routers/test_game_knowledge_rag_router.py.
3. The implementation adds a very small answer-layer wrapper that hands backend-owned service config into the existing answer path.
4. Router now passes game_service as a backend-owned object into that wrapper.
5. Router does not choose provider and does not call get_rag_model_client(...) directly.
6. Request body still does not carry provider name, and frontend remains unchanged.
7. Provider resolution still goes through the existing resolver and get_rag_model_client(...).
8. Runtime providers remain limited to deterministic_mock and disabled.
9. Unknown provider remains clear-fail.
10. Provider factory initialization failure still falls back only to disabled with warning.
11. no_current_release and insufficient_context still return before provider selection.
12. Citation validation still trusts only context.citations.
13. Retrieval and context boundaries remain unchanged and were not widened.
14. No real external provider was added.

Acceptance:

1. This slice implements only minimal live config handoff and is not real LLM integration.
2. Request-level provider hint and frontend provider control remain disallowed.
3. Router is only a backend-owned config handoff surface and is not a provider selector.

Validation note from implementation round:

1. Focused pytest result: 59 passed.
2. git diff --check: clean.

Next-step note:

1. Preferred next slice: P3.rag-model-3 external provider adapter boundary review.
2. That next slice should review how a real external provider adapter would fit behind the existing registry and client protocol boundaries, without implementing a real provider yet.
3. If external-provider review is intentionally deferred, the next planning alternative is RAG UI planning or P3.8/P3.9 planning, with external-provider boundary review still the higher-priority backend dependency.

### P3.rag-model-3 [S] External Provider Adapter Boundary Review

Depends on: P3.rag-model-2g

Status as of 2026-05-08: completed as a docs-only boundary review.

Tasks:

1. Define where a real external provider adapter may sit in the existing RAG backend layering.
2. Define what adapter contract it must satisfy.
3. Preserve the current retrieval, context, grounding, citation-validation, and structured-query boundaries.
4. Keep credential, provider-runtime, and provider-rollout concerns in review scope only.
5. Keep real external provider implementation out of scope.

Implemented scope note:

1. The review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-rag-model-3-external-provider-adapter-boundary-review-2026-05-08.md.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The review records that any future external provider adapter must sit behind the existing registry and client protocol boundaries.
4. The review records that any future adapter must implement the existing RagModelClient protocol and accept only bounded prompt payload rather than reading artifacts directly.
5. The review does not allow release-artifact reads, raw-source reads, pending-state reads, SVN reads, request-body provider hint, frontend provider control, environment-variable-driven live source selection, or ProviderManager reuse by default in this slice.
6. The review does not authorize new runtime provider names in this slice.
7. The review keeps unknown provider clear-fail, initialization failure fallback-to-disabled or explicit clear-fail, structured-query boundary, workbench-flow boundary, citation-validation boundary, and no-candidate-evidence or vector-store widening unchanged.

Acceptance:

1. The review does not implement a real external provider.
2. The review does not add runtime providers, router changes, request-schema changes, frontend changes, or ProviderManager integration.
3. The review can directly guide a later external-provider adapter implementation plan.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to git diff --check.

Next-step note:

1. The next recommended slice is P3.rag-model-3a external provider adapter implementation plan.
2. P3.rag-model-3a should remain planning-only and must not directly implement a real external provider.
3. Real provider implementation must remain deferred until adapter plan, credential boundary, timeout or cost policy, and grounding or citation test plan are settled.

### P3.rag-model-3a [S] External Provider Adapter Implementation Plan

Depends on: P3.rag-model-3

Status as of 2026-05-08: completed as a docs-only implementation plan.

Tasks:

1. Define the minimal file-touch set for a future external provider adapter skeleton.
2. Define the adapter class shape and protocol conformance requirements.
3. Define the prompt-payload and response-shape constraints for the future skeleton.
4. Define how timeout, retry, cost, token-limit, and secret placeholders should be represented without implementing real I/O.
5. Define the focused test plan and acceptance criteria for a future adapter skeleton slice.

Implemented scope note:

1. The plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-rag-model-3a-external-provider-adapter-implementation-plan-2026-05-08.md.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The plan recommends a future adapter module such as src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py or a more conservative src/ltclaw_gy_x/game/knowledge_rag_provider_adapters.py.
4. The plan requires any future adapter class to implement RagModelClient and accept only RagAnswerPromptPayload while returning only RagModelClientResponse.
5. The plan keeps network I/O out of the future skeleton slice and limits that slice to contract shape, injected config placeholders, and tests.
6. The plan does not authorize runtime provider expansion, router changes, request-schema changes, frontend changes, environment-variable reads, or ProviderManager integration.

Acceptance:

1. The plan is implementation planning only and does not implement a real external provider.
2. The plan can directly guide a later skeleton-only adapter implementation slice.
3. The plan keeps retrieval, context, citation-validation, structured-query, and workbench-flow boundaries unchanged.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to git diff --check.

Next-step note:

1. The next recommended slice is P3.rag-model-3b external provider adapter skeleton implementation.
2. P3.rag-model-3b should still avoid real network calls and real provider integration.
3. Real provider implementation must remain deferred until the skeleton, credential boundary, timeout or cost policy, and grounding or citation tests are settled.

### P3.external-provider-1 / P3.rag-model-3b [S] Backend External Provider Adapter Skeleton

Depends on: P3.rag-model-3a

Status as of 2026-05-09: completed.

Tasks:

1. Add the smallest external provider adapter skeleton module behind the existing client boundary.
2. Keep the slice free of real network I/O and real provider integration.
3. Preserve router, request, frontend, registry allowlist, retrieval, context, and citation-validation boundaries.
4. Add focused adapter tests and answer-layer regression coverage.
5. Record closeout and verified outcomes.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-model-3b-external-provider-adapter-skeleton-closeout-2026-05-08.md.
2. This slice is also treated as P3.external-provider-1 completed.
3. The backend skeleton module is src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py.
4. The skeleton implements RagModelClient, accepts only bounded prompt payload shape, and returns only RagModelClientResponse shape.
5. The skeleton is not a real LLM integration and does not perform real HTTP.
6. The skeleton does not read real credential material and does not read environment variables.
7. The skeleton does not modify router provider selection, frontend UI, or the RAG request schema.
8. Runtime providers remain limited to deterministic_mock and disabled, and this slice does not roll out a new runtime provider.
9. Provider read authority remains bounded: the client does not read raw source, pending state, SVN, candidate_evidence, or release artifacts directly.
10. Citation validation remains in the answer layer and still trusts only context.citations.
11. Retrieval, context, no_current_release, and insufficient_context boundaries remain unchanged.
12. No real external provider was added.

Acceptance:

1. This slice implements only an adapter skeleton and is not real external provider integration.
2. The slice adds no frontend or request provider control.
3. The slice keeps router, registry allowlist, retrieval, context, and citation boundaries intact.

Recorded implementation validation results:

1. Focused pytest result: 57 passed in 0.55s.
2. Focused pytest coverage includes tests/unit/game/test_knowledge_rag_external_model_client.py, tests/unit/game/test_knowledge_rag_model_registry.py, tests/unit/game/test_knowledge_rag_model_client.py, and tests/unit/game/test_knowledge_rag_answer.py.
3. NUL check result: src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py = 0.
4. NUL check result: tests/unit/game/test_knowledge_rag_external_model_client.py = 0.
5. NUL check result: tests/unit/game/test_knowledge_rag_answer.py = 0.
6. NUL check result: tests/unit/game/test_knowledge_rag_model_client.py = 0.
7. git diff --check reported no whitespace error for this slice.
8. The only git diff --check output was pre-existing unrelated line-ending warnings for docs/tasks/knowledge/mvp/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md, scripts/README.md, scripts/migrate_to_cdev.ps1, and scripts/wheel_build.ps1.

Next-step note:

1. The backend external provider adapter skeleton is now complete.
2. The next recommended slice is P3.external-provider-2 credential/config skeleton boundary review or implementation planning.
3. The next slice should still remain backend-only and should not connect a real provider.
4. Real external provider integration still remains unimplemented.

### P3.external-provider-2 [S] Credential/Config Skeleton Implementation

Depends on: P3.external-provider-1, P3.provider-credential-boundary-review

Status as of 2026-05-09: completed.

Tasks:

1. Land the backend-owned credential/config skeleton on the external adapter boundary only.
2. Keep the slice disabled-by-default and keep external provider behavior outside runtime rollout.
3. Add allowlist gating ahead of credential resolver and transport.
4. Keep GameProject, request schema, endpoint surface, router behavior, and runtime provider allowlist unchanged.
5. Record implementation outcomes and bounded validation without authorizing real-provider rollout.

Implemented scope note:

1. This implementation is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-2-credential-config-boundary-2026-05-09.md.
2. The backend-owned config shape now includes `enabled`, `provider_name`, optional `model_name`, `timeout_seconds`, optional `base_url`, optional `proxy`, optional `max_output_tokens`, `allowed_providers`, `allowed_models`, and an optional env config entry shape.
3. `enabled` defaults to false, so the credential/config skeleton remains disabled-by-default.
4. This slice is still a credential/config skeleton only and is not real external provider integration.
5. The slice does not connect a real LLM, does not perform real HTTP, and does not read real credential material.
6. Frontend still exposes no provider/model UI, and the RAG request schema remains unchanged.
7. Request-like `provider_name`, `model_name`, or `api_key` fields do not participate in provider selection.
8. Provider/model allowlist validation now occurs before credential resolver and transport, and allowlist failure safely degrades without entering the external call path.
9. Missing credential, disabled state, and allowlist failure all degrade safely and do not generate a fake answer.
10. `no_current_release` and `insufficient_context` still return before provider/config/credential path execution.
11. Runtime providers remain only deterministic_mock and disabled, and this slice does not roll out a runtime external provider.
12. The responder compatibility bridge remains limited to local fake transport and test seam compatibility.

Acceptance:

1. This slice implements only backend credential/config skeleton behavior and is not real external provider integration.
2. The slice keeps external provider runtime rollout blocked.
3. The slice keeps Ask limited to `{ query }`, keeps GameProject free of provider/model UI, and keeps router free of direct provider selection.

Validation note:

1. Focused pytest result from the implementation round: `59 passed in 1.04s`.
2. NUL check result for the touched Python files: all `0`.
3. `git diff --check` reported no whitespace error for this slice.
4. The only `git diff --check` output was pre-existing unrelated line-ending warnings for docs/tasks/knowledge/mvp/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md, scripts/README.md, scripts/migrate_to_cdev.ps1, and scripts/wheel_build.ps1.

Next-step note:

1. The next recommended slice is backend service config handoff or assembly-point boundary review.
2. That next slice should stay backend-only and must not become runtime rollout.
3. Real external provider integration still remains unimplemented.

### P3.external-provider-3 [S] Backend Service Config Wiring Skeleton

Depends on: P3.external-provider-2

Status as of 2026-05-09: implementation completed as a backend service config wiring skeleton.

Tasks:

1. Freeze where backend-owned config may enter the live RAG answer path.
2. Freeze router limits for service-config handoff.
3. Freeze answer-layer responsibility for service-config interpretation and warning merge.
4. Keep env reads, runtime rollout, frontend provider/model UI, and request-schema changes out of scope.
5. Record the next acceptable implementation slice without authorizing real-provider rollout.

Implemented scope note:

1. This review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-3-service-config-wiring-boundary-2026-05-09.md.
2. The approved live handoff entry remains `build_rag_answer_with_service_config(...)`.
3. The live answer path now accepts backend-owned service config through the answer/provider-selection layer, not through router/provider selection.
4. `knowledge_rag_provider_selection.py` parses backend-owned `external_provider_config`; request-like `provider`, `model`, `provider_name`, `model_name`, and `api_key` fields do not participate in provider selection.
5. `future_external` can reach the external model client skeleton only through backend-owned config interpretation, but it still is not a runtime supported provider.
6. Runtime providers remain only `deterministic_mock` and `disabled`.
7. Missing config and unknown provider fail clearly or degrade through the existing safe path; there is no silent provider switch.
8. Router behavior is not widened: Ask still sends only `query`, and router still does not call the provider registry directly.
9. The slice adds no new API, no frontend change, no Ask request schema change, no real HTTP, no real credential, and no real LLM rollout.
10. NUL repair in related tests was validation recovery only and not logic expansion.

Acceptance:

1. `build_rag_answer_with_service_config(...)` remains the only live handoff entry.
2. Backend-owned external provider config is interpreted by the answer/provider-selection layer.
3. Request body provider/model/api_key fields are ignored.
4. Router behavior and Ask request schema remain unchanged.
5. Runtime rollout remains blocked; `future_external` is not user/runtime selectable.

Validation note:

1. Focused pytest recorded for the implementation slice: `84 passed in 11.05s`.
2. Focused coverage included `test_game_knowledge_rag_router.py`, `test_knowledge_rag_answer.py`, `test_knowledge_rag_provider_selection.py`, `test_knowledge_rag_model_registry.py`, and `test_knowledge_rag_external_model_client.py`.
3. Focused NUL check recorded: 9 related files were `NUL=0`.
4. `git diff --check` for this slice's related files had empty output.
5. `test_knowledge_rag_model_registry.py` and `test_knowledge_rag_external_model_client.py` were safely rewritten as clean UTF-8 to restore collection after NUL pollution; that rewrite is not logic expansion.

Next-step note:

1. The next recommended slice is runtime allowlist boundary review.
2. That next slice should decide when, how, and under what conditions `future_external` may enter the runtime provider set.
3. Do not directly connect a real provider before that boundary review.

### P3.external-provider-4 [S] Runtime Allowlist Boundary Review

Depends on: P3.external-provider-3

Status as of 2026-05-09: boundary review completed as a docs-only slice.

Tasks:

1. Freeze when `future_external` may enter the runtime provider set.
2. Freeze that runtime allowlist entry remains backend-owned rather than request-owned.
3. Freeze the combined gating conditions for any future runtime entry.
4. Freeze clear-fail and `disabled` fallback rules before any runtime rollout implementation.
5. Freeze router, request, UI, credential, and transport boundaries for a later allowlist implementation plan.

Implemented scope note:

1. This review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-4-runtime-allowlist-boundary-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, request schema, registry contents, or public API.
3. `future_external` is not added to `SUPPORTED_RAG_MODEL_PROVIDERS` in this slice.
4. Runtime providers still remain only `deterministic_mock` and `disabled`.
5. The future runtime entry decision remains backend-owned through config interpretation and registry decision, not router, request body, frontend UI, or `ProviderManager.active_model`.
6. Future runtime entry requires all of the following together: disabled-by-default explicit enablement, credential presence, provider allowlist, model allowlist, and explicit timeout/cost/privacy policy.
7. Unknown provider must clear-fail and must not silently switch.
8. Provider init failure may only clear-fail or fall back to `disabled`, and must not fall back to another real provider.
9. `no_current_release` and `insufficient_context` must still return before provider, credential, or transport work.
10. Citation grounding remains answer-service-owned and limited to `context.citations`, and `candidate_evidence` still does not automatically enter RAG.
11. The slice adds no real LLM, no real HTTP, no real credential, no new API, no frontend change, and no Ask request-schema change.

Acceptance:

1. The review clearly states that this slice does not change runtime allowlist membership.
2. The review clearly states that `future_external` remains outside `SUPPORTED_RAG_MODEL_PROVIDERS`.
3. The review clearly states that provider/model/api_key still must not come from request body.
4. The review clearly states that router still must not choose provider or call `get_rag_model_client(...)` directly.
5. The review clearly states the cumulative gating conditions required before any future runtime entry.
6. The review clearly states the required failure behavior for unknown provider, init failure, missing credential, and allowlist failure.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check -- docs/tasks/...` and keyword review confirming that the text does not describe runtime rollout or real provider integration.

Next-step note:

1. The next recommended slice is runtime allowlist implementation plan.
2. That next slice must stay backend-owned and must not become direct real-provider rollout.
3. Real external provider integration still remains unimplemented.

### P3.external-provider-5 [S] Runtime Allowlist Implementation Plan

Depends on: P3.external-provider-4

Status as of 2026-05-09: implementation plan completed as a docs-only slice.

Tasks:

1. Define the minimum backend code touchpoints for future runtime allowlist entry.
2. Define the minimum focused tests required before code lands.
3. Define explicit prohibited items so runtime allowlist work does not widen into rollout.
4. Define rollback risks and rollback exit criteria before implementation.
5. Keep the plan separate from real provider connectivity.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-5-runtime-allowlist-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. This plan still does not add `future_external` to `SUPPORTED_RAG_MODEL_PROVIDERS` in the current code.
4. The minimum future code surface is limited to `knowledge_rag_model_registry.py`, `knowledge_rag_answer.py`, `knowledge_rag_provider_selection.py`, `knowledge_rag_external_model_client.py`, and the five focused test files that already cover this path.
5. The plan keeps router unchanged and keeps provider selection backend-owned.
6. The plan requires future tests to prove unknown-provider clear-fail, `disabled`-only fallback on init failure, early-return preservation, request-field ignore behavior, transport suppression on allowlist or credential failure, and citation-boundary preservation.
7. The plan explicitly forbids real provider connection, real HTTP, real credential integration, new request fields, frontend provider control, router-side provider selection, and runtime widening to any second real provider.
8. The plan explicitly records rollback triggers for router drift, request-owned selection, early-return regression, fake-answer regression, citation-boundary regression, and accidental real-provider rollout.

Acceptance:

1. The plan clearly lists the minimum future code files.
2. The plan clearly lists the minimum future test files and behavior checks.
3. The plan clearly lists prohibited items.
4. The plan clearly lists rollback risks and rollback exit criteria.
5. The plan clearly states that current runtime allowlist membership is unchanged.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check -- docs/tasks/...` and keyword review confirming that the text does not describe real provider rollout or real provider integration.

Next-step note:

1. The next recommended slice is backend-only minimal runtime allowlist implementation.
2. That next slice must still keep the external client skeleton-only and must not become real provider rollout.
3. Real external provider integration still remains unimplemented.

### P3.external-provider-6 [S] Backend-Only Minimal Runtime Allowlist Implementation

Depends on: P3.external-provider-5

Status as of 2026-05-09: implementation completed as a backend-only minimal runtime allowlist slice.

Tasks:

1. Add `future_external` to the backend runtime provider allowlist.
2. Keep runtime selection owned by backend service config and registry decision.
3. Remove answer-layer ambiguity so runtime support is owned by the registry.
4. Preserve clear-fail behavior for missing or invalid external config.
5. Preserve router, request, UI, credential, and early-return boundaries.

Implemented scope note:

1. This closeout is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-6-runtime-allowlist-closeout-2026-05-09.md.
2. The semantic implementation files are `knowledge_rag_model_registry.py`, `knowledge_rag_answer.py`, `test_knowledge_rag_model_registry.py`, and `test_knowledge_rag_answer.py`.
3. `future_external` is now part of `SUPPORTED_RAG_MODEL_PROVIDERS` in backend code.
4. Runtime path entry for `future_external` now remains owned by the registry and still requires backend-owned `external_provider_config`.
5. The router remains unchanged and still does not choose provider or call `get_rag_model_client(...)` directly.
6. Request-body provider/model/api_key fields remain ignored.
7. `ProviderManager.active_model` remains out of scope.
8. Missing or invalid external config for `future_external` now clear-fails rather than silently switching provider.
9. The external client remains disabled-by-default skeleton-only, with no real LLM, no real HTTP, and no real credential integration.
10. The slice adds no API, no frontend change, and no Ask request-schema change.

Acceptance:

1. `future_external` enters runtime allowlist only through backend-owned config and registry decision.
2. Router/request/UI still do not own provider selection.
3. Unknown provider still clear-fails.
4. Missing or invalid external config still clear-fails or stays on the safe path.
5. `no_current_release` and `insufficient_context` still bypass provider initialization.
6. `candidate_evidence` still does not enter provider input.

Validation note:

1. Focused pytest for this slice: `86 passed in 1.44s`.
2. Focused NUL check was run for touched backend and focused test files.
3. Final `git diff --check` is required for touched files.

Next-step note:

1. The next recommended step is a later dedicated rollout review.
2. Real external provider integration still remains unimplemented.

### P3.external-provider-7 [S] Real Provider Rollout Boundary Review

Depends on: P3.external-provider-6

Status as of 2026-05-09: boundary review completed as a docs-only slice.

Tasks:

1. Freeze the conditions required before any later real provider rollout may begin.
2. Freeze provider-selection, credential, transport, request, and UI ownership during any later rollout.
3. Freeze required failure behavior and rollback triggers before any real transport or real credential work is attempted.
4. Keep rollout planning separate from frontend provider controls and Ask request-schema changes.
5. Keep current runtime allowlist support distinct from real provider rollout approval.

Implemented scope note:

1. This review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-7-real-provider-rollout-boundary-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The review confirms that current backend runtime allowlist support for `future_external` is not sufficient to authorize real rollout.
4. Any future rollout must remain backend-owned across provider selection, credential resolution, transport creation, and disable-switch control.
5. Router, request body, frontend UI, and `ProviderManager.active_model` remain outside provider-selection authority for this path.
6. The review keeps real HTTP, real credential integration, API expansion, frontend changes, and Ask request-schema changes out of scope.
7. The review freezes credential, allowlist, runtime, HTTP-client, logging, DLP, API, router, frontend, testing, and rollback gates before any later rollout plan.

Acceptance:

1. The review clearly states that real provider rollout remains unimplemented.
2. The review clearly states that current runtime allowlist support does not by itself authorize real rollout.
3. The review clearly states that router/request/UI still do not own provider selection.
4. The review clearly states that Ask request schema remains unchanged.
5. The review clearly states the required failure behavior and rollback triggers for any later rollout slice.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check -- docs/tasks/...` and keyword review confirming that the text does not describe completed real provider rollout.

Next-step note:

1. The next recommended slice is a real provider rollout implementation plan or a mocked HTTP client skeleton plan.
2. Real external provider integration still remains unimplemented.

### P3.external-provider-8a [S] Mocked HTTP Client Skeleton Implementation Plan

Depends on: P3.external-provider-7

Status as of 2026-05-09: implementation plan completed as a docs-only slice.

Tasks:

1. Define the next-round mocked transport seam without authorizing real HTTP.
2. Define the next-round credential-source, allowlist, feature-flag, redaction, and rollback requirements.
3. Define the minimum file scope for the next code round.
4. Define the focused test matrix for mocked transport behavior and boundary preservation.
5. Treat source code as controlling truth and record any source-vs-doc risk explicitly.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8a-mocked-http-client-skeleton-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The plan is source-based and explicitly records that `game/service.py` contains `SimpleModelRouter` real-provider bridge logic outside the RAG path, which must not be reused as a shortcut into the RAG provider path.
4. The plan keeps real provider rollout, real HTTP, real credential integration, API changes, frontend changes, Ask request-schema changes, router provider selection, and `ProviderManager.active_model` changes out of scope.
5. The next-round minimum code surface is limited to external client, narrow provider-selection or registry guards if needed, and the focused backend test files.
6. The plan freezes mocked transport seam rules, credential-source rules, provider and model allowlist rules, runtime feature-flag rules, logging and DLP rules, router and frontend boundaries, and focused test expectations before implementation.

Acceptance:

1. The plan clearly states that this round is docs-only and not implementation.
2. The plan clearly states that this round does not change runtime behavior.
3. The plan clearly states the minimum next-round file scope.
4. The plan clearly states credential, DLP, redaction, allowlist, router, request, and frontend boundaries.
5. The plan clearly states that the next recommended slice is mocked HTTP client skeleton implementation rather than production rollout.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check -- docs/tasks/...` and keyword review confirming that the text does not describe implementation completed, runtime rollout completed, or production provider enablement.

Next-step note:

1. The next recommended slice is mocked HTTP client skeleton implementation.
2. Production real provider rollout still remains unimplemented.

### P3.external-provider-8b [S] Mocked HTTP Client Skeleton Implementation

Depends on: P3.external-provider-8a

Status as of 2026-05-09: completed.

Tasks:

1. Land the minimum backend-only mocked transport gate required by the 8a plan.
2. Require an explicit backend-owned transport enable switch beyond adapter `enabled`.
3. Keep mocked transport injectable for focused tests without authorizing real HTTP.
4. Preserve backend-owned config coercion and answer-path boundaries.
5. Validate the direct external-client, provider-selection, and answer regression surface.

Implemented scope note:

1. This implementation is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-8b-mocked-http-client-skeleton-closeout-2026-05-09.md.
2. The landed code adds `transport_enabled` to `ExternalRagModelClientConfig` and short-circuits external client execution before credential resolution or transport invocation when that gate is off.
3. The implementation keeps mocked transport injectable only when backend-owned config explicitly enables it.
4. The implementation updates focused unit tests for external client behavior, answer behavior, and backend-owned config coercion.
5. This slice adds no real provider, no real HTTP, no real credential integration, no API change, no frontend change, and no Ask request-schema change.

Acceptance:

1. `enabled=True` alone does not authorize transport invocation.
2. `transport_enabled=False` prevents both credential resolution and transport invocation.
3. `transport_enabled=True` still allows the mocked transport seam in focused tests.
4. backend-owned config coercion preserves `transport_enabled`.
5. answer-path warning behavior remains aligned with the new gate semantics.

Validation note:

1. Focused pytest for this slice passed: `60 passed in 0.05s`.
2. Focused scope: `test_knowledge_rag_external_model_client.py`, `test_knowledge_rag_answer.py`, and `test_knowledge_rag_provider_selection.py`.

Next-step note:

1. The next recommended slice is a later real provider rollout implementation plan or later real transport design review.
2. Production real provider rollout still remains unimplemented.

### P3.external-provider-9 [S] Real Transport Design Review

Depends on: P3.external-provider-8b

Status as of 2026-05-09: design review completed as a docs-only slice.

Tasks:

1. Review the current external-provider runtime path from source code and focused tests.
2. Confirm the current 8b gate behavior before any later real transport work.
3. Define future real transport contract boundaries without implementing transport.
4. Define future allowlist hardening, credential, HTTP-client, DLP, logging, runtime-gate, rollback, and router or frontend boundaries.
5. Record any source-vs-doc mismatch as a risk or follow-up rather than as a completed capability.

Implemented scope note:

1. This review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-9-real-transport-design-review-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The review is source-based and confirms that `ExternalRagModelClientConfig` currently has both `enabled` and `transport_enabled`, and that `transport_enabled=False` blocks resolver and injected transport before either can run.
4. The review records that current RAG path still has no real HTTP client and no real credential resolver, and that mocked transport still enters only through injected transport or responder seams.
5. The review records that `SimpleModelRouter` still contains a real-provider bridge outside the current RAG provider path and treats that as a source-level risk rather than as a completed RAG capability.
6. The review records that current allowlist logic does not yet hard-require non-empty `allowed_providers` and `allowed_models` when `transport_enabled=True`, and freezes that as a required future hardening item before any real transport slice.

Acceptance:

1. The review clearly states that this round is docs-only and not implementation.
2. The review clearly states that this round does not authorize real provider rollout.
3. The review clearly states that the current 8b gate remains valid in the source baseline.
4. The review clearly states the future real transport contract, credential, DLP, logging, allowlist, runtime-gate, rollback, router, request, and frontend boundaries.
5. The review clearly records the current source-level risks that still block any future real rollout.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check -- docs/tasks/...` and keyword review confirming that the text does not describe production transport or provider enablement.

Next-step note:

1. The next recommended slice is a real transport skeleton implementation plan or an allowlist hardening implementation slice.
2. Production real provider rollout still remains unimplemented.

### P3.external-provider-10 [S] Allowlist Hardening Implementation

Depends on: P3.external-provider-8b, P3.external-provider-9

Status as of 2026-05-09: completed.

Tasks:

1. Harden the mocked external-provider runtime path so `transport_enabled=True` requires explicit non-empty backend-owned provider and model allowlists.
2. Ensure missing or blank provider and model selections degrade to warnings before credential resolution and before transport.
3. Preserve the existing disabled and not-connected early-return behavior when `enabled=False` or `transport_enabled=False`.
4. Preserve request and router boundaries so request-like provider, model, api_key, and service_config fields remain ignored.
5. Revalidate the focused backend and router tests for the current RAG path.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-10-allowlist-hardening-closeout-2026-05-09.md.
2. `ExternalRagModelClient._validate_selection()` now treats `allowed_providers` and `allowed_models` as hard gates when `transport_enabled=True`.
3. Missing or blank `provider_name` now returns `External provider adapter skeleton provider is not allowed.` before credential resolution and transport.
4. Missing or blank `model_name` now returns `External provider adapter skeleton model is not allowed.` before credential resolution and transport.
5. `enabled=False` and `transport_enabled=False` still return their prior warnings and do not require allowlists.
6. Request-like payload fields remain ignored by prompt normalization and router request handling remains thin.
7. Focused validation for this slice passed in `95 passed in 2.02s` across external client, answer, provider-selection, model-registry, and router tests.

Acceptance:

1. Missing or empty provider allowlists block before credential resolution and transport.
2. Missing or empty model allowlists block before credential resolution and transport.
3. Blank provider or model selection blocks before credential resolution and transport.
4. Disabled or not-connected states still degrade without requiring allowlists.
5. Router and request boundaries remain unchanged.

Validation note:

1. Post-edit validation ran focused pytest for external client, answer, provider-selection, model-registry, and router tests.
2. Post-edit validation also ran `git diff --check`, NUL-byte scan, and keyword review.

Next-step note:

1. The next recommended slice is a real transport skeleton implementation plan that preserves the hardened allowlist gate.
2. Production real provider rollout still remains unimplemented.

### P3.external-provider-11 [S] Gate-Order Hardening Implementation

Depends on: P3.external-provider-10

Status as of 2026-05-09: completed.

Tasks:

1. Move early disabled and not-connected gates ahead of payload normalization in the mocked external-provider client.
2. Ensure malformed direct payload input no longer raises shape errors when adapter is disabled or transport is not connected.
3. Preserve payload validation for the transport-enabled path.
4. Preserve P10 allowlist hardening order so allowlist still blocks before credential resolution and transport.
5. Revalidate focused external client, answer, provider-selection, model-registry, and router tests.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-11-gate-order-hardening-closeout-2026-05-09.md.
2. `ExternalRagModelClient.generate_answer(...)` now checks `enabled` and `transport_enabled` before `_normalize_prompt_payload(...)`.
3. `enabled=False` now returns the disabled warning before payload normalization.
4. `transport_enabled=False` now returns the not-connected warning before payload normalization.
5. Only `enabled=True` plus `transport_enabled=True` now performs prompt-payload normalization.
6. P10 allowlist hardening remains unchanged after normalization and still blocks before credential resolution and transport.
7. Focused validation for this slice passed in `29 passed in 0.04s` for the external client file and passed full focused regression across external client, answer, provider-selection, model-registry, and router tests.

Acceptance:

1. Disabled branch does not normalize malformed payloads.
2. Not-connected branch does not normalize malformed payloads.
3. Disabled and not-connected branches do not call resolver or transport.
4. Transport-enabled branch still raises existing payload validation errors.
5. Router, request, frontend, and provider-selection boundaries remain unchanged.

Validation note:

1. Post-edit validation ran focused pytest for external client, answer, provider-selection, model-registry, and router tests.
2. Post-edit validation also ran `git diff --check`, NUL-byte scan, and keyword review.

Next-step note:

1. The next recommended slice is a real transport skeleton implementation plan rather than production rollout.
2. Production real provider rollout still remains unimplemented.

### P3.external-provider-12 [S] Real Transport Skeleton Implementation Plan

Depends on: P3.external-provider-11

Status as of 2026-05-09: planned as a docs-only slice.

Tasks:

1. Define the next-round real transport skeleton as backend-only and non-production.
2. Freeze the maximum allowed implementation surface for that next round.
3. Freeze transport contract, credential seam, redaction, error mapping, and boundary rules.
4. Freeze API, router, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` boundaries.
5. Define the focused test matrix required before any skeleton implementation lands.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-12-real-transport-skeleton-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The plan is source-based and confirms that P10 allowlist hardening and P11 gate-order hardening are already completed preconditions.
4. The plan keeps the next-round code surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, registry, or answer-layer follow-ups if strictly necessary.
5. The plan keeps router, Ask schema, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
6. The plan keeps credential resolution unimplemented beyond the current injected seam and still forbids env-value reads, secret-store reads, and production transport.
7. The plan defines the next recommended slice as `P3.external-provider-13` real transport skeleton implementation rather than production rollout.

Acceptance:

1. The plan clearly states that P12 is docs-only and does not change runtime behavior.
2. The plan clearly states the next-round allowed code surface and forbidden files.
3. The plan clearly defines transport contract, error mapping, redaction, and credential-seam rules.
4. The plan clearly freezes API, router, frontend, and provider-selection boundaries.
5. The plan clearly defines the focused test matrix for the next implementation round.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review.

Next-step note:

1. The next recommended slice is `P3.external-provider-13` real transport skeleton implementation.
2. That next slice must still remain skeleton-only and must not become production rollout.

### P3.external-provider-13 [S] Real Transport Skeleton Implementation

Depends on: P3.external-provider-12

Status as of 2026-05-09: completed as a backend-only slice.

Tasks:

1. Add a named backend-only non-network transport skeleton inside the external client implementation surface.
2. Keep the default skeleton path non-production and non-network.
3. Define redacted request-preview shape for focused contract testing.
4. Preserve P10 allowlist hardening, P11 gate-order hardening, and answer-layer citation grounding.
5. Keep credential resolution injected-only and keep router, Ask schema, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` unchanged.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-13-real-transport-skeleton-closeout-2026-05-09.md.
2. The semantic code change is limited to `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py` plus focused external-client tests.
3. A named non-network skeleton transport now exists as `ExternalRagModelHttpTransportSkeleton`.
4. The skeleton builds only a redacted request preview and strips query strings from previewed URL-like values.
5. The skeleton does not perform real HTTP, does not open sockets, does not read files, does not read `os.environ`, and does not read any secret store.
6. The default skeleton invocation fails safely and is mapped to `External provider adapter skeleton request failed.` rather than to any provider raw message.
7. P10 allowlist hardening remains preserved and still blocks resolver or transport when provider or model allowlists are missing, empty, blank, or disallowed.
8. P11 gate-order hardening remains preserved and still keeps disabled and not-connected gates ahead of payload normalization.
9. Credential resolver behavior remains injected-only and unimplemented as a real resolver.
10. This slice adds no API, no router change, no frontend change, and no Ask request-schema change.

Acceptance:

1. A named non-network transport skeleton exists in the backend external-client implementation surface.
2. The skeleton exposes a redacted request-preview shape without `api_key` or `Authorization` material.
3. The skeleton performs no real HTTP, file I/O, env read, or socket I/O.
4. Default skeleton failure maps to a safe warning.
5. P10 allowlist hardening, P11 gate-order hardening, and answer-layer grounding remain preserved.

Validation note:

1. Focused external-client pytest passed: `32 passed in 0.04s`.
2. Required five-file focused pytest passed: `104 passed in 1.91s`.
3. Post-edit validation also includes `git diff --check`, NUL-byte scan on touched Python and docs files, and keyword review.

Next-step note:

1. The next recommended slice is not production rollout.
2. The next recommended slice should be either a credential resolver boundary or implementation plan, or an admin config boundary review.

### P3.external-provider-14 [S] Credential Resolver Boundary And Implementation Plan

Depends on: P3.external-provider-13

Status as of 2026-05-09: completed as a docs-only slice.

Tasks:

1. Define the next-round credential resolver skeleton as backend-only and non-production.
2. Freeze the maximum allowed implementation surface for that next round.
3. Freeze credential resolver contract, secret-source policy, redaction, DLP, and logging rules.
4. Freeze the relationship between resolver skeleton and the existing P13 non-network transport skeleton.
5. Freeze API, router, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` boundaries.
6. Define the focused test matrix required before any resolver skeleton implementation lands.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-14-credential-resolver-boundary-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The plan is source-based and confirms that P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton are already completed preconditions.
4. The plan keeps the next-round code surface centered on `knowledge_rag_external_model_client.py`, with only narrow contingency allowance for provider-selection, model-registry, or answer-layer follow-ups if strictly necessary.
5. The plan confirms that current RAG external-provider path still uses injected credential resolver only and still has no secret-store integration, no env value reads, and no provider-manager credential loading.
6. The plan keeps router, Ask schema, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` out of scope for the next round.
7. The plan keeps future real secret sources, provider-manager bridge, admin config UI, and rollout rules out of the next round and marks them for later dedicated review.
8. The plan defines the next recommended slice as `P3.external-provider-15` credential resolver skeleton implementation or a separate admin config boundary review rather than production rollout.

Acceptance:

1. The plan clearly states that P14 is docs-only and does not change runtime behavior.
2. The plan clearly states the next-round allowed code surface and forbidden files.
3. The plan clearly defines credential resolver contract, secret-source policy, redaction, DLP, and logging rules.
4. The plan clearly freezes API, router, frontend, and provider-selection boundaries.
5. The plan clearly defines the focused test matrix for the next implementation round.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review.

Next-step note:

1. The next recommended slice is `P3.external-provider-15` credential resolver skeleton implementation.
2. That next slice must still remain backend-only, non-production, and must not read real secret sources.

### P3.external-provider-15 [S] Credential Resolver Skeleton Implementation

Depends on: P3.external-provider-14

Status as of 2026-05-09: completed as a backend-only skeleton slice.

Tasks:

1. Add a named default credential resolver skeleton inside the external client path.
2. Keep the default resolver skeleton limited to backend-owned metadata only.
3. Keep default resolver behavior as safe not-configured degradation.
4. Preserve injected resolver seam and injected transport seam behavior.
5. Preserve P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton behavior.

Implemented scope note:

1. This closeout is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-15-credential-resolver-skeleton-closeout-2026-05-09.md.
2. This slice adds `ExternalRagModelCredentialResolverSkeleton` inside `knowledge_rag_external_model_client.py` and keeps the implementation local to the external client path.
3. The default resolver skeleton validates only backend-owned `provider_name`, `model_name`, and env-var-name metadata, and returns `None` by default.
4. The default resolver skeleton does not read env values, does not access secret store, does not read config-file secret values, does not access `ProviderManager`, and does not access `SimpleModelRouter`.
5. Resolver exceptions now map to the existing safe not-configured warning instead of surfacing raw exception text.
6. Injected resolver success plus injected transport success remains unchanged.
7. Injected resolver success plus default P13 transport skeleton still safe-fails without network.
8. Router, Ask schema, frontend, `ProviderManager.active_model`, and `SimpleModelRouter` remain out of scope and unchanged.

Acceptance:

1. A named resolver skeleton exists and is used by default when no injected resolver seam is supplied.
2. Default resolver behavior still degrades safely to `External provider adapter skeleton is not configured.`
3. Resolver exceptions do not leak raw secret-like text.
4. P10 allowlist hardening, P11 gate-order hardening, and P13 non-network transport skeleton remain preserved.
5. No real secret source, API change, router change, request-schema change, or frontend change is introduced.

Validation note:

1. Focused external-client pytest passed: `34 passed in 0.04s`.
2. Required five-file focused pytest passed: `106 passed in 1.93s`.
3. Post-edit validation also includes `git diff --check`, NUL-byte scan on touched Python and docs files, and keyword review.

Next-step note:

1. The next recommended slice is not production rollout.
2. The next recommended slice should be either an admin config boundary review or a credential source governance plan.

### P3.external-provider-16 [S] Credential Source Governance Boundary Review

Depends on: P3.external-provider-15

Status as of 2026-05-09: completed as a docs-only governance slice.

Tasks:

1. Freeze the current post-P15 source-truth baseline for credential sourcing.
2. Define credential-source governance rules and forbidden ownership paths.
3. Define future candidate source categories without selecting an implementation.
4. Define a draft source-precedence and safe-failure policy for future review.
5. Separate admin config governance from formal-knowledge acceptance governance.
6. Freeze DLP, redaction, logging, rollback, and test-matrix requirements for any future real credential source work.

Implemented scope note:

1. This review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-16-credential-source-governance-boundary-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The review confirms that after P15 the runtime still has only a resolver skeleton, still has zero real credential sources, and still has no production credential capability.
4. The review confirms that secret store, provider manager, provider router, and `SimpleModelRouter` exist elsewhere in the repository but are still outside the current Ask RAG credential path.
5. The review freezes credential ownership as backend-only and explicitly forbids request-body, frontend, router, map, formal-map, snapshot, export, docs, tasks, and ordinary fast-test input as credential sources.
6. The review separates admin config governance from formal-knowledge acceptance and keeps both out of the current Ask/runtime path.
7. The review defines future candidate source categories, source-precedence draft, rollback requirements, DLP rules, and implementation test matrix without authorizing any real source integration.
8. The review defines the next recommended slice as `P17` admin config boundary review or `P17` credential source implementation plan rather than production rollout.

Acceptance:

1. The review clearly states that post-P15 runtime still has no production credential source.
2. The review clearly forbids request, frontend, router, `ProviderManager`, and `SimpleModelRouter` as credential-source owners for the current path.
3. The review clearly separates formal-knowledge acceptance from runtime credential governance.
4. The review clearly freezes DLP, redaction, rollback, and test-matrix requirements for future real-source work.
5. The review clearly keeps the next step at governance or implementation planning rather than rollout.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review.

Next-step note:

1. The next recommended slice is not production rollout.
2. The next recommended slice should be either `P17` admin config boundary review or `P17` credential source implementation plan.

### P3.external-provider-17 [S] Backend Env-Var Credential Source Implementation Plan

Depends on: P3.external-provider-16

Status as of 2026-05-09: completed as a docs-only implementation plan.

Tasks:

1. Freeze the post-P16 source-truth baseline before any real source implementation.
2. Select a single minimal backend-owned credential source candidate for the next implementation round.
3. Define the exact P18 code surface, forbidden files, resolver contract, DLP rules, rollback rules, and focused test matrix.
4. Keep formal-knowledge acceptance governance separate from runtime credential governance.
5. Define closeout expectations for the next implementation round.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-17-env-credential-source-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The plan confirms that after P16 the runtime still has zero real credential sources and that P17 itself does not implement env reads.
4. The plan selects backend env-var credential source as the minimal P18 candidate because `ExternalRagModelEnvConfig.api_key_env_var` already exists as backend-owned metadata and this path does not require router, frontend, admin UI, secret store, `ProviderManager`, or `SimpleModelRouter` integration.
5. The plan keeps secret store, keychain, deployment-managed references, and admin-managed references out of the next implementation round.
6. The plan keeps P18 implementation local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
7. The plan freezes env-read ordering so that any future env value read can occur only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
8. The plan keeps the next recommended slice as `P18` backend env-var credential source implementation rather than any rollout or broader credential architecture work.

Acceptance:

1. The plan clearly states that P17 does not implement env value reads.
2. The plan clearly states that P18 is the first round that may implement env value reads.
3. The plan clearly keeps request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of credential ownership.
4. The plan clearly freezes DLP, redaction, rollback, and focused test requirements for P18.
5. The plan clearly keeps the next step at `P18` implementation rather than rollout.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review.

Next-step note:

1. The next recommended slice is `P18` backend env-var credential source implementation.

### P3.external-provider-18 [S] Backend Env-Var Credential Source Implementation

Depends on: P3.external-provider-17

Status as of 2026-05-09: completed as a backend-only implementation.

Tasks:

1. Implement the single minimal backend-owned env-var credential source selected in P17.
2. Keep the implementation local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
3. Preserve P10 allowlist hardening and P11 gate-order hardening.
4. Keep env reads inside resolver logic only and only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
5. Keep request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of credential ownership.

Implemented scope note:

1. This implementation is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-18-env-credential-source-closeout-2026-05-09.md.
2. The runtime now has a named backend-only default env-aware resolver, `ExternalRagModelEnvCredentialResolver`.
3. Default external client construction now uses that resolver only when no injected `credential_resolver` and no responder-backed resolver are supplied.
4. The resolver reads only `env.api_key_env_var` from backend-owned metadata and safe-fails to `External provider adapter skeleton is not configured.` on missing, blank, or failing env reads.
5. P10 allowlist hardening, P11 gate-order hardening, and the P13 non-network transport skeleton remain preserved.
6. Ask request schema, router authority, frontend, `ProviderManager.active_model`, `SimpleModelRouter`, and `secret_store` remain unchanged.
7. This slice remains backend-only, does not add real HTTP, and does not authorize production credential rollout or real provider rollout.

Acceptance:

1. Env reads occur only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
2. Missing env config, blank env-var name, missing env value, blank env value, and env read exceptions all safely degrade to the existing not-configured warning.
3. Injected resolver and responder seams still override the default env source.
4. Default env resolver plus default transport skeleton still safe-fails without network.
5. No request-body, frontend, router, `ProviderManager`, `SimpleModelRouter`, or `secret_store` ownership drift is introduced.

Validation note:

1. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py` passed in `47 passed in 0.05s`.
2. `pytest tests/unit/game/test_knowledge_rag_external_model_client.py tests/unit/game/test_knowledge_rag_answer.py tests/unit/game/test_knowledge_rag_provider_selection.py tests/unit/game/test_knowledge_rag_model_registry.py tests/unit/routers/test_game_knowledge_rag_router.py` passed in `119 passed in 2.03s`.
3. Post-edit validation for this slice also requires `git diff --check`, NUL-byte scan on touched files, and keyword review.

Next-step note:

1. The next recommended slice is a backend-only secret-source precedence or real-transport governance review, not production rollout.
2. That next slice must still remain backend-only, non-production, and must not widen into secret store, `ProviderManager`, `SimpleModelRouter`, frontend, or router ownership.

### P3.external-provider-19 [S] Backend-Only Real HTTP Transport Governance And Implementation Plan

Depends on: P3.external-provider-18

Status as of 2026-05-09: completed as a docs-only implementation plan.

Tasks:

1. Freeze the post-P18 source-truth baseline before any future real HTTP transport work.
2. Define the exact P20 code surface, transport contract, error mapping, redaction, rollback, and focused test matrix.
3. Keep transport planning separate from credential-source changes, router or frontend widening, and provider rollout approval.
4. Preserve formal-knowledge acceptance separation from runtime credential and provider governance.
5. Define closeout expectations for the next implementation round.

Implemented scope note:

1. This plan is recorded in docs/tasks/knowledge/mvp/knowledge-p3-external-provider-19-real-http-transport-governance-implementation-plan-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, tests, request schema, registry contents, or public API.
3. The plan confirms that after P18 the current Ask RAG runtime has a backend-owned env-var credential source but still has zero real HTTP transports and zero real provider rollouts.
4. The plan confirms that current env reads still occur only through `ExternalRagModelEnvConfig.api_key_env_var` and only after enabled gate, transport-enabled gate, payload normalization, and allowlist validation succeed.
5. The plan keeps P20 local to `knowledge_rag_external_model_client.py` plus focused tests and closeout docs.
6. The plan keeps router, frontend, Ask schema, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of scope for P20.
7. The plan records the unreachable trailing `return None` in `ExternalRagModelEnvCredentialResolver` as future code cleanup only and does not authorize code change in this slice.
8. The plan keeps P20 as backend-only real HTTP transport minimal implementation or skeleton implementation rather than any production rollout or credential-source expansion.

Acceptance:

1. The plan clearly states that P19 does not implement real HTTP.
2. The plan clearly states that P20 is the first round that may implement minimal real HTTP transport behavior.
3. The plan clearly keeps current env credential source as the only implemented credential source for this Ask RAG path.
4. The plan clearly keeps request, frontend, router, `ProviderManager`, `SimpleModelRouter`, and `secret_store` out of provider and credential ownership.
5. The plan clearly defines transport contract, warning mapping, DLP or redaction, rollback, and focused test requirements for P20.

Validation note:

1. This docs-only pass does not run pytest.
2. This docs-only pass does not run TypeScript.
3. Post-edit validation for this slice is limited to `git diff --check` on touched docs files, NUL-byte scan on touched docs files, and keyword review.

Next-step note:

1. The next recommended slice is P20 backend-only real HTTP transport minimal implementation or skeleton implementation, not production rollout.

### P3.rag-ui-1 [S] Minimal Product-Entry UI On Existing Answer Endpoint

Depends on: P3.4b, P3.rag-model-3b

Status as of 2026-05-08: completed.

Tasks:

1. Add the smallest frontend API typing and client method for the existing backend RAG answer endpoint.
2. Add a minimal GameProject knowledge Q&A entry on the existing knowledge release surface.
3. Render `mode`, `answer`, `release_id`, `citations`, and `warnings`.
4. Surface explicit `no_current_release` and `insufficient_context` states.
5. Keep provider selection, real external provider integration, request-schema changes, and broader chat UX out of scope.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-minimal-closeout-2026-05-08.md.
2. The implementation files are console/src/api/types/game.ts, console/src/api/modules/gameKnowledgeRelease.ts, console/src/pages/Game/GameProject.tsx, and console/src/pages/Game/GameProject.module.less.
3. The UI sends only `query` to the existing backend answer endpoint and does not expose provider or model controls.
4. The UI renders current backend fields only and does not invent a new response contract.
5. The UI keeps structured-query and workbench-flow guardrail messaging explicit.
6. No backend code, router contract, request schema, provider registry, or real external provider integration was added in this slice.

Acceptance:

1. The slice lands a minimal product-entry RAG UI without widening backend or provider boundaries.
2. The slice does not expose frontend provider control.
3. The slice does not add real external provider integration.

Validation note from implementation round:

1. VS Code Problems check on touched frontend files: no errors found.
2. `pnpm build` could not run because `pnpm` was unavailable in the environment.
3. `npm run build` could not run because `npm` was unavailable in the environment.
4. `git diff --check`: clean.

### P3.rag-ui-2 [S] Product-Flow UX Enhancement Plan

Depends on: P3.rag-ui-1

Status as of 2026-05-08: planned.

Tasks:

1. Plan the next small-step UX enhancement on the existing answer endpoint.
2. Limit the scope to frontend product-flow improvements such as recent question history, static example questions, copy answer, and citation locate or jump.
3. Keep provider, router, request-schema, model-client, and runtime-provider boundaries unchanged.
4. Keep `knowledge.read` Ask-button disablement and handler guard unchanged.
5. Record allowed scope, forbidden scope, acceptance criteria, rollback conditions, and validation expectations for a future implementation round.

Planned scope note:

1. This slice is planned in docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-2-product-flow-plan-2026-05-08.md.
2. The preferred next step is pure frontend UX enhancement rather than provider credential or transport boundary work.
3. Recent-question history should remain local UI state or session-level frontend state only.
4. Example questions should remain static UI suggestions only.
5. Copy answer should remain a frontend-only convenience action.
6. Citation locate or jump must stay limited to the citations already returned by the backend.
7. No backend code, request-schema change, provider control, or external provider integration is included in this plan.

Acceptance:

1. The plan keeps the next step small and frontend-focused.
2. The plan does not widen provider, router, request, or citation-grounding boundaries.
3. The plan keeps RAG Q&A separate from administrator acceptance and release-entry workflows.
4. The next implementation target is explicitly `P3.rag-ui-2a`: static example questions, recent question history, copy answer, and local citation focus.
5. Citation focus is limited to local focus or scroll inside already-rendered returned citations and must not add backend artifact or raw-source reads.
6. The next implementation must not add backend endpoints, request-schema fields, provider controls, model controls, save actions, accept actions, publish actions, or formal-knowledge writes.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. Post-edit validation for this pass is limited to git diff --check.

### P3.rag-ui-2a [S] Frontend UX Enhancement Implementation

Depends on: P3.rag-ui-2

Status as of 2026-05-08: completed.

Tasks:

1. Implement static example questions in the existing Knowledge Q&A section.
2. Implement recent question history in component-local state only.
3. Implement copy-answer behavior using the browser clipboard API only.
4. Implement local citation focus or scroll inside the rendered citation list only.
5. Preserve `knowledge.read` Ask-button disablement and handler guard.
6. Preserve query-only payload and all provider, router, and runtime-provider boundaries.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-2a-closeout-2026-05-08.md.
2. The implementation files are console/src/pages/Game/GameProject.tsx and console/src/pages/Game/GameProject.module.less.
3. Static example questions populate the existing query input only and do not auto-submit.
4. Recent question history remains component-local, capped at 5 items, stores only query plus mode plus timestamp, and is not persisted.
5. Copy-result uses the browser clipboard API only and does not write files or knowledge assets.
6. Citation focus remains local scroll or highlight over returned citations only and does not read artifacts or raw source.
7. No backend code, no request-schema change, no provider or model control, and no external provider integration were added.

Acceptance:

1. The slice completes all four planned frontend UX enhancements.
2. The slice keeps the effective request payload at `query` only.
3. The slice keeps `knowledge.read` Ask-button disablement and handler guard intact.
4. The slice keeps RAG Q&A separate from administrator acceptance and release-entry workflows.

Validation note from implementation round:

1. VS Code Problems check on touched frontend files: no errors found.
2. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
3. Focused backend RAG regression: 70 passed.
4. `git diff --check`: clean.
5. Optional `./node_modules/.bin/vite build` could not complete because Rollup's native optional dependency failed to load with a macOS code-signature or optional-dependency error.

### P3.rag-ui-2b [S] Frontend Hardening And Helper Extraction

Depends on: P3.rag-ui-2a

Status as of 2026-05-08: completed.

Tasks:

1. Extract pure helper logic from the GameProject RAG UI without changing request or answer semantics.
2. Improve maintainability of recent-history, copy-text, citation-value, and warning-classification logic.
3. Apply only minimal frontend polish for wrapping or overflow in the existing RAG entry.
4. Preserve `knowledge.read` Ask-button disablement and handler guard.
5. Do not add backend code, request-schema fields, provider controls, model controls, or external provider integration.
6. Do not introduce a new frontend test framework when none already exists in the console workspace.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-2b-closeout-2026-05-08.md.
2. The implementation files are console/src/pages/Game/GameProject.tsx, console/src/pages/Game/GameProject.module.less, and console/src/pages/Game/ragUiHelpers.ts.
3. Recent-question history shaping now uses a dedicated pure helper.
4. Copy-result text assembly now uses a dedicated pure helper.
5. Citation field-value formatting and guardrail-warning classification now use dedicated pure helpers.
6. Minimal narrow-screen wrapping polish was added for example buttons, action buttons, and citation metadata.
7. No backend code, no request-schema change, no provider or model control, and no external provider integration were added.
8. No frontend test framework was added because the console workspace does not already define one.

Acceptance:

1. The slice improves maintainability without changing the effective request payload.
2. The slice keeps `knowledge.read` Ask-button disablement and handler guard intact.
3. The slice keeps recent history, copy-result, and citation focus frontend-local only.
4. The slice keeps RAG Q&A separate from administrator acceptance and release-entry workflows.

Validation note from implementation round:

1. Targeted frontend ESLint passed: `./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/ragUiHelpers.ts`.
2. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
3. Focused backend RAG regression: `70 passed`.
4. `git diff --check`: clean.

### P3.rag-ui-3 [S] Product Experience Consolidation Plan

Depends on: P3.rag-ui-2b

Status as of 2026-05-08: completed as a docs-only product experience consolidation plan.

Tasks:

1. Decide whether the current RAG MVP entry should remain inside GameProject or split into a standalone Knowledge Q&A surface.
2. Define the product display hierarchy across `answer`, `insufficient_context`, and `no_current_release`.
3. Define the read-only next-step guidance for `insufficient_context`.
4. Define how precise numeric or row-level questions should route toward structured query and how change or edit intent should route toward numeric workbench.
5. Define the next-step stance for citation grouping, citation reading view review needs, recent-history scope, copy-result scope, and minimum future test strategy.
6. Recommend the next implementation slice without widening provider, router, request, or model boundaries.

Implemented scope note:

1. The plan is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-3-product-experience-consolidation-plan-2026-05-08.md`.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The plan keeps the current MVP product entry inside GameProject rather than splitting to a standalone Knowledge Q&A surface.
4. The plan defines `answer` as the primary success state, `insufficient_context` as the primary recoverable failure state, and `no_current_release` as the primary readiness blocker state.
5. The plan recommends read-only next-step guidance for `insufficient_context` rather than provider or transport expansion.
6. The plan keeps precise numeric or row-level questions routed toward structured query and keeps change or edit intent routed toward numeric workbench.
7. The plan recommends citation display grouping as a future presentation-only enhancement and explicitly requires a separate boundary review before any citation reading-view implementation.
8. The plan keeps recent-question history component-local and non-persistent by default.
9. The plan treats expanded copy affordances as optional future planning only.
10. The plan records a minimum future frontend test-strategy direction without introducing a new test framework in this slice.
11. The plan explicitly recommends `P3.rag-ui-3a` as the next slice.
12. The plan explicitly recommends frontend-only product refinement before provider credential or transport work.

Acceptance:

1. The plan keeps GameProject as the current MVP entry.
2. The plan keeps provider or model control closed.
3. The plan keeps the effective request payload limited to `query` only.
4. The plan keeps router, provider-selection, retrieval, and citation-validation boundaries unchanged.
5. The plan recommends `P3.rag-ui-3a` rather than provider credential or transport work as the next implementation slice.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not rerun pytest.
3. This docs-only pass does not rerun TypeScript checks.
4. Post-edit validation for this pass is limited to `git diff --check`.

Next-step note:

1. The next recommended slice is `P3.rag-ui-3a` frontend-only product experience refinement.
2. `P3.rag-ui-3a` should strengthen the three-state display hierarchy, add read-only next-step hints for `insufficient_context`, and refine structured-query or workbench entry affordance planning without widening backend boundaries.

### P3.rag-ui-3a [S] Frontend-Only Product Experience Refinement

Depends on: P3.rag-ui-3

Status as of 2026-05-08: completed.

Tasks:

1. Refine the display hierarchy across `answer`, `insufficient_context`, and `no_current_release` inside the existing GameProject RAG entry.
2. Add read-only next-step hints for `insufficient_context`.
3. Preserve the existing structured-query and workbench guardrail copy while adding read-only compact path labels only.
4. Add citation display grouping based only on returned citations.
5. Preserve existing example questions, recent-question history, copy result, citation focus, and `knowledge.read` guards.
6. Do not widen request payload, router behavior, provider or model control, registry behavior, or external-provider scope.

Implemented scope note:

1. This slice is closed out in docs/tasks/knowledge/mvp/knowledge-p3-rag-ui-3a-closeout-2026-05-08.md.
2. The implementation files are console/src/pages/Game/GameProject.tsx, console/src/pages/Game/GameProject.module.less, and console/src/pages/Game/ragUiHelpers.ts.
3. `answer` now keeps answer body as the primary content, with state metadata, warnings, and citations remaining auxiliary.
4. `insufficient_context` now shows read-only next-step hints without auto-retry, fabricated answer, or backend widening.
5. `no_current_release` now shows readiness-blocker guidance without adding build or publish actions.
6. Structured-query and workbench path labels remain read-only and do not navigate.
7. Citation grouping is presentation-only and derived only from returned citations.
8. No backend code, no request-schema change, no provider or model control, and no external provider integration were added.

Acceptance:

1. The slice keeps the RAG MVP entry inside GameProject.
2. The slice keeps `answer`, `insufficient_context`, and `no_current_release` visually distinct without changing backend semantics.
3. The slice keeps `answerRagQuestion(...)` limited to `{ query }` only.
4. The slice keeps Ask-button `knowledge.read` disablement and handler-side guard intact.
5. The slice keeps citation review limited to returned citations only.

Validation note from implementation round:

1. Targeted frontend ESLint passed: `./node_modules/.bin/eslint src/pages/Game/GameProject.tsx src/pages/Game/ragUiHelpers.ts`.
2. Console TypeScript no-emit validation passed: `./node_modules/.bin/tsc -b --noEmit`.
3. Focused backend RAG regression: `70 passed`.
4. `git diff --check`: clean.

### P3.8 [S] RAG / Structured Query / Workbench Routing Boundary Planning

Depends on: P3.rag-ui-3a, P3.permission-3, P3.rag-model-2g

Status as of 2026-05-09: completed as a docs-only routing boundary review.

Tasks:

1. Define the product boundary between ordinary current-release RAG Q&A, structured query, and workbench flow.
2. Keep this slice planning-only and do not implement navigation, deep links, or route handoff.
3. Keep structured-query routing limited to exact numeric, row-level, field-level, and value-level lookup intent.
4. Keep workbench routing limited to change or edit intent only.
5. Keep ordinary RAG Q&A read-only and separate from test-plan, candidate, formal-map, release, and administrator-acceptance workflows.
6. Freeze future routing constraints for any later `Go to structured query` or `Go to workbench` action.
7. Reconfirm request, router, provider-selection, citation, and endpoint boundaries without changing code.

Implemented scope note:

1. The review is recorded in docs/tasks/knowledge/mvp/knowledge-p3-8-rag-routing-boundary-review-2026-05-09.md.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. Ordinary RAG Q&A is reaffirmed as a read-only explanatory surface over the current release only.
4. Structured query is reaffirmed as the route for exact numeric, row-level, field-level, and value-level lookup behavior only.
5. Workbench flow is reaffirmed as the route for change, edit, modify, patch, add, remove, rewrite, or set intent only.
6. Ordinary RAG Q&A remains forbidden from automatically creating test plans, release candidates, formal map, release builds, or release publish actions.
7. Administrator acceptance remains outside ordinary RAG Q&A, recent-question history, copy result, citation review, and routing hints.
8. Any future `Go to structured query` or `Go to workbench` action must be explicit user-triggered frontend behavior only.
9. Any future routing action must not auto-submit, auto-write a test plan, auto-create a candidate, auto-build, or auto-publish.
10. Permission checks for future structured-query or workbench entry remain separate and must still be enforced explicitly.
11. The product-facing query payload remains `{ query }` only.
12. Request body is not authorized to carry provider name, model name, provider hint, or service config.
13. Router remains thin and must not select provider or call `get_rag_model_client(...)` directly.
14. `build_rag_answer_with_service_config(...)` remains the current answer handoff path.
15. Citation grouping and citation focus remain derived only from returned citations.
16. This slice does not authorize any citation artifact endpoint or raw-source reading endpoint.

Acceptance:

1. The review keeps ordinary RAG Q&A, structured query, and workbench flow explicitly separated by product role.
2. The review keeps structured query limited to precise fact lookup and keeps workbench limited to change or edit intent.
3. The review keeps ordinary RAG Q&A read-only and outside administrator-acceptance or release-governance workflows.
4. The review keeps the product-facing request payload limited to `{ query }` only.
5. The review keeps request-body provider or model control closed and keeps router provider selection forbidden.
6. The review keeps citation grouping or focus based only on returned citations and authorizes no new artifact or raw-source reading endpoint.
7. The review adds no backend code, no frontend code, no new API, no real provider, and no request-schema change.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8a [S] Frontend Routing Affordance Discovery / Minimal Implementation Planning

Depends on: P3.8

Status as of 2026-05-09: completed as a docs-only discovery and planning slice.

Tasks:

1. Discover whether the current console frontend already exposes a structured-query destination.
2. Discover whether the current console frontend already exposes a reusable NumericWorkbench destination.
3. Judge whether a future `Go to structured query` and `Go to workbench` affordance can land without backend API expansion or auto-submit behavior.
4. Keep this slice docs-only unless both destinations are explicit enough for a narrow frontend-only implementation plan.

Implemented scope note:

1. The discovery report is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8a-routing-affordance-discovery-2026-05-09.md`.
2. Discovery confirms that NumericWorkbench already has an explicit frontend route at `/numeric-workbench`, existing sidebar entry, deep-link search-param support, and separate `workbench.read` or `workbench.test.write` permission handling.
3. Discovery confirms that the current RAG UI shows only read-only structured-query labels and warning hints, not a real structured-query route or page.
4. Discovery confirms that no dedicated structured-query page, route, tab, or component currently exists in `console/src`.
5. Discovery notes that the legacy `gameApi.query(...)` wrapper alone is not treated as a sufficient structured-query frontend destination.
6. The recommended outcome for this round is docs-only and not a combined `P3.8b` implementation yet.
7. A later workbench-only affordance slice may be feasible, but a combined structured-query plus workbench affordance slice should wait until the structured-query destination is defined explicitly.
8. This slice adds no backend code, no frontend code, no router change, no request-schema change, no provider or model control, and no API expansion.

Acceptance:

1. The discovery clearly lists current available frontend entry points.
2. The discovery clearly lists gaps that block a combined implementation.
3. The recommendation stays docs-only when the structured-query target remains unclear.
4. The discovery preserves the `{ query }` payload boundary and all `P3.8` non-writing routing constraints.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8b [S] Workbench Affordance Boundary Review

Depends on: P3.8a

Status as of 2026-05-09: completed as a docs-only boundary review.

Tasks:

1. Define where a future `Go to workbench` affordance may appear in the current RAG MVP entry.
2. Decide whether generic `insufficient_context` next-step hints may host the first-version affordance.
3. Freeze the interaction and navigation boundary for a minimal workbench-only affordance.
4. Freeze the permission boundary and keep structured query out of this slice.

Implemented scope note:

1. The boundary review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8b-workbench-affordance-boundary-review-2026-05-09.md`.
2. This slice is docs-only and does not modify backend code, frontend code, routers, request schema, or public API.
3. The first-version workbench affordance is limited to explicit workbench or change-intent guardrail surfaces only.
4. The first-version workbench affordance is explicitly not allowed to appear from generic `insufficient_context` next-step hints alone.
5. Any future affordance must remain explicit user click only and must not auto-jump on warning render or state render.
6. The recommended first version may navigate only to `/numeric-workbench`.
7. The review does not recommend freeform-query handoff because NumericWorkbench currently defines only `session`, `table`, `row`, and `field` deep-link support.
8. Entry permission remains `workbench.read`, while later mutation inside NumericWorkbench remains controlled by `workbench.test.write`.
9. The review keeps `knowledge.build` and `knowledge.publish` out of the workbench-entry requirement.
10. Structured query remains outside this slice and stays a separate destination-boundary problem.
11. This slice adds no backend code, no frontend code, no router change, no request-schema change, no provider or model control, and no API expansion.

Acceptance:

1. The review keeps the future affordance workbench-only rather than combined with structured query.
2. The review limits the first version to explicit workbench guardrail surfaces.
3. The review rejects generic `insufficient_context` hints as a first-version trigger.
4. The review keeps the first version limited to plain navigation to `/numeric-workbench`.
5. The review explains why freeform-query handoff is not recommended yet.
6. The review preserves the `{ query }` payload boundary and all existing provider, router, and citation boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8c [S] Frontend-Only Go To Workbench Affordance Implementation

Depends on: P3.8b

Status as of 2026-05-09: completed.

Tasks:

1. Add the minimal `Go to workbench` affordance only in explicit workbench guardrail contexts.
2. Keep the first version user-triggered only.
3. Keep the first version limited to plain navigation to `/numeric-workbench`.
4. Add explicit `workbench.read` disabled behavior when capability context exists.
5. Keep structured query out of this implementation slice.

Implemented scope note:

1. This slice is closed out in `docs/tasks/knowledge/mvp/knowledge-p3-8c-go-to-workbench-closeout-2026-05-09.md`.
2. The implementation files are `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/GameProject.module.less`.
3. A minimal `Go to workbench` button now appears only in the static workbench guardrail block and in warning rows using the existing workbench warning.
4. Generic `insufficient_context` next-step hints remain button-free.
5. Clicking the button navigates only to `/numeric-workbench`.
6. The first version does not pass freeform query text and does not auto-submit anything inside NumericWorkbench.
7. The button stays enabled when capability context is absent, preserving local trusted fallback.
8. When capability context exists and `workbench.read` is missing, the button is disabled with fixed copy `Requires workbench.read permission.`.
9. The entry button does not require `knowledge.build` or `knowledge.publish`, and `workbench.test.write` still governs later write actions only.
10. This slice adds no backend code, no new API, no request-schema change, no provider or model control, no real LLM integration, and no structured-query affordance.

Acceptance:

1. The button appears only in explicit workbench guardrail contexts.
2. The button does not appear from generic `insufficient_context` hints.
3. The button navigates only after explicit user click.
4. The first version navigates only to `/numeric-workbench`.
5. The first version does not auto-submit, auto-create test plans or candidates, build, or publish.
6. The slice preserves the `{ query }` request boundary and all existing provider, router, and citation boundaries.

Validation note from implementation round:

1. Frontend TypeScript no-emit validation ran with no output.
2. Targeted ESLint for `console/src/pages/Game/GameProject.tsx` and `console/src/pages/Game/ragUiHelpers.ts` ran with no output.
3. `git diff --check` ran with no output.
4. Editor diagnostics reported no errors in `GameProject.tsx`, `ragUiHelpers.ts`, or `GameProject.module.less`.
5. No GameProject or RAG UI frontend test suite was found for this slice, so no frontend component test was run.
6. No backend pytest was run because this slice did not touch backend code.

### P3.8d [S] Structured-Query Destination Discovery / Boundary Review

Depends on: P3.8a, P3.8c

Status as of 2026-05-09: completed as a docs-only discovery and boundary review slice.

Tasks:

1. Re-check whether the current frontend already has a dedicated structured-query destination.
2. Judge whether legacy `gameApi.query(agentId, q, mode)` is sufficient to act as the destination contract.
3. Freeze where a future `Go to structured query` first version should land.
4. Decide whether the product should first add a minimal structured-query panel or keep the current read-only label.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8d-structured-query-destination-discovery-2026-05-09.md`.
2. Discovery reconfirms that the current frontend still has no dedicated structured-query page, route, tab, or reusable component.
3. Discovery reconfirms that `GameProject.tsx` and `ragUiHelpers.ts` expose only read-only structured-query labels and warning copy.
4. Discovery confirms that `gameApi.query(...)` has no current visible call site in `console/src` and is therefore not a sufficient product destination by itself.
5. Discovery rejects both NumericWorkbench and IndexMap as the current structured-query destination because one is the mutation surface and the other is an index-browsing surface rather than a query-execution surface.
6. The recommended first explicit destination is a new minimal structured-query panel inside the existing GameProject surface.
7. The recommended current action is still docs-only: keep the read-only label and do not implement a `Go to structured query` button yet.
8. Any future structured-query destination must stay explicit-click only, must not auto-submit, must not auto-write test plans or candidates, and must not build or publish.
9. Destination-entry permission must remain separate from `knowledge.read`, and this slice does not require `knowledge.build` or `knowledge.publish`.
10. This slice adds no backend code, no frontend code, no router change, no request-schema change, no provider or model control, and no API expansion.

Acceptance:

1. The review confirms that no dedicated structured-query destination currently exists.
2. The review confirms that legacy `gameApi.query(...)` is not enough by itself.
3. The review keeps NumericWorkbench out of the structured-query destination role.
4. The review keeps IndexMap out of the structured-query destination role.
5. The review recommends defining a minimal structured-query panel before any frontend affordance implementation.
6. The review preserves the `{ query }` request boundary and all existing provider, router, and citation boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8e [S] Minimal Structured-Query Panel Contract Review

Depends on: P3.8d

Status as of 2026-05-09: completed as a docs-only contract review slice.

Tasks:

1. Freeze the first-version structured-query destination as an in-page GameProject panel.
2. Freeze first-version entry, prefill, submit, and result-display behavior.
3. Freeze the permission boundary for the future panel without changing backend code.
4. Judge whether the existing `gameApi.query(agentId, q, mode)` wrapper is already sufficient as a product-facing submit contract.

Implemented scope note:

1. The contract review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8e-structured-query-panel-contract-2026-05-09.md`.
2. The first-version structured-query destination is defined as a minimal panel inside the existing GameProject surface, not a new global route.
3. The first-version panel is limited to exact numeric, row-level, field-level, and value-level lookup only and explicitly excludes change or edit or modify intent.
4. A future `Open structured query` affordance is allowed only as explicit user click inside explicit structured-query warning contexts, and opening the panel must not auto-submit.
5. First-version prefill is allowed only as local input seeding from the current RAG query and must not auto-submit.
6. The first-version panel remains read-only and does not create test plans or candidates and does not build or publish.
7. The review records that the current `gameApi.query(...)` wrapper is not yet a sufficient product contract by itself because the current frontend lacks typed request or response models, documented mode semantics, and a frozen read-only result shape.
8. The review therefore defers direct submit binding to a later narrow API contract or typing review rather than a backend redesign.
9. The review keeps `knowledge.build` and `knowledge.publish` out of the panel-entry requirement and recommends a dedicated structured-query read capability rather than treating `knowledge.read` as the permanent destination-entry contract.
10. The review preserves the `{ query }` RAG payload boundary, adds no backend code, adds no frontend code, adds no provider or model control, and does not change `P3.8c` workbench affordance behavior.

Acceptance:

1. The review freezes the first-version destination as an in-page GameProject panel.
2. The review keeps the panel lookup-only and keeps mutation intent out.
3. The review allows future explicit open and optional prefill but forbids auto-submit.
4. The review keeps first-version results read-only and non-writing.
5. The review records the specific gap that blocks immediate direct adoption of `gameApi.query(...)` as a stable product contract.
6. The review preserves the `{ query }` request boundary and all existing provider, router, and citation boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8f [S] Structured-Query Submit Contract / Typing Review

Depends on: P3.8e

Status as of 2026-05-09: completed as a docs-only submit-contract and typing-review slice.

Tasks:

1. Freeze which backend endpoint the future minimal structured-query panel should submit to.
2. Freeze the first-version request contract and first-version mode strategy.
3. Freeze the frontend response typing or normalization contract needed for a read-only panel.
4. Freeze submit-side permission expectations without changing backend code.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8f-structured-query-submit-contract-2026-05-09.md`.
2. The review confirms that `gameApi.query(agentId, q, mode)` currently sends `POST /agents/{agentId}/game/index/query`.
3. The review confirms that the current backend request shape is only `q: string` plus `mode: string = "auto"`.
4. The review confirms that the current backend response shape is an untyped dict with top-level `mode` and `results` only.
5. The review confirms that current observed backend response branches are `not_configured`, `exact_table`, `exact_field`, and `semantic_stub`.
6. The review confirms that there is no stable backend enum or frontend type union for query mode today and that `auto` is the only mode with explicit backend logic.
7. The review freezes the first-version panel submit contract to query plus fixed `auto` mode only, with no provider, model, provider hint, service config, or write-oriented flags.
8. The review recommends a frontend typed wrapper or normalization layer over the existing endpoint instead of direct raw use of the current untyped `gameApi.query(...)` transport helper.
9. The review freezes a normalized read-only panel response contract with explicit request mode, result mode, status, message, warnings, items, and error fields, and with display items normalized into table-result and field-result variants.
10. The review keeps source-like display limited to already returned `source_path` and field `references` and does not authorize new citation artifact or raw-source endpoints.
11. The review keeps prefill allowed only as local input state and keeps submit explicit user click only.
12. The review keeps submit read-only and forbids test-plan creation, candidate creation, build, publish, or mutation behavior.
13. The review records that first-version permission may temporarily use `knowledge.read` as an interim read gate if no dedicated structured-query read capability exists yet, while still keeping `knowledge.build` and `knowledge.publish` out of scope and preserving dedicated structured-query read as the preferred long-term model.
14. The review preserves the `{ query }` RAG request boundary, does not change the RAG router, does not change provider selection, does not add real LLM integration, and does not change `P3.8c` workbench affordance behavior.

Acceptance:

1. The review freezes `/game/index/query` as the reuse target for the first-version panel submit path.
2. The review freezes first-version submit request fields to query plus fixed `auto` mode only.
3. The review records that current response shape is too loose for direct product use and therefore requires frontend normalization.
4. The review freezes a read-only normalized response typing contract for the future panel.
5. The review keeps submit explicit, read-only, and non-writing.
6. The review preserves the `{ query }` request boundary and all existing provider, router, and citation boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. Post-edit validation for this pass is limited to documentation error checking.

### P3.8g [F] Minimal Structured-Query Panel Implementation

Depends on: P3.8f

Status as of 2026-05-09: completed as a frontend-only implementation slice.

Tasks:

1. Add the first explicit `Open structured query` affordance only in explicit structured-query guardrail contexts.
2. Add the first in-page GameProject structured-query panel with explicit open and explicit submit.
3. Add the frontend typed wrapper and normalization layer over the existing `/game/index/query` endpoint.
4. Keep the first version read-only and preserve existing RAG, workbench, router, and provider boundaries.

Implemented scope note:

1. The implementation is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8g-minimal-structured-query-panel-closeout-2026-05-09.md`.
2. The static structured-query guardrail and the existing `STRUCTURED_FACT_WARNING` warning row now both expose `Open structured query`.
3. Opening the panel is user-triggered only, may prefill from the current RAG query only when the local panel draft is still empty, and does not auto-submit.
4. Submit remains user-triggered only, stays disabled until a `selectedAgent` exists, and sends only the panel query with fixed `auto` request mode to the existing `/game/index/query` endpoint.
5. The frontend now normalizes the returned response into explicit request mode, result mode, status, message, warnings, items, and error fields.
6. The first version keeps display read-only and limits normalized items to exact table-result and field-result variants only.
7. Source-like display remains limited to already returned `source_path`, `references`, and `tags` fields.
8. If capability context is absent, local trusted fallback remains intact.
9. If no `selectedAgent` exists, submit is disabled.
10. If capability context exists and `knowledge.read` is missing, both open and submit are disabled with `Requires knowledge.read permission.`.
11. This slice changes only `console/src` and `docs/tasks`, adds no backend API, changes no backend `src`, and does not change `P3.8c` workbench affordance behavior.

Acceptance:

1. The first explicit structured-query destination now exists inside GameProject as a minimal panel.
2. The panel is opened only by explicit click and never auto-submits.
3. Submit remains read-only and uses only query plus fixed `auto` mode.
4. The frontend no longer directly relies on the raw `/game/index/query` response shape in the UI.
5. The panel keeps mutation, candidate, build, publish, and workbench behavior out of scope.
6. The `{ query }` RAG boundary and all existing provider, router, and citation boundaries remain unchanged.

Validation note:

1. Editor diagnostics ran on the touched frontend files.
2. Frontend TypeScript no-emit validation ran.
3. Targeted ESLint ran on `GameProject.tsx`, `ragUiHelpers.ts`, and the new structured-query helper module.
4. `git diff --check` ran.
5. No frontend component test was run because no existing GameProject or RAG UI frontend test suite was found for this slice.
6. No backend pytest was run because this slice did not touch backend code.

### P3.8h [S] RAG MVP Interaction Validation / Closeout

Depends on: P3.8, P3.8b, P3.8c, P3.8f, P3.8g

Status as of 2026-05-09: completed as a validation-and-closeout slice.

Tasks:

1. Re-validate the current `P3.8` interaction surface against the frozen routing and submit boundaries.
2. Confirm that current frontend behavior remains explicit-click only and read-only where intended.
3. Confirm that permission-gated disabled behavior and local trusted fallback remain intact.
4. Record a closeout decision without adding new functionality.

Implemented scope note:

1. The validation closeout is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-8h-rag-mvp-interaction-validation-2026-05-09.md`.
2. Validation confirms that RAG Ask still sends only `{ query }`.
3. Validation confirms that `Open structured query` appears only in the static structured guardrail block and the `STRUCTURED_FACT_WARNING` warning row.
4. Validation confirms that opening structured query only opens the local panel and does not auto-submit.
5. Validation confirms that prefill remains local input-state only.
6. Validation confirms that structured-query submit remains fixed to `auto` mode and that normalized output remains read-only table-result or field-result display only.
7. Validation confirms that no test-plan, candidate, build, publish, or SVN behavior was added.
8. Validation confirms that `Go to workbench` appears only in the static workbench guardrail block and the `CHANGE_QUERY_WARNING` warning row.
9. Validation confirms that `Go to workbench` still navigates only to `/numeric-workbench` with no freeform-query handoff.
10. Validation confirms that explicit capability context missing `knowledge.read` disables Ask, `Open structured query`, and `Submit structured query`.
11. Validation confirms that explicit capability context missing `workbench.read` disables `Go to workbench`.
12. Validation confirms that capability-context absence keeps local trusted fallback intact.
13. This slice changes only `docs/tasks` and adds no backend or frontend behavior.

Acceptance:

1. The current `P3.8` interaction surface still satisfies the frozen routing and submit boundaries.
2. The current interaction surface remains explicit-click only and non-writing by default.
3. The current interaction surface preserves permission gating and local trusted fallback as intended.
4. The current interaction surface adds no backend change, no API, no request-schema expansion, and no provider or model control.
5. `P3.8` can be treated as closed from the MVP interaction perspective.

Validation note:

1. Frontend TypeScript no-emit validation ran.
2. Targeted ESLint ran on the actual interaction-surface frontend files.
3. `git diff --check` ran.
4. A minimal browser smoke was attempted and reached shell-load confirmation only; full in-app interaction smoke remained limited by local frontend-backend environment issues.
5. No backend pytest was run because this slice did not touch backend code.

I18n closeout note:

1. A frontend-only `P3.8` i18n closeout is now complete for the current RAG MVP interaction surface.
2. The i18n closeout covered visible copy for `Knowledge Q&A`, `Ask`, `insufficient_context`, `no_current_release`, citations, `Open structured query`, `Structured query panel`, `Go to workbench`, `Workbench flow`, and the `knowledge.read` / `workbench.read` permission hints.
3. The i18n closeout changed frontend copy surfaces only: `console/src/pages/Game/GameProject.tsx`, `console/src/pages/Game/ragUiHelpers.ts`, `console/src/locales/en.json`, and `console/src/locales/zh.json`.
4. The i18n closeout added no product-logic change, no backend change, no API change, no RAG schema change, no provider change, and no SVN change.
5. The i18n closeout validation passed JSON parse for `en.json` and `zh.json`, frontend TypeScript no-emit, targeted ESLint, `git diff --check`, and editor diagnostics.
6. Local 8088 static-page verification must rebuild `console` first and point `QWENPAW_CONSOLE_STATIC_DIR` at the latest `console/dist`; otherwise the page may still render an old bundle.

I18n runtime-fix closeout note:

1. The `P3.8` RAG MVP i18n runtime-fix is now complete for the latest static-bundle validation path.
2. The runtime-fix root cause was not the runtime language state and not a standalone `8088` old-bundle issue.
3. The actual root cause was that the `console` subproject had not been reliably producing the latest production `dist`, so the static page did not reliably load the newest bundle.
4. The runtime-fix round therefore closed the issue by explicitly rebuilding from the `console` directory and revalidating against the latest emitted `console/dist` bundle.
5. This runtime-fix round only patched missing locale keys in `console/src/locales/en.json` and `console/src/locales/zh.json`: `ragCitationsTitle`, `ragCitationsHint`, and `ragEmptyState`.
6. This runtime-fix round did not change product logic, backend code, API behavior, RAG schema, provider behavior, or SVN behavior.
7. Static verification must explicitly run a production build inside the `console` directory and then point `QWENPAW_CONSOLE_STATIC_DIR` to the latest `console/dist`; otherwise local static verification may still surface an older bundle or English fallback copy.
8. Latest-dist runtime revalidation on `8091` confirmed Chinese P3.8 copy for `知识问答`, `提问`, `示例问题`, `结构化查询面板`, `打开结构化查询`, `前往工作台`, and the Chinese RAG empty state.
9. Remaining English copy such as `Knowledge Release Status` and `Formal map review` is outside the scoped `P3.8` RAG i18n surface for this round and was intentionally left unchanged.

### P3.provider-credential-boundary-review [S] Provider Credential / Transport / Safety Boundary Review

Depends on: P3.rag-model-3, P3.8h

Status as of 2026-05-09: completed as a docs-only boundary review.

Tasks:

1. Freeze credential ownership and secret-source rules before any real external provider is connected.
2. Freeze provider or model selection boundaries without adding frontend provider control.
3. Freeze transport, timeout, retry, cost, token, logging, privacy, grounding, read, and failure boundaries.
4. Keep the current `{ query }` RAG request boundary and keep GameProject unchanged.
5. Keep real external provider integration out of scope.

Implemented scope note:

1. The review is recorded in `docs/tasks/knowledge/mvp/knowledge-p3-provider-credential-boundary-review-2026-05-09.md`.
2. Credentials are defined as backend-owned only and are explicitly disallowed from frontend request body, RAG query body, GameProject UI, or per-request provider config.
3. Server-side config remains allowed for backend-owned selection policy and non-secret provider settings.
4. Environment variables are not approved as live provider or model selection inputs in this slice and are allowed for future secret material only if a later implementation explicitly opts in under backend-owned startup-time constraints.
5. A future credential store is recommended before any non-trivial real-provider rollout, but is not implemented or required in this docs-only slice.
6. Provider and model selection remain backend-only and remain disallowed from frontend UI, request body, and `ProviderManager.active_model` in this slice.
7. A future backend allowlist is allowed and recommended for provider and model gating.
8. Any future external provider must remain a single injected model client behind the existing registry and answer-service boundaries.
9. Router still must not call provider code directly, and answer service still must consume only bounded context payload plus query.
10. Recommended first-version backend timeout is 15 seconds, with retry disabled by default because retry can amplify both latency and cost.
11. Future real-provider path must enforce backend-owned max chunks, max chars, output-token cap, and budget controls before rollout.
12. Logging rules remain conservative: API keys and raw secrets must never be logged, full query and full chunk logging should not be enabled by default, and redaction is required for sensitive fields.
13. Citation grounding remains unchanged: provider output citation ids must still validate only against `context.citations`, and invalid or empty provider output must degrade safely rather than fabricate an answer.
14. Provider client must not read raw source, pending state, SVN, `candidate_evidence`, or release artifacts directly.
15. Required failure cases include credential missing, provider disabled, provider timeout, provider HTTP error, invalid provider response, and cost or budget exceeded, and all must return safe warnings or `insufficient_context` where appropriate rather than fake grounded answer.
16. This slice does not modify `src/`, `console/src/`, request schema, router behavior, or frontend UI.
17. Real external provider integration remains unimplemented.

Acceptance:

1. The review freezes backend-owned credential and provider-selection boundaries before real provider rollout.
2. The review keeps Ask limited to `{ query }` and keeps GameProject free of provider or model UI.
3. The review keeps transport, timeout, retry, cost, privacy, grounding, read, and failure boundaries conservative.
4. The review does not implement a real provider, add a runtime provider, or add a new API.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. This docs-only pass does not run TypeScript.
4. Post-edit validation for this pass is limited to documentation error checking.

### P3.9 [P] Optional `table_facts.sqlite`

Depends on: P1.4

Tasks:

1. Build a lightweight SQLite fact index for precise reads.
2. Keep it release-owned.
3. Do not use vector search for row-level facts.

Acceptance:

1. Query by table + primary key works.
2. Query by field filter works for common scalar values.
3. Manifest records sqlite path and hash or build metadata.

### P3.10 [P] Release Rollback UX/API

Depends on: P1.7

Status as of 2026-05-10: completed.

Tasks:

1. List release history.
2. Set previous release as current.
3. Show current release and previous release.

Acceptance:

1. Admin can switch current release back to an older release.
2. Query immediately uses the restored current release.

Implemented scope note:

1. This slice is closed out in `docs/tasks/knowledge/mvp/knowledge-p3-10-release-rollback-closeout-2026-05-10.md`.
2. Backend adds a structured `GET /game/knowledge/releases/status` endpoint that returns `current`, `previous`, and `history` under the existing release router.
3. Release history now includes backend current marker state through `is_current` plus a narrow `label` field.
4. Previous release is derived as the first older available release after current in descending `(created_at, release_id)` history order.
5. Rollback still reuses the existing `POST /game/knowledge/releases/{release_id}/current` endpoint and still reuses the existing `set_current_release(...)` store path.
6. Rollback still only changes `releases/current.json` and does not rebuild, publish, mutate artifacts, mutate pending test plans, or mutate working formal map.
7. Current-release keyword query and RAG current-release context now have explicit rollback-following regression coverage.
8. The existing GameProject release panel now reads structured status, shows current and previous release, and exposes explicit rollback-to-previous UX with confirmation.
9. The frontend still adds no provider, model, or API key UI and does not enter build, publish, or RAG/provider configuration flows after rollback.
10. This slice does not continue external-provider work and keeps P20 frozen at P19 docs-only.

Validation note:

1. Focused backend validation passed in `50 passed in 1.90s` across release store, release router, RAG context, and current-release query router tests.
2. Frontend TypeScript no-emit passed through the local `node_modules/.bin/tsc` binary.
3. Targeted frontend ESLint passed through the local `node_modules/.bin/eslint` binary.
4. The `pnpm` wrapper path was blocked by workspace `approve-builds` enforcement, so frontend validation was run through local binaries instead.

Next-step note:

1. The next recommended slice is P3.11 permissions hardening, not external-provider P20.

### P3.11 [P] Permissions Hardening

Depends on: P1.7, P2.3, P3.2

Status as of 2026-05-10: completed.

Capability groups:

```text
knowledge.read
knowledge.build
knowledge.publish
knowledge.map.read
knowledge.map.edit
knowledge.candidate.read
knowledge.candidate.write
workbench.read
workbench.test.write
workbench.test.export
```

Compatibility or naming decision:

1. `knowledge.map.read` is retained as the final MVP map-review read capability.
2. It is not collapsed into `knowledge.read` in P3.11 because candidate-map and saved-formal-map review remain narrower governance-oriented read surfaces.
3. `knowledge.candidate.read` and `knowledge.candidate.write` are retained as the final MVP release-candidate capabilities.
4. They are not silently replaced by `workbench.candidate.mark` in P3.11 because the current backend already distinguishes candidate read from candidate write, and collapsing them would change semantics.
5. `workbench.candidate.mark` is therefore treated as not adopted in the current MVP capability vocabulary.
6. `workbench.test.export` is retained and now controls the existing workbench draft-export or proposal-create path.

Acceptance:

1. Build/publish/map edit are admin-only by default.
2. Workbench test flow can be granted without knowledge publish.
3. Read-only users cannot modify test plans, releases, formal map state, or release-candidate state.
4. General release, query, and RAG reads require `knowledge.read`.
5. Candidate-map and saved-formal-map reads require `knowledge.map.read`.
6. Release-candidate list and write routes remain on `knowledge.candidate.read` and `knowledge.candidate.write`.
7. Workbench draft export or proposal create requires `workbench.test.export`.
8. Local trusted fallback remains unchanged when no explicit capability context exists.

### P3.12 [R] P3 Review Gate

Status as of 2026-05-10: passed.

Checklist:

1. Map is editable through UX.
2. RAG reads current release only.
3. Precise values go through structured query.
4. Release rollback works.
5. Permission split is enforced.

Closeout note:

1. This review gate is closed out in `docs/tasks/knowledge/mvp/knowledge-p3-12-review-gate-closeout-2026-05-10.md`.
2. The current conservative interpretation of `Map is editable through UX` is saved-formal-map save plus saved-formal-map status editing in GameProject, not candidate-map editing and not relationship-editor scope.
3. Review confirmed that current-release RAG remains release-owned and current-pointer-driven only.
4. Review confirmed that precise value lookup remains routed to structured query through explicit `mode="auto"` submit rather than through the ordinary RAG entry.
5. Review confirmed that rollback remains a current-pointer switch only and that query plus RAG follow the restored release.
6. Review confirmed that the final MVP permission split remains enforced across release, map, candidate, workbench read or write, and workbench export surfaces.
7. This round found no new product blocker and made only a minimal documentation-drift correction in the earlier P3.11 closeout.
8. Focused review-gate regression passed in `68 passed in 1.98s` across release, map, current-release RAG, test plan, release candidate, and workbench export gate tests.
9. The final handover is recorded in `docs/tasks/knowledge/mvp/knowledge-p0-p3-mvp-final-handover-2026-05-10.md`.

### Post-MVP Scope Decision Review [S]

Status as of 2026-05-10: completed as a docs-only review.

Tasks:

1. Review the post-MVP baseline after `P3.12` closeout and final handover.
2. Evaluate post-MVP candidate routes without implementing code.
3. Decide whether `P20` should resume by default.
4. Name one recommended mainline plus 2-3 optional routes.
5. Provide a next-slice prompt seed with allowed scope, forbidden scope, validation, and reporting rules.

Implemented scope note:

1. This review is recorded in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-scope-decision-review-2026-05-10.md`.
2. The review confirms that `P0-P3` MVP is closed through `P3.12` and that external-provider remains frozen at `P3.external-provider-19`.
3. The review confirms that `P20` real HTTP transport must not continue by default.
4. The review evaluates `P20`, `P3.9 table_facts.sqlite`, relationship-editor or graph-governance UX, release packaging or final QA, provider admin/config boundary, and structured-query hardening.
5. The review recommends `release packaging / final QA / handoff hardening` as the next mainline rather than defaulting to `P20`.
6. The review names `structured query hardening`, `provider rollout admin/config boundary review`, and optional `P3.9 table_facts.sqlite` planning as the most reasonable follow-on alternatives.
7. The review keeps relationship editor, graph canvas, real provider rollout, and `P20` resume deferred unless a later dedicated slice explicitly reopens them.

Acceptance:

1. The review gives one explicit recommended mainline.
2. The review gives 2-3 optional routes and explains why they are not the default mainline.
3. The review explicitly states why `P20` is not the default next step.
4. The review preserves current permission, Ask-schema, provider-selection, and formal-knowledge/fast-test boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. This docs-only pass does not run TypeScript.
4. Post-edit validation for this slice is limited to `git diff --check`, touched-docs NUL check, and keyword review.

### Post-MVP Pilot Readiness Checklist / Final QA Plan [S]

Status as of 2026-05-10: completed as a docs-only planning and QA-checklist slice.

Tasks:

1. Re-check the current MVP runtime truth after P3.12 closeout and post-MVP scope decision review.
2. Define what pilot readiness means for the current local-first MVP.
3. Freeze the final manual QA checklist across environment, release, map, RAG, structured query, workbench, permissions, and recovery.
4. Freeze pilot readiness pass criteria without executing pytest or TypeScript in this round.
5. Provide the next-slice seed for actual pilot QA execution and handoff hardening.

Implemented scope note:

1. This review is recorded in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-pilot-readiness-checklist-2026-05-10.md`.
2. The review confirms that the current phase is pilot readiness rather than new feature development.
3. The review confirms that external-provider remains frozen at `P3.external-provider-19` and that `P20` real HTTP transport remains deferred.
4. The review confirms that `P3.9 table_facts.sqlite`, relationship editor, graph canvas, and real provider rollout are not pilot blockers.
5. The review defines pilot readiness as local startup plus release build, current-release query or RAG, structured query, conservative formal-map flow, NumericWorkbench fast-test flow, export draft proposal, rollback, permission clarity, and recovery clarity.
6. The review freezes a user-path QA checklist for environment or startup, release build or current release, formal knowledge or map, RAG or structured query, NumericWorkbench, permissions, and error or recovery.
7. The review freezes the pass criteria for the next execution round: manual critical-path QA, focused backend pytest, frontend TypeScript no-emit, targeted ESLint, static bundle smoke, docs or handover completeness, recovery clarity, and explicit non-enablement of `P20` or SVN integration.
8. The review recommends `Post-MVP Pilot QA Execution / Handoff Hardening` as the next slice and does not recommend `P20`, real provider rollout, relationship editor implementation, graph canvas implementation, or `table_facts` implementation as the next mainline.

Acceptance:

1. The review states clearly that pilot readiness is not production readiness.
2. The review states clearly what the current MVP must prove before pilot.
3. The review provides a path-based QA checklist rather than a broad wishlist.
4. The review provides explicit pilot pass criteria and explicit known limitations.
5. The review preserves Ask-schema, provider, map-governance, fast-test, and SVN boundaries.

Validation note:

1. This slice is docs-only.
2. This docs-only pass does not run pytest.
3. This docs-only pass does not run TypeScript.
4. Post-edit validation for this slice is limited to `git diff --check`, touched-docs NUL check, and keyword review.

### Post-MVP Pilot QA Execution / Handoff Hardening [S]

Status as of 2026-05-10: completed as an execution and closeout slice with no source-code blocker fix required.

Tasks:

1. Execute the focused backend regression required by the pilot-readiness checklist.
2. Execute frontend TypeScript, targeted ESLint, and production bundle validation.
3. Run a minimal isolated startup or browser smoke path without reopening deferred scope.
4. Judge whether any observed issue is a real pilot blocker.
5. Produce a pilot QA closeout and handoff record.

Implemented scope note:

1. This closeout is recorded in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-pilot-qa-closeout-2026-05-10.md`.
2. The execution round configured the repo-local Python environment and ran focused backend pytest for release, current-release query or RAG, map, test-plan, release-candidate, change-proposal, and capability-helper coverage.
3. The execution round ran frontend TypeScript no-emit, targeted ESLint, and production `console` build.
4. The execution round also ran an isolated `ltclaw init` plus `ltclaw doctor` plus `ltclaw app` smoke with `QWENPAW_CONSOLE_STATIC_DIR` pointed at the latest `console/dist`.
5. The browser smoke confirmed that GameProject and NumericWorkbench load, that rollback plus structured-query affordances render, that structured query remains explicit-open plus explicit-submit, and that workbench export remains a draft path rather than publish.
6. The isolated runtime reported safe degraded responses when `local project directory` was not configured, rather than exposing a crash or silent failure.
7. This round found no source-code pilot blocker, so no backend or frontend code was changed.

Acceptance:

1. Focused backend regression passes.
2. Frontend TypeScript passes and targeted ESLint has no error.
3. Production bundle builds and can be served from the latest `console/dist`.
4. The isolated smoke validates page load plus error-state clarity without reopening `P20`, real-provider rollout, or SVN integration.
5. The closeout makes clear which remaining items are operator-side environment prerequisites rather than product blockers.

Validation note:

1. This slice runs executable validation rather than docs-only checks.
2. The closeout records backend pytest `113 passed in 2.47s`.
3. The closeout records successful frontend TypeScript no-emit and production bundle build.
4. The closeout records targeted ESLint with warnings only and no error.

### Post-MVP Data-Backed Pilot Validation [S]

Status as of 2026-05-10: completed as an execution and closeout slice after two narrow configured-runtime blocker fixes.

Tasks:

1. Configure a real local project directory instead of relying on degraded smoke.
2. Generate current indexes from real local data.
3. Save a conservative formal map and use it to build at least one real knowledge release.
4. Validate current-release query, RAG, structured query, and rollback against real release data.
5. Validate NumericWorkbench draft export against real table data without collapsing it into publish.
6. Produce a data-backed pilot closeout record.

Implemented scope note:

1. This closeout is recorded in `docs/tasks/knowledge/pilot-validation/knowledge-post-mvp-data-backed-pilot-closeout-2026-05-10.md`.
2. The execution round used `/Users/Admin/CodeBuddy/20260501110222/test-data` as the real local project directory and generated current indexes from 8 real `.xlsx` tables.
3. The round fixed a configured-runtime `game/index/status` crash in `src/ltclaw_gy_x/game/retrieval.py`.
4. The round fixed current-index persistence so project-level build-from-current-indexes can read rebuilt artifacts in `src/ltclaw_gy_x/game/index_committer.py`.
5. The round saved a conservative formal map, built real releases `pilot-real-data-r1-direct` and `pilot-real-data-r2-api`, and validated set-current plus rollback.
6. The round validated current-release query, structured query, RAG context or answer, and NumericWorkbench draft export against that real data path.

Acceptance:

1. Real current indexes are generated from a real local project directory.
2. At least one real current knowledge release exists.
3. Current-release query, structured query, and RAG all return real release-backed data rather than degraded placeholders.
4. NumericWorkbench export remains draft-only and does not automatically enter the formal knowledge release.
5. The closeout distinguishes real pilot blockers from operator-side prerequisites and deferred scope.

Validation note:

1. This slice runs executable validation rather than docs-only checks.
2. `POST /game/index/rebuild` scanned 8 files and indexed 8 tables.
3. `GET /game/index/status` returned `configured=true` and `table_count=8` after the blocker fix.
4. `POST /game/knowledge/releases/build-from-current-indexes` succeeded after the current-index persistence fix.
5. Real current-release query, RAG context or answer, structured query, and NumericWorkbench draft dry-run all succeeded against the same real data set.

### Post-MVP Engineering Roadmap [S]

Status as of 2026-05-10: moved to a separate post-MVP planning document.

Active document:

1. `docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md`

Checklist status:

1. P0-P3 MVP remains closed and accepted.
2. This checklist should no longer carry detailed post-MVP execution plans.
3. New post-MVP implementation work should read the roadmap document above and create its own scoped closeout.
4. The current highest-value implementation lane is backend-only real LLM transport, but it must start as an explicit P20 slice and must not change Ask schema, expose provider or API-key UI, or claim production rollout.

---

## Historical P0-P3 Suggested Parallel Work Plan

This section is retained as historical execution context for the completed P0-P3 MVP. Do not use it as the active next-step plan after the post-MVP pilot closeouts. Use `docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md` for new work.

### Day 1 Morning

1. Engineer A: P0.2 path helpers.
2. Engineer B: P0.3 release/test plan models.
3. Engineer C: frontend terminology sweep P0.1.

Review gate: P0.4.

### Day 1 Afternoon

1. Engineer A: P1.1 release store.
2. Engineer B: P1.4 table schema export.
3. Engineer C: P1.7 release API skeleton.
4. Engineer D: P1.9 frontend release UX skeleton.

Review gate: release can be created from fixture data.

### Day 2

1. Engineer A: P1.8 current release query.
2. Engineer B: P1.5/P1.6 doc and script stub exports.
3. Engineer C: P2.1/P2.3 test plan store/API.
4. Engineer D: P2.4 test plan UX.

Review gate: full P1 release loop and basic test plan loop.

### Day 3+

1. P2.5/P2.6 candidate selection.
2. P3.3 answer-adapter boundary review.
3. P3.4 minimal answer-service skeleton.
4. P3.5/P3.6 map candidate and map API.
5. P3.8 RAG router.
6. P3.10/P3.11 rollback and permission hardening.

---

## Non-Goals Until After P3

1. SVN update or commit integration.
2. Multi-user distribution of release assets.
3. Enterprise audit workflow.
4. Full vector database migration.
5. Raw document mirroring inside release.
6. Automatic inclusion of workbench test changes.
7. Large refactor of all existing `game/*` SVN names.

---

## Final Acceptance For P0-P3

The implementation is successful when:

1. Admin can build a local knowledge release from local project resources.
2. Current release can be switched and rolled back.
3. Knowledge query reads current release only.
4. Numeric planner can edit values, preview, save a test plan, export/upload for engine test, and discard.
5. Test plans never enter formal knowledge by default.
6. Admin can optionally include selected verified release candidates during release build.
7. Existing game index and workbench APIs remain compatible.
8. User-facing UX no longer presents P1 as SVN-driven.

Final closeout note:

1. P0-P3 MVP final handover is recorded in `docs/tasks/knowledge/mvp/knowledge-p0-p3-mvp-final-handover-2026-05-10.md`.
2. P3.12 passed and closes the current P0-P3 MVP mainline.
3. External-provider remains frozen at `P3.external-provider-19`; `P20` is deferred until a new explicit scoped slice is opened.
4. `P3.9 table_facts.sqlite`, relationship editor, graph canvas, and real provider rollout remain optional or deferred and are not blockers for this MVP acceptance.
