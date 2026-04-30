# Agent-3：DocLibrary + KnowledgeBase 空壳页 + 导航接入（前端可见）

## 目标
按交接文档 P2 / P1 的预留位，加 2 个新前端页面 + 侧边栏导航。**只做 UI 空壳**（带骨架数据 + 调用 mock 接口），不做后端真实功能。给后续 Agent 留接入点。

## 验收标准
1. 侧边栏（折叠 + 展开两种状态）多 2 项：`文档库 / Doc Library`、`知识库 / Knowledge Base`
2. 路由 `/doc-library`、`/knowledge-base` 可访问，不进 404
3. 两个页面都是基本布局：`PageHeader` + 左侧筛选/分类树（mock 3-5 条）+ 右侧列表（mock 3-5 条）+ 空状态/加载态完整
4. 调用占位 API（前端有 stub，后端有最小路由返回 `{ items: [] }`）：
   - `GET /api/agents/{agentId}/game-doc-library/documents`
   - `GET /api/agents/{agentId}/game-knowledge-base/entries`
5. 路由注册到 `agent_scoped.py`（参考现有 game_project / game_index 写法）
6. i18n：`zh.json` / `en.json` / `ja.json` / `ru.json` 都补 `nav.docLibrary` / `nav.knowledgeBase` + 页面文案 key（占位文案即可）
7. `pnpm --dir console build` 通过；后端测试不退化（112 tests）

## 涉及文件
- 新增后端（仅 stub）：
  - `src/ltclaw_gy_x/app/routers/game_doc_library.py`（≤30 行，只 list 返回空）
  - `src/ltclaw_gy_x/app/routers/game_knowledge_base.py`（≤30 行）
- 修改后端：
  - `src/ltclaw_gy_x/app/routers/agent_scoped.py`（在第 76-96 行附近 import + include_router）
- 新增前端：
  - `console/src/pages/Game/DocLibrary.tsx`
  - `console/src/pages/Game/DocLibrary.module.less`
  - `console/src/pages/Game/KnowledgeBase.tsx`
  - `console/src/pages/Game/KnowledgeBase.module.less`
  - `console/src/api/modules/gameDocLibrary.ts`
  - `console/src/api/modules/gameKnowledgeBase.ts`
- 修改前端：
  - `console/src/pages/Game/index.ts`（导出新页面）
  - `console/src/App.tsx` 路由表
  - `console/src/layouts/Sidebar.tsx`（折叠 + 展开两处都加菜单项）
  - `console/src/layouts/constants.ts`（path / i18n key 映射）
  - `console/src/locales/{zh,en,ja,ru}.json`

## 关键背景
- **不要**装新依赖（chromadb / faiss 这些是 Agent-4 的事）
- 现有 GameProject / IndexMap / SvnSync 的页面结构是**最佳模板**，照搬布局、PageHeader 用法、antd 组件风格
- mock 数据写在前端 useState 初始值或 api 模块的 fallback 里都可以，但**接口调用必须真发出去**（后端 stub 返回空数组），方便后续切换
- 路由 basename 适配 `/console`（参考 App.tsx 现有 `getRouterBasename`）
- 两页都要有：搜索框（无功能 OK）、分类/标签 Tag、空状态 antd `Empty`
- 不要做任何拖拽 / 编辑 / 上传 — 纯只读展示
- DocLibrary 推荐字段（mock）：title / type(策划案/数值表/文档/任务) / status(草稿/待确认/已确认/归档) / updated_at / author
- KnowledgeBase 推荐字段（mock）：title / category(机制/数值规律/历史决策) / source(文档/对话/手动) / created_at

## 工作步骤
1. 复制 GameProject.tsx 当模板，改造成 DocLibrary.tsx（去掉表单，换成 Table + 左侧 Tree）
2. 同上做 KnowledgeBase.tsx
3. 加 api 模块（参考 game.ts 的写法，复用 axios instance）
4. App.tsx 路由表 + Sidebar.tsx 两处菜单项 + constants.ts
5. 4 个 i18n 文件补 key（不会日/俄文就用英文占位，加 `// TODO i18n` 注释）
6. 后端 stub 路由（参考 game_index.py 第 31-37 行写法），只返回 `{ items: [] }`
7. 注册到 agent_scoped.py
8. `pnpm --dir console build` + `pytest tests/unit -q` 双绿
9. 启 ltclaw app + 浏览器访问 `/console/doc-library` `/console/knowledge-base` 截图描述

## 输出物
- 新增 6 个文件（2 后端 + 4 前端 + 2 less）
- 修改 ~7 个文件
- 验证截图描述：侧边栏新菜单项 + 两个新页面打开效果
- pnpm build 输出（最后 5 行）+ pytest 结尾

## 不要做
- 不要碰 service.py / svn_watcher.py / table_indexer.py（Agent-1/2 在改）
- 不要装新依赖
- 不要做后端真实功能
- 不要改 game_index / game_svn / game_change 现有路由
- 不要改 auth.py 的 _PUBLIC_PATHS

## 冲突清单
- 与 Agent-1 / Agent-2 在文件层面完全不冲突
- 唯一可能并发：`agent_scoped.py` — 本任务只在第 76-96 行**追加 2 行 import + 2 行 include_router**，使用 `multi_replace_string_in_file` 一次完成；其他人不动这文件
