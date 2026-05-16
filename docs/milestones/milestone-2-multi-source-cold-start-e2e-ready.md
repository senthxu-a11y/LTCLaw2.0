# Milestone 2：Multi-Source Cold-start E2E Ready

## 1. 里程碑结论

Milestone 2 已达到以下状态：

Multi-Source Cold-start E2E Ready

本里程碑表示在不恢复 Legacy KB、不恢复 SVN 主线、不引入 txtai、且不绕过 Map/Release 边界的前提下，M1 的单源 CSV 冷启动基线已经扩展为可验证的多源冷启动闭环。

当前确认通过的完整链路为：

Project Setup
→ Source Discovery
→ Rule-only Cold-start Job
→ Raw Index / Raw Script Index / Raw Doc Index
→ Canonical Facts
→ Candidate latest
→ Save Formal Map
→ Build Release
→ Publish Current
→ RAG 查询 table/doc/script
→ NumericWorkbench 仅读取 table

## 2. 已通过范围

本里程碑已验证以下 source types：

### 2.1 Tables

- CSV
- XLSX（只读取第一个非空 sheet）
- TXT table（注释行跳过，首个非注释行为 header）

### 2.2 Documents

- Markdown
- TXT document
- DOCX（只读取标题和正文段落）

### 2.3 Scripts

- C# `.cs`
- Lua `.lua`
- Python `.py`

脚本范围仅限静态证据：

- 允许静态索引、symbol 提取、table/field 引用提取
- 不执行脚本
- 不做运行时分析

## 3. 已通过链路

1. Project Setup 可配置 tables sources
2. Project Setup 可配置 docs sources
3. Project Setup 可配置 scripts sources
4. Source Discovery 可同时发现 tables/docs/scripts
5. XLSX table 可进入 rule-only cold-start
6. TXT table 可进入 rule-only cold-start
7. Markdown document 可进入 Candidate → Release → RAG
8. TXT document 可进入 Candidate → Release → RAG
9. DOCX document 可进入 Candidate → Release → RAG
10. Script evidence 可进入 Candidate → Release → RAG
11. Candidate refs 同时包含 table/doc/script
12. Formal Map 可显式保存
13. Release 可显式构建
14. Current Release 可显式发布
15. RAG 可返回 table citation
16. RAG 可返回 doc citation
17. RAG 可返回 script citation
18. NumericWorkbench 仍只显示 table sources
19. M1 minimal CSV smoke 未回归

## 4. 验收样例

主验证项目：

examples/multi_source_project

已落库样例资产：

### 4.1 Tables

- examples/multi_source_project/Tables/HeroTable.csv
- examples/multi_source_project/Tables/WeaponConfig.xlsx
- examples/multi_source_project/Tables/EnemyConfig.txt

### 4.2 Docs

- examples/multi_source_project/Docs/BattleSystem.md
- examples/multi_source_project/Docs/CharacterGrowth.txt
- examples/multi_source_project/Docs/EconomyLoop.docx

### 4.3 Scripts

- examples/multi_source_project/Scripts/DamageCalculator.cs
- examples/multi_source_project/Scripts/CharacterGrowthService.lua
- examples/multi_source_project/Scripts/drop_formula.py

M1 基线样例仍为：

- examples/minimal_project/Tables/HeroTable.csv

## 5. 自动化验收命令

以下命令为本里程碑已经执行并确认通过的命令。

### 5.1 M2A Tables

1. `./.venv/bin/python -m pytest tests/unit/game/test_xlsx_table_source.py -q`
结果：已执行，通过

2. `./.venv/bin/python -m pytest tests/unit/game/test_txt_table_source.py -q`
结果：已执行，通过

### 5.2 M2B Documents

3. `./.venv/bin/python -m pytest tests/unit/game/test_markdown_doc_source.py -q`
结果：已执行，通过

4. `./.venv/bin/python -m pytest tests/unit/game/test_txt_doc_source.py -q`
结果：已执行，通过

5. `./.venv/bin/python -m pytest tests/unit/game/test_docx_doc_source.py -q`
结果：已执行，通过

### 5.3 M2C Scripts

6. `./.venv/bin/python -m pytest tests/unit/game/test_script_evidence_source.py -q`
结果：已执行，通过（2 passed）

### 5.4 M2D Multi-source Smoke

7. `./.venv/bin/python -m pytest tests/unit/scripts/test_run_map_cold_start_smoke.py tests/unit/scripts/test_run_multi_source_cold_start_smoke.py -q`
结果：已执行，通过（7 passed）

