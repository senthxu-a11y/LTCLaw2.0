# P1-02 重复系统治理 P1 项

来源：总规划书 18.11 P1 治理项。

## 目标

在 P0 完成正式链路收口后，继续治理关系、schema、草案、更新流程和 Candidate 语义的重复系统问题。

## Checklist

- [ ] DependencyGraph vs Formal Map relationships：关系来源收口。
- [ ] TableIndex vs Canonical Schema：schema 层级收口。
- [ ] ProposalStore vs Draft Overlay：草案边界收口。
- [ ] SVN watcher auto-index vs Admin Rebuild：更新流程收口。
- [ ] release-based candidate vs source-based candidate：candidate 语义收口。

## 边界定义

- [ ] DependencyGraph = 技术索引 / 影响分析证据。
- [ ] Formal Map relationships = 正式知识结构关系。
- [ ] TableIndex = 原始/半结构索引。
- [ ] Canonical Schema = Map/RAG 使用的规范化表结构。
- [ ] Draft Overlay = 当前工作台运行态上下文。
- [ ] ProposalStore = 可持久化的草案/改动记录。
- [ ] candidate-from-release = 复核当前 Release 的 Map/Artifacts 快照。
- [ ] candidate-from-source = 基于当前 Source / Canonical Facts 生成新的候选 Map。

## 验收标准

- [ ] RAG 的知识结构以 Formal Map relationships 为准。
- [ ] Workbench Impact 可以引用 DependencyGraph，但必须标注来源。
- [ ] Workbench 可继续使用 TableIndex 做行定位，字段语义逐步引用 Canonical Schema。
- [ ] Draft / Proposal 不进入 Formal Map、Release、正式 RAG。
- [ ] 管理员主动 Rebuild 是正式流程。
- [ ] candidate-from-source 成为管理员更新 Map 的主路径。

## 禁止范围

- [ ] 不把 DependencyGraph 做成第二套 Map。
- [ ] 不把 TableIndex 长期作为正式 schema 语义来源。
- [ ] 不让 SVN watcher 默认开启自动索引。

