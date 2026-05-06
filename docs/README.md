# docs 目录说明

当前 docs 目录按“计划 / 任务 / agent 派工 / 地基 / 已完成 / 资料 / 记忆”七类组织：

- `plans/`：即将开发或正在细化的架构、范围、实施规划文档。
- `tasks/`：进行中的任务派发、阶段任务清单、迁移与执行检查清单。
- `agent-tasks/`：可直接分派给 agent 的独立任务卡。
- `foundations/`：新版框架地基、基础规范与主线基线文档。
- `completed-plans/`：已经完成或仅用于回顾的历史计划、阶段进度文档。
- `materials/`：交接稿、原始资料、样本、模板等参考材料。
- `memory/`：项目长期记忆与权威约束文档。

快速入口：

- 当前知识库与数值工作台架构主线看 `plans/knowledge-architecture-handover-2026-05-06.md`。
- P1 本地优先范围决策看 `plans/knowledge-p1-local-first-scope-2026-05-06.md`。
- P0-P3 精确施工清单看 `tasks/knowledge-p0-p3-implementation-checklist.md`。
- DLP 绕行与安全写文件手册固定看 `memory/dlp-incident.md`。
- 涉及迁移、canary、自检的操作清单固定看 `tasks/MIGRATION_CHECKLIST.md`。
- 任务派发与阶段执行卡统一放 `tasks/`，不再散落在根目录。

建议约定：

- 即将进入开发、需要持续细化的架构/范围稿，优先放 `plans/`。
- 新的任务卡、执行单、迁移单，优先放 `tasks/`。
- 可并行交给 agent 执行的单点任务，优先放 `agent-tasks/`。
- 跨多个阶段反复作为主线依据的基础规范，优先放 `foundations/`。
- 某个计划结束后，再移入 `completed-plans/`。
- 外部原件、样本、模板、交接材料统一放入 `materials/`。
