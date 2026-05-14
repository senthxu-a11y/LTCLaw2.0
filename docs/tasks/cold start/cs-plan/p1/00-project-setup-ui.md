# P1-00 Project Setup UI

## 目标

用户能在明确入口完成 Local Project Root、Tables Root、Include Patterns 和 Source Discovery，不再去找隐藏 YAML、SVN Root 或 Advanced 页面。

## 允许

- 新增或完善 `Game -> Project Setup` 页面。
- 调用 P0 的 setup-status、project root、tables config、source discover 接口。
- 展示 project key 和 project bundle root。
- 展示 build readiness 的 blocking reason 和 next action。
- 补前端 helper 测试。

## 禁止

- 不做后台 job。
- 不做一键 cold start 构建。
- 不保存 Formal Map。
- 不 Build Release。
- 不 Publish / Set Current。
- 不把 SVN Root 作为主配置入口。

## 页面区块

1. Local Project Root
2. Tables Source
3. Source Discovery
4. Build Pipeline Status

## 验收

- 能输入并保存 local project root。
- 能输入并保存 tables root/include/exclude/header row。
- 能点击检查数据源。
- 能显示 discovered/unsupported/excluded/errors。
- 无表时禁用后续构建入口。
- 能复制诊断信息。

