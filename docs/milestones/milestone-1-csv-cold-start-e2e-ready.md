# Milestone 1：CSV Cold-start E2E Ready

## 1. 里程碑结论

Milestone 1 已通过，状态为：

CSV Cold-start E2E Ready

本里程碑结论不是单点功能通过，而是最小用户链路的完整闭环已经通过人工验收与针对性自动化验证。

当前确认通过的完整链路为：

Project Setup
→ Source Discovery
→ Rule-only Cold-start Job
→ Raw Index
→ Canonical Facts
→ Candidate latest
→ Map Editor
→ Save Formal Map
→ Build Release
→ Publish Current
→ RAG 查询
→ NumericWorkbench 读取 HeroTable

## 2. 已通过链路

1. Project Setup 配置 Local Project Root
2. Tables Source 配置 CSV 路径
3. Source Discovery 发现 HeroTable.csv
4. Rule-only Cold-start Job 成功
5. Raw Table Index 生成
6. CanonicalTableSchema 生成
7. Candidate latest.json 生成
8. latest_diff.json 生成
9. Map Editor 读取 latest source candidate
10. Save Formal Map 成功
11. Build Release 成功
12. Publish Current Release 成功
13. RAG 能回答 HeroTable 结构
14. NumericWorkbench 能看到并读取 HeroTable
15. 前端确认命中最新 UI / 正确后端代理

## 3. 验收样例

测试样例路径：

examples/minimal_project/Tables/HeroTable.csv

内容：

```csv
ID,Name,HP,Attack
1,HeroA,100,20
```

## 4. 自动化验收命令

以下命令为本里程碑应执行或已执行的验收命令。未实际执行的命令一律标记为“待人工补充”，不视为已通过。

已记录命令：

1. `python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only`
状态：待人工补充

2. `pytest tests/unit/game/test_raw_index_rebuild.py`
状态：待人工补充

3. `pytest tests/unit/game/test_canonical_facts_committer.py`
状态：待人工补充

4. `pytest tests/unit/game/test_cold_start_job_pipeline.py`
状态：待人工补充

5. `pytest tests/unit/routers/test_game_knowledge_map_source_latest_router.py`
状态：待人工补充

6. `cd console`
`npm test -- projectSetupHelpers`
状态：待人工补充

7. `cd console`
`npm test -- coldStartJobHelpers`
状态：待人工补充

附加说明：以下“如果存在则列入”的测试路径已核对，当前仓库中不存在，因此未列入本里程碑命令清单：

- `tests/unit/game/test_query_router_raw_index_fallback.py`
- `tests/unit/game/test_change_applier_raw_index_fallback.py`
- `tests/unit/routers/test_game_project_capability_status.py`

本轮实际已执行的补充验证命令：

1. `pytest tests/unit/routers/test_game_project_router.py tests/unit/game/test_change_applier.py tests/unit/game/test_cold_start_release_rag_e2e.py -q`
结果：已执行，通过（34 passed）

2. `cd console && pnpm exec tsc -b --noEmit .`
结果：已执行，通过

3. `pytest tests/unit/game/test_service.py tests/unit/game/test_query_router.py tests/unit/routers/test_game_index_router.py tests/unit/routers/test_game_workbench_router.py -q`
结果：已执行，通过（63 passed）

## 5. 人工验收结果模板

- 测试时间：2026-05-15
- 当前 commit：7dadb49a641a76d437e0f1d225b0017aa7ed9152（Milestone 1 业务基线，docs freeze 之前的最新功能提交）
- 前端访问地址：http://127.0.0.1:5174
- 后端地址：http://127.0.0.1:18080
- Vite proxy target：http://127.0.0.1:18080
- Frontend Build ID：待人工补充（当前 Vite dev 默认值为 `dev-frontend`）
- Project Root：examples/minimal_project
- Project Bundle Root：待人工补充
- Cold-start Job ID：待人工补充
- Candidate refs：latest.json、latest_diff.json
- Formal Map 状态：已人工确认可读取并可显式保存成功
- Release ID：待人工补充
- Current Release：已人工确认可显式发布成功，具体 release id 待人工补充
- RAG 测试问题：HeroTable 这张表有哪些字段？主键是什么？
- RAG 回答摘要：已人工确认可回答 HeroTable 结构，并能命中当前 release 上下文；具体回答文本待人工补充
- NumericWorkbench 表读取结果：已人工确认可读取 HeroTable；运行时可见表头 `ID, Name, HP, Attack`，样例行 `1, HeroA, 100, 20` 可被读取，`把hp翻倍` 场景可生成 HP=200 的工作台建议
- 结论：人工验收通过。Milestone 1 达到 CSV Cold-start E2E Ready，可冻结为项目基线

## 6. 已验证能力

