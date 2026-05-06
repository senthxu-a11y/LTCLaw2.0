# Knowledge Workbench P0-P3 Implementation Checklist

> Date: 2026-05-06
> Scope: Game planner knowledge workbench, local-first knowledge releases, numeric workbench test plans
> Source plans:
> - `docs/plans/knowledge-architecture-handover-2026-05-06.md`
> - `docs/plans/knowledge-p1-local-first-scope-2026-05-06.md`

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

### P1.8 [S] Add Current Release Query API

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

### P1.9 [P] Frontend Minimal Release UX

Depends on: P1.7 API shape

Tasks:

1. Add or adapt page section for release status.
2. Show current release id, build time, counts.
3. Provide build release button for admin.
4. Provide set-current action if multiple releases exist.

Likely files:

1. `console/src/api/modules/gameKnowledgeRelease.ts`
2. `console/src/api/types/game.ts`
3. Existing game project or knowledge pages under `console/src/pages/**`

Acceptance:

1. Admin can build and switch release from UI.
2. Normal user does not see scan/map/build controls unless already authorized.
3. UI copy says "knowledge release", not "SVN sync".

### P1.10 [R] P1 Review Gate

Checklist:

1. A local project directory can produce a release.
2. `current.json` points to that release.
3. Query reads current release.
4. Raw source resources are not copied into release.
5. Existing `/game/index/*` still works as before.

---

## P2. Numeric Workbench Test Plans And Release Candidates

Goal: separate fast numeric testing from formal knowledge release.

### P2.1 [S] Add Test Plan Store

Depends on: P0.2, P0.3

Tasks:

1. Store workbench test plans in app-owned pending storage.
2. Use JSONL for P2.
3. Do not require administrator acceptance.

Likely new file:

1. `src/ltclaw_gy_x/game/test_plan_store.py`

Minimum operations:

```text
create_test_plan
list_test_plans
get_test_plan
update_test_plan_status
delete_or_discard_test_plan
mark_release_candidate
list_release_candidates
```

Acceptance:

1. Users can save test plans without touching release assets.
2. Test plan statuses are `draft`, `testing`, `kept`, `discarded`.
3. Release candidate is separate from ordinary test plan state.

### P2.2 [P] Convert Workbench Patch Shape To Test Plan Shape

Depends on: P2.1

Tasks:

1. Keep existing `ChangeOp` usable internally.
2. Add wrapper shape for `WorkbenchTestPlan`.
3. Preserve before/after, table, primary key, field, source path.
4. Add optional engine test reference.

Likely files:

1. `src/ltclaw_gy_x/game/change_proposal.py`
2. `src/ltclaw_gy_x/app/routers/game_workbench.py`
3. `console/src/api/modules/gameWorkbench.ts`
4. `console/src/pages/Game/NumericWorkbench.tsx`

Acceptance:

1. Existing preview API still works.
2. New save-test-plan action can persist current pending edits.
3. No API says `accepted` or `rejected` for normal test flow.

### P2.3 [P] Add Test Plan API

Depends on: P2.1

Endpoint prefix:

```text
/game/workbench/test-plans
```

Endpoints:

```text
POST /game/workbench/test-plans
GET  /game/workbench/test-plans
GET  /game/workbench/test-plans/{id}
PATCH /game/workbench/test-plans/{id}
POST /game/workbench/test-plans/{id}/discard
POST /game/workbench/test-plans/{id}/mark-release-candidate
GET  /game/workbench/release-candidates
```

Acceptance:

1. Numeric planner can save, keep, discard, and mark release candidate.
2. Marking release candidate does not alter current knowledge release.
3. API does not require maintainer role for ordinary save/test/discard.
4. Candidate inclusion remains admin-only during release build.

### P2.4 [P] Frontend Test Plan UX

Depends on: P2.3 API shape

Tasks:

1. Add save test plan action in numeric workbench.
2. Add test plan list or drawer.
3. Add statuses: draft, testing, kept, discarded.
4. Add "mark as release candidate" only for kept or verified plans.
5. Make copy clear: "This does not update the knowledge release."

Likely files:

