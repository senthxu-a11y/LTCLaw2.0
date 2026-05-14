# P0-03 Canonical Facts Rebuild

## 目标

Raw TableIndex 生成后，能 rule-only 生成 CanonicalTableSchema。

## 允许

- 新增或完善 `canonical_facts_committer.py`。
- 新增或完善 `POST /game/knowledge/canonical/rebuild`。
- 读取 raw table indexes。
- 调用已有 `build_canonical_table_schema(table_index)`。
- 写入 `get_project_canonical_table_schema_path(project_root, table_id)`。
- 使用 atomic write。
- 补后端窄测。

## 禁止

- 不调用 LLM。
- 不生成 Candidate Map。
- 不保存 Formal Map。
- 不 Build Release。
- 不 Publish / Set Current。
- 不接入 KB/retrieval。

## 请求

```json
{
  "scope": "tables",
  "rule_only": true,
  "force": false
}
```

## 返回合同

必须返回：

- `success`
- `raw_table_index_count`
- `canonical_table_count`
- `written[]`
- `errors[]`
- `warnings[]`
- `next_action=build_candidate_from_source`

## 验收

- HeroTable raw index 能生成 HeroTable canonical。
- 关闭模型配置仍然成功。
- `canonical_table_count=1`。
- canonical 文件路径正确。
- JSON 可被 `CanonicalTableSchema.model_validate()` 读取。
- primary key semantic_type 为 `id`。
- source 为 `raw_index_rule`。

