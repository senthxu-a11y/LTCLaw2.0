# P0-05 Map-gated RAG 改造

来源：总规划书 Phase 6、18.2、19.3.3、20 技术雷区 2。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只收口正式 RAG 的读取边界，不恢复 KB 为正式系统，不允许普通策划绕过 Map 或更新正式知识底座。

## 目标

RAG 必须通过 Map Router 获取 allowed refs 后再读取 Release Artifacts，不允许自由扫描 artifacts，不允许读取 KB 作为并列正式知识源。

## Capability 与 Legacy 兼容说明

- [ ] 本任务只允许引用已有 capability 名称 `knowledge.read`；不新增与 RAG 查询相关的新 capability。
- [ ] 本任务不赋予普通策划 `knowledge.build` 或 `knowledge.publish`。
- [ ] legacy retrieval 仅允许作为 debug / fallback / migration 兼容层，不得回升为正式查询入口。

## Checklist

- [ ] 定义 Map Router 输入：query + current release + optional focus refs。
- [ ] 定义 Map Router 输出：allowed refs。
- [ ] 定义 allowed refs 到 Release Artifacts 的解析逻辑。
- [ ] 定义 RAG Context Builder 只能读取 allowed refs 对应证据。
- [ ] 定义 citation 格式。
- [ ] 定义 RAG 不读取 raw source。
- [ ] 定义 RAG 不读取 pending。
- [ ] 定义 RAG 不读取 KB。
- [ ] 定义 RAG 不读取普通 session draft，除非作为显式 Draft Overlay。
- [ ] 降级 legacy retrieval 为 debug / fallback。
- [ ] 移除 KB 作为正式查询入口。
- [ ] 避免 `retrieval.py` 成为正式知识结构来源。
- [ ] 定义 answer adapter 只消费 context，不直接读 artifacts。
- [ ] 定义 insufficient_context 行为。

## Citation 必须保留

- [ ] `citation_id`
- [ ] `release_id`
- [ ] `artifact_path`
- [ ] `source_path`
- [ ] row / field / title 等定位信息
- [ ] Workbench citation deep-link

## 输出物

- [ ] Map-gated RAG 设计说明。
- [ ] Map Router 接口草案。
- [ ] RAG Context Builder 新边界。
- [ ] Legacy retrieval 降级策略。

## 验收标准

- [ ] RAG 查询先经过 Map Router。
- [ ] RAG 只读取 allowed refs 对应 Release Artifacts。
- [ ] RAG 不全量扫描 artifacts 作为正式检索路径。
- [ ] RAG 不读取 KB。
- [ ] ignored / deprecated refs 不进入正式 evidence。
- [ ] citation deep-link 到 Workbench 不被破坏。

## 禁止范围

- [ ] 不丢 citation。
- [ ] 不把 legacy retrieval 作为正式查询入口。
- [ ] 不让 RAG 绕过 Map 直接检索全量 artifacts。

