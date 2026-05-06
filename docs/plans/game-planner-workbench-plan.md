LTCLAW 游戏策划工作台 — 开发计划
文档定位：本文档是「游戏策划工作台」功能的完整开发规划，由产品与架构讨论直接沉淀而来。后续 Coding Agent 或开发者可将本文档作为任务说明直接接手开发，无需再重新对齐需求背景。

补充状态（2026-05-06）：本计划中的“数值工作台”部分，现已从早期的 Chat/Drawer 附属能力演化为独立的“会话驱动本地调值工作台”。后续涉及 NumericWorkbench 的施工、验收与回顾，优先参考 `docs/foundations/numeric-workbench-session-ux-plan.md` 与最新进度文档，而不是仅按本文早期表述执行。

1. 背景与目标
1.1 痛点
游戏策划团队日常工作高度依赖数值表（Excel）、策划案（Markdown / Docx）和版本控制（SVN）。然而现有工作流存在几个明显断层：

查表成本高：数值表结构复杂、字段命名不统一，策划查一个字段往往要翻多张表。
文档碎片化：策划案散落在各个目录，没有统一的状态流转（草稿 → 确认 → 归档）。
经验无法沉淀：调数值的上下文（为什么改、影响了哪些系统）只存在于即时通讯和个人记忆里，人员流动后容易丢失。
新人上手慢：没有全局数据地图，新成员理解数值体系要花大量时间。
1.2 要解决的问题
本项目在 LTCLAW-GY.X 现有能力（Chat / Agents / Models / Backups / Approvals）的基础上，新增一套游戏策划工作平台，核心解决：

数值表与文档的自动索引与自然语言查询。
策划案与版本报告的结构化生成与管理。
团队经验的知识库沉淀与复用。
1.3 范围
数据源	说明
数值表（Excel / CSV）	存放在 SVN，含字段定义、ID 段划分、依赖关系
策划文档（Markdown / Docx）	存放在 SVN，含策划案、更新日志、规范文档
SVN 版本历史	作为 change_history（变更窗口），用于生成版本报告和追溯修改
不在范围内：代码文件、美术资源、服务器日志。

2. 关键约束
在动手设计之前，有几个硬约束必须写清楚，所有架构决策都必须在这些约束下运行。

2.1 SVN 无法使用服务器端 Hook
团队使用的 SVN 托管环境不支持配置服务器端 post-commit hook，因此无法在提交时自动触发索引重建。

解决方案：改用维护者本地轮询服务。由维护者在自己的本地机器上运行一个后台进程，定时执行 svn update 并检测文件变更，触发索引重建。轮询间隔在项目配置页可调（默认 5 分钟）。

2.2 索引结果提交到 SVN 实现全员同步
索引器生成的 .ltclaw_index/ 目录作为普通文件提交到 SVN。全体成员通过日常 svn update 自动获取最新索引，无需各自独立运行索引服务。

2.3 多成员一致性与配置基线
索引配置（SVN 路径、目录语义、ID 段划分、轮询间隔）统一存放在游戏项目配置页，并随 SVN 同步到全员。
所有成员使用相同的索引快照，避免"各自理解不同的数值体系"问题。
3. 总体架构
本节描述系统各组件的职责和数据流向。在阅读后续 UI 规划和开发清单时，可回到这里对照确认组件边界。

3.1 数据流
SVN（唯一数据源）
    │
    ▼ 定时 svn update（维护者本地机器）
SVN 本地轮询服务（svn_watcher.py）
    │ 检测文件变更
    ├─→ 数值表变更 ──→ AI 表索引器（table_indexer.py）
    │                      ├── 解析 Excel 结构 + 字段含义
    │                      └── 增量更新依赖图（dependency_resolver.py）
    │
    └─→ 文档变更 ───→ AI 文档索引器（document_indexer.py）
                           └── Markdown / Docx 分块 + 向量化
    │
    ▼ 索引结果写入
.ltclaw_index/（存入 SVN，全员 svn update 自动同步）
    ├── table_index.json     表结构 + 字段描述
    ├── doc_index.json       文档摘要 + 分块
    ├── dependency_graph.json 表间依赖
    └── change_history.json  滚动变更窗口
    │
    ▼ 查询侧
三层查询路由（query_router.py）
    ├── 精确查询（表名 / 字段名直查）
    ├── 关联查询（依赖图展开）
    └── 语义查询（向量相似度检索）
    │
    ├─→ game_query Skill ──→ Chat（自然语言问答）
    ├─→ 知识库（KnowledgeBase）
    ├─→ 文档生成 Skill ────→ 策划案 / 更新日志
    └─→ 文档库（DocLibrary）
