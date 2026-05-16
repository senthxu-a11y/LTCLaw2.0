# Workspace / Agent / Storage Manual Smoke 2026-05-16

执行信息:
- 执行日期: 2026-05-16
- 分支: foundation/workspace-agent-storage-from-m1
- commit: 60d1b0051a9409f09348ce80dfd0a0665dae278c
- 前端地址: http://127.0.0.1:5175
- 后端地址: http://127.0.0.1:18082
- Workspace Root: /Users/Admin/LTClawFullSmokeWorkspace
- 备用空 Workspace Root: /Users/Admin/LTClawFullSmokeWorkspace_Empty
- Project Root: /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project
- Table Root: Tables
- 使用 agent:
	- default
	- LTCLAW-GY.X_QA_Agent_0.2

状态约定:
- 仅使用 passed / failed / blocked。
- failed 表示产品链路和预期不一致，已经拿到明确复现证据。
- blocked 表示当前环境没有足够前置条件继续验证，且本轮按要求不擅自修复。

前置说明:
- 在全新未建 workspace 的初始状态下，default 先显示为 legacy viewer；这不是本轮验收的通过态。
- 按用户要求先执行 item 1 创建 Workspace Root 后，default 已切换为 admin，capability_source=workspace.agents，is_legacy_role_fallback=false，然后继续后续 23 项。

| # | 检查项 | 状态 | 备注 |
|---|---|---|---|
| 1 | 设置 Workspace Root | passed | UI 成功设置 /Users/Admin/LTClawFullSmokeWorkspace；workspace.yaml 已创建；Current Workspace Root 与落盘目录同步刷新。 |
| 2 | 设置 Project Root | passed | Project Root 成功保存为 minimal_project；Project Bundle Root 落在 /Users/Admin/LTClawFullSmokeWorkspace/projects/minimal_project-200c235d46f2。 |
| 3 | Table Root = Tables | passed | UI 中 configured root = Tables；Source Discovery 显示 resolved root 为 /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project/Tables。 |
| 4 | Source Discovery 显示 resolved path | passed | 首屏显示 configured root、resolved root、exists；发现 1 个 CSV：Tables/HeroTable.csv。 |
| 5 | Rule-only cold-start 首屏显示 progress | passed | 点击后约 2.5s 内出现 cold-start job panel，含 job_id、status、stage 与计数。 |
| 6 | cold-start succeeded | passed | job 385e1a6265104142843578c4901828a6 成功结束；discovered/raw/canonical/candidate 均为 1，warnings/errors 为 0。 |
| 7 | 进入 Map Editor | passed | /game/map 页面正常加载，不空白。 |
| 8 | source candidate 可见 | passed | Map Editor 显示 candidate map，diff review 中可见 system:herotable-csv 与 table:HeroTable。 |
| 9 | 保存 Formal Map | blocked | 按用户要求“不要自动保存 Formal Map”；仅确认 default/admin 下 Save Candidate as Formal Map 按钮可见且可用。 |
| 10 | Build Release | blocked | 按用户要求“不要自动 Build Release”；且本轮未先保存 Formal Map。 |
| 11 | Publish Current | blocked | 按用户要求“不要自动 Publish Current”；且本轮未生成 release。 |
| 12 | 打开 /numeric-workbench | passed | /numeric-workbench 页面正常加载，不空白。 |
| 13 | /game/workbench redirect 到 /numeric-workbench | passed | 访问 /game/workbench 后地址栏自动跳到 /numeric-workbench。 |
| 14 | 表列表可见 | passed | default 下 NumericWorkbench 成功显示 HeroTable，且可读到 1 行数据：HeroA / 100 / 20。 |
| 15 | 切换 QA agent | passed | 通过顶部 agent selector 成功切到 LTCLAW-GY.X_QA_Agent_0.2；UI 与 capability 状态均刷新为 viewer。 |
| 16 | Project Root 不消失 | passed | 切到 QA 后 Current Workspace Root 与顶层 Current Environment 的 Project Root 仍保留；最终 setup-status API 也返回同一 workspace/project 路径。 |
| 17 | Map 不消失 | passed | 切到 QA 后 candidate/source-latest 仍为 200，Map Editor 中 candidate 仍可读。 |
| 18 | Current Release 不消失 | blocked | 本轮未执行 Save Formal Map / Build Release / Publish Current，因此不存在 current release 可验证“切 agent 后仍可读”。 |
| 19 | Workbench 表不消失 | failed | 切到 QA 后仍能看到 HeroTable 页签，但表体为“暂无数据”；QA 的 rows 接口返回 412，未恢复到 default 下可读状态。 |
| 20 | viewer 写操作 disabled | passed | QA/viewer 下 Project 页 Rule-only 按钮 disabled；Map Editor 的 Build Candidate Review / Save Candidate as Formal Map disabled；NumericWorkbench 的导出/写回按钮 disabled。 |
| 21 | maintainer/admin 写操作 enabled | passed | default/admin 下 Rule-only cold-start 可执行且成功；Map Editor 中 Save Candidate as Formal Map 按钮可用。release/publish 动作本轮未执行。 |
| 22 | 切换另一个 Workspace 后旧数据不显示 | passed | 切到空 Workspace 后，旧 discovery/candidate/workbench 数据不再显示；当前 workspace 根已切换为 /Users/Admin/LTClawFullSmokeWorkspace_Empty。 |
| 23 | 切回原 Workspace 后数据恢复 | failed | 切回原 workspace 后 candidate map 与 NumericWorkbench 数据恢复，但 Project 页 Source Discovery 与 build readiness 未完全恢复，仍显示 0 / project_root_not_configured。 |

