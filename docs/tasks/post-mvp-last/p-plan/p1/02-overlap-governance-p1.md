# P1-02 重复系统治理 P1 项

来源：总规划书 18.11 P1 治理项。

## 目标

P1-02 只补齐重复系统的边界标注、主从关系和后续迁移方向，避免在 P1 阶段继续把多套系统混成“第二正式链路”。

本轮边界如下：

- 不改 RAG context / Map Router。
- 不改 Release build / publish。
- 不改 Workbench source write wrapper。
- 不改 Model Router / capability。
- 不实现 Canonical Schema / Canonical Facts。
- 不实现 source/canonical-based candidate builder。
- 不恢复 SVN watcher / auto-index。

## 五组重复系统边界

### 1. DependencyGraph vs Formal Map relationships

- DependencyGraph：technical index / impact evidence，只服务于依赖分析、Workbench impact、工程排查。
- Formal Map relationships：正式知识结构关系，是 Release 与正式 RAG 读取的知识结构来源。
- 主从关系：Formal Map relationships 是正式语义主链路；DependencyGraph 只是技术证据，不得提升成第二套 Formal Map。
- 当前代码标注：Workbench preview 的 impacts 返回 `source_type = dependency_graph`，并明确 `is_formal_map_relationship = false`。

### 2. TableIndex vs Canonical Schema

- TableIndex：raw / semi-structured index，当前继续用于表行定位、兼容期表结构读取与工程分析。
- Canonical Schema：后续 Map / RAG 使用的规范化 schema 层。
- 主从关系：TableIndex 不是长期正式 schema 语义来源；Canonical Schema 才是后续正式结构层，但 P1-02 只定义边界，不实现。

### 3. ProposalStore vs Draft Overlay

- Draft Overlay：Workbench 运行态上下文，用于当前会话中的临时草案、预览与操作上下文。
- ProposalStore：持久化草案 / 改动记录，用于审阅与留痕，不是知识事实仓库。
- 主从关系：两者都不是 Formal Map、Release、正式 RAG 的输入。

### 4. SVN watcher auto-index vs Admin Rebuild

- SVN watcher auto-index：历史自动化思路，当前继续 frozen，不恢复默认自动索引。
- Admin Rebuild：正式更新流程，由管理员显式触发，用于重建项目级正式索引与知识产物。
- 主从关系：正式更新流程以管理员主动 Rebuild 为准；watcher 不作为默认正式更新链路。

### 5. release-based candidate vs source/canonical-based candidate

- candidate-from-release：复核当前 Release 的 map / artifacts snapshot，用于检查当前正式快照，不是管理员更新 Map 的主路径。
- candidate-from-source：后续基于 Source / Canonical Facts 生成候选 Map 的主路径。
- 主从关系：release-based candidate 只承担 review current release snapshot 的角色；source/canonical-based candidate 才是后续正式重建方向。

## 当前代码治理标注

- `retrieval.py` 继续属于 legacy / debug / migration-only 辅助面，不进入正式 Release、正式 RAG、Workbench Suggest 主链路。
- `dependency_resolver.py` 的 DependencyGraph 输出只表示 technical impact evidence。
- `game_workbench.py` 在 preview impacts 返回中显式标注 dependency_graph 来源，避免与 Formal Map relationship 混淆。
- release-based candidate 的主语义收口在本文件文档，不在 P1-02 中改 candidate builder 算法。

## 验收标准

- RAG 的知识结构仍以 Formal Map relationships 为准。
- Workbench Impact 如引用 DependencyGraph，必须标注其为 technical evidence / impact evidence，不是 Formal Map relationship。
- Workbench 可继续用 TableIndex 做行定位，但文档明确字段语义后续逐步引用 Canonical Schema。
- Draft / Proposal 不进入 Formal Map、Release、正式 RAG。
- 管理员主动 Rebuild 是正式更新流程；SVN watcher 不默认开启自动索引。
- candidate-from-release 被定义为 review current release snapshot；candidate-from-source 被定义为后续管理员更新 Map 主路径。
- 不产生 P2 的 Canonical Schema / Canonical Facts 实现代码。

## 当前完成状态

- 已完成：五组重复系统的主从关系文档化。
- 已完成：Workbench impact 的 DependencyGraph 来源标注。
- 已完成：legacy retrieval 与正式知识链路的边界说明保留。
- 未完成：Canonical Schema 数据结构与持久化。
- 未完成：source/canonical-based candidate builder。
- 未完成：任何 P2 级别事实抽取或正式 schema 实现。

## 禁止范围

- 不把 DependencyGraph 做成第二套 Formal Map。
- 不把 TableIndex 写成长期正式 schema 语义来源。
- 不把 Draft Overlay / ProposalStore 接入 Release 或正式 RAG。
- 不让 SVN watcher 默认开启自动索引。
- 不用“治理”名义重构 P0 / P1 已验收主链路。