3.2 组件关系一览
组件	类型	职责
svn_watcher.py	后端后台服务	轮询 SVN 变更，触发索引重建
table_indexer.py	后端模块	解析 Excel，AI 生成字段描述，维护依赖图
document_indexer.py	后端模块	解析 Markdown / Docx，分块向量化
dependency_resolver.py	后端模块	维护表间依赖图（AI 推断 + 规则校验）
index_committer.py	后端模块	将索引结果 svn commit 到仓库
query_router.py	后端 Skill	三层查询路由
game_query Skill	后端 Skill	接收自然语言，返回结构化查询结果
文档生成 Skill	后端 Skill	套模板生成策划案 / 更新日志
SVNSync 页面	前端页面	轮询状态、日志、手动触发
GameProject 配置页	前端页面	SVN 路径、目录语义、轮询间隔等配置
IndexMap 页面	前端页面	数值表全景可视化（列表 → 节点图）
DocLibrary 页面	前端页面	文档状态流转与搜索
KnowledgeBase 页面	前端页面	知识条目管理与健康度看板
Chat 扩展	前端扩展	模式选择 + 结构化卡片渲染
PlanPanel Drawer 扩展	前端扩展	引用表 / 字段高亮 + 产出文档
4. 信息分层
不同类型的数据有不同的来源、可信度和生命周期。在实现时必须严格区分，避免将 AI 产出的草稿当作确认知识处理。

4.1 三层数据定义
层级	名称	来源	可信度	存储位置
L1	源文档	SVN 原始文件（Excel / Markdown / Docx）	最高，人工维护	SVN 原始目录
L2	AI 产出文档	AI 生成的策划案草稿、更新日志草稿	中，需人工确认	SVN Docs/Drafts/ 目录
L3	索引元数据	AI 自动提取的字段描述、依赖图、向量索引	辅助参考，可能有误	.ltclaw_index/ 目录
4.2 "已确认"进入知识库的门槛
并非所有 AI 输出都可以直接进入知识库。知识库条目必须满足以下至少一个条件：

策划通过「确认调整」按钮明确批准了 AI 的描述。
文档在文档库中完成了草稿 → 已确认的状态流转。
维护者通过知识库页面手动录入或纠正了条目。
原则：AI 负责生成和维护，人类负责最终确认。知识库是经过人类校验的知识，不是原始 AI 输出的堆积。

5. UI / 交互规划
5.1 导航结构变更
现有导航在以下位置纯追加，不改动任何现有导航项。

control-group
└── svn-sync（新增）        SVN 同步状态页

game-group（新增整组）
├── index-map               索引地图
├── doc-library             文档库
└── knowledge-base          知识库

settings-group
└── game-project（新增）    游戏项目配置
5.2 Chat 作为策划工作平台
Chat 是策划最主要的工作入口，所有功能都通过 Chat 触达，不新增独立工作台页面。

模式选择栏（加在输入框上方）：

模式	触发行为
自由	当前默认行为，不变
策划案	进入策划案生成流程，调用文档生成 Skill
数值查询	调用 game_query Skill，返回 NumericCard
文档生成	出现文档类型选择（更新日志 / 规范文档等）
知识查询	查知识库，返回知识条目卡片
结构化卡片类型：

NumericCard：表名 + 字段列表 + 关键字段高亮 + 历史变更摘要
DesignDocCard：策划案草稿 + 数值配置区 + 待确认项 + 操作按钮
DocGenCard：文档类型 + 时间范围选择 + 预览区
Chat 消息渲染改动说明（影响范围极小）：

// 现有逻辑（保留不动）：
// message → 渲染为 Markdown 文字

// 新增判断（在现有渲染前加 switch）：
switch (message.type) {
  case 'table_ref':  return <NumericCard ... />
  case 'doc_draft':  return <DesignDocCard ... />
  case 'approval':   return <ApprovalCard ... />   // 已有组件，直接复用
  default:           // 原有 Markdown 渲染，完全不变
}
5.3 PlanPanel Drawer 扩展为"上下文面板"
PlanPanel Drawer 在现有「当前计划进度」基础上新增两个 Section，不改动现有逻辑。

PlanPanel Drawer
├── 当前计划进度（现有，不动）
├── 引用的数值表（新增）
│     └── 本次对话引用的表名 + 关键字段（高亮显示）
└── 产出文档（新增）
      └── 本次对话生成的草稿文档卡片 + 操作按钮
非阻塞型决策按钮放在 Drawer 里（不打断消息流）：

