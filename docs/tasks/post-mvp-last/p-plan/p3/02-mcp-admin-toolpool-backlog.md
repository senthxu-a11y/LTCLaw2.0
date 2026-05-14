# P3-02 后续 MCP 管理员工具池 Backlog

来源：总规划书 Phase 12、13.1。

## 目标

把数据整理、批量检查、清洗 dry-run、字段归一化报告等能力留给后续 MCP 工具池，不进入当前阶段核心范围。

本轮只定义 backlog、工具分类、输入输出与禁止范围，不实现任何 MCP tool，不接入主链路，不新增后端工具执行能力。

## Checklist

- [x] 定义 MCP Tool Pool 作为后续方向。
- [x] 表结构检查工具。
- [x] 主键 / 外键一致性检查工具。
- [x] 重复 ID / 空行 / 异常值扫描工具。
- [x] 表间引用检查工具。
- [x] 字段归一化报告工具。
- [x] 数据清洗 dry-run 工具。
- [x] Map 构建辅助分析工具。
- [x] 明确这些工具后续只走管理员工具入口，不进入 P0-P2 主链路阻塞项。
- [x] 明确工具池默认只做 read-only / report / dry-run。
- [x] 明确真实写入必须另走已验收的 Workbench source write 或未来显式管理员确认流程。
- [x] 明确 MCP 工具池不自动删表。
- [x] 明确 MCP 工具池不自动改表名。
- [x] 明确 MCP 工具池不自动改路径。
- [x] 明确 MCP 工具池不自动执行清洗。
- [x] 明确 MCP 工具池不自动发布 Map/RAG/Release。

## 输出物

- [x] MCP Tool Pool 后续规划。
- [x] 管理员工具池边界说明。
- [x] 未来工具描述表。

## 信息架构

- MCP Tool Pool 是后续管理员工具入口下的专项 backlog，用于承接批量检查、数据整理、清洗 dry-run、字段归一化报告、Map 构建辅助分析等低频但高风险的治理动作。
- 这些能力不进入 P0-P2 主链路，不成为 Project / Knowledge / Map Editor / NumericWorkbench 日常流程的阻塞项。
- 当前阶段只保留规划文档，不创建 MCP tool、不创建 router/service、不创建 capability、不提供可执行入口。
- 后续如实现，默认落在管理员工具入口；普通策划与只读角色不应在主工作流中看到这些工具能力。

## 工具池分类

### 1. 表结构检查工具

- 目标：检查表头、注释行、列数、主键字段存在性、约定字段缺失等结构问题。
- 定位：只读检查与报告，不修改源文件。

### 2. 主键 / 外键一致性检查工具

- 目标：核对主键唯一性、外键目标存在性、外键字段类型与目标主键格式是否一致。
- 定位：只读检查与报告，不自动修复。

### 3. 重复 ID / 空行 / 异常值扫描工具

- 目标：扫描重复主键、空记录、格式异常值、非法枚举值、明显越界值。
- 定位：只读扫描与报告，可输出风险清单。

### 4. 表间引用检查工具

- 目标：检查表间引用闭环、悬空引用、跨表命名不一致、引用路径断裂。
- 定位：只读分析与引用报告，不重写引用关系。

### 5. 字段归一化报告工具

- 目标：输出字段名、字段类型、枚举值、单位、命名风格等归一化差异报告。
- 定位：只读报告，不自动重命名字段，不自动改表头。

### 6. 数据清洗 dry-run 工具

- 目标：给出潜在清洗动作预览，例如去除尾随空格、标准化空值表达、统一大小写、合并重复候选。
- 定位：dry-run only，只生成拟议变更预览，不执行写入。

### 7. Map 构建辅助分析工具

- 目标：辅助分析候选 Map 构建输入、实体覆盖率、关系缺口、疑似重复实体、疑似孤立节点。
- 定位：只读分析与报告，不自动保存 Formal Map，不自动发布任何知识版本。

## 未来工具描述表

| tool name | input | output | side effect | required capability | current status |
| --- | --- | --- | --- | --- | --- |
| schema_audit_report | project bundle path, table metadata, table conventions | schema issue list, severity summary, report artifact | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| key_consistency_report | table indexes, pk/fk declarations, reference targets | pk/fk consistency report, broken refs list | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| data_anomaly_scan | target tables or project scope, scan rules | duplicate ID list, blank row list, abnormal value report | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| cross_table_reference_report | table graph, field refs, reference rules | dangling refs, inconsistent ref patterns, dependency summary | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| field_normalization_report | field names, types, enum samples, naming rules | normalization diff report, suggested canonical groups | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| cleanup_dry_run_preview | target tables, cleanup policy, optional filters | dry-run patch preview, affected row summary, risk notes | dry-run only, no writes | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |
| map_build_analysis_report | formal map snapshot, candidate inputs, entity/ref summaries | coverage report, suspected duplicates, missing edge report | none | 沿用未来管理员入口的既有能力控制，不在本阶段新增 capability | backlog |

## 写入边界

- MCP Tool Pool 默认只做 read-only / report / dry-run。
- 任何真实写入都不能直接由工具池自动执行。
- 若未来确有写入需求，必须复用已验收的 Workbench source write，或进入未来显式管理员确认流程。
- 工具池不得绕开现有治理边界，不得变相成为未审计的批量写入入口。

## 当前阶段禁止范围

- [x] 不实现任何 MCP tool。
- [x] 不新增后端 router/service。
- [x] 不新增 capability。
- [x] 不实现 LLM 生成数据整理脚本能力。
- [x] 不接入 KB/retrieval。
- [x] 不自动执行数据清洗。
- [x] 不自动删表。
- [x] 不自动改表名。
- [x] 不自动改路径。
- [x] 不自动修改项目源文件结构。
- [x] 不自动发布 Map/RAG/Release。
- [x] 不自动保存 Formal Map。
- [x] 不自动执行 Release build。
- [x] 不自动执行 Publish / Set Current。
- [x] 不把工具池能力并入 P0-P2 主链路。

## 与现有主链路的关系

- P0-P2 主链路继续只承载已验收的 Project / Knowledge / Map / Workbench 流程。
- MCP Tool Pool 只作为后续管理员工具池 backlog，不是当前阶段的主链路能力，不得成为上线阻塞项。
- Release、RAG、Map、Workbench source write、Model Router 都不在本任务改动范围内。
- 这些工具即便未来实现，也只能作为管理员辅助分析或 dry-run 能力，不能直接替代正式发布与写入流程。

## 验收标准

- [x] 当前阶段只保留 backlog 和边界说明。
- [x] 任何工具池能力都不进入 P0-P2 主链路阻塞项。
- [x] 后续实现时必须走管理员工具入口。
- [x] 默认 side effect 被限制为 none 或 dry-run，不提供真实写入。
- [x] 文档明确列出自动删表、自动改表名、自动改路径、自动执行清洗、自动发布 Map/RAG/Release 为禁止范围。

