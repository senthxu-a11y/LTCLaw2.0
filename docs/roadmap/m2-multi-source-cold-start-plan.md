# LTClaw M2 多源知识冷启动详细施工计划

版本：M2-MULTI-SOURCE-COLD-START-PLAN-01
状态：Roadmap Draft
前置基线：Milestone 1 - CSV Cold-start E2E Ready
冻结记录：docs/milestones/milestone-2-multi-source-cold-start-e2e-ready.md
目标产品线：LTClaw Game Knowledge Workspace
目标读者：Coding Agent / 技术负责人 / 评审人员 / 人工验收人员

## 0. 一句话结论

M2 的目标不是替换 M1，而是在不破坏现有 CSV 冷启动闭环的前提下，把 LTClaw 从单一 CSV 表格冷启动扩展为本地项目多源知识冷启动闭环：

```text
Table Sources
+ Document Sources
+ Script Evidence Sources
-> Source Discovery
-> Source Index
-> Canonical Knowledge
-> Candidate Map
-> Formal Map
-> Release
-> RAG / NumericWorkbench
```

本计划是施工计划，不是代码实现。

## 1. 当前 M1 CSV Cold-start E2E 基线

### 1.1 M1 已完成能力

当前已跑通的 M1 主链路：

```text
Project Setup
-> Source Discovery
-> Rule-only Cold-start Job
-> Raw Index
-> Canonical Facts
-> Candidate latest
-> Map Editor
-> Save Formal Map
-> Build Release
-> Publish Current
-> RAG 查询
-> NumericWorkbench 读取 HeroTable
```

M1 当前基线是：

```text
CSV Cold-start E2E Ready
```

### 1.2 M1 不可破坏项

M2 任意 Lane 完成后，都必须保证以下能力仍可用：

- /game/project 能保存 Project Root。
- /game/project 能保存 Table Source。
- /game/project 能执行 Source Discovery。
- /game/project 能启动 Rule-only Cold-start Job。
- CSV HeroTable.csv 仍能生成 Raw Index。
- CSV HeroTable.csv 仍能生成 Canonical Facts。
- CSV HeroTable.csv 仍能进入 Candidate Map。
- Candidate latest 仍能被 Map Editor 读取。
- Formal Map 仍能显式保存。
- Build Release 仍能显式触发。
- Publish Current 仍能显式触发。
- RAG 仍只消费 Current Release。
- NumericWorkbench 仍能读取 CSV 表。
- 前端仍命中最新 UI，不回退到旧 dist 或旧后端。

### 1.3 M1 固定回归命令

每个 M2 Lane 完成后都必须执行：

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
pytest tests/unit/game/test_raw_index_rebuild.py
pytest tests/unit/game/test_canonical_facts_committer.py
pytest tests/unit/game/test_cold_start_job_pipeline.py
pytest tests/unit/routers/test_game_knowledge_map_source_latest_router.py
```

如果命令不存在、路径不同或当前项目命名已变化，Agent 必须停止并汇报，不允许伪造通过结果。

## 2. M2 总目标

M2 支持三类数据源：

```text
1. Table Sources
   CSV / XLSX single-sheet / TXT table

2. Document Sources
   Markdown / TXT document / DOCX

3. Script Evidence Sources
   C# / Lua / Python / 配置脚本文本
