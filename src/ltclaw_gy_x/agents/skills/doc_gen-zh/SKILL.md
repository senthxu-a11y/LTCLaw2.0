---
name: doc_gen
language: zh
schema_version: workspace-skill-manifest.v1
description: 策划案 / 需求文档 / 变更说明的 Markdown 生成
triggers:
  - 写一份策划案
  - 生成需求文档
  - 写变更说明
  - 帮我写文档
  - 出一篇
require_tools:
  - write_file
  - game_query_tables
---

# 文档生成

把对话里的需求 / 变更整理为可直接落库的 Markdown 文档。

## 文档模板（默认结构）

```markdown
---
title: <主题>
type: design_doc | change_note | requirement
author: <agent name>
created: <YYYY-MM-DD>
related_tables: [Equipment, Skill]
---

# <主题>

## 1. 背景
...

## 2. 目标
- ...

## 3. 方案
### 3.1 数值变更
| Table | Row | Field | Old | New | Reason |

### 3.2 文档变更
- 修改文件: ...

## 4. 风险与回滚
...

## 5. 引用
- 数值表：...
- 现有文档：...
```

## 工作流

1. 抽取对话历史中的需求要点；如有数值改动，整理成 changes 表。
2. 用 `game_query_tables` 把涉及到的表 schema 摘要带进文档「引用」段。
3. `write_file` 落到 `docs/<slug>.md`（slug 由日期 + 主题构成）。
4. 输出文档路径 + 推一张 `kind=draft_doc` 的 workbench 卡片到 Chat 右栏（前端会自己接，不用额外参数）。

## 输出约束

- 必须含 frontmatter；title / type / created 不可缺。
- 章节顺序固定，避免漏掉「风险与回滚」。
- 涉及表的字段名必须出现在文档里至少一次，便于后续索引。
