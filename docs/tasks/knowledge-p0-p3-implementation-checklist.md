# Knowledge Workbench P0-P3 Implementation Checklist

> Date: 2026-05-06
> Scope: Game planner knowledge workbench, local-first knowledge releases, numeric workbench test plans

Source plans:

- `docs/plans/knowledge-architecture-handover-2026-05-06.md`
- `docs/plans/knowledge-p1-local-first-scope-2026-05-06.md`

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
Follow docs/tasks/knowledge-p0-p3-implementation-checklist.md exactly.
Implement only the requested phase or task range.
Preserve existing /game/index, /game/workbench, and /game-knowledge-base compatibility.
Do not add SVN credential, commit, login, password, or URL handling.
Prefer additive modules and avoid SVN hot-path files unless necessary.
Run relevant checks and stop at the review gate with a concise status report.
```

Recommended first prompt for GPT-5.4:

```text
请先完整阅读 docs/tasks/knowledge-p0-p3-implementation-checklist.md，以及它引用的两份 source plans。
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

1. The boundary review is recorded in `docs/tasks/knowledge-p1-9b-build-ux-boundary-review-2026-05-07.md`.
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
4. This boundary is reviewed in `docs/tasks/knowledge-p1-9c-review-gate-2026-05-07.md`.

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

1. The review is recorded in `docs/tasks/knowledge-p2-4-candidate-release-inclusion-review-2026-05-07.md`.
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

1. The review is recorded in `docs/tasks/knowledge-p3-1-rag-read-boundary-review-2026-05-07.md`.
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

1. The review is recorded in `docs/tasks/knowledge-p3-3-rag-answer-adapter-boundary-review-2026-05-07.md`.
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

1. The review is recorded in `docs/tasks/knowledge-p3-7a-formal-map-read-save-boundary-review-2026-05-07.md`.
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

1. Safe-build formal-map consumption is not implemented yet.
2. Formal map review UX is not implemented yet.
3. Frontend exposure should wait until role-gating for formal map writes is decided.

### P3.7b+ [P] Safe-Build Formal Map Consumption Boundary

Depends on: P3.7b backend store/API validation

Status as of 2026-05-07: next recommended construction slice.

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

### P3.7c [P] Map Review UX

Depends on: P3.7b API shape, P3.7b+ safe-build consumption rule

Tasks:

1. Candidate inbox.
2. System map view.
3. Actions: accept, change system, mark deprecated, ignore.
4. Avoid raw JSON editing as primary UX.

Acceptance:

1. Admin can classify resources without editing JSON.
2. Formal map changes are visible before release build.

Next-step note:

1. The next recommended follow-up is P3.7b+ safe-build formal-map consumption.
2. After P3.7b+ is locked, design or implement UI on top of that boundary.
3. The key open rule is whether the next safe build should prefer `working/formal_map.json` and how that saved formal map should be snapshotted into `release/map.json`.

### P3.8 [S] RAG Router Over Current Release

Depends on: P1.8, P3.2, P3.4

Tasks:

1. Route explanation/relationship queries to release JSONL + lightweight search.
2. Route precise value queries to structured query path.
3. Route modification intents to workbench path.

Decision examples:

```text
"How does skill damage work?" -> knowledge query
"What is SkillTable 1029 damage?" -> structured query
"Change 1029 damage to 120" -> workbench test plan flow
```

Acceptance:

1. RAG does not answer precise values from semantic chunks when structured path is available.
2. All knowledge answers include release id and source path.
3. Ambiguous requests ask user to choose view or route.

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

Tasks:

1. List release history.
2. Set previous release as current.
3. Show current release and previous release.

Acceptance:

1. Admin can switch current release back to an older release.
2. Query immediately uses the restored current release.

### P3.11 [P] Permissions Hardening

Depends on: P1.7, P2.3, P3.2

Capability groups:

```text
knowledge.read
knowledge.build
knowledge.publish
knowledge.map.edit
workbench.read
workbench.test.write
workbench.test.export
workbench.candidate.mark
```

Acceptance:

1. Build/publish/map edit are admin-only by default.
2. Workbench test flow can be granted without knowledge publish.
3. Read-only users cannot modify test plans or releases.

### P3.12 [R] P3 Review Gate

Checklist:

1. Map is editable through UX.
2. RAG reads current release only.
3. Precise values go through structured query.
4. Release rollback works.
5. Permission split is enforced.

---

## Suggested Parallel Work Plan

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
