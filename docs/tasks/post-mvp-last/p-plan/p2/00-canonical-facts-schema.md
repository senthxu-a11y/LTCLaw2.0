# P2-00 Canonical Facts / Canonical Schema 层

来源：总规划书 Phase 5、3.3、5。

## 目标

P2-00 在 Raw Index 和 Map 之间补一层稳定的规范化事实模型，用于后续逐步接入 Candidate Map、Release 输入与更稳的结构化语义治理。

本轮边界如下：

- 只定义 Canonical Table Schema、Canonical Doc Facts、Canonical Script Facts 的数据结构与路径规范。
- 只实现从 Raw Index 派生初始草案的 deterministic 规则转换。
- 不接入 Map Candidate 主流程。
- 不改 Release / RAG / Workbench 主链路。
- 不做管理员 UI。

## 数据结构

### Canonical Table Schema

- `schema_version = canonical-table-schema.v1`
- `table_id`
- `source_path`
- `source_hash`
- `primary_key`
- `fields`
- `updated_at`

### Canonical Field

- `raw_header`
- `canonical_header`
- `aliases`
- `semantic_type`
- `description`
- `confidence`
- `confirmed`
- `source`
- `raw_type` 可选

### Canonical Doc Facts

- `schema_version = canonical-doc-facts.v1`
- `doc_id`
- `source_path`
- `source_hash`
- `title`
- `summary`
- `semantic_tags`
- `related_refs`
- `confidence`
- `confirmed`

### Canonical Script Facts

- `schema_version = canonical-script-facts.v1`
- `script_id`
- `source_path`
- `source_hash`
- `symbols`
- `responsibilities`
- `related_refs`
- `confidence`
- `confirmed`

## Raw Table Index 与 Canonical Table Schema 的区别

- Raw Table Index 负责文件可读性、编码识别、解析、header row、空列裁剪、基础类型推断、source_hash 等 rule layer 职责。
- Canonical Table Schema 负责在 Raw Table Index 之上形成稳定、可复用、可逐步人工修订的字段语义草案。
- 当前 Workbench 行定位仍继续使用 `TableIndex`；P2-00 不删除 `TableIndex`，也不改变现有兼容逻辑。

## 规则转换

Canonical Schema 从 `TableIndex` 派生初始草案的规则如下：

- `raw_header = FieldInfo.name`
- `canonical_header` 使用 deterministic 规则归一化：
	- trim
	- CamelCase 拆词
	- 空格、横线、斜杠归一到 `_`
	- 非字母数字字符清理
	- 多个 `_` 折叠
	- 全部转小写
- `aliases` 至少包含 raw header；若 raw header 与 canonical header 不同，则二者都保留
- `semantic_type` 由基础规则初判：`id`、`reference`、`number`、`text`、`bool`、`list`、`unknown`
- `description` 复用 `FieldInfo.description`
- `confidence` 从 `FieldConfidence` 做 deterministic 映射：
	- `confirmed -> 1.0`
	- `high_ai -> 0.75`
	- `low_ai -> 0.4`
- `confirmed = true` 仅当原字段 confidence 为 `confirmed`，或未来显式人工确认
- `source = raw_index_rule`
- `raw_type` 复用 `FieldInfo.type`

本轮规则转换必须 deterministic，不调用 LLM。

## Canonical Doc Facts / Script Facts 草案规则

- Canonical Doc Facts 当前可从 `DocIndex` 直接派生：
	- `doc_id` 由 `source_path` 的稳定哈希生成
	- `semantic_tags` 先用 `doc_type` 的小写规则值
	- `related_refs` 先从 `related_tables` 映射为 `table:<table_id>`
- Canonical Script Facts 当前可从 `CodeFileIndex` 直接派生：
	- `script_id` 由 `source_path` 的稳定哈希生成
	- `symbols` 取顶层 symbol 名称，保持 deterministic 顺序
	- `responsibilities` 取 symbol summary 去重后的顺序列表
	- `related_refs` 从 code references 与 symbol references 派生 `table:*`、`field:*`、`symbol:*`

这些草案用于定义后续可逐步接入的结构层，不代表已接管 Release 或 Candidate Map 主流程。

## 持久化路径

canonical facts 路径继续落在 P1-00 的 `bundle_root/project` 兼容层下：

- `get_project_canonical_tables_dir(project_root)` -> `bundle_root/project/indexes/canonical/tables/`
- `get_project_canonical_docs_dir(project_root)` -> `bundle_root/project/indexes/canonical/docs/`
- `get_project_canonical_scripts_dir(project_root)` -> `bundle_root/project/indexes/canonical/scripts/`

单文件 helper：

- `get_project_canonical_table_schema_path(project_root, table_id)` -> `.../tables/<table-id>.json`
- `get_project_canonical_doc_facts_path(project_root, doc_id)` -> `.../docs/<doc-id>.json`
- `get_project_canonical_script_facts_path(project_root, script_id)` -> `.../scripts/<script-id>.json`

## Canonical Facts 与 Release Artifacts 的关系

- Canonical Facts 是后续可逐步接入的 Release 输入层。
- Release Artifacts 是发布快照层。
- 本轮不改 Release 导出，不把 `table_schema.jsonl` 切换为从 Canonical Schema 导出。
- 本轮也不改 RAG 当前只消费 Current Release + Map-gated artifacts 的行为。

## LLM 边界

- 文件存在、编码识别、Excel/CSV/TXT 解析、header row 定位、空列裁剪、基础类型推断、source_hash 计算，仍由 Raw Index / rule layer 完成。
- LLM 在本轮最多只可作为未来“字段语义理解 / 字段别名合并”的接口草案方向，不能跳过 Raw Index 直接生成正式 schema。
- 如果后续接入 LLM，必须走统一 Model Router，不能新增 provider 或 API 配置。
- LLM 不能决定底层文件是否可读，也不能替代 Raw Index 的解析职责。

## 当前完成状态

- 已完成：Canonical Table Schema / Field / Doc Facts / Script Facts 数据结构。
- 已完成：从 `TableIndex`、`DocIndex`、`CodeFileIndex` 派生初始 canonical 草案的 deterministic 规则函数。
- 已完成：canonical 目录与单文件路径 helper。
- 未完成：Map 构建切换到 Canonical Schema。
- 未完成：Release 实际改为从 Canonical Facts 导出。
- 未完成：source/canonical-based candidate builder。
- 未完成：管理员 UI、字段归一化报告工具、P2-01 / P2-02 范围事项。

## 禁止范围

- 不让 LLM 决定底层文件是否可读。
- 不跳过 Raw Index 直接让 LLM 生成正式 schema。
- 不为了验收标准提前改 Release / RAG 主链路。
- 不把 P2-01 Candidate Map review 提前实现。