```

统一目标：

```text
Source -> Canonical -> Candidate Map -> Formal Map -> Release -> RAG
```

但 NumericWorkbench 只处理表格类数据：

```text
table:* only
```

## 3. 全局硬约束

- 每个 Lane 都不能影响 M1 CSV Cold-start E2E。
- 每个 Lane 都必须跑 M1 回归。
- SVN 不属于当前主线。
- 不恢复 Legacy KB。
- 不接 txtai。
- RAG 不能绕过 Map。
- 文档不能直接喂给 RAG。
- NumericWorkbench 只处理表格类数据。
- DOCX 第一版只解析正文和标题，不处理图片、批注、修订、嵌入对象、复杂表格。
- XLSX 第一版只读取第一个非空 sheet。
- TXT table 和 TXT document 必须分开配置。
- Script evidence 第一版只做静态证据，不执行代码。
- 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish Current。
- 不自动写回文档。
- 不自动写回脚本。
- 不自动生成脚本。
- 不扩大管理员与普通策划权限边界。

### 3.1 SVN 与外部知识库边界

M2 禁止恢复或引入以下主线：

```text
SVN watcher
SVN sync
SVN commit
SVN status
Legacy KB
```

LTClaw 在本轮只管理本地 Project Root 下的文件。

### 3.2 RAG 入口边界

禁止：

```text
Markdown / TXT document / DOCX / Script -> 直接喂给 RAG
```

必须：

```text
Source
-> Canonical
-> Candidate Map
-> Formal Map
-> Release
-> RAG
```

RAG 只允许读取 Current Release。

### 3.3 数据类型边界

必须显式区分：

```text
TXT table != TXT document
XLSX table != DOCX document
```

不同 source type 必须进入不同 canonical artifact：

```text
表格 -> table_schema / table facts
文档 -> doc_knowledge / doc chunks
脚本 -> script_evidence / script refs
```

## 4. Source 类型矩阵

| Source Type | 输入格式 | Canonical / Release Artifact | Map Ref | 进入 RAG | 进入 NumericWorkbench |
| --- | --- | --- | --- | --- | --- |
| Table | .csv / .xlsx / .txt(table) | table_schemas.jsonl | table:<table_id> | 是，经 Map 和 Release | 是 |
| Document | .md / .txt(document) / .docx | doc_knowledge.jsonl | doc:<doc_id> | 是，经 Map 和 Release | 否 |
| Script Evidence | .cs / .lua / .py | script_evidence.jsonl | script:<script_id> | 是，经 Map 和 Release | 否 |

补充要求：

- Table source 可以进入 NumericWorkbench。
- Document 与 Script source 不得显示在 NumericWorkbench。
- RAG citation 必须能区分 table / doc / script。
- Script evidence 只保留静态文本证据与 symbol 信息，不执行任何代码。

## 5. 多源测试项目规划

### 5.1 新建测试项目

新增测试项目：

```text
examples/multi_source_project/
├── Tables/
├── Docs/
└── Scripts/
```

约束：

- 不污染 examples/minimal_project。
- M1 minimal project 保持稳定。
- 多源测试项目只用于 M2 lane 验证与 smoke。

### 5.2 表格测试文件

#### Tables/HeroTable.csv

```csv
ID,Name,HP,Attack
1,HeroA,100,20
2,HeroB,120,25
```

验收要求：

- table:HeroTable
- fields = ID, Name, HP, Attack
- primary_key = ID
- row_count = 2
- NumericWorkbench 可读

#### Tables/WeaponConfig.xlsx

建议首个非空 sheet 名称：Weapons

表格内容：

| ID | WeaponName | Attack | Rarity |
| --- | --- | ---: | --- |
| 1001 | IronSword | 12 | Common |
| 1002 | FireStaff | 25 | Rare |

验收要求：

- Source Discovery 识别 xlsx。
- 只读取第一个非空 sheet。
- table_id = WeaponConfig。
- fields = ID, WeaponName, Attack, Rarity。
- row_count = 2。
- NumericWorkbench 可读。

#### Tables/EnemyConfig.txt

```text
# Enemy config table
ID	Name	HP	Attack
2001	Slime	30	5
2002	Goblin	50	8
```

验收要求：

- TXT table 被识别为 table source。
- 忽略 # 或 // 注释行。
- 第一行非注释行为 header。
- table_id = EnemyConfig。
- fields = ID, Name, HP, Attack。
- row_count = 2。
- NumericWorkbench 可读。

### 5.3 文档测试文件

#### Docs/BattleSystem.md

```markdown
# Battle System Design

## Overview

The battle system uses HP and Attack values from HeroTable and WeaponConfig.

## Damage Formula

Base damage is calculated from character Attack plus weapon Attack.

## Related Tables

- HeroTable
- WeaponConfig

## Notes

