# P0-00 Minimal Sample + Project Setup API

## 目标

建立 cold start 的最小样例，并提供 Project Setup 后端状态与配置接口。此切片只处理项目根目录和表源配置，不执行 discovery/raw/canonical/candidate 构建。

## 允许

- 新增 `examples/minimal_project/Tables/HeroTable.csv`。
- 新增或完善 `GET /game/project/setup-status`。
- 新增或完善 `PUT /game/project/root`。
- 新增或完善 `PUT /game/project/sources/tables`。
- 使用现有 project bundle/path helper。
- 将表源配置保存到 project bundle 下的 source/tables 配置文件。
- 补后端窄测。

## 禁止

- 不做 Source Discovery 实际扫描接口。
- 不做 Raw Index rebuild。
- 不做 Canonical Facts rebuild。
- 不做 Candidate Map 构建。
- 不做前端页面。
- 不引入 SVN Root 作为主配置。
- 不接入 LLM、KB、retrieval。

## 接口合同

### `GET /game/project/setup-status`

必须返回：

- `project_root`
- `project_root_exists`
- `project_bundle_root`
- `project_key`
- `tables_config.roots`
- `tables_config.include`
- `tables_config.exclude`
- `tables_config.header_row`
- `tables_config.primary_key_candidates`
- `discovery.discovered_table_count`
- `discovery.unsupported_table_count`
- `discovery.excluded_table_count`
- `discovery.error_count`
- `build_readiness.blocking_reason`
- `build_readiness.next_action`

默认 include 至少包含：

```text
**/*.csv
**/*.xlsx
**/*.txt
```

### `PUT /game/project/root`

请求：

```json
{ "project_root": "..." }
```

校验：

- 非空。
- 必须是本地路径。
- 拒绝 `svn://`、`http://`、`https://`。
- 路径必须存在。

返回：

- `project_key`
- `project_bundle_root`
- 最新 `setup_status`

### `PUT /game/project/sources/tables`

请求字段：

- `roots`
- `include`
- `exclude`
- `header_row`
- `primary_key_candidates`

校验：

- `header_row >= 1`
- `roots` 不能为空
- include/exclude 按列表保存

返回：

- `effective_config`
- 最新 `setup_status`

## 验收

- minimal sample 文件存在且内容为 `ID,Name,HP,Attack` / `1,HeroA,100,20`。
- 新项目 root 保存后返回 project key 和 bundle root。
- table config 保存后能再次从 setup status 读出。
- 默认 include 包含 csv/xlsx/txt。
- 非本地 URL 被拒绝。
- header_row 小于 1 被拒绝。