存入文档库：将草稿保存到 SVN Docs/Drafts/
确认调整：将数值建议确认进知识库
标记有误：标记 AI 描述错误，触发知识库纠错
阻塞型决策按钮放在消息流里（复用现有 ApprovalCard 模式）：

写入数值表前的确认：必须策划明确批准才执行
5.4 决策按钮放置原则
类型	放置位置	说明
阻塞型（写入操作）	消息流（ApprovalCard）	不批准则操作不执行，需要打断注意力
非阻塞型（存储/确认/标记）	PlanPanel Drawer	不影响对话流程，策划可随时处理
5.5 索引可视化分层策略
面对几百张数值表时，不能一次性全部展示，采用分层浏览：

层级	视图名称	内容
L1	系统全景	所有系统模块（战斗 / 背包 / 任务等）的分组气泡图
L2	系统内视图	单个系统内所有表及依赖关系
L3	表焦点视图	单张表的所有字段 + 直接依赖表
实现顺序：先上线分组列表视图（开发成本低，立刻可用），节点图（reactflow）作为 P3 体验升级，不阻塞主线。

6. 开发优先级与顺序
优先级定义
P0：基础设施，没有它其他功能都无法运行
P1：核心价值，直接解决最高频痛点
P2：提效工具，让体验更完整
P3：锦上添花，有了更好，没有也能用
P0 — 基础设施
目标：环境统一 + 本地轮询服务 + 索引自动生成

这是整个系统的地基。在 P0 完成之前，查询、文档生成、知识库等所有功能都无从实现。优先级最高，必须第一个做。

新增文件：

文件路径	说明
scripts/setup.sh	一键环境初始化，安装依赖，检查 svn 工具
scripts/setup.bat	Windows 版本
src/ltclaw_gy_x/game/svn_watcher.py	本地轮询服务主体
src/ltclaw_gy_x/game/table_indexer.py	Excel 解析 + AI 字段描述
src/ltclaw_gy_x/game/document_indexer.py	Markdown / Docx 分块
src/ltclaw_gy_x/game/dependency_resolver.py	依赖图维护
src/ltclaw_gy_x/game/index_committer.py	索引结果 svn commit
src/ltclaw_gy_x/app/routers/game_project.py	游戏项目配置 API
src/ltclaw_gy_x/app/routers/svn_sync.py	SVN 同步状态 API
console/src/pages/GameProject/	游戏项目配置页（前端）
console/src/pages/SVNSync/	SVN 同步状态页（前端）
改动现有文件：

文件路径	改动内容	性质
console/src/constants.ts	新增路由 key / path	纯追加
console/src/layouts/Sidebar.tsx	新增 control-group → svn-sync、settings-group → game-project	纯追加
任务清单：

 setup.sh / setup.bat：一键安装 Python 依赖、检查 svn 命令行工具
 游戏项目配置页：SVN 路径、目录语义配置（表目录 / 文档目录 / 索引目录）、ID 段划分表、轮询间隔（默认 5 分钟）、模板绑定
 SVN 本地轮询服务：定时 svn update + 变更检测，轮询间隔从配置读取；防并发锁
 AI 表索引器：解析 Excel（openpyxl），AI 生成每个字段的中文描述，输出 table_index.json
 AI 文档索引器：解析 Markdown / Docx，分块，输出 doc_index.json
 依赖图维护：AI 推断表间依赖（通过字段名相似度 + ID 段规则），增量更新 dependency_graph.json
 索引提交器：将 .ltclaw_index/ 变更 svn add + svn commit
 SVN 同步状态页：实时日志流、当前状态卡片（上次同步时间 / 索引覆盖表数）、手动触发按钮
验收标准：

✅ 新成员运行 bash setup.sh 后项目可启动
✅ 维护者启动轮询服务后，SVN 有文件变更 → 索引自动更新
✅ .ltclaw_index/ 内容正确生成并通过 svn commit 同步
✅ SVN 同步状态页可查看运行日志和手动触发
P1 — 核心查询能力
目标：策划可以在 Chat 里用自然语言问任何数值问题

P0 完成后，索引已经准备好，P1 的任务是让这些索引真正可以被策划使用。查询能力和知识库可以并行开发（无强依赖）。

新增文件：

文件路径	说明
src/ltclaw_gy_x/game/query_router.py	三层查询路由
src/ltclaw_gy_x/agents/skills/game_query/	game_query Skill
console/src/pages/Chat/ModeSelector/	模式选择栏组件
console/src/pages/Chat/cards/NumericCard.tsx	数值查询结果卡片
src/ltclaw_gy_x/app/routers/knowledge_base.py	知识库 API
console/src/pages/KnowledgeBase/	知识库页面（前端）
改动现有文件：

