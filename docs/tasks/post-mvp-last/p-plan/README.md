# LTClaw Post-MVP P 计划任务拆分索引

来源总规划书：

- `docs/tasks/post-mvp-last/ltclaw_post_mvp_map_rag_workbench_architecture (1).md`

本目录只负责把总规划书中的 checklist 和任务拆成可执行小文档。原始总规划书仍是最高优先级依据；如果拆分文档和总规划书冲突，以总规划书为准。

## 新机器 / 新会话启动规程

每次换电脑、换分支、开启新 agent 会话或从 `main` 重新创建工作分支时，必须先读本节指定文档，再决定施工任务。不要只根据 IDE 当前打开文件开工。

### main 起点必须读取

按顺序读取：

1. `docs/tasks/post-mvp-last/p-plan/README.md`
2. `docs/tasks/post-mvp-last/ltclaw_post_mvp_map_rag_workbench_architecture (1).md`
3. 当前要施工的 P 文档，例如 `p0/00-architecture-boundary-freeze.md`
4. 如果当前任务会碰代码，再读总规划书第 19 节和第 20 节：
   - 第一批执行顺序
   - Agent 任务模板
   - 关键收口项验收标准
   - Legacy 迁移策略
   - 最小测试清单
   - Agent 执行前置约束与技术雷区
   - Agent 执行前必须检查的源码点

### 开工前必须确认

- [ ] 当前分支来自最新 `main` 或团队约定的集成分支。
- [ ] 已读取本 README 和总规划书。
- [ ] 已确认当前 P 阶段；P0 未完成前，不进入 P1/P2/P3 实现。
- [ ] 已确认当前任务只属于一个明确 slice。
- [ ] 已复制并填写本文档的 Agent 任务模板。
- [ ] 已确认本任务是否触碰正式知识链路。
- [ ] 已确认本任务是否触碰真实源表写回。
- [ ] 已确认本任务是否新增或改变 capability。
- [ ] 已确认本任务是否改变 Release 输入。
- [ ] 已确认本任务是否改变 RAG context 行为。
- [ ] 已确认本任务是否改变模型调用路径。
- [ ] 已确认 legacy 兼容策略。

### 不允许的启动方式

- [ ] 不允许只读当前打开的单个任务文档就开始改代码。
- [ ] 不允许跳过 P0 直接做体验增强。
- [ ] 不允许把多个 P 文档合并成一次“大改造”。
- [ ] 不允许在不了解总规划书禁止范围的情况下新增 API、权限、写回或模型配置。

### 新分支建议

从 `main` 创建分支时，分支名建议带 P 阶段和任务号：

```text
p0-00-architecture-boundary-freeze
p0-01-svn-freeze-hide
p0-02-kb-formal-chain-removal
p0-03-agent-profile-capabilities
```

每个分支默认只处理一个任务文档；如果必须拆更小，使用后缀：

```text
p0-02a-release-kb-removal
p0-02b-rag-kb-removal
p0-02c-retrieval-legacy-mark
```

## 执行总原则

必须严格遵守：

```text
先收口边界
再迁移旧逻辑
再补新功能
最后优化体验
```

禁止一次性完成全部架构改造。每个任务必须控制在一个明确 slice 内，交付时必须说明是否触碰正式知识链路、真实源表写回、capability、Release 输入、RAG context、模型调用路径和 legacy 兼容。

## P 计划映射

### P0：架构收口和安全边界

先完成正式链路、权限、写回、RAG 和模型调用的收口。P0 未完成前，不进入 Canonical Schema、Map Diff Review、管理员面板等后续建设。

- [p0/00-architecture-boundary-freeze.md](p0/00-architecture-boundary-freeze.md)
- [p0/01-svn-freeze-hide.md](p0/01-svn-freeze-hide.md)
- [p0/02-formal-knowledge-chain-dedup.md](p0/02-formal-knowledge-chain-dedup.md)
- [p0/03-agent-profile-capabilities.md](p0/03-agent-profile-capabilities.md)
- [p0/04-workbench-source-write-audit.md](p0/04-workbench-source-write-audit.md)
- [p0/05-map-gated-rag.md](p0/05-map-gated-rag.md)
- [p0/06-unified-model-router.md](p0/06-unified-model-router.md)
- [p0/07-workbench-suggest-context-builder.md](p0/07-workbench-suggest-context-builder.md)

### P1：项目数据包和路径治理

在 P0 收口后，统一 project bundle、source 配置、路径分层和 legacy path 兼容。

- [p1/00-project-bundle-paths.md](p1/00-project-bundle-paths.md)
- [p1/01-release-artifacts-boundary.md](p1/01-release-artifacts-boundary.md)
- [p1/02-overlap-governance-p1.md](p1/02-overlap-governance-p1.md)

### P2：Map 构建体验

补 Canonical Facts / Canonical Schema、source/canonical-based Candidate Map、Map Diff Review 和 LLM 辅助解释。

- [p2/00-canonical-facts-schema.md](p2/00-canonical-facts-schema.md)
- [p2/01-map-first-candidate-review.md](p2/01-map-first-candidate-review.md)
- [p2/02-admin-map-build-experience.md](p2/02-admin-map-build-experience.md)

### P3：体验增强

只在 P0-P2 主链路稳定后做 UI 体验增强、管理员聚合查看和后续 MCP 工具池规划。

- [p3/00-workbench-suggest-ui-evidence.md](p3/00-workbench-suggest-ui-evidence.md)
- [p3/01-admin-panel-audit-version.md](p3/01-admin-panel-audit-version.md)
- [p3/02-mcp-admin-toolpool-backlog.md](p3/02-mcp-admin-toolpool-backlog.md)

## Agent 任务模板

每个实现任务必须复制以下模板并填完整：

```text
任务名称：

目标：

允许修改的文件：

禁止修改的文件：

必须保持兼容的接口：

新增/修改的数据结构：

新增/修改的 capability：

验收标准：

不做范围：

风险点：

需要人工验证的点：
```

## 第一批执行顺序

P0 内部第一批任务必须先做“收口”，不要先做体验和新功能：

1. KB 正式链路移除。
2. Agent Profile / capabilities 补齐。
3. 新增 `workbench.source.write` 权限。
4. Workbench 写回真实源表 wrapper + audit。
5. RAG 改为 Map-gated。
6. 统一 Model Router。
7. Workbench Suggest Context Builder + `evidence_refs` 合同补齐。

第一批完成后，才能进入 Canonical Schema、Map Diff Review、管理员面板等后续建设。
