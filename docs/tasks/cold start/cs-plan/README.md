# Cold Start 分布施工计划

本文档把 `LTClaw_Cold_Start_Core_Task_Checklist_And_Verification.md` 拆成可分布执行的小切片。主目标不变：

```text
Project Setup UI/API -> Source Discovery -> Raw Index -> Canonical Facts -> Candidate Map
```

最小验收样例固定为：

```text
examples/minimal_project/Tables/HeroTable.csv
```

成功结果固定为：

```json
{
  "success": true,
  "discovered_table_count": 1,
  "raw_table_index_count": 1,
  "canonical_table_count": 1,
  "candidate_table_count": 1,
  "candidate_refs": ["table:HeroTable"],
  "mode": "rule_only",
  "llm_used": false,
  "next_action": "review_candidate_map"
}
```

## 边界

- 只做 cold start 最小闭环，不做大范围重构。
- rule-only 必须不依赖 LLM。
- 不依赖 SVN。
- 不接入 KB/retrieval 作为正式输入。
- Candidate Map 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish / Set Current。
- 后台 job 只能编排 cold start 链路，不扩大为通用任务系统。

## 执行顺序

1. `p0/00-minimal-sample-and-project-setup-api.md`
2. `p0/01-source-discovery.md`
3. `p0/02-raw-index-rebuild.md`
4. `p0/03-canonical-facts-rebuild.md`
5. `p0/04-build-readiness-and-candidate.md`
6. `p0/05-smoke-script.md`
7. `p1/00-project-setup-ui.md`
8. `p1/01-cold-start-job.md`
9. `p1/02-progress-ui-and-one-click.md`
10. `p2/00-boundary-tests-and-final-acceptance.md`

P0 先保证命令行和 API 核心链路跑通；P1 再补 UI 与后台 job；P2 做边界测试和最终验收。