8. `./.venv/bin/python scripts/run_multi_source_cold_start_smoke.py --project examples/multi_source_project --rule-only`
结果：已执行，通过；发现 3 tables、3 docs、3 scripts，并成功完成 candidate / release / RAG smoke

9. `./.venv/bin/python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only`
结果：已执行，通过；M1 CSV smoke 保持成功

### 5.5 M1 回归

10. `./.venv/bin/python -m pytest tests/unit/game/test_cold_start_job_pipeline.py tests/unit/game/test_cold_start_release_rag_e2e.py tests/unit/routers/test_game_project_router.py tests/unit/routers/test_game_knowledge_map_source_latest_router.py -q`
结果：已执行，通过（28 passed）

## 6. 已验证能力

- Tables/docs/scripts 三类 source 的 project-local config 持久化
- Discovery 总览包含 tables/docs/scripts 计数
- Cold-start job 统计 discovered/raw/canonical/candidate 的 doc/script counts
- Candidate latest 持久化 table/doc/script refs
- Release artifact 同时包含 `table_schema`、`doc_knowledge`、`script_evidence`
- RAG 仅基于 current release 读取 evidence
- RAG citation 带 `ref`
- Script evidence 在 workspace session code index 缺失时可回退到项目 raw scripts
- Script ref 使用可读的文件 stem，例如 `script:DamageCalculator`
- NumericWorkbench 未扩展到 doc/script，仍保持 table-only 边界

## 7. Lane Closeout 记录

本里程碑对应的 lane closeout 记录如下：

- docs/completed-plans/m2a-2-txt-table-closeout.md
- docs/completed-plans/m2b-1-markdown-doc-source-closeout.md
- docs/completed-plans/m2b-2-txt-doc-closeout.md
- docs/completed-plans/m2b-3-docx-doc-closeout.md
- docs/completed-plans/m2c-1-script-evidence-closeout.md
- docs/completed-plans/m2d-small-real-project-smoke-closeout.md

补充说明：

- M2A-1 XLSX 单 sheet lane 已实现并通过 focused tests / M1 回归 / smoke，但当前未单独落一份 closeout 文档。

## 8. 明确未覆盖范围

以下范围不属于 Milestone 2，且不得误报为已支持：

- XLSX 多 sheet 同时入库
- 复杂 Excel 样式、公式求值、合并单元格语义
- JSON / YAML / TSV 冷启动
- 富文本 DOCX 复杂元素解析
- 图片、批注、修订、复杂表格解析
- 脚本执行、脚本运行时分析、沙箱执行
- 自动保存 Formal Map
- 自动 Build Release
- 自动 Publish Current
- 恢复 SVN watcher 主线
- 恢复 Legacy KB
- 接入 txtai
- 大规模真实项目导入压测
- 完整前端人工 UI 验收结论

## 9. 风险与约束

当前实现明确依赖以下约束：

- 多源冷启动仍是 rule-only 扩门，不是重构主链路
- 文档和脚本必须经过 Candidate / Formal Map / Release 才能进入 RAG
- Script evidence 第一版保持 deterministic，优先稳定可解释，而不是语言完备性
- Multi-source smoke 中的 RAG 校验使用显式 `focus_refs` 以保持确定性

## 10. 人工验收状态

以下结论尚未在本里程碑文档中宣称“已人工通过”，仍待后续单独记录：

- UI Project Setup 页面完整人工操作截图与录屏
- UI Discovery 总览人工确认
- Map Editor 候选与关系展示人工确认
- NumericWorkbench 在多源项目下的完整人工操作
- 前端最新版本命中确认

也就是说，本里程碑当前冻结的是：

后端链路 + 样例项目 + 自动化验证 + smoke 脚本验证

若需要追加产品/UI 验收，应单独补充人工 smoke 记录，而不是覆盖本文件中的自动化结论。

## 11. 结论

Milestone 2 代表 LTClaw 已从单一 CSV cold-start 基线，扩展为可验证的 multi-source cold-start 闭环，覆盖 tables、documents、scripts 三类 source，并仍然保持：

- M1 CSV 基线不回归
- Map-first 边界不被绕过
- Release-gated RAG 不被绕过
- NumericWorkbench table-only 约束不被破坏

后续迭代应在此基础上继续推进 UI 人工验收、真实项目更大规模验证或新的 source type，而不是回退到隐式路径、Legacy KB 或未受控的数据入口。
