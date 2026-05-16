# Workspace / Agent / Storage Foundation Closeout 2026-05-16

## 1. 开发基线
- 当前分支: foundation/workspace-agent-storage-from-m1
- baseline commit sha: f696c1f5774e538db10b5cbdc1509779f58bab10
- 当前开发基线来源 commit: 5b49d02bf7628cff16040a1afc9f8909d93ce077
- foundation 分支: foundation/workspace-agent-storage-from-m1
- 是否从 milestone-1-csv-cold-start-e2e-ready 创建: 是
- 备份分支: backup/m2-ui-experimental-main
- 说明: foundation worktree 从 M1 稳定 tag 建立，当前 main 仅保留为参考，不作为继续开发基线。

## 2. Data Workspace 目录结构
当前已落地并由 paths helper 驱动的目标结构:

```text
<workspace_root>/
├── workspace.yaml
├── projects/
│   └── <project_key>/
│       └── project/
│           ├── sources/
│           ├── indexes/
│           ├── maps/
│           ├── releases/
│           ├── rag/
│           └── runtime/
├── agents/
│   └── <agent_id>.yaml
├── sessions/
│   └── <agent_id>/
│       └── <session_id>/
├── audit/
└── cache/
```

## 3. Scope 边界
### Project-scoped
- Project Bundle Root
- source configs
- raw / canonical indexes
- candidate / formal maps
- releases / current release
- rag
- project runtime artifacts

### Agent-scoped
- workspace agent profile: agents/<agent_id>.yaml
- capability boundary

### Session-scoped
- workbench session dir
- proposals / drafts
- ui_state

### Cache-scoped
- llm cache
- retrieval cache
- temp cache

## 4. 旧路径兼容策略
- 未配置 active_workspace_root 时，仍走 working/game_data/projects 旧路径。
- 不自动迁移旧数据。
- 不删除旧 game_data/projects。
- legacy user_config.my_role 仍保留为 capability fallback。
- legacy user_config.agent_profiles 在配置了 workspace root 后会同步写入 workspace agent profile，但 workspace agent profile 优先。

## 5. 本次完成内容
### M1 冷启动保护
- DEFAULT_TABLES_INCLUDE_PATTERNS 改为仅默认包含 CSV / XLSX。
- TXT table 仅在显式 include 时被识别，不会默认进入 M1 rule-only cold-start。
- M1 CSV cold-start smoke 持续通过。

### docs/scripts optional 安全闭环
- docs.yaml / scripts.yaml 已接入 cold-start warning-only 扫描。
- roots 缺失、无可用文件、配置无效、扫描异常只写 warning / error payload，不阻塞 table-only cold-start 成功。
- docs/scripts warning 不影响 discovered_table_count / raw_table_index_count / canonical_table_count / candidate_table_count。
- 当前没有恢复下午 M2 的 markdown / docx / script evidence 全链路重建。

### Data Workspace Root
- 新增 workspace pointer: working/game_data/user/workspace_pointer.yaml
- 新增 workspace.yaml 读写与目录布局初始化。
- project bundle 根路径可切换到 <workspace_root>/projects/<project_key>。
- setup-status / storage API 返回当前 workspace root、pointer、workspace.yaml 路径和 workspace 目录信息。

### Agent / Permission / Project Scope
- request capability 解析优先读取 workspace agent profile。
- capability-status 返回:
  - agent_id
  - role
  - capabilities
  - capability_source
  - is_legacy_role_fallback
  - missing_required_capabilities
- default agent 在设置 workspace root 时自动创建。
- project data 与 agent session / capability 边界分离：切 agent 不再改变 project bundle 根路径。

### UI / Route
- Project 页首屏新增 Current Environment 区块。
- Project 页新增 Workspace Root 输入、设置、新建、复制路径能力。
- Project 页首屏显示 Workspace Root / Project Root / Project Bundle Root / Current Project / Current Agent / Role / Capability Source。
- Source Discovery 显示 configured root -> resolved root，并标记 exists / missing。
- cold-start 首屏卡显示 docs/scripts/warnings/errors 计数位。
- 新增 /game/workbench -> /numeric-workbench redirect。
- Map Editor 顶部在存在 source candidate 时提示“发现冷启动候选地图，请保存为正式地图”。

## 6. 自动化验证结果
### M1 smoke
- 命令: PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
- 结果: 通过
- 关键结果: discovered_table_count=1, raw_table_index_count=1, canonical_table_count=1, candidate_table_count=1, candidate_refs=["table:HeroTable"]

### Workspace / Agent / Storage 回归
- 命令: PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest -q tests/unit/game/test_paths.py tests/unit/app/test_agent_context.py tests/unit/routers/test_game_project_router.py -k 'workspace or capability_status or setup_status or project_root or storage_summary or agent_profile'
- 结果: 22 passed, 20 deselected

