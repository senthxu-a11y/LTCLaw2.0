# P0-01 Source Discovery

## 目标

用户配置 project root 和 tables source 后，系统能立即扫描并告诉用户找到了哪些表文件。

## 允许

- 新增或完善 `POST /game/project/sources/discover`。
- 从 project root + tables config 扫描文件。
- 支持 include/exclude patterns。
- 支持 csv/xlsx/txt。
- 将 xls 标记为 unsupported。
- 补后端窄测。

## 禁止

- 不生成 Raw Index。
- 不生成 Canonical Facts。
- 不生成 Candidate Map。
- 不修改 Formal Map、Release、RAG。
- 不接入 KB/retrieval。

## 返回合同

必须返回：

- `success`
- `project_root`
- `table_files[]`
  - `source_path`
  - `format`
  - `status`
  - `reason`
- `excluded_files[]`
- `unsupported_files[]`
- `errors[]`
- `summary.discovered_table_count`
- `summary.available_table_count`
- `summary.excluded_table_count`
- `summary.unsupported_table_count`
- `summary.error_count`
- `next_action`

没找到可用表时：

```text
next_action=configure_tables_source
```

找到表时：

```text
next_action=run_raw_index
```

## 验收

- `examples/minimal_project` 能发现 1 张 `Tables/HeroTable.csv`。
- `~$Temp.xlsx` 被 excluded。
- `OldTable.xls` 被 unsupported。
- include 不匹配时 discovered count 为 0 且 next_action 明确。
- 中文路径可以扫描。

