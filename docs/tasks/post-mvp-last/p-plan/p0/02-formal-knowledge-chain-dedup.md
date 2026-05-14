# P0-02 正式知识链路与重复系统收口

来源：总规划书 Phase 0.6、18.1-18.10、19.3.1、19.4。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只收口正式知识链路边界，不新增 P1/P2/P3 能力，不让普通策划接触 Formal Map、Current Release 或正式 RAG 的发布入口。

## 目标

冻结唯一正式知识链路，移除 KB、legacy retrieval、DependencyGraph、ProposalStore、TableIndex 等系统在正式链路里的重叠职责。

正式链路只能是：

```text
Source
→ Raw Index
→ Canonical Facts
→ Candidate Map
→ Formal Map
→ Release
→ Release Artifacts
→ Map-gated RAG
→ Chat / Workbench Suggest
```

## Capability 与 Legacy 边界

- [ ] 本任务只允许引用已有 capability 名称：`knowledge.read`、`knowledge.build`、`knowledge.publish`、`workbench.source.write`。
- [ ] 本任务不新增 capability，只澄清谁可以读取、构建、发布正式知识，以及真实源表写回与知识底座更新的隔离关系。
- [ ] legacy KB、legacy retrieval、SimpleModelRouter 只允许保留为 migration / debug / fallback，不得回升为正式链路。

## Checklist

- [ ] 确认 Formal Map 是唯一正式知识结构。
- [ ] 确认 Release Artifacts 是唯一正式证据快照。
- [ ] 确认 Map-gated RAG 是唯一正式项目知识查询入口。
- [ ] 确认 KB 不再作为正式知识系统。
- [ ] 确认 Release 不再读取 KB / workspace KB / session KB。
- [ ] 确认 RAG 不再读取 KB。
- [ ] 确认 Workbench Suggest 不再读取 KB 作为正式证据。
- [ ] 确认普通 Chat 的项目知识来源只走 Map-gated RAG。
- [ ] 确认 legacy `retrieval.py` 不再作为正式查询入口。
- [ ] 确认 legacy retrieval 仅可作为 debug / migration / fallback 工具。
- [ ] 确认 DependencyGraph 只作为技术索引 / 影响分析证据。
- [ ] 确认 Formal Map relationships 才是正式知识关系。
- [ ] 确认 TableIndex 是 raw / semi-structured index，不是最终正式 schema。
- [ ] 确认 Canonical Schema 是 Map/RAG 使用的正式规范化 schema。
- [ ] 确认 ProposalStore 只是可持久化草案记录。
- [ ] 确认 Draft Overlay 只是当前工作台运行态上下文。
- [ ] 确认 Draft / Proposal 不进入 Formal Map、Release、正式 RAG。
- [ ] 确认 `workbench.test.export` 不等于真实源表写回。
- [ ] 确认真实源表写回必须使用 `workbench.source.write`。
- [ ] 确认 `my_role` 只作为 legacy shortcut。
- [ ] 确认 Agent Profile capabilities 是新权限标准。
- [ ] 确认 SimpleModelRouter 只是过渡桥。
- [ ] 确认正式模型调用走统一 Model Router。

## 输出物

- [ ] 正式知识链路定义。
- [ ] Legacy / Debug / Runtime / Draft 分类表。
- [ ] KB 移除清单。
- [ ] retrieval 降级清单。
- [ ] DependencyGraph 与 Formal Map relationships 边界说明。
- [ ] TableIndex 与 Canonical Schema 边界说明。
- [ ] ProposalStore 与 Draft Overlay 边界说明。
- [ ] 权限旧标准到新标准迁移说明。

## 验收标准

- [ ] Release build 不再调用 `get_kb_store`。
- [ ] Release build 不再读取 workspace/session KB。
- [ ] RAG context 不再读取 `knowledge_base`。
- [ ] Workbench Suggest 不再把 KB 作为正式 evidence。
- [ ] Chat 项目知识只走 Current Release + Map-gated RAG。
- [ ] 历史 KB 代码如保留，必须标记 legacy / migration，不参与正式链路。

## 禁止范围

- [ ] 不直接删除所有 KB 代码。
- [ ] 不让 legacy retrieval 成为正式知识结构来源。
- [ ] 不让 Proposal / Draft 污染 Formal Map、Release 或正式 RAG。

