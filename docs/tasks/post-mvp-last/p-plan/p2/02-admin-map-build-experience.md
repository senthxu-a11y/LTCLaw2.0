# P2-02 管理员 Map 构建体验

来源：总规划书 P2、5.2、Phase 11。

## 目标

在 P0/P1 主链路稳定后，补齐管理员构建 Map 的体验：字段归一化、关系候选、系统聚类、Diff Review 和 Diff 解释。

## Checklist

- [ ] 接入 Canonical Schema 层。
- [ ] 接入 LLM 字段归一化。
- [ ] 接入 LLM 关系候选。
- [ ] 接入 LLM 系统聚类。
- [ ] 提供 Map Diff Review。
- [ ] 提供 LLM Diff 解释。
- [ ] 管理员可以查看新增 / 删除 / 变化项。
- [ ] 管理员确认后才保存 Formal Map。
- [ ] 保存 Formal Map 不自动 Build Release。

## 输出物

- [ ] 管理员 Map 构建流程说明。
- [ ] Map Diff Review UI 信息结构。
- [ ] LLM Diff 解释输入输出草案。
- [ ] Candidate Map 审核状态定义。

## 验收标准

- [ ] 管理员能区分 Candidate Map、Formal Map、Release Map。
- [ ] LLM 解释只作为辅助，不自动发布知识底座。
- [ ] active / ignored / deprecated 状态在 review 中可见。

## 禁止范围

- [ ] 不在 P0 未完成前做体验优先开发。
- [ ] 不让 LLM 自动确认 Formal Map。
- [ ] 不自动 Build / Publish Release。