- CSV Source Discovery
- CSV Rule-only Raw Index
- Canonical Facts 生成
- Candidate latest 持久化
- Diff Review 生成
- Map Editor source-latest 读取
- Formal Map 显式保存
- Release 显式构建
- Current Release 显式发布
- Map-gated RAG 查询
- NumericWorkbench raw index fallback
- 前端最新版本命中确认

## 7. 明确未覆盖范围

以下范围未包含在 Milestone 1 内：

- Excel / XLSX 冷启动
- TXT 游戏配置表冷启动
- XLSX 多 sheet
- JSON / YAML / TSV
- 真实项目大规模表批量导入
- LLM 字段语义增强
- LLM 自动生成整理脚本
- 新增字段
- 新增表
- 删除表
- 改表名
- 改路径
- 自动保存 Formal Map
- 自动 Build Release
- 自动 Publish Current
- SVN watcher
- Legacy KB 恢复

## 8. 冻结范围

短期冻结以下核心链路，不应随意改动：

- Project Setup
- Source Discovery
- Raw Index Rebuild
- Canonical Facts Committer
- Cold-start Job
- Source Candidate Store
- Map Editor source-latest
- Formal Map Save
- Release Build / Publish
- RAG current release query
- NumericWorkbench raw index fallback
- Vite proxy / frontend freshness

如需修改上述内容，必须单独开 Lane，并先补回归测试。

## 9. 下一轮建议

建议下一轮拆为以下三个 Lane：

### Lane 2A：XLSX 单 sheet 冷启动

目标：
支持 `.xlsx` 第一个非空 sheet 的 cold-start。

禁止：
不做多 sheet。
不做复杂 Excel 样式解析。
不做公式求值。
不做真实项目批量兼容。

### Lane 2B：TXT 游戏配置表冷启动

目标：
支持当前项目约定格式的 `.txt` 表。

前置条件：
明确 TXT 表格式规范，包括分隔符、表头行、注释行、字段说明行。

### Lane 2C：真实项目小规模批量表冷启动

目标：
从 1 张表扩展到 5-10 张真实 CSV 表，验证路径、编码、主键、重复表名、错误诊断。

## 10. 结论

Milestone 1 代表 LTClaw 的 Map-first / RAG / NumericWorkbench 最小闭环已经建立。后续功能必须基于这个稳定链路向外扩展，不应再回退到 Legacy KB 或隐式路径管理。

## 11. 提交到仓库

这份冻结文档必须提交到远端仓库，作为 Milestone 1 的正式项目基线记录。

提交要求：

1. 本次提交必须是 docs-only commit。
2. 不允许修改任何业务代码。
3. 不允许修改测试代码。
4. 不允许修改配置文件。
5. 不允许顺手重构。
6. 不允许补功能。
7. 不允许改 Excel/TXT 支持范围。
8. 不允许改 cold-start / Map / RAG / NumericWorkbench 链路。

提交前必须执行：

`git status`

确认只有以下文件变更：

`docs/milestones/milestone-1-csv-cold-start-e2e-ready.md`

如果出现其他文件变更，必须停止并汇报，不允许提交。

提交命令：

`git add docs/milestones/milestone-1-csv-cold-start-e2e-ready.md`
`git commit -m "docs: freeze milestone 1 csv cold-start e2e"`
`git push origin main`

提交后必须执行：

`git status`
`git rev-parse HEAD`

并记录 commit hash。

## 12. 打 tag

文档 push 到 `origin/main` 成功后，打 tag。

Tag 名称：

`milestone-1-csv-cold-start-e2e-ready`

Tag 的含义：

CSV 冷启动 E2E 链路已经通过人工验收，并冻结为 Milestone 1 基线。

执行命令：

`git tag milestone-1-csv-cold-start-e2e-ready`
`git push origin milestone-1-csv-cold-start-e2e-ready`

打 tag 前必须确认：

1. 文档 commit 已成功 push 到 `origin/main`。
2. `git status` clean。
3. 当前 `HEAD` 是刚才的 docs-only commit。
4. 没有未提交代码修改。

如果 tag 已存在，不要覆盖，不要 force push。请停止并汇报：

`tag already exists`

## 13. 最终交付回复格式

完成后必须按以下格式回复：

### 变更类型

docs-only

### 新增文件

docs/milestones/milestone-1-csv-cold-start-e2e-ready.md

### Commit

<commit hash>

### Push 状态

已推送到 origin/main / 未推送，原因是...

### 工作区状态

clean / not clean

### 是否触碰代码

否

### 是否自动打 tag

是

### Tag

milestone-1-csv-cold-start-e2e-ready

### Tag Push 状态

已推送 / 未推送，原因是...

### 测试结果记录

说明哪些测试是已执行，哪些是待人工补充。
不要编造。

### 待人工补充项

列出文档里仍需人工填写的验收记录字段。