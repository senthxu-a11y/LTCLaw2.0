# P0-03 Agent Profile / Capabilities 权限体系

来源：总规划书 Phase 3、18.7、19.3.5。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只定义本地 Agent Profile 与 capability gate，不引入服务端账号系统，不把普通策划提升为知识发布者，也不扩大为审批系统。

## 目标

在不做服务端账号系统的前提下，用本地 Agent Profile 管理角色边界和能力开关，并把 capability gate 真正接入后端 request context。

## Legacy 兼容说明

- [ ] `my_role` 仅保留为 legacy shortcut 和兼容映射。
- [ ] 旧权限入口如暂时保留，只能映射到 Agent Profile capabilities，不得继续作为长期权限标准。

## Checklist

- [ ] 定义 `agent profile.yaml` 格式。
- [ ] 定义 `agent_id` / `display_name` / `role` / `capabilities` 字段。
- [ ] 定义 role 模板：viewer / planner / source_writer / admin。
- [ ] 补充 capability：`workbench.source.write`。
- [ ] 确认 capability：`knowledge.read`。
- [ ] 确认 capability：`knowledge.map.read`。
- [ ] 确认 capability：`knowledge.map.edit`。
- [ ] 确认 capability：`knowledge.build`。
- [ ] 确认 capability：`knowledge.publish`。
- [ ] 确认 capability：`workbench.read`。
- [ ] 确认 capability：`workbench.test.write`。
- [ ] 确认 capability：`workbench.test.export`。
- [ ] 定义 `*` 管理员能力。
- [ ] 定义前端按钮隐藏 / disabled 行为。
- [ ] 定义后端接口 capability gate。
- [ ] 定义 `my_role` 到 Agent Profile capabilities 的 legacy 映射。
- [ ] 定义“本地权限不是安全防黑客机制”的产品说明。

## 输出物

- [ ] Agent Profile 配置规范。
- [ ] Capability 列表。
- [ ] Role 模板。
- [ ] 权限展示 UI 规则。
- [ ] 后端接口权限矩阵。

## 验收标准

- [ ] 当前 agent profile 可以被加载。
- [ ] capabilities 可以注入 request state。
- [ ] `require_capability` 可以读取 agent capabilities。
- [ ] 前端按钮根据 capabilities 显示/隐藏或 disabled。
- [ ] 后端接口也执行 capability gate。
- [ ] `my_role` 被映射为 legacy shortcut。
- [ ] `workbench.source.write` 已加入前后端 capability 类型。

## 禁止范围

- [ ] 不做服务端账号系统。
- [ ] 不把前端按钮隐藏当成唯一权限控制。
- [ ] 不立即删除 `my_role`，先做兼容映射。

