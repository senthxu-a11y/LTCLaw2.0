# P2-00 Canonical Facts / Canonical Schema 层

来源：总规划书 Phase 5、3.3、5。

## 目标

在 Raw Index 和 Map 之间补上稳定的规范化事实层，降低 Map 构建和维护难度。

## Checklist

- [ ] 定义 Raw Table Index 与 Canonical Table Schema 的区别。
- [ ] 定义 `raw_header`。
- [ ] 定义 `canonical_header`。
- [ ] 定义 `aliases`。
- [ ] 定义 `semantic_type`。
- [ ] 定义 `description`。
- [ ] 定义 `confidence`。
- [ ] 定义 `confirmed`。
- [ ] 定义字段归一化的规则优先级。
- [ ] 定义 LLM 字段语义理解输入输出。
- [ ] 定义 LLM 字段别名合并输入输出。
- [ ] 定义 Canonical Doc Facts。
- [ ] 定义 Canonical Script Facts。
- [ ] 定义 canonical facts 的持久化路径。
- [ ] 定义 canonical facts 与 Release Artifacts 的关系。

## LLM 边界

- [ ] 文件存在、编码识别、Excel/CSV/TXT 解析、Header row 定位、空列裁剪、基础类型推断、source_hash 计算必须由规则层完成。
- [ ] LLM 只介入文档语义分类、字段语义理解、脚本职责理解、跨源关系候选、字段别名归并、系统聚类等语义环节。
- [ ] 所有 LLM 调用必须走统一 Model Router。

## 输出物

- [ ] Canonical Schema 数据结构。
- [ ] Canonical Facts 目录规范。
- [ ] 字段归一化规则。
- [ ] LLM 语义分析接口草案。

## 验收标准

- [ ] Map 构建优先消费 Canonical Schema。
- [ ] Release table_schema 可逐步从 Canonical Schema 导出。
- [ ] TableIndex 不再作为正式 schema 语义来源。

## 禁止范围

- [ ] 不让 LLM 决定底层文件是否可读。
- [ ] 不跳过 Raw Index 直接让 LLM 生成正式 schema。

