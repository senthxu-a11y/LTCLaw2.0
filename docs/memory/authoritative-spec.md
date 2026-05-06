# 权威需求文档（必读）

> 来源：`/memories/repo/AUTHORITATIVE-spec.md`。游戏策划工作台产品的**唯一权威依据**，其余早期草稿一律作废。

**唯一产品依据**：
1. `docs/materials/LTCLAW_策划工作台_交接文档.html`（v1.1） — 核心需求和框架
2. `docs/foundations/numeric-workbench-spec.md` — 数值工作台执行规范

旧文件 `/memories/ltclaw-mvp-plan.md` §0~§6 的"Doc Generator/Config Table/Task Export"作废。
旧文件 `docs/plans/game-planner-workbench-plan.md` 是早期方向稿，被交接文档 v1.1 覆盖。

## 10 项已拍板设计决策（硬约束）
1. **自动化边界**：索引层全自动；数值/文档/逻辑由人决策
2. **SVN 共享方案**：`.ltclaw_index/` 提交 SVN（仅 JSON，**不存向量**），向量本地按需重建
3. **变更感知**：维护者本地轮询，非 SVN hook
4. **防冲突**：版本号仲裁 + 随机抖动；先用方案 A（指定主索引机），后期升级方案 B（竞争）
5. **Chat 不新建页面**：在现有 Chat 中扩展（PlanPanel Drawer + 模式选择栏）
6. **决策按钮分两类**：阻塞型(写入) → 消息流 ApprovalCard；非阻塞型(存档/确认/标记) → Drawer
7. **文档模板开放**：用户自维护 `Docs/Templates/`，配置写回 `project_config.yaml` 提交 SVN
8. **节点图选 reactflow**：列表视图先上，节点图主线稳定后单独排期
9. **版本记录分层**：表级 JSON 30 天明细 → weekly/ 6 个月 → milestone 永久；过滤"无意义变更"（5%/1行/字段增删才记）
10. **不破坏现有功能**：仅 4 文件改（constants.ts/Sidebar.tsx/PlanPanel/index.tsx/Chat/index.tsx），纯扩展

## 自动化分级（写入边界）
- L1 查询/建议：完全自动
- L2 小批量写入：≤10 行 ≤3 字段，分支提交 + Review
- L3 批量写入：>10 行或跨多表，人确认后执行
- L4 结构变更：永远不自动，只生成操作指南

## 索引产物结构（.ltclaw_index/）
```
.ltclaw_index/
├── registry.json          # 中枢：版本号、文件清单、校验和
├── project_config.yaml    # 团队共享配置
├── dependency_graph.json  # 全局依赖图（节点+边+置信度）
├── tables/<TableName>.json
├── docs/<DocName>.json
├── code/                  # C# 轻量解析
└── history/               # 版本聚合（30天明细/weekly/milestone）
```

## 三层查询路由
意图识别 → {精确(单表字段) | 关联(跨表) | 历史(变更) | 影响分析(依赖图) | 模糊(向量)} → 结果组装+置信度标注

## 导航变更（4 个改动文件）
- `control-group` + svn-sync
- **新 game-group**：index-map / doc-library / knowledge-base / **数值工作台**(独立页 `/game/workbench`)
- `settings-group` + game-project

## Chat 改造点
- 模式选择栏：自由 / 策划案 / 数值查询 / 文档生成 / 知识查询
- 卡片：NumericCard / DesignDocCard / DocGenCard
- PlanPanel Drawer 加两 Section：引用的数值表 + 产出文档
- 数值工作台路由下，Drawer 内容切换为 AISuggestionPanel（条件渲染，原逻辑不动）

## 数值工作台（独立页面 + Chat Drawer 双入口）
**路由**：`/game/workbench`
**布局**：上下可拖动分割（默认 6:4，最小 20%）
- 上半：多表并列（每列 240px 固定，超 4 张横向滚动）
- 下半：实时影响预览（防抖 300ms 调 `POST /api/game/workbench/preview`）
- 右 Drawer：AISuggestionPanel（可用 ID / 同类参考值 / 建议区间 / 可复用资源 / 待确认 Checklist）

**核心组件**（新建在 `console/src/pages/Game/`）：
- NumericWorkbench.tsx 主页
- TableColumn / ImpactPreview / DamageChain / AISuggestionPanel

**API 草案**：
- GET  /api/game/workbench/context
- POST /api/game/workbench/preview
- GET  /api/game/workbench/ai-suggest
- POST /api/game/change/propose（复用现有 R-6 ChangeProposal）

**跳转**：Chat Drawer 字段旁 [在数值工作台中打开] → `/game/workbench?tableId=&fieldKey=` → 自动滚到列 + highlight 300ms

**生成变更草稿**：复用 R-6 ChangeProposal + ApprovalCard 阻塞流（已完工）

## 后端关键模块清单
```
src/ltclaw_gy_x/
├── svn_watcher/                   # 轮询服务（新）
│   ├── watcher.py / file_classifier.py / svn_client.py
├── indexer/                       # AI 索引器（新）
│   ├── ai_indexer.py / table_indexer.py / document_indexer.py
│   ├── code_indexer.py / dependency_resolver.py / index_committer.py
├── knowledge_base/                # 知识库（新）
└── app/routers/{game_project,svn_sync,index_map,doc_library,knowledge_base}.py
agents/skills/{game_query,numeric_assist,doc_gen}-zh
```

## 已完工对照（2026-04-28）
- ✅ GameProject 配置页（P0）
- ✅ SvnClient + SvnSync 页 + changelog SSE（P0）
- ⚠️ R-6 ChangeProposal 写回闭环 = **P2 安全网（抢前完工）**，将被数值工作台 + ApprovalCard 直接复用，未浪费

## 缺口（按优先级）
P0 还差：
- svn_watcher（核心）
- table_indexer / document_indexer / dependency_resolver / index_committer
- registry.json 中枢、history/ 分层归档、5% 阈值过滤
- setup.sh / setup.bat
- 前端 game-group 三个空壳页（IndexMap/DocLibrary/KnowledgeBase）+ 侧边栏 game-group

## 用户须确认开工项
1. 维护者本地 SVN 工作目录路径
2. ID 段划分样本（hero:1000~1999 类）
3. Docs/Templates/ 现有文档样本 2-3 份
4. 轮询间隔（默认 5 分钟可吗）
5. 向量库选型：chromadb vs faiss-cpu
6. Excel 文件名规律
7. 是否先用方案 A（指定一台主索引机器）
