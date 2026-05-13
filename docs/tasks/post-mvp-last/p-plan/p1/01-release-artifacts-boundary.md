# P1-01 Release 与 Release Artifacts 收口

来源：总规划书 Phase 7、3.6、3.7、19.3.6。

## 目标

Release 成为 Formal Map + Canonical Facts 的快照，Release Artifacts 成为证据仓库；Release 不再依赖 KB、普通 Draft、Proposal 或 session 私有数据。

## Checklist

- [ ] 定义 Release 由管理员触发 Build。
- [ ] 定义 Release 不自动触发。
- [ ] 定义 Release 不依赖普通策划 Draft Overlay。
- [ ] 定义 Release 不依赖 session 私有 KB。
- [ ] 移除 `_load_approved_doc_entries(workspace)` 作为正式 Release 输入。
- [ ] 将 approved docs / doc facts 收口到 project-owned canonical docs。
- [ ] 定义 `manifest.json`。
- [ ] 定义 `map.json`。
- [ ] 定义 `indexes/table_schema.jsonl`。
- [ ] 定义 `indexes/doc_knowledge.jsonl`。
- [ ] 定义 `indexes/script_evidence.jsonl`。
- [ ] 定义 `indexes/candidate_evidence.jsonl`。
- [ ] 定义 Release Artifacts 的 hash / count 记录。
- [ ] 定义 current release 切换方式。
- [ ] 定义 rollback / set current 行为。
- [ ] 定义 Release 与 RAG current 的关系。

## Bootstrap / Strict Mode

- [ ] bootstrap mode：首次初始化，可从当前 indexes 生成临时 map，但必须显式 warning。
- [ ] strict mode：正式流程，必须有 Formal Map 才能 Build Release。

## 输出物

- [ ] Release 数据结构说明。
- [ ] Release Artifacts 说明。
- [ ] Build / Publish 流程说明。
- [ ] Rollback 策略。

## 验收标准

- [ ] Release 输入来自 Formal Map + project-owned canonical facts。
- [ ] Release 不读取 KB。
- [ ] Release 不读取普通 Draft / Proposal。
- [ ] `map.json` 是 Formal Map 的 release snapshot。
- [ ] Build Release 默认不自动 Publish。
- [ ] Publish / Set Current 由管理员显式触发。

## 禁止范围

- [ ] 不破坏首次 bootstrap。
- [ ] 不无提示自动 bootstrap。
- [ ] 不让 Release 读取 workspace/session KB。

