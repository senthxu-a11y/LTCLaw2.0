# P0-04 Workbench 真实源表写回 Wrapper 与审计

来源：总规划书 Phase 9、Phase 10、19.3.2、19.3.6、20 技术雷区 7-10。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只定义真实源表写回边界、审计和限制，不实现 SVN 流程，不让普通策划更新 Formal Map、Current Release 或正式 RAG。

## 目标

让普通策划在具备 `workbench.source.write` 时，把 Draft Change 直接写回真实源表；所有真实写回必须经过 wrapper、op allowlist、后端硬校验和 agent audit。

## Capability 与 Legacy 兼容说明

- [ ] 本任务只允许引用已有 capability 名称 `workbench.source.write`；不新增新的写回 capability。
- [ ] `workbench.test.write` / `workbench.test.export` 仍只代表测试写入或导出，不等于真实源表写回。
- [ ] 如存在 legacy 写回入口，只能兼容到 wrapper / audit 新边界，不得继续直连底层写回主链路。

## Checklist

- [ ] 确认写回目标是真实源表，不是新文件。
- [ ] 新增或明确 `WorkbenchSourceWriteService`。
- [ ] 写回前检查 `workbench.source.write`。
- [ ] 写回只允许 `update_cell`。
- [ ] 写回只允许当前阶段开放的 `insert_row`。
- [ ] 普通工作台禁用 `delete_row`。
- [ ] 禁止新增字段。
- [ ] 禁止新增表。
- [ ] 禁止删除字段。
- [ ] 禁止删除表。
- [ ] 禁止改表名。
- [ ] 禁止改表路径。
- [ ] 禁止改主键。
- [ ] 写回前显示 SVN Update 提示，但不执行 SVN Update。
- [ ] 不做 source_hash 强校验。
- [ ] 不做文件锁。
- [ ] 不做自动备份。
- [ ] 写回成功后记录 agent audit。
- [ ] 写回失败时返回明确错误。
- [ ] 写回后不自动触发 Rebuild / Release / Publish。
- [ ] 明确 `.xlsx` / `.csv` / `.txt` 支持范围，`.xls` 不承诺写回。
- [ ] TXT 表写回必须保留 header metadata。

## 审计日志字段

- [ ] `event_type`
- [ ] `agent_id`
- [ ] `session_id`
- [ ] `time`
- [ ] `release_id_at_write`
- [ ] `source_files`
- [ ] `changes`
- [ ] `old_value`
- [ ] `new_value`
- [ ] `reason`
- [ ] 写回失败是否记录

## 输出物

- [ ] Workbench Source Write 规则。
- [ ] 写回真实表 UX 流程。
- [ ] 禁止结构变更清单。
- [ ] 写回成功 / 失败返回格式。
- [ ] Agent 审计日志格式。
- [ ] 写回日志持久化规则。

## 验收标准

- [ ] 没有 `workbench.source.write` 时不能写真实源表。
- [ ] `delete_row` 在普通工作台写回中被拦截。
- [ ] schema ops 全部被拦截。
- [ ] 写回成功后生成 agent audit。
- [ ] 写回后不触发 Rebuild / Release / Publish。

## 禁止范围

- [ ] 不开放 delete_row。
- [ ] 不开放新增字段 / 新增表。
- [ ] 不让普通策划更新知识底座。
- [ ] 不直接从普通工作台调用底层 `ChangeApplier`。