### docs/scripts optional 回归
- 命令: PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest -q tests/unit/game/test_cold_start_job_pipeline.py tests/unit/routers/test_game_knowledge_map_cold_start_job_router.py
- 结果: 9 passed

### M1 保护回归
- 命令:
  - PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest -q tests/unit/routers/test_game_project_router.py -k 'default_table_include_does_not_include_txt or accepts_txt_when_explicitly_included or source_discovery_finds_minimal_project_sample'
  - PYTHONPATH=$PWD/src /Users/Admin/LTCLaw2.0/.venv/bin/python -m pytest -q tests/unit/game/test_raw_index_rebuild.py
- 结果: 通过

### 前端静态验证
- 命令: cd console && pnpm exec tsc --noEmit
- 结果: 通过
- 命令: cd console && pnpm exec eslint src/pages/Game/GameProject.tsx src/pages/Game/MapEditor/index.tsx src/layouts/MainLayout/index.tsx
- 结果: 通过

## 7. Workspace smoke 结果
- 自动化覆盖: 已覆盖
- 覆盖内容:
  - workspace-root API 创建 pointer / workspace.yaml
  - setup-status 返回 active_workspace_root
  - project bundle root 写入 workspace/projects/<project_key>
- 人工 smoke: 未执行

## 8. Agent 切换 smoke 结果
- 自动化覆盖: 已部分覆盖
- 覆盖内容:
  - workspace agent profile 优先于 legacy user_config.agent_profiles
  - capability-status 反映 workspace.agents 与 legacy fallback
  - project bundle 根路径按 workspace/project 计算，不再按 agent workspace 目录分叉
- 人工 smoke: 未执行

## 9. Workspace 切换 smoke 结果
- 自动化覆盖: 已部分覆盖
- 覆盖内容:
  - active_workspace_root pointer 切换
  - workspace/projects / agents / sessions / cache 路径重定向
- 人工 smoke: 未执行

## 10. NumericWorkbench smoke 结果
- 自动化覆盖: 无页面级 smoke
- 静态验证: TS / ESLint 通过
- 风险: 未做实际浏览器点击验证

## 11. Route redirect smoke 结果
- 已新增前端路由 /game/workbench -> /numeric-workbench
- 静态验证: TS / ESLint 通过
- 人工 smoke: 未执行

## 12. M2 选择性恢复内容
- 本轮未选择性恢复下午 M2 parser。
- 没有引入 txtai。
- 没有恢复 SVN 主线。
- 没有引入 docs/scripts 阻塞 cold-start 的依赖链。

## 13. 未恢复的下午 M2 内容
- docs / scripts 多源重建链路
- markdown / docx / script evidence 全链路 smoke
- multi_source_project 的完整 UI / build / publish 收口
- docs/scripts canonical rebuild / release / rag 的正式解析与索引流水线

## 14. 是否建议用 foundation 替换 main
- 当前结论: 暂不建议直接替换 main
- 原因:
  - 后端 foundation 已稳定保护 M1 并完成 workspace/agent/storage 核心边界收口
  - 但尚未完成人工 smoke
  - docs/scripts optional 只完成了安全 warning-only 闭环，尚未恢复完整多源索引链路

## 15. 未覆盖风险
- docs/scripts optional 当前只做到 warning-only 安全闭环，尚未恢复真正的 docs/scripts rebuild 能力。
- 未执行浏览器级人工 smoke，Workspace 切换、Agent 切换、Map Editor 提示、NumericWorkbench 可见性仍缺少真实交互验证。
- 未执行多源 smoke，因此 foundation 当前明确优先保护 M1，而不是恢复 M2。
- manual smoke 模板已创建，但尚未执行任何手工验收项。

## 16. 已完成项
- foundation baseline 已提交并推送到远端 foundation/workspace-agent-storage-from-m1。
- Data Workspace Root / workspace pointer / workspace.yaml 已落地。
- Project-scoped / Agent-scoped / Session-scoped / Cache-scoped 路径边界已落地并有自动化覆盖。
- capability_source / is_legacy_role_fallback / missing_required_capabilities 已接入。
- /game/workbench -> /numeric-workbench redirect 已接入。
- docs/scripts optional warning-only 闭环已落地并有自动化覆盖。

## 17. 未完成项
- 人工 smoke 尚未执行。
- workspace 切换 E2E 尚未执行。
- agent 切换 E2E 尚未执行。
- 多源 M2 smoke 尚未恢复。

## 18. 下一步建议
- 先按 manual smoke 模板执行人工验收，确认 Workspace 切换 / Agent 切换 / NumericWorkbench / Release 读写权限。
- 在不扩新 source type 的前提下，再决定是否补 docs/scripts 的正式 raw/canonical rebuild。
- 在人工 smoke 和必要 E2E 补齐前，暂不建议替换 main。