DamageCalculator.cs implements the current prototype formula.
```

验收要求：

- doc:BattleSystem
- title = Battle System Design
- chunks >= 3
- related_refs 包含 table:HeroTable 与 table:WeaponConfig
- RAG 能引用该 doc
- NumericWorkbench 不显示该 doc

#### Docs/CharacterGrowth.txt

```text
Character Growth Design

Overview
Characters grow by increasing level, HP, and Attack.

Related Tables
HeroTable is used as the base character table.

Rules
HP grows faster than Attack.
Early levels should be cheap.
```

验收要求：

- TXT document 被识别为 document source。
- doc:CharacterGrowth。
- 按段落 chunk。
- RAG 能回答角色成长设计。
- 不进入 NumericWorkbench。

#### Docs/EconomyLoop.docx

建议正文内容：

```text
Economy Loop Design

The economy loop connects battle rewards, character growth, and equipment upgrades.

Gold is used to upgrade characters and weapons.

Related Tables:
- HeroTable
- WeaponConfig
```

验收要求：

- DOCX document 被识别。
- doc:EconomyLoop。
- 只读取标题和正文段落。
- 忽略图片、样式、批注、修订与复杂表格。
- RAG 可引用。
- NumericWorkbench 不显示。

### 5.4 脚本测试文件

#### Scripts/DamageCalculator.cs

```csharp
public class DamageCalculator
{
    public int CalculateDamage(int heroAttack, int weaponAttack)
    {
        return heroAttack + weaponAttack;
    }
}
```

验收要求：

- script:DamageCalculator
- 识别类名 DamageCalculator
- 识别函数 CalculateDamage
- summary 包含 damage / attack
- RAG 可引用 script evidence

#### Scripts/CharacterGrowthService.lua

```lua
local CharacterGrowthService = {}

function CharacterGrowthService.calculate_hp(base_hp, level)
    return base_hp + level * 10
end

return CharacterGrowthService
```

验收要求：

- script:CharacterGrowthService
- 识别函数 calculate_hp
- RAG 可引用

#### Scripts/drop_formula.py

```python
def calculate_gold_reward(stage_level: int) -> int:
    return 100 + stage_level * 20
