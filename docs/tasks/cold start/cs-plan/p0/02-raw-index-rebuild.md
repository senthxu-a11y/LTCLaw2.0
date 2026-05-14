# P0-02 Raw Index Rebuild

## 目标

Source Discovery 找到表后，能 rule-only 生成 Raw TableIndex。

## 允许

- 新增或暴露 `POST /game/knowledge/raw-index/rebuild`。
- 支持 `scope=tables`。
- 使用 Source Discovery 的可用表文件。
- 生成 TableIndex。
- 写入 project bundle 下 raw table index 文件。
- 补后端窄测。

## 禁止

- 不生成 Canonical Facts。
- 不生成 Candidate Map。
- 不调用 LLM。
- 不修改 Formal Map、Release、RAG。
- 不接入 KB/retrieval。

## 请求

```json
{
  "scope": "tables",
  "rule_only": true
}
```

## 返回合同

必须返回：

- `success`
- `raw_table_index_count`
- `indexed_tables[]`
  - `table_id`
  - `source_path`
  - `row_count`
  - `field_count`
  - `primary_key`
- `errors[]`
- `next_action=run_canonical_rebuild`

## 验收

- HeroTable.csv 生成 1 个 TableIndex。
- `row_count=1`。
- `field_count=4`。
- `primary_key=ID`。
- 输出目录存在 table index 文件。
- CSV UTF-8 和 UTF-8 BOM 可读。
- 空表头、空文件、错误 header_row 返回文件级错误。
- 单表失败不阻断其他表。

