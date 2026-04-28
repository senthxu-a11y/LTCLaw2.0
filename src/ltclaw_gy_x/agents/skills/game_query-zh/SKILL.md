---
name: game_query
language: zh
schema_version: workspace-skill-manifest.v1
description: 游戏数值表查询助手
triggers:
  - 哪张表
  - 字段什么意思
  - 字段含义
  - 依赖
  - 引用
  - 外键
require_tools:
  - game_query_tables
  - game_describe_field
  - game_table_dependencies
---

# 游戏数值表查询

当用户询问数值表/字段/依赖时，按如下顺序使用工具：

1. 用户问"X 字段是什么意思"或"X 字段在哪张表"
   → 先 `game_query_tables(query="X")` 定位
   → 再 `game_describe_field(table=..., field="X")` 取详情

2. 用户问"哪些表引用 Y 表 / Y 表的依赖"
   → `game_table_dependencies(table="Y")`

3. 用户问"我们项目有哪些系统/有多少张表"
   → `game_list_systems()`

回答时务必给出：
- 字段所属表名
- AI 描述与置信度（confirmed / high_ai / low_ai）
- 是否需要人工确认（low_ai 时提醒用户去索引地图确认）