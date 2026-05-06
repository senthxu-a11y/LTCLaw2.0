# Knowledge P1 Local-First Scope Decision

> Date: 2026-05-06
> Scope: Game planner knowledge workbench / RAG / structured data workbench
> Purpose: Capture the latest scope reduction before continuing on another machine.

---

## 1. Decision Summary

P1 should not treat SVN as part of the core architecture.

The first stage should be local-first:

1. Read local project resources.
2. Generate derived knowledge assets.
3. Let the application query and use those derived assets.
4. Keep original project files outside the knowledge publishing flow.

In P1, the administrator is not a source-file publisher. The administrator is only a knowledge-asset builder.

One-line rule:

> P1 does not write back to SVN, does not upload original resources, and does not auto-sync project files. It only reads local project resources and produces versioned knowledge assets.

---

## 2. Why This Reduces Complexity

The previous architecture still carried too much implicit SVN weight:

1. SVN credentials.
2. Working-copy state.
3. Conflict handling.
4. Polling or auto-sync behavior.
5. Commit permissions.
6. Generated index assets mixed with project source files.
7. User confusion between "sync source project" and "sync knowledge release".

Removing SVN from P1 makes the system boundary much cleaner:

```text
Local project resources
   -> scan
   -> map
   -> indexes
   -> vectors
   -> release assets
   -> query / workbench usage
```

SVN can return later as a resource-pull adapter:

```text
svn update -> refresh local project directory
```

It should not participate in:

1. Knowledge governance rules.
2. Release semantics.
3. RAG routing.
4. Structured query logic.
5. Workbench patch logic.

---

## 3. Administrator Boundary

In P1, the administrator can:

1. Select a local project root.
2. Configure table, document, and script directories.
3. Scan local resources.
4. Generate a map candidate.
5. Review and confirm the map.
6. Build indexes.
7. Build or refresh vector assets.
8. Generate a local knowledge release.
9. Switch the current release version.

The administrator cannot:

1. Upload original source tables.
2. Upload original design documents.
3. Upload original scripts.
4. Commit to SVN.
5. Modify the source repository through the knowledge publishing flow.
6. Publish unreviewed candidate assets as formal knowledge.

This means the administrator manages derived assets, not project source files.

---

## 4. Asset Boundary

P1 should separate source resources from generated knowledge assets.

Source resources are read-only inputs:

```text
project_root/
  Tables/
  Docs/
  Scripts/
```

Generated knowledge assets are application-owned outputs:

```text
.knowledge_workbench/
  working/
    map_candidate.json
    scan_snapshot.json
    build_logs/
  releases/
    v2026.05.06.001/
      manifest.json
      map.json
      indexes/
        table_schema.jsonl
        table_facts.sqlite
        doc_knowledge.jsonl
        script_evidence.jsonl
      vectors/
      release_notes.md
    current.json
  pending/
    patches.jsonl
```

The release directory should not contain:

1. Raw xlsx/csv source tables.
2. Raw design documents.
3. Raw scripts.
4. SVN metadata.
5. Unreviewed map candidates.
6. Temporary workbench edits.

---

## 5. P1 MVP Loop

The smallest useful P1 loop is:

```text
1. Select local project directory.
2. Scan tables, documents, and scripts.
3. Generate map draft.
4. Administrator confirms map.
5. Build release assets.
6. Query current release.
7. Use workbench for precise table operations.
8. Create pending patch for modifications.
```

This loop intentionally excludes:

1. SVN update.
2. SVN commit.
3. Multi-user distribution.
4. Auto polling.
5. Incremental publishing.
6. Enterprise permission model.
7. Full audit workflow.

---

## 6. Query Boundary

P1 still keeps the core split:

```text
Explanation and relationships -> map route + RAG
Precise values and modifications -> structured query + structured patch
```

RAG should read from the current release only.

Structured queries may need an explicit view selection:

1. `published_view`: query facts from the current release.
2. `working_view`: query current local source resources.
3. `pending_changes_view`: inspect pending patches.

This prevents confusion such as:

> I just changed a value in the workbench. Why does the published knowledge query not show it?

The answer is:

> Because P1 separates working data from published knowledge assets. A workbench change enters pending patches first, then can be included in a future release after review.

---

## 7. Workbench Boundary

The workbench can read local source resources and produce structured pending patches.

The workbench should not directly mutate the published knowledge release.

Recommended P1 patch shape:

```json
{
  "id": "patch_001",
  "status": "pending",
  "operation": "update_cell",
  "table": "SkillTable",
  "primary_key": {
    "field": "id",
    "value": "1029"
  },
  "field": "damage",
  "before": "100",
  "after": "120",
  "source_path": "Tables/SkillTable.xlsx",
  "created_by": "user",
  "created_at": "2026-05-06T00:00:00Z"
}
```

Patch status should stay minimal in P1:

1. `pending`
2. `accepted`
3. `rejected`

Accepted patches can be considered during the next build, but the first implementation can keep this manual.

---

## 8. Implementation Priority

To keep the difficulty curve flat, implement in this order:

1. Local project configuration.
2. Release directory and `manifest.json`.
3. Minimal `map.json` schema.
4. Table schema index.
5. Document knowledge index.
6. Simple published-query API.
7. Pending patch queue.
8. RAG over current release.
9. Optional table fact index.

Do not start with SVN integration.

Do not start with multi-user release distribution.

Do not start with a full vector database if keyword or local JSONL search is enough to validate the workflow.

---

## 9. Relationship With LTClaw

For now, LTClaw can remain the host shell.

But new core concepts should be designed as if they can become independent later:

```text
agentId -> projectId
agent workspace -> project workspace
game_index -> knowledge release store
SVN sync -> optional resource pull adapter
```

The product kernel is no longer "an LTClaw agent feature".

It is becoming:

```text
Game planner knowledge workbench
```

LTClaw is useful as a temporary host, not as the long-term domain model.

---

## 10. Next Handoff Note

When continuing on another machine, keep this rule in front:

> First prove the local-first knowledge asset loop. SVN can wait.

The next concrete artifacts to design are:

1. `manifest.json`
2. `map.json`
3. `table_schema.jsonl`
4. `doc_knowledge.jsonl`
5. `patches.jsonl`

Once these are stable, RAG and structured query become much easier to implement safely.
