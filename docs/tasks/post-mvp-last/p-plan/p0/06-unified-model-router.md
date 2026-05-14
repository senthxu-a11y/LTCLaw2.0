# P0-06 统一模型配置与 Model Router

来源：总规划书 Phase 2、18.9、19.3.4、20 技术雷区 6。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只统一模型调用边界，不引入新的产品能力，不在各模块回填独立 API 配置，也不扩展到 P1/P2/P3 的功能建设。

## 目标

统一 Map、RAG、Chat、Workbench、字段描述、表摘要、DependencyResolver 等所有 LLM 调用，禁止每个模块独立配置 API。

## Capability 与 Legacy 兼容说明

- [ ] 本任务不新增 capability，只统一既有模块的模型调用入口。
- [ ] 本任务只允许沿用 P0-03 中已有 capability 名称，例如 `knowledge.read`、`knowledge.build`、`knowledge.publish`、`workbench.read`、`workbench.source.write`；模型路由统一不单独派生新的权限语义。
- [ ] 权限体系仍以 P0-03 中已有 capability 名称为准，本任务不改变谁能发布知识或写真实源表。
- [ ] `call_model(prompt, model_type)`、SimpleModelRouter、ProviderManager 仅作为兼容桥接，不得继续演化为并行正式入口。

## Checklist

- [ ] 定义统一模型配置入口。
- [ ] 定义 Model Router 为唯一模型调用入口。
- [ ] 禁止 Map 模块单独配置 API。
- [ ] 禁止 RAG 模块单独配置 API。
- [ ] 禁止 Chat 模块单独配置 API。
- [ ] 禁止 Workbench 模块单独配置 API。
- [ ] 禁止功能模块绕过 Model Router 直连 provider。
- [ ] 定义 model_type：default / field_describer / table_summarizer / map_builder / map_diff_explainer / rag_answer / workbench_suggest。
- [ ] 定义 model_type 到实际模型的映射规则。
- [ ] 定义统一 timeout / retry / fallback。
- [ ] 定义统一空响应和解析失败处理。
- [ ] 定义模型配置 UI 只出现在统一设置页。
- [ ] 各功能页只显示当前模型配置和 model_type，不提供 API 填写入口。

## 兼容要求

- [ ] 兼容 ProviderManager active model。
- [ ] 兼容 AnthropicProvider。
- [ ] 兼容 OpenAI-compatible provider。
- [ ] 兼容当前 TableIndexer 调用方式。
- [ ] 兼容当前 DependencyResolver 调用方式。
- [ ] 兼容当前 Workbench Suggest 调用方式。
- [ ] 保留 `call_model(prompt, model_type)` 作为 compatibility adapter。

## 输出物

- [ ] 统一模型配置规范。
- [ ] Model Router 调用规范。
- [ ] model_type 映射表。
- [ ] 模型失败处理策略。
- [ ] 模型配置 UI 边界说明。

## 验收标准

- [ ] Map 构建、RAG 回答、Chat、Workbench Suggest 均调用统一 Model Router。
- [ ] TableIndexer 字段描述调用统一 Model Router。
- [ ] DependencyResolver 调用统一 Model Router。
- [ ] 不存在模块私自配置 API Key / Base URL / Provider / Model。
- [ ] 模型失败返回结构化错误，不只返回空字符串。

## 禁止范围

- [ ] 不直接替换为全新接口导致旧调用失效。
- [ ] 不在 Map / RAG / Chat / Workbench 页面新增独立 API 配置。

