# Workspace / Agent / Storage Manual Smoke 2026-05-16

执行信息:
- 执行日期: 2026-05-16
- 分支: foundation/workspace-agent-storage-from-m1
- commit: 34f2ecc53ff7833323e3f2b3426d79609c06d61c
- 前端地址: http://127.0.0.1:5175
- 后端地址: http://127.0.0.1:18082
- Workspace Root: /Users/Admin/LTClawSmokeWorkspace
- 备用空 Workspace Root: /Users/Admin/LTClawSmokeWorkspace_Empty
- Project Root: /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project
- 使用 agent:
	- default
	- LTCLAW-GY.X_QA_Agent_0.2

状态约定:
- 仅使用 passed / failed / blocked。
- failed 表示产品链路和预期不一致，已经拿到明确复现证据。
- blocked 表示当前环境没有足够前置条件继续验证，且本轮按要求不擅自修复。

| # | 检查项 | 状态 | 备注 |
|---|---|---|---|
| 1 | 设置 Workspace Root | passed | UI 成功设置 /Users/Admin/LTClawSmokeWorkspace；workspace.yaml 已创建；projects / agents / sessions / audit / cache 目录均存在。 |
| 2 | 设置 Project Root | passed | Project Root 成功保存为 minimal_project；Project Bundle Root 落在 /Users/Admin/LTClawSmokeWorkspace/projects/minimal_project-200c235d46f2。 |
| 3 | Table Root = Tables | passed | UI 中 configured root = Tables；Source Discovery 显示 resolved root 为 /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project/Tables。 |
| 4 | Source Discovery 显示 resolved path | passed | 首屏显示 configured root、resolved root、exists；发现 Tables/HeroTable.csv。 |
| 5 | Rule-only cold-start 首屏显示 progress | failed | Rule-only 按钮在 viewer 下可点击，但点击后直接 403，首屏没有出现 job_id/status/stage/progress 的 job panel。 |
| 6 | cold-start succeeded | failed | 未能启动 cold-start；后端 POST /api/agents/default/game/knowledge/map/cold-start-jobs 返回 403 Missing capability: knowledge.candidate.write。 |
| 7 | 进入 Map Editor | passed | /game/map 页面正常加载，不空白。 |
| 8 | source candidate 可见 | failed | 因 cold-start 未成功，Map Editor 显示 Candidate Map = No map available；GET /api/agents/default/game/knowledge/map/candidate/source-latest 返回 404 No source candidate map is available。 |
| 9 | 保存 Formal Map | blocked | 当前没有 source candidate，且 Map Editor 显示 Save Candidate as Formal Map disabled；本轮未发现 maintainer 配置入口。 |
| 10 | Build Release | blocked | 没有 formal map / candidate 基线，且没有 maintainer agent 可执行显式 Build Release。 |
| 11 | Publish Current | blocked | 没有 release 可发布，且没有 maintainer agent 可执行显式 Publish Current。 |
| 12 | 打开 /numeric-workbench | passed | /numeric-workbench 页面正常加载，不空白。 |
| 13 | /game/workbench redirect 到 /numeric-workbench | passed | 访问 /game/workbench 后地址栏自动跳到 /numeric-workbench。 |
| 14 | 表列表可见 | failed | NumericWorkbench 会话可打开，但表列表为空；GET /api/agents/default/game/index/tables?page=1&size=200 返回 items=[]。点击“重建本地表索引”后仍为 403。 |
| 15 | 切换 QA agent | passed | 通过顶部 agent selector 成功切到 LTCLAW-GY.X_QA_Agent_0.2；UI toast 显示“智能体切换成功”。 |
| 16 | Project Root 不消失 | failed | 切到 QA 后 Workspace Root 仍在，但 Project Root 和 Project Bundle Root 变成 -；GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/project/setup-status 返回 project_root=null。 |
| 17 | Map 不消失 | failed | 切到 QA 后 map 读链路随 project_root 丢失；GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/knowledge/map/candidate/source-latest 返回 400 Local project directory not configured。 |
| 18 | Current Release 不消失 | blocked | 本轮未先成功构建 release，无法验证“同一个 current release 仍可读”；同时 GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/knowledge/releases/current 返回 500 Knowledge release metadata is invalid。 |
| 19 | Workbench 表不消失 | blocked | default 下本就未出现表列表，无法验证切 QA 后“同一批表仍然可见”；QA 下 index/tables 仍为空。 |
| 20 | viewer 写操作 disabled | failed | viewer 下 Rule-only 冷启动构建和 NumericWorkbench“重建本地表索引”按钮都可点击，但点击后分别返回 403；写操作没有被前置 disabled。Map Editor 的 Save Candidate as Formal Map 倒是 disabled。 |
| 21 | maintainer 写操作 enabled | blocked | 当前仅发现两个 viewer agent，且智能体管理页没有 role / capability 配置入口；无法切到 maintainer 验证写链路。 |
| 22 | 切换另一个 Workspace 后旧数据不显示 | blocked | 由于 maintainer 链路未跑通、且 agent 切换已导致 project_root 丢失，本轮没有继续做 workspace 切换，以免把 agent 级问题和 workspace 隔离问题混在一起。 |
| 23 | 切回原 Workspace 后数据恢复 | blocked | 同第 22 项；前置 workspace 切换未执行。 |