1. `console/src/pages/**/NumericWorkbench*`
2. `console/src/api/modules/gameWorkbench.ts`
3. `console/src/api/types/game.ts`

Repository-confirmed files:

1. `console/src/pages/Game/NumericWorkbench.tsx`
2. `console/src/pages/Game/NumericWorkbench.module.less`
3. `console/src/pages/Game/components/DirtyList.tsx`
4. `console/src/pages/Game/components/ImpactPanel.tsx`

Acceptance:

1. User can test quickly without seeing admin approval language.
2. User can discard a test plan.
3. Candidate marking is visible but not confused with publish.

### P2.5 [S] Release Build Candidate Selection

Depends on: P1.7, P2.1

Tasks:

1. Extend release build request to accept candidate ids.
2. Default candidate list is empty.
3. Include selected candidates in manifest build metadata.
4. Apply selected candidates only to derived release indexes, not source files.

Important rule:

```text
No selected candidates -> release is built from current local project resources only.
```

Acceptance:

1. Admin can build release with zero candidates.
2. Admin can build release with selected candidates.
3. Selected candidates are recorded in `manifest.json`.
4. Ordinary test plans are excluded by default.

### P2.6 [P] Frontend Release Candidate Selection UX

Depends on: P2.5 API shape

Tasks:

1. On release build page, show verified release candidates.
2. Default all candidates unchecked.
3. Show table, primary key, field, before/after, test note.
4. Let admin choose candidates for this release.

Acceptance:

1. Build page makes it clear candidates are optional.
2. Normal users do not see release build controls.

### P2.7 [R] P2 Review Gate

Checklist:

1. Numeric workbench fast-test loop does not require admin.
2. Test plans persist outside release directories.
3. Release build can optionally include selected candidates.
4. Existing workbench preview and query still work.

---

## P3. Map Governance, RAG Routing, And Hardening

Goal: make releases useful and safer without changing the P1/P2 boundaries.

### P3.1 [S] Map Candidate Builder

Depends on: P1.3, P1.4

Tasks:

1. Generate a basic map candidate from table schema, docs, and scripts.
2. Use path rules and system hints first.
3. Use LLM only as an enhancement, with deterministic fallback.

Likely files:

1. New `src/ltclaw_gy_x/game/map_builder.py`
2. Existing `src/ltclaw_gy_x/game/dependency_resolver.py`

Acceptance:

1. Candidate map can be generated without LLM.
2. LLM failure does not block release build.
3. Candidate objects include confidence/source.

### P3.2 [P] Map Review API

Depends on: P3.1

Endpoints:

```text
GET  /game/knowledge/map/candidate
POST /game/knowledge/map/candidate/rebuild
GET  /game/knowledge/map
PUT  /game/knowledge/map
```

Acceptance:

1. Admin can inspect current candidate.
2. Admin can save formal map.
3. Release build uses formal map when present.

### P3.3 [P] Map Review UX

Depends on: P3.2 API shape

Tasks:

1. Candidate inbox.
2. System map view.
3. Actions: accept, change system, mark deprecated, ignore.
4. Avoid raw JSON editing as primary UX.

Acceptance:

1. Admin can classify resources without editing JSON.
2. Formal map changes are visible before release build.

### P3.4 [S] RAG Router Over Current Release

Depends on: P1.8, P3.2

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

### P3.5 [P] Optional `table_facts.sqlite`

Depends on: P1.4

Tasks:

1. Build a lightweight SQLite fact index for precise reads.
2. Keep it release-owned.
3. Do not use vector search for row-level facts.

Acceptance:

1. Query by table + primary key works.
2. Query by field filter works for common scalar values.
3. Manifest records sqlite path and hash or build metadata.

### P3.6 [P] Release Rollback UX/API

Depends on: P1.7

Tasks:

1. List release history.
2. Set previous release as current.
3. Show current release and previous release.

Acceptance:

1. Admin can switch current release back to an older release.
2. Query immediately uses the restored current release.

### P3.7 [P] Permissions Hardening

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

### P3.8 [R] P3 Review Gate

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
2. P3.1/P3.2 map candidate and map API.
3. P3.4 RAG router.
4. P3.6 rollback.
5. P3.7 permission hardening.

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
