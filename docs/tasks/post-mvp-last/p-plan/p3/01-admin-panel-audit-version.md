# P3-01 管理员面板、版本显示与审计聚合

来源：总规划书 P3、Phase 10、Phase 11。

## 目标

把 Map/RAG/Release 管理员能力集中到本地管理入口，并补齐当前知识版本显示和多个 agent 写回日志聚合查看。

## Checklist

- [ ] 显示当前 project bundle 路径。
- [ ] 显示 source config 路径。
- [ ] 显示当前 Release ID。
- [ ] 显示当前 Map hash。
- [ ] 显示 RAG status。
- [ ] 显示 Formal Map 状态。
- [ ] 提供 Rebuild Index 按钮。
- [ ] 提供 Candidate Map 生成按钮。
- [ ] 提供 Map Diff Review 入口。
- [ ] 提供 Save Formal Map 操作。
- [ ] 提供 Build Release 按钮。
- [ ] 提供 Publish / Set Current 操作。
- [ ] 提供主动知识一致性检查按钮。
- [ ] 提供 agent audit 聚合查看入口。
- [ ] 不向普通策划展示管理员操作。
- [ ] 工作台显示当前知识版本。
- [ ] Draft Overlay 明确标记。
- [ ] RAG citation 到工作台建议上下文形成闭环。

## 输出物

- [ ] Admin Panel 信息架构。
- [ ] 管理员操作权限矩阵。
- [ ] 管理员操作确认流程。
- [ ] 管理员聚合查看设计。

## 验收标准

- [ ] 管理员操作都受 capability gate 控制。
- [ ] Build Release 和 Publish / Set Current 是两个显式操作。
- [ ] agent audit 可按 agent 分开查看，也可聚合查看。
- [ ] 普通策划看不到管理员操作入口。

## 禁止范围

- [ ] 不做中心化审计服务。
- [ ] 不把管理员操作暴露给普通策划。
- [ ] 不让一致性检查自动打扰普通策划。