## 失败 / 阻塞明细

### 5. Rule-only cold-start 首屏显示 progress
- 实际现象: viewer 下按钮可点击，但请求立即 403；首屏没有出现 job panel。
- 复现路径: Project 页面 -> Source Discovery 成功 -> 点击“Rule-only 冷启动构建”。
- 截止步骤: 点击按钮后 toast 报错 Missing capability: knowledge.candidate.write。
- 相关接口或前端路径:
	- 前端: /game/project
	- 接口: POST /api/agents/default/game/knowledge/map/cold-start-jobs
- 是否影响 M1 cold-start: 是，阻止通过 UI 跑 M1 rule-only cold-start。

### 6. cold-start succeeded
- 实际现象: cold-start 未创建 job，无法进入 succeeded。
- 复现路径: 同第 5 项。
- 截止步骤: 后端直接返回 403。
- 相关接口或前端路径:
	- 接口: POST /api/agents/default/game/knowledge/map/cold-start-jobs
- 是否影响 M1 cold-start: 是，UI 链路无法执行。

### 8. source candidate 可见
- 实际现象: Map Editor 显示 Candidate Map = No map available。
- 复现路径: cold-start 失败后进入 /game/map。
- 截止步骤: source-latest 返回 404。
- 相关接口或前端路径:
	- 前端: /game/map
	- 接口: GET /api/agents/default/game/knowledge/map/candidate/source-latest
- 是否影响 M1 cold-start: 间接影响，因 cold-start 失败导致后续地图候选不可见。

### 14. 表列表可见
- 实际现象: NumericWorkbench 中表列表为空；HeroTable 未出现。
- 复现路径: /numeric-workbench -> 继续默认会话。
- 截止步骤: 页面提示“当前没有可用表”；点击“重建本地表索引”后返回 403。
- 相关接口或前端路径:
	- 前端: /numeric-workbench
	- 接口: GET /api/agents/default/game/index/tables?page=1&size=200
	- 接口: POST /api/agents/default/game/index/rebuild
- 是否影响 M1 cold-start: 不直接影响 M1 构建，但影响 cold-start 后表工作台可用性。

### 16. Project Root 不消失
- 实际现象: 切换到 QA 后，Workspace Root 保持，但 Project Root / Project Bundle Root 变成空。
- 复现路径: Project 页面 -> 顶部 agent selector -> 切到 LTCLAW-GY.X_QA_Agent_0.2。
- 截止步骤: Project 页面 Current Environment 显示 Project Root = -。
- 相关接口或前端路径:
	- 前端: /game/project
	- 接口: GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/project/setup-status
- 是否影响 M1 cold-start: 是，agent 切换后无法继续基于当前项目执行任何游戏链路。

### 17. Map 不消失
- 实际现象: 切到 QA 后 map 相关读取报“Local project directory not configured”。
- 复现路径: 切换 QA -> 打开 /game/map 或调用 source-latest。
- 截止步骤: source-latest 返回 400。
- 相关接口或前端路径:
	- 前端: /game/map
	- 接口: GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/knowledge/map/candidate/source-latest
- 是否影响 M1 cold-start: 是，agent 切换后项目上下文被打断。

### 20. viewer 写操作 disabled
- 实际现象: viewer 下至少两个写入口没有预先 disabled，而是点击后 403。
- 复现路径:
	- Project 页面点击“Rule-only 冷启动构建”
	- NumericWorkbench 点击“重建本地表索引”
- 截止步骤: 后端分别返回 403 Missing capability。
- 相关接口或前端路径:
	- 前端: /game/project, /numeric-workbench
	- 接口: POST /api/agents/default/game/knowledge/map/cold-start-jobs
	- 接口: POST /api/agents/default/game/index/rebuild
- 是否影响 M1 cold-start: 是，会把权限问题延后到请求期暴露，阻断 UI 验收链路。

## 关键接口摘要

### setup-status
- default:
	- active_workspace_root: /Users/Admin/LTClawSmokeWorkspace
	- project_root: /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project
	- project_bundle_root: /Users/Admin/LTClawSmokeWorkspace/projects/minimal_project-200c235d46f2
	- project_key: minimal_project-200c235d46f2
	- build_readiness.next_action: ready_for_discovery
