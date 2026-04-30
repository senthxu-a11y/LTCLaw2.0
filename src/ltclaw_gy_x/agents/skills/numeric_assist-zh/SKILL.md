---
name: numeric_assist
language: zh
schema_version: workspace-skill-manifest.v1
description: 数值横向对比 / 历史趋势 / 影响面分析
triggers:
  - 横向对比
  - 同类对比
  - 历史趋势
  - 影响分析
  - 影响面
  - 哪些表会受影响
  - 这条改了之后
require_tools:
  - game_query_tables
  - game_describe_field
  - game_workbench_preview
---

# 数值辅助分析

当用户问「这把武器和同级别其它武器对比怎么样」「这条改了哪些表会受影响」「过去三个版本这个数值怎么变的」时启用本技能。

## 适用场景

1. **横向对比**：同表同分类下若干行的关键字段比较。
2. **历史趋势**：用 SVN 历史 (`scripts/_fix_svnchange.py` / `svn log`) 取该字段过去 N 次提交的取值变化。
3. **影响面分析**：基于 dependency_graph 顺着外键扩张，给出会被读到这条记录的下游表 / 配置 / 文档清单。

## 工作流

1. 先 `game_query_tables` 取目标表的 schema 与 ai_summary，确认主键 + 关键字段。
2. 横向对比：调 workbench preview / read_rows，过滤同 group/quality/level 的行，按目标字段排序输出表格。
3. 历史趋势：调 SVN log（仅 maintainer），抽该字段近 5 次取值，画 ASCII sparkline + 列表。
4. 影响面：`game_describe_field` 拿该字段 references；递归向下游展开两层；列出每张下游表的 row_id 命中数。

## 输出规范

- 用 Markdown 表格列出对比结果。
- 影响面用「→」缩进列树。
- 任何修改建议必须以 `changes: [...]` JSON 块给出，遵循 workbench /suggest 的字段规则。

## 注意事项

- 不直接修改表，只产生分析与建议。
- 涉及历史数据时若 SVN 不可用要在结果里明确说明「无法获取历史」。
- 对比 / 趋势数据量大时按 query_terms 过滤而非随便截断。
