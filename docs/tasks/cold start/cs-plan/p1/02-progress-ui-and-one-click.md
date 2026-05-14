# P1-02 Progress UI + Rule-only 一键构建

## 目标

提供 `[Rule-only 冷启动构建]` 按钮，并用后台 job 展示进度。

## 允许

- 在 Project Setup / Map Review 合适位置增加 rule-only cold start 按钮。
- 创建 cold-start job。
- 展示 progress/stage/message/current_file/counts。
- 支持取消、重试、复制诊断信息。
- 页面切换和刷新后恢复 active job。
- 成功后提供查看 Candidate Map / Diff Review / 保存 Formal Map 的入口。
- 补前端 helper/static 测试。

## 禁止

- 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish / Set Current。
- 不让进度条直接驱动写源表或知识发布。
- 不接入 KB/retrieval。

## 验收

- 按钮只在 Project Root 和 Tables Source 有效时可用。
- 默认 `rule_only=true`。
- minimal_project 一键成功。
- 进度条不会一直卡 0%。
- 构建中切换页面再回来进度仍在。
- 构建完成显示 candidate count 和 refs。
- 构建失败显示失败阶段和下一步。