- QA:
	- active_workspace_root: /Users/Admin/LTClawSmokeWorkspace
	- project_root: null
	- project_bundle_root: null
	- build_readiness.blocking_reason: project_root_not_configured

### capability-status
- default:
	- agent_id: default
	- role: viewer
	- capability_source: workspace.agents
	- is_legacy_role_fallback: false
	- missing_required_capabilities: knowledge.build, knowledge.publish, knowledge.map.edit, knowledge.candidate.write, workbench.test.write, workbench.test.export, workbench.source.write
- QA:
	- agent_id: LTCLAW-GY.X_QA_Agent_0.2
	- role: viewer
	- capability_source: game_user_config.my_role
	- is_legacy_role_fallback: true

### source-latest
- default: 404, detail = No source candidate map is available
- QA: 400, detail = Local project directory not configured

### current release
- default: 404, detail = No current knowledge release is set
- QA: 500, detail = Knowledge release metadata is invalid

### index/tables
- default: 200, items = []
- QA: 200, items = []

## 结论
- passed: 8
- failed: 7
- blocked: 8
- 当前不建议替换 main。
- 直接阻塞项:
	- viewer 写入口没有统一前置 disabled，导致 cold-start / index rebuild 在请求期才 403
	- agent 切换会丢失 project_root / project_bundle_root，破坏 workspace/project 数据保持
	- 当前没有 maintainer agent，也没有可见的 role/capability 配置入口，无法完成显式 Save Formal Map / Build Release / Publish Current 验证

## Workspace Switch UI Follow-up

执行信息:
- 执行日期: 2026-05-16
- commit: 78a5f8409603112523f3377f369cae7540aa3cd8
- 前端地址: http://127.0.0.1:5175/game/project
- 后端地址: http://127.0.0.1:18082
- Workspace A: /Users/Admin/LTCLaw2.0-foundation/.tmp_manual_workspace_smoke/workspace-a
- Workspace B: /Users/Admin/LTCLaw2.0-foundation/.tmp_manual_workspace_smoke/workspace-b
- 使用 agent:
	- LTCLAW-GY.X_QA_Agent_0.2
	- default

| # | 检查项 | 状态 | 备注 |
|---|---|---|---|
| F1 | Project 页面显示 Workspace Switcher 卡片 | passed | 页面顶部出现“工作区 / Workspace”“当前工作区”“切换工作区”“打开/切换工作区”“新建工作区”等文案，且 guardrail 明确写出“切换工作区会切换 Project Data / Agent Profiles / Sessions / Cache；切 agent 只切换权限和 session”。 |
| F2 | 从空状态新建 Workspace A | passed | 点击“新建工作区”后，当前工作区卡片立刻刷新为 workspace-a，并显示 workspace.yaml 路径。toast 显示“已切换工作区：.../workspace-a”。 |
| F3 | Workspace A 切换后状态刷新闭环 | passed | Current Environment 的 Workspace Root 同步变为 workspace-a；“当前实际数据落盘目录”中的 Agent 目录、Session 目录、Cache 目录全部切到 workspace-a。 |
| F4 | 从 Workspace A 再切到 Workspace B | passed | 点击“新建工作区”后，当前工作区卡片立刻刷新为 workspace-b；Agent 目录和 Session 目录一起切到 workspace-b。 |
| F5 | 切换后浏览器刷新仍保持 Workspace B | passed | 手动 reload /game/project 后，Current Workspace Root 仍为 workspace-b，workspace.yaml 路径仍为 workspace-b/workspace.yaml。 |
| F6 | 切 agent 不切 Project Data | passed | 从 QA 切到 default 后，当前 agent 从 LTCLAW-GY.X_QA_Agent_0.2 变为 default，role 从 viewer 变为 admin，Agent 目录变为 workspace-b/agents/default；但 Current Workspace Root 保持 workspace-b，不回退也不丢失。 |
| F7 | 切 agent 后 capability / storage 一起刷新 | passed | 当前 role、capability_source、Current Agent、Agent 目录都已刷新到 default；Workspace Root 和 workspace.yaml 不变，符合“只切权限和 session”的预期。 |

结论:
- 本 follow-up 只验证 Workspace Switch UI 和切换后的状态刷新闭环。
- 结果: 7 passed, 0 failed, 0 blocked。
- 结论: 该页面现在已经具备清晰的 Workspace Switcher 表达，并且完成了“切换工作区 -> 重新加载 setup/capability/workspace-root/storage/cold-start 状态 -> 页面呈现同步更新”的闭环。
