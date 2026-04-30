# 项目记忆与经验沉淀（docs/memory）

本目录归档 LTCLAW-GY.X 在长期协作中积累的项目记忆与踩坑经验，从 `/memories/` 各 scope 中导出，便于团队成员/新接手 agent 快速对齐。

## 文件总览

| 文件 | 范围 | 用途 |
|---|---|---|
| [architecture.md](architecture.md) | 架构 | FastAPI 装配链 / 多 Agent 运行时 / Workspace / Provider / Plugin / Channel / 路由 / 配置 / 安全 / 测试 / 扩展点速查（**新成员必读**） |
| [authoritative-spec.md](authoritative-spec.md) | 产品 | 权威需求文档（10 项硬约束、自动化分级、`.ltclaw_index/` 结构、Chat 改造点、数值工作台规范） |
| [mvp-plan.md](mvp-plan.md) | 产品 | 游戏策划生产力 MVP 计划 + 历次冒烟/闭环记录（R-1 ~ R-6 写回闭环、SVN 真连冒烟、T-D B 路径 PASS） |
| [svn-environment.md](svn-environment.md) | 环境 | 公司 SVN 环境约束（TortoiseSVN-only / SlikSVN 兼容 / SvnClient 双模式 mode 探测） |
| [dlp-incident.md](dlp-incident.md) | 环境 | DLP 加密事件回顾 + 安全写文件方式 + DLP 命中规律 + 恢复手册 |
| [collaboration-conventions.md](collaboration-conventions.md) | 协作 | 跨工作区记忆迁移流程 / 项目身份 / 用户偏好 / DLP 应对详细姿势 |
| [session-log-2026-04-30.md](session-log-2026-04-30.md) | 进度 | 主线 2026-04-30 收工状态：IndexMap LLM 通路完工、重建索引按钮、数值工作台 v0、关键环境事实 |

## 阅读顺序

1. **新成员快速上手**：`architecture.md` → `authoritative-spec.md` → `mvp-plan.md`。
2. **接手前先排雷**：`dlp-incident.md` → `svn-environment.md` → `collaboration-conventions.md`。
3. **复盘当前进度**：`session-log-2026-04-30.md`。

## 维护策略

- 这些文件来自 GitHub Copilot 协作过程中的 `/memories/`，是只增不减的项目记忆/经验沉淀。
- 当架构、SVN 环境策略、DLP 规则、产品规范出现重大变更时，请同步更新对应 markdown，并在变更顶部追加日期标记。
- 若新增了项目级共识（例如新硬约束、踩坑教训），优先放入对应文件，必要时新增主题文件并更新本 README 索引表。
