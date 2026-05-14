# P0-04 Build Readiness + Candidate Map

## 目标

系统能判断 cold start 构建是否 ready，并能从 canonical facts 生成 Candidate Map。

## 允许

- 新增或完善 `GET /game/knowledge/map/build-readiness`。
- 增强 `POST /game/knowledge/map/candidate/from-source` 的 diagnostics。
- Candidate 成功时返回 candidate count 和 refs。
- 补后端窄测。

## 禁止

- Candidate Map 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish / Set Current。
- 不读取 KB/retrieval/session draft/workbench dirty state。
- 不调用 LLM。

## Build Readiness 返回字段

必须返回：

- `project_root`
- `project_bundle_root`
- `source_config_exists`
- `tables_config_exists`
- `discovered_table_count`
- `raw_table_index_count`
- `canonical_table_count`
- `has_formal_map`
- `has_current_release`
- `blocking_reason`
- `next_action`
- `raw_tables_dir`
- `canonical_tables_dir`
- `candidate_read_dir`
- `same_project_bundle`

`blocking_reason` 只允许这些语义：

```text
project_root_missing
tables_source_missing
no_table_sources_found
no_raw_indexes
no_canonical_facts
candidate_ready
formal_map_missing
release_missing
ready
path_mismatch
```

## Candidate diagnostics

无 canonical facts 时必须返回 diagnostics：

- `raw_table_index_count`
- `canonical_table_count`
- `canonical_tables_dir`
- `blocking_reason`
- `next_action`

成功时必须返回：

- `candidate_table_count`
- `candidate_refs`

## 验收

- 无 project root -> `project_root_missing`。
- 有表但无 raw index -> `no_raw_indexes`。
- 有 raw index 无 canonical -> `no_canonical_facts`。
- 有 canonical -> `candidate_ready`。
- 目录不一致 -> `path_mismatch`。
- canonical 有 1 张表时 candidate map 有 `table:HeroTable`。
- Candidate Map 不自动保存 Formal Map / Build Release / Publish Current。

