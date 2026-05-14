# P1-01 Cold-start Job

## 目标

构建不能被切换页面打断。前端只订阅 job 状态。

## 允许

- 新增 cold-start job API：
  - `POST /game/knowledge/map/cold-start-jobs`
  - `GET /game/knowledge/map/cold-start-jobs/{job_id}`
  - `POST /game/knowledge/map/cold-start-jobs/{job_id}/cancel`
- job 状态写入 project runtime build_jobs。
- job 编排 P0 核心链路。
- 保留最近 20 条 job。
- 同项目已有 running job 时不重复创建。
- 支持 timeout、cancel、partial_outputs。
- 补后端窄测。

## 禁止

- 不做通用任务系统。
- 不自动保存 Formal Map。
- 不自动 Build Release。
- 不自动 Publish / Set Current。
- 不调用 LLM。
- 不接入 KB/retrieval。

## Stage

```text
checking_project_root
discovering_sources
building_raw_index
building_canonical_facts
building_candidate_map
generating_diff_review
done
failed
```

## Job 状态字段

- `job_id`
- `status`
- `stage`
- `progress`
- `message`
- `current_file`
- `counts`
- `warnings`
- `errors`
- `next_action`
- `partial_outputs`

## 验收

- 点击构建后切换页面，job 继续。
- 刷新浏览器后可通过 job id 恢复状态。
- 重复点击不会启动两个 job。
- 取消后 `status=cancelled`。
- 失败时有 stage/error/next_action。
- 成功后返回 candidate result。

