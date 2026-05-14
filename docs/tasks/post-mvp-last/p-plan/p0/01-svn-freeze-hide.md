# P0-01 SVN 能力冻结与隐藏

来源：总规划书 Phase 0.5、18.8、20 关键原则。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只冻结和隐藏 LTClaw 内的 SVN 暴露面，不恢复 SVN runtime 为主流程能力，不把 SVN、服务端账号、审批流、文件锁、自动备份重新纳入当前阶段。

## 目标

将 SVN 从 LTClaw 当前版本的功能面中移除。SVN 仍由团队外部流程负责同步、恢复、冲突处理，但不再由 LTClaw 执行 update、commit、watch、权限管理或状态轮询。

## Legacy 兼容说明

- [ ] `svn_root` 仅作为旧字段兼容输入，不再代表产品能力边界。
- [ ] SVN 模块如暂时保留，仅允许作为被冻结的 legacy 依赖，不允许继续扩展成当前阶段功能。
- [ ] LTClaw 文案、入口和主流程都必须转向普通 filesystem root / project root 语义。

## Checklist

- [ ] 隐藏所有 SVN 相关 UI。
- [ ] 移除或隐藏 SVN 权限配置入口。
- [ ] 禁用 SVN watcher。
- [ ] 禁用 SVN heartbeat / polling。
- [ ] 禁用 LTClaw 内部 SVN update 操作。
- [ ] 禁用 LTClaw 内部 SVN commit 操作。
- [ ] 禁用 SVN 状态错误在项目主页展示。
- [ ] 保留本地项目路径作为普通 filesystem root。
- [ ] 将配置中的 `svn_root` 语义逐步改名为 `project_root` 或 `source_root`。
- [ ] 若短期不能改名，内部兼容旧字段，但产品文案不再出现 SVN。
- [ ] 代码层先冻结 SVN 模块，不作为主流程依赖。
- [ ] 后续确认无依赖后，再物理删除 SVN 模块。

## 输出物

- [ ] SVN 冻结策略。
- [ ] SVN UI 隐藏清单。
- [ ] SVN runtime 禁用清单。
- [ ] `svn_root` 到 `project_root` 的字段迁移计划。

## 禁止范围

- [ ] 不删除尚有依赖的 SVN 模块。
- [ ] 不默认开启 SVN watcher 自动索引。
- [ ] 不在写回成功后自动执行 SVN commit。

## 验收标准

- [ ] 普通和管理员主流程都不依赖 SVN runtime。
- [ ] 产品文案不再把 SVN 操作表现为 LTClaw 内置功能。
- [ ] 写回真实表前仅提示用户自行 SVN Update。

