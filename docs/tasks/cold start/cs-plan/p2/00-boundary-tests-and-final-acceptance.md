# P2-00 Boundary Tests + Final Acceptance

## 目标

补齐 cold start 的路径、编码、格式边界测试，并完成最终验收记录。

## 允许

- 补 Windows/path 边界测试。
- 补 CSV 编码和错误格式测试。
- 补 XLSX 基础测试。
- 补 UI/API/smoke 最终验收文档。

## 禁止

- 不新增功能。
- 不扩大格式支持范围。
- 不接入 LLM、SVN、KB/retrieval。
- 不改变 Candidate/Formal/Release 边界。

## Windows 路径测试

- `E:\\test_project`
- 路径中包含空格
- 路径中包含中文
- 大小写扩展名 `.CSV`
- 反斜杠路径保存后能正常解析

## CSV 编码测试

- UTF-8
- UTF-8 BOM
- 空文件
- 空表头
- header_row 错误
- 缺主键时能 fallback 或明确 warning

## XLSX 测试

- 单 sheet
- 多 sheet
- 空 sheet 跳过
- `~$Temp.xlsx` 排除
- `.xls` 标记 unsupported

## 最终验收

必须通过：

- 用户能找到 Project Setup。
- 用户能设置 Local Project Root。
- 用户能设置 Tables Root。
- Source Discovery 能发现 HeroTable.csv。
- Raw Index 生成 1。
- Canonical Facts 生成 1。
- Candidate Map 生成 1。
- 构建有后台 job。
- 构建有进度条。
- 切换页面不打断。
- 刷新页面能恢复。
- 失败有 stage/error/next_action。
- Rule-only 不依赖 LLM。
- 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish Current。
- smoke 脚本一次通过。

可以宣布核心链路可用的条件：

```text
examples/minimal_project 在 rule-only 模式下，
从 Project Setup UI 和 smoke 脚本两条路径都能一次跑通。
```