## 失败 / 阻塞明细

### 9. 保存 Formal Map
- 实际现象: default/admin 下按钮已可用，但本轮按用户要求不执行写入动作。
- 阻塞原因: 用户明确要求不要自动保存 Formal Map。
- 相关接口或前端路径:
	- 前端: /game/map

### 10. Build Release
- 实际现象: 本轮未构建 release。
- 阻塞原因: 用户明确要求不要自动 Build Release，且前置 Formal Map 未保存。
- 相关接口或前端路径:
	- 前端: /game/map

### 11. Publish Current
- 实际现象: 本轮未发布 current release。
- 阻塞原因: 用户明确要求不要自动 Publish Current，且前置 release 未构建。
- 相关接口或前端路径:
	- 前端: /game/map

### 18. Current Release 不消失
- 实际现象: default 与 QA 的 current release 查询均为 404 No current knowledge release is set。
- 阻塞原因: 本轮按限制未执行 Save Formal Map / Build Release / Publish Current，因此没有 current release 可以验证 agent 切换后的保持性。
- 相关接口或前端路径:
	- 接口: GET /api/agents/default/game/knowledge/releases/current
	- 接口: GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/knowledge/releases/current

### 19. Workbench 表不消失
- 实际现象: QA 下 HeroTable 标签还在，但表体为空，页面显示“暂无数据”。
- 复现路径: default 完成 cold-start 并确认 HeroTable 有数据 -> 顶部切 QA -> 打开 /numeric-workbench。
- 截止步骤: QA 的 rows 查询返回 412，导致 QA 侧无法继续读取同一张表的内容。
- 相关接口或前端路径:
	- 前端: /numeric-workbench
	- 接口: GET /api/agents/LTCLAW-GY.X_QA_Agent_0.2/game/index/tables/HeroTable/rows?offset=0&limit=500

### 23. 切回原 Workspace 后数据恢复
- 实际现象: 切回原 workspace 后 candidate map 与 NumericWorkbench 数据恢复，但 Project 页 Source Discovery 和 build readiness 仍未回到切换前状态。
- 复现路径: default -> 切到空 workspace -> 再切回 /Users/Admin/LTClawFullSmokeWorkspace -> 查看 /game/project。
- 截止步骤: 页面仍显示 discovery=0，build_readiness 仍是 project_root_not_configured / ready_for_discovery，而不是切换前已发现 Tables/HeroTable.csv 的状态。
- 相关接口或前端路径:
	- 前端: /game/project

## 关键接口摘要

### setup-status
- default:
	- 200 OK
	- active_workspace_root = /Users/Admin/LTClawFullSmokeWorkspace
	- project_root = /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project
	- project_root_exists = true
- QA:
	- 200 OK
	- active_workspace_root = /Users/Admin/LTClawFullSmokeWorkspace
	- project_root = /Users/Admin/LTCLaw2.0-foundation/examples/minimal_project
	- 与 default 指向相同 workspace / project

### capability-status
- default:
	- 200 OK
	- agent_id = default
	- role = admin
	- capability_source = workspace.agents
	- is_legacy_role_fallback = false
	- knowledge.candidate.write / knowledge.map.edit / knowledge.publish = true
- QA:
	- 200 OK
	- agent_id = LTCLAW-GY.X_QA_Agent_0.2
	- role = viewer
	- capability_source = game_user_config.my_role
	- is_legacy_role_fallback = true
	- knowledge.candidate.write / knowledge.map.edit / knowledge.publish = false

### source-latest
- default:
	- 200 OK
	- candidate_map 中包含 herotable-csv 与 HeroTable，源文件为 Tables/HeroTable.csv
- QA:
	- 200 OK
	- 与 default 返回相同 candidate_map 结构，可读链路保留

### current release
- default: 404, detail = No current knowledge release is set
- QA: 404, detail = No current knowledge release is set

### index/tables
- default:
	- 200 OK
	- 1 个表: HeroTable
	- 字段: ID(int), Name(str), HP(int), Attack(int)
- QA:
	- 200 OK
	- 也返回 HeroTable 摘要
	- 但 rows 读取仍返回 412，导致 QA NumericWorkbench 表体为空

## 结论
- passed: 17
- failed: 2
- blocked: 4
- 本轮相对上一轮已确认修复的旧问题:
	- default 在 workspace 创建后恢复为 admin，可执行 cold-start
	- cold-start job panel 与 source candidate 可见
	- default NumericWorkbench 可读到 HeroTable 数据
	- QA 切换后 Project Root 与 candidate map 不再直接丢失
	- viewer 写入口已前置 disabled
- 当前剩余失败项:
	- QA NumericWorkbench 仍无法读取行数据
	- 切回原 Workspace 后 Project 页 Source Discovery / readiness 没有完全恢复
- 当前不建议替换 main。