```

验收要求：

- script:drop_formula
- 识别函数 calculate_gold_reward
- RAG 可引用

## 6. Lane 切分与开发顺序

建议分支：

```text
m2-0-multi-source-plan
m2a-1-xlsx-single-sheet
m2b-1-markdown-doc-source
m2a-2-txt-table
m2b-2-txt-doc
m2b-3-docx-doc
m2c-1-script-evidence
m2d-small-real-project-smoke
```

开发顺序建议：

1. M2-0：多源规划落仓库。
2. M2A-1：XLSX single-sheet table。
3. M2B-1：Markdown document source。
4. M2A-2：TXT table。
5. M2B-2：TXT document。
6. M2B-3：DOCX document。
7. M2C-1：Script evidence。
8. M2D：真实项目小规模多源冷启动 smoke。

强约束：

- 每个 Lane 只解决一个 source type 或一个规划任务。
- 禁止在一个 PR 或一次提交中混合多个 source type。
- 禁止借机重构 Cold-start 主状态机、Map Editor 保存逻辑、Release 语义、RAG 主逻辑、NumericWorkbench 写回逻辑。
- 新 source type 第一版必须可配置关闭，不能默认扫描整个项目下所有 .txt / .md / .cs 文件。

## 7. 每个 Lane 的 Checklist

### 7.1 M2-0 多源规划落仓库

允许修改：

```text
docs/roadmap/m2-multi-source-cold-start-plan.md
```

禁止修改：

```text
src/**
console/src/**
tests/**
examples/**
配置文件
```

实现 Checklist：

- 新增或更新 M2 多源冷启动计划书。
- 明确 Table / Document / Script 三类 source。
- 明确每类 source 的输入格式。
- 明确每类 source 的 output artifact。
- 明确每类 source 的 Map ref。
- 明确每类 source 是否进入 RAG。
- 明确每类 source 是否进入 NumericWorkbench。
- 明确 examples/multi_source_project 规划与样例内容。
- 明确各 Lane 的实现、测试、人工验收、评审、closeout、回滚要求。
- 明确禁止范围、风险与对策、分支与提交策略。
- 明确 M1 回归必须保留。

自动化测试 Checklist：

- 以文档评审为主，无代码测试。
- 提交前执行 git status。
- 提交前执行 git diff --name-only。
- 确认只有 docs/roadmap/m2-multi-source-cold-start-plan.md 发生变化。

人工验收 Checklist：

- 文档结构完整。
- 所有必填要求已覆盖。
- 所有硬约束已显式写明。
- 没有混入代码实现内容。

### 7.2 M2A-1 XLSX single-sheet table

实现 Checklist：

- Source Discovery 识别 .xlsx。
- .xlsx 状态从 recognized 升级到 available。
- cold_start_supported = true。
- 只读取第一个非空 sheet。
- 第一行作为 header。
- 后续行为 data rows。
- 空行跳过。
- 生成 table_id。
- 生成 raw table index。
- 生成 canonical table schema。
- Candidate Map 包含 table:WeaponConfig。
- NumericWorkbench 能读取 rows。
- CSV M1 smoke 不受影响。

自动化测试 Checklist：

- 新增 tests/unit/game/test_xlsx_table_source.py。
- xlsx 文件被 discovery 识别为 available。
- 第一个非空 sheet 被读取。
- header 正确。
- rows 正确。
- 空 sheet 被跳过。
- 多 sheet 文件只读第一个非空 sheet。
- 公式单元格行为必须在测试中写清是不用求值还是仅使用 cached value。
- M1 回归命令全部通过。

人工验收 Checklist：

- Project Setup 指向 examples/multi_source_project。
- Source Discovery 发现 WeaponConfig.xlsx。
- Rule-only Cold-start succeeded。
- Candidate refs 包含 table:WeaponConfig。
- Map Editor 可见 WeaponConfig。
- Save Formal Map 成功。
- Build Release 成功。
- RAG 询问 WeaponConfig 有哪些字段时，回答包含 ID、WeaponName、Attack、Rarity。
- NumericWorkbench 显示 IronSword 与 FireStaff。
- 重新跑 M1 HeroTable CSV smoke 通过。

### 7.3 M2B-1 Markdown document source

实现 Checklist：

- Document Source Discovery 识别 .md。
- Markdown parser 读取一级标题。
- 按 heading 切 section。
- 生成稳定 doc_id。
- 保留 source_path。
- 生成 doc chunks。
- 提取简单 related_refs，例如 HeroTable、WeaponConfig。
- 生成 CanonicalDocKnowledge。
- Candidate Map 包含 doc:BattleSystem。
- Release artifact 包含 doc knowledge。
- RAG context 能检索 doc chunks。
- citation 能显示 doc:BattleSystem。
- NumericWorkbench 不显示 doc。

自动化测试 Checklist：

- 新增 tests/unit/game/test_markdown_doc_source.py。
- Markdown 文件被 discovery 识别。
- 一级标题提取为 title。
- 二级标题切成 chunks。
- source_path 保留。
- doc_id 生成稳定。
- related_refs 可识别 HeroTable 与 WeaponConfig。
- Candidate Map 包含 doc ref。
- Release artifact 包含 doc chunk。
- RAG context 可命中文档。
- NumericWorkbench 不出现 doc。
- M1 回归命令全部通过。

人工验收 Checklist：

- Project Setup 配置 Docs source。
- Discovery 显示 docs count > 0。
- Cold-start 生成 Candidate Map。
- Map Editor candidate 概览显示 docs > 0。
- Save Formal Map 成功。
- Build Release 成功。
- RAG 询问战斗系统设计如何规定伤害公式时，回答引用 BattleSystem.md。
- Citation 包含 doc:BattleSystem。
- NumericWorkbench 表列表不包含 BattleSystem。
- M1 CSV smoke 仍通过。

### 7.4 M2A-2 TXT table

实现 Checklist：

- TXT table source 必须显式配置，不自动把所有 txt 当表。
- Source Discovery 根据 table source include 识别。
- 编码优先 utf-8。
- 分隔符为 tab。
- 注释行 # 或 // 跳过。
- 表头行为第一行非注释行。
- 后续非空非注释行为数据行。
- rows 正确。
- table_id = EnemyConfig。
- Candidate Map 包含 table:EnemyConfig。
- NumericWorkbench 可读。
- TXT document 不得误识别为 table。
- M1 CSV smoke 仍通过。

自动化测试 Checklist：

- 新增 tests/unit/game/test_txt_table_source.py。
- tab 分隔成功。
- 注释行跳过。
- 空行跳过。
- header 提取正确。
- rows 提取正确。
- TXT document 不误入 table source。
- M1 回归命令全部通过。

人工验收 Checklist：

- Discovery 发现 EnemyConfig.txt。
- Candidate refs 包含 table:EnemyConfig。
- NumericWorkbench 能读 Slime 与 Goblin。
- RAG 能回答 EnemyConfig 字段。
- TXT document 不出现在 Workbench。
- M1 CSV smoke 通过。

### 7.5 M2B-2 TXT document

实现 Checklist：

- TXT document source 必须显式配置。
- 不与 TXT table 混淆。
- 按空行或标题切 chunk。
- 生成 doc_id。
- 生成 doc chunks。
- Candidate Map 包含 doc:CharacterGrowth。
- RAG 可引用。
- NumericWorkbench 不显示。
- M1 CSV smoke 仍通过。

自动化测试 Checklist：

- 新增 tests/unit/game/test_txt_doc_source.py。
- TXT document 被 discovery 识别为 document source。
- chunk 切分稳定。
- doc_id 稳定。
- Candidate Map 包含 doc ref。
- NumericWorkbench 不出现 doc。
- M1 回归命令全部通过。

人工验收 Checklist：

- Discovery docs count 包含 CharacterGrowth.txt。
- Candidate refs 包含 doc:CharacterGrowth。
- RAG 能回答角色成长规则。
- Workbench 不显示 CharacterGrowth。
- M1 CSV smoke 通过。

### 7.6 M2B-3 DOCX document

实现 Checklist：

- DOCX source discovery。
- 读取标题与正文段落。
- 按标题或段落切 chunk。
- 保留 source_path。
- 生成 doc_id。
- Candidate Map 包含 doc:EconomyLoop。
- Release artifact 包含 doc chunk。
- RAG 可引用。
- NumericWorkbench 不显示。
- M1 CSV smoke 仍通过。

自动化测试 Checklist：

- 新增 tests/unit/game/test_docx_doc_source.py。
- DOCX 被 discovery 识别。
- 标题提取正确。
- 正文段落读取正确。
- 图片、批注、修订、复杂表格被忽略。
- Candidate Map 包含 doc ref。
- Release artifact 包含 doc chunk。
- NumericWorkbench 不出现 doc。
- M1 回归命令全部通过。

人工验收 Checklist：

- Discovery docs count 包含 EconomyLoop.docx。
- Candidate refs 包含 doc:EconomyLoop。
- RAG 能回答经济循环设计。
- Workbench 不显示 EconomyLoop。
- M1 CSV smoke 通过。

### 7.7 M2C-1 Script evidence

实现 Checklist：

- Script source discovery。
- C# 文件识别。
- Lua 文件识别。
- Python 文件识别。
- script_id 生成。
- 静态提取类名、函数名、symbol。
- 提取可能表名引用。
- 保留 snippets。
- Candidate Map 包含 script refs。
- Release artifact 包含 script evidence。
- RAG 可引用 script evidence。
- NumericWorkbench 不显示 scripts。
- M1 CSV smoke 仍通过。

自动化测试 Checklist：

- 新增 tests/unit/game/test_script_evidence_source.py。
- 三种脚本类型均被 discovery 识别。
- symbol 提取正确。
- snippet 保留正确。
- Candidate Map 包含 script ref。
- Release artifact 包含 script evidence。
- NumericWorkbench 不出现 script。
- M1 回归命令全部通过。

人工验收 Checklist：

- Discovery scripts count > 0。
- Candidate refs 包含 script:DamageCalculator。
- RAG 能回答哪个脚本实现伤害计算。
- Workbench 不显示 script。
- M1 CSV smoke 通过。

### 7.8 M2D 真实项目小规模多源冷启动 smoke

实现 Checklist：

- Project Setup 能配置 tables、docs、scripts。
- Discovery 总览显示 tables/docs/scripts。
- 错误诊断清楚。
- Cold-start job 不再只统计 table。
- Candidate Map 显示 tables/docs/scripts。
- Formal Map 保存成功。
- Release build 成功。
- RAG 能引用 table/doc/script。
- NumericWorkbench 只显示 tables。
- M1 CSV smoke 仍通过。

自动化测试 Checklist：

- 优先新增 tests/e2e/test_multi_source_cold_start.py。
- 如果当前仓库无合适 e2e 入口，可先落 tests/unit/game/test_multi_source_cold_start_pipeline.py。
- 执行 M2 source-type 覆盖测试。
- 执行全部 M1 回归命令。

人工验收 Checklist：

- HeroTable 有哪些字段。
- WeaponConfig 有哪些字段。
- 战斗系统文档如何描述伤害公式。
- CharacterGrowth 文档如何描述成长规则。
- 哪些脚本与伤害计算有关。
- 哪些文档描述了 HeroTable。
- 哪些脚本引用了表格字段。

## 8. Release Artifact 规划

M2 后 Release 应包含：

```text
release_manifest.json
map_snapshot.json
table_schemas.jsonl
doc_knowledge.jsonl
script_evidence.jsonl
relationships.jsonl
rag_chunks.jsonl
```

### 8.1 表格 artifact

文件：table_schemas.jsonl

字段：

```text
table_id
source_path
fields
primary_key
row_count
summary
```

### 8.2 文档 artifact

文件：doc_knowledge.jsonl

字段：

```text
doc_id
source_path
title
summary
chunks
related_refs
```

### 8.3 脚本 artifact

文件：script_evidence.jsonl

字段：

```text
script_id
source_path
symbols
referenced_tables
summary
snippets
```

### 8.4 关系 artifact

文件：relationships.jsonl

建议先限制为：

```text
describes
references
implemented_by
depends_on
derived_from
```

示例：

```text
doc:CharacterGrowth describes table:HeroTable
doc:BattleSystem references table:WeaponConfig
script:DamageCalculator implemented_by doc:BattleSystem
script:DamageCalculator references table:WeaponConfig
```

M2 初期不做复杂自动关系推理。第一版关系来源只允许：

- 文件名匹配
- 文本中出现表名
- 脚本中出现表名
- 人工确认后的 Formal Map

## 9. RAG 验收标准

RAG 必须满足：

- 只读取 Current Release。
- 不直接读取 source 文件。
- 不直接读取未发布 candidate。
- citation 包含 table:* / doc:* / script:*。
- 能区分来源类型。
- 回答中能说明证据来源。
- 文档与脚本都必须经 Map 和 Release 后才能被 RAG 检索。

建议测试问题：

```text
HeroTable 有哪些字段？
WeaponConfig 有哪些字段？
战斗系统设计如何定义伤害公式？
哪个脚本实现了伤害计算？
角色成长规则来自哪篇文档？
```

## 10. NumericWorkbench 验收标准

NumericWorkbench 必须满足：

- 只显示 table sources。
- 显示 HeroTable、WeaponConfig、EnemyConfig。
- 不显示 BattleSystem、CharacterGrowth、EconomyLoop。
- 不显示 DamageCalculator、CharacterGrowthService、drop_formula。
- 能读取 xlsx table rows。
- 能读取 txt table rows。
- CSV 原逻辑不受影响。

## 11. 自动化测试总清单

### 11.1 M1 回归

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
pytest tests/unit/game/test_raw_index_rebuild.py
pytest tests/unit/game/test_canonical_facts_committer.py
pytest tests/unit/game/test_cold_start_job_pipeline.py
pytest tests/unit/routers/test_game_knowledge_map_source_latest_router.py
```

### 11.2 M2A 表格扩展

```bash
pytest tests/unit/game/test_xlsx_table_source.py
pytest tests/unit/game/test_txt_table_source.py
```

### 11.3 M2B 文档扩展

```bash
pytest tests/unit/game/test_markdown_doc_source.py
pytest tests/unit/game/test_txt_doc_source.py
pytest tests/unit/game/test_docx_doc_source.py
```

### 11.4 M2C 脚本证据

```bash
pytest tests/unit/game/test_script_evidence_source.py
```

### 11.5 M2D E2E

```bash
pytest tests/e2e/test_multi_source_cold_start.py
```

若当前仓库没有合适的 e2e 入口，可先使用：

```text
tests/unit/game/test_multi_source_cold_start_pipeline.py
```

## 12. 人工 Smoke 总清单

### 12.1 Project Setup

- 能配置 Table Sources。
- 能配置 Document Sources。
- 能配置 Script Sources。
- Discovery 显示 tables/docs/scripts。
- 异常文件可见。
- 不误把 TXT document 当 TXT table。

### 12.2 Cold-start Job

- Job 显示 tables count。
- Job 显示 docs count。
- Job 显示 scripts count。
- latest candidate 存在。
- latest diff 存在。

### 12.3 Map Editor

- Candidate overview 显示 tables/docs/scripts。
- Candidate refs 包含 table/doc/script。
- Formal Map 保存成功。
- Relationship warnings 不编造。

### 12.4 Release / RAG

- Build Release 成功。
- Publish Current 成功。
- RAG 能回答 table 问题。
- RAG 能回答 doc 问题。
- RAG 能回答 script 问题。
- citation 带 ref。

### 12.5 NumericWorkbench

- 只显示表格。
- 能读 CSV。
- 能读 XLSX。
- 能读 TXT table。
- 不显示 doc/script。

## 13. 评审流程

每个 Lane 必须经过以下门禁。

### 13.1 Pre-Review 提交前自检

Agent 必须提交：

```text
1. 改动文件列表
2. 本 Lane 目标
3. 本 Lane 禁止范围确认
4. 自动化测试结果
5. M1 回归结果
6. 人工 smoke 结果
7. 已知风险
```

### 13.2 Code Review 代码评审

评审人员检查：

- 是否只实现当前 Lane。
- 是否没有混入其他 source type。
- 是否没有破坏 M1。
- 是否没有绕过 Map。
- 是否没有绕过 Release。
- 是否没有让 Workbench 显示 doc/script。
- 是否没有自动保存 Formal Map。
- 是否没有自动 Build Release。
- 是否没有自动 Publish Current。
- 是否没有恢复 SVN 主线。
- 是否没有恢复 Legacy KB。
- 是否没有接 txtai。
- 是否有测试。
- 是否有 smoke 记录。

### 13.3 Product Review 产品评审

产品侧确认：

- UI 是否清楚说明该 source type 状态。
- 错误是否可理解。
- 用户是否知道下一步。
- 不支持范围是否明确。
- 没有让用户误以为支持多 sheet、复杂 DOCX、脚本执行。

### 13.4 Merge Gate 合并门禁

合并前必须满足：

- 自动化测试通过。
- M1 回归通过。
- 本 Lane smoke 通过。
- closeout 文档已写。
- 无无关文件。
- 无未确认失败项。
- 评审人确认。

## 14. Closeout 要求

每个 Lane 完成后必须新增：

```text
docs/tasks/m2/<lane-name>-closeout-YYYY-MM-DD.md
```

Closeout 必须包含：

```text
# <Lane Name> Closeout

## 1. 目标
## 2. 改动文件
## 3. 未修改范围确认
## 4. 实现内容
## 5. 自动化测试结果
## 6. M1 回归结果
## 7. 人工 Smoke 结果
## 8. 不支持范围
## 9. 已知风险
## 10. 后续建议
```

必填项：

- 当前 commit。
- 当前分支。
- 新增样例文件。
- 新增测试文件。
- 自动化测试命令与结果。
- M1 回归命令与结果。
- 人工 smoke 结论。
- 是否触碰 backend。
- 是否触碰 frontend。
- 是否触碰 API schema。
- 是否影响 Release / RAG / Workbench。
- 明确不支持范围。

## 15. 回滚策略

如果任意 Lane 破坏 M1，必须优先回滚该 Lane。

### 15.1 回滚触发条件

- M1 CSV smoke 失败。
- Map Editor 无法读取 latest source candidate。
- Formal Map 无法保存。
- Build Release 失败。
- RAG 无法读取 Current Release。
- NumericWorkbench 无法读取 CSV HeroTable。
- 前端命中旧版本或旧后端。
- Workbench 错误显示 doc/script。
- RAG 绕过 Release 直接读 source。

### 15.2 回滚方式

优先：

```bash
git revert <lane_commit>
```

禁止：

```text
force push main
覆盖 tag
手动删除历史
```

### 15.3 回滚后动作

必须重新执行：

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

并补充：

```text
docs/tasks/m2/<lane-name>-rollback-note-YYYY-MM-DD.md
```

## 16. 禁止范围

M2 施工期间禁止：

- 恢复 SVN 主线。
- 恢复 Legacy KB。
- 接入 txtai。
- 文档绕过 Map 直接进 RAG。
- Script evidence 绕过 Release 直接进 RAG。
- 让 NumericWorkbench 显示 doc 或 script。
- 自动保存 Formal Map。
- 自动 Build Release。
- 自动 Publish Current。
- DOCX 第一版支持图片、批注、修订、复杂表格。
- XLSX 第一版支持多 sheet 融合、公式求值、样式语义。
- Script evidence 执行代码。
- 把所有 .txt 默认扫成同一 source type。
- 借机重构主链路。

## 17. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| XLSX 解析边界不清 | 引发多 sheet、公式、样式预期膨胀 | 第一版严格限制为第一个非空 sheet，并在测试与 UI 中写明范围 |
| TXT table 与 TXT document 混淆 | 错误进入错误 pipeline | 分开 include 配置，discovery 阶段即区分类型 |
| DOCX 复杂内容不可控 | 用户误以为支持富文档语义 | 只支持标题与正文段落，复杂元素明确忽略 |
| Script evidence 过度扩展 | 引入执行风险和平台差异 | 只做静态文本分析，禁止执行代码 |
| 新 source 影响 M1 | 破坏现有 CSV 闭环 | 每个 Lane 强制执行 M1 回归，失败即停止或回滚 |
| RAG 绕过 Map / Release | 破坏知识治理边界 | 在设计、测试、评审中强制校验只读 Current Release |
| Workbench 混入 doc/script | 破坏产品边界 | 在候选数据、release 和 UI 三层限制仅 table 可见 |
| 多源 PR 过大 | 评审与定位困难 | 每个 Lane 单独分支、单独提交、单独 closeout |

## 18. 分支与提交策略

建议分支：

```text
m2-0-multi-source-plan
m2a-1-xlsx-single-sheet
m2b-1-markdown-doc-source
m2a-2-txt-table
m2b-2-txt-doc
m2b-3-docx-doc
m2c-1-script-evidence
m2d-small-real-project-smoke
```

提交策略：

- 每个 Lane 单独提交，不混改。
- 每个 PR 只覆盖一个 Lane。
- 提交前必须检查 git status。
- 提交前必须检查 git diff --name-only。
- 如果出现本 Lane 之外的文件，必须停止并汇报。

建议提交信息：

```text
docs: plan m2 multi-source cold-start
feat(game): support xlsx single-sheet table source
feat(game): support markdown document source
feat(game): support txt table source
feat(game): support txt document source
feat(game): support docx document source
feat(game): add script evidence source
test(game): add multi-source cold-start smoke
```

## 19. 本文档提交要求

本次任务只新增或更新本文档，不修改代码。

提交前必须确认：

```bash
git status
git diff --name-only
```

目标结果：

```text
只有 docs/roadmap/m2-multi-source-cold-start-plan.md 发生变化
```