文件路径	改动内容	性质
console/src/pages/Chat/index.tsx	加模式选择栏 + 卡片类型判断渲染	扩展（原渲染逻辑不动）
console/src/pages/PlanPanel/index.tsx	加「引用的数值表」「产出文档」两个 Section	扩展（现有计划逻辑不动）
console/src/layouts/Sidebar.tsx	新增 game-group（含 knowledge-base）	纯追加
console/src/constants.ts	新增路由 key / path	纯追加
任务清单：

 三层查询路由：精确查询（表名 / 字段名）→ 关联查询（依赖图展开）→ 语义查询（向量检索）；三层依次命中即停
 game_query Skill：接收自然语言问题，调用查询路由，返回结构化 JSON（含表名、字段列表、高亮字段、历史变更摘要）
 Chat 模式选择栏：横向 Tab 标签，点击切换模式；自由模式下与现有行为完全一致
 NumericCard 组件：展示表名、字段列表、高亮关键字段、历史变更摘要；支持展开 / 折叠
 PlanPanel Drawer 扩展：新增两个 Section（引用的数值表 + 产出文档）；非阻塞操作按钮
 知识库后端：向量库读写（chromadb 或 faiss-cpu），经验知识结构化存储
 知识库页面：分类树（左侧）+ 条目列表（中间）+ 健康度看板（右侧）；支持手动确认 / 纠错
验收标准：

✅ 策划问"HitStopFrame 是什么" → Chat 返回 NumericCard，含字段描述和历史
✅ 策划问"剑士伤害相关的表" → Drawer 展开，列出引用的表和高亮字段
✅ [存入文档库] 按钮可点击（文档库 P2 完成后完整联通）
✅ 知识库健康度看板显示索引覆盖率
✅ 维护者可手动确认 / 纠正字段描述
P2 — 文档生成与文档库
目标：策划案和文档标准化产出，所有产出文档统一管理

P1 之后，策划已经可以查数据了。P2 让策划可以直接在 Chat 里生成标准格式的策划案和更新日志，并通过文档库统一管理。文档生成先做，文档库紧跟（有依赖关系）。

新增文件：

文件路径	说明
src/ltclaw_gy_x/agents/skills/doc_gen/	文档生成 Skill
console/src/pages/Chat/cards/DesignDocCard.tsx	策划案草稿卡片
console/src/pages/Chat/cards/DocGenCard.tsx	文档生成配置卡片
src/ltclaw_gy_x/app/routers/doc_library.py	文档库 API
console/src/pages/DocLibrary/	文档库页面（前端）
改动现有文件：

文件路径	改动内容	性质
console/src/pages/Chat/index.tsx	补充文档生成模式下的类型选择 UI	扩展
console/src/layouts/Sidebar.tsx	新增 game-group → doc-library	纯追加
console/src/constants.ts	新增路由 key / path	纯追加
任务清单：

文档生成
 文档生成 Skill：加载文档模板（策划案 / 更新日志 / 规范文档），从索引自动填充数值，生成结构化草稿
 DesignDocCard 组件：展示策划案草稿，含数值配置区（自动从索引填充）、待确认项列表、操作按钮
 DocGenCard 组件：选择文档类型（更新日志 / 系统规范 / 数值说明），选择时间范围（更新日志用），预览区
 Chat 文档类型选择：选择「文档生成」模式后出现二级选项（类型 + 关联系统）
 阻塞型写入确认：数值写入操作复用 ApprovalCard，策划批准后才执行
文档库
 文档库后端：读取 SVN Docs/ 目录文件，管理状态（草稿 / 待确认 / 已确认 / 归档），提供搜索接口
 文档库页面：分组列表（左侧按系统分组）+ 文档列表（中间）+ Markdown 预览（右侧）
 文档状态流转：草稿 → 待确认 → 已确认 → 归档；「已确认」状态的文档自动进入知识库
验收标准：

✅ "帮我写冰封术策划案" → DesignDocCard 展示，数值自动从索引填充
✅ 选"更新日志" + 时间范围 → DocGenCard 展示，内容从 change_history 生成
✅ 写入数值表操作弹出 ApprovalCard，批准后才执行
✅ Chat 里 [存入文档库] → 文档库立刻出现该草稿
✅ 策划确认文档 → 状态流转到已确认 → 自动进入知识库
✅ 历史文档可搜索、可预览
P3 — 索引可视化（可独立排期）
目标：项目全景可视化，降低新人上手成本

