# P0-05 Smoke Script

## 目标

提供一个命令验证 cold start 核心链路，不依赖 UI。

## 允许

- 新增 `scripts/run_map_cold_start_smoke.py`。
- 使用 `examples/minimal_project`。
- 通过 API/helper 执行：
  1. 配置 project root
  2. 配置 tables root
  3. Source Discovery
  4. Raw Index
  5. Canonical Facts
  6. Candidate from source
- 失败时打印 diagnostics。
- 补 smoke 相关测试或文档验证。

## 禁止

- 不调用 LLM。
- 不依赖 SVN。
- 不依赖 KB/retrieval。
- 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish / Set Current。

## 命令

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

## 成功输出

```json
{
  "success": true,
  "discovered_table_count": 1,
  "raw_table_index_count": 1,
  "canonical_table_count": 1,
  "candidate_table_count": 1,
  "candidate_refs": ["table:HeroTable"],
  "llm_used": false
}
```

## 验收

- 干净环境运行一次成功。
- 关闭模型配置仍然成功。
- 删除 canonical 后重跑成功。
- 删除 raw index 后重跑成功。
- 失败时包含 stage/reason/path/next_action。