P3 不阻塞任何 P0-P2 功能，列表视图先上线（成本低），节点图（reactflow）作为后续体验升级单独排期。

新增文件：

文件路径	说明
src/ltclaw_gy_x/app/routers/index_map.py	索引地图 API（分组信息 + 依赖图 JSON）
console/src/pages/IndexMap/	索引地图页面（先上列表视图）
改动现有文件：

文件路径	改动内容	性质
console/src/layouts/Sidebar.tsx	新增 game-group → index-map	纯追加
console/src/constants.ts	新增路由 key / path	纯追加
任务清单：

 索引地图后端：输出分组信息 + 完整依赖图 JSON，支持按系统过滤
 列表视图：表分组列表 + 字段详情面板 + 依赖关系文字说明（无需 reactflow）
 系统分组配置：AI 自动推断分组 + 人工在配置页确认修改
 reactflow 节点图（P3 体验升级）：三层视图（系统全景 / 系统内 / 表焦点），点击下钻
新增前端依赖：reactflow（仅节点图任务需要，列表视图不依赖）

验收标准：

✅ 列表视图：可浏览所有表分组、查看字段详情
✅ 节点图：点击系统气泡 → 展开系统内表 → 点击表节点 → 展开字段和依赖（P3 节点图任务完成后）
✅ 新成员可通过列表视图理解数值体系全貌
7. 回归验证清单
每个优先级（P0 / P1 / P2）完成后，必须执行以下回归验证，确保现有功能未受影响。

原则：所有新功能均为扩展，不修改现有逻辑。但仍需在每个里程碑后人工验证一遍，防止意外回归。

每个优先级完成后验证：

□ Chat 对话正常（发消息 → 正常回复 → 原有 Markdown 渲染不变）
□ Agent 配置正常（新建 / 编辑 / 删除 Agent 流程正常）
□ Models 配置正常（模型列表加载正常，连接测试通过）
□ Backups 正常（备份创建 / 恢复流程正常）
□ Approvals 正常（工具守卫审批卡片正常显示和操作）
□ 侧边栏导航正常（现有导航项不缺失、点击正常跳转）
重点关注文件（每次改动后人工 review）：

console/src/pages/Chat/index.tsx（新增了卡片类型判断）
console/src/pages/PlanPanel/index.tsx（新增了两个 Section）
console/src/layouts/Sidebar.tsx（新增了导航项）
8. 技术栈与新增依赖
8.1 后端新增依赖
依赖	用途	必要性
chromadb 或 faiss-cpu	向量库（知识库 + 语义查询）	P1 必须，二选一
openpyxl	解析 Excel 数值表	P0 必须（现有项目可能已有）
python-docx	解析 Docx 文档	P0 文档索引器需要
svn 命令行工具	SVN 操作	P0 必须（系统级安装）
8.2 前端新增依赖
依赖	用途	必要性
reactflow	索引地图节点图	P3 节点图任务，其他阶段不需要
其他所有功能均基于现有技术栈扩展，无需新增依赖。

9. 未来扩展
9.1 冻结分支策略
当某个游戏版本进入封板期（数值冻结）时，建议：

从 SVN 创建冻结 Tag（例如 tags/v1.2.0-freeze）。
将当时的 .ltclaw_index/ 快照作为该版本的基线索引单独保存。
游戏项目配置页支持切换"当前活跃版本"，切换后查询和文档生成基于对应版本的索引。
若仓库已有 freeze 分支工作流，可直接复用其分支保护规则。

9.2 多游戏项目支持
当前设计默认单个游戏项目。未来若需要支持多个项目（如同时维护端游 + 手游两套数值体系），扩展点为：

game-project 配置页改为项目列表，支持多项目切换。
.ltclaw_index/ 按项目 ID 分目录存储。
Chat 模式选择栏增加项目上下文切换。
9.3 标签与归档
知识库和文档库均预留标签系统接口（tags 字段），初期不做 UI，P3 后可补充标签筛选和批量归档功能。

10. 开工检查清单
在开始第一行代码之前，请确认以下前提条件均已满足：

□ 现有项目本地可启动（ltclaw-gy-x app 正常运行）
□ 确认维护者本地 SVN 工作目录路径
□ 整理一份 ID 段划分表样本（如 hero:1000~1999）
□ 找 2~3 份现有文档样本放进 Docs/Templates/（作为文档生成模板参考）
□ 确认轮询间隔预期（建议默认 5 分钟）
□ 确认向量库选型（chromadb 部署简单，faiss-cpu 无服务器依赖）
□ 确认 Excel 数值表的实际文件名规律（方便索引器快速识别）