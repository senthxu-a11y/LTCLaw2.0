# LTClaw 冷启动端到端闭环修复方案：Candidate Map 持久化与 Map Editor 读取契约

## 0. 问题结论

当前问题不是 capability，也不是前端按钮单点问题。

真正问题是：

```text
cold_start_job 的成功态定义
与
Map Editor 默认读取契约
不一致。
```

当前 Rule-only 冷启动虽然能完成：

```text
Source Discovery
→ Raw Index
→ Canonical Facts
→ Candidate Map 计算
→ Job status = succeeded
```

但没有形成端到端闭环：

```text
Job succeeded
→ Candidate Map 可被 Map Editor 读取
→ 用户保存 Formal Map
→ Build Release
→ Publish Current
→ RAG 可用
```

断点有两个：

```text
断点 A：cold_start_job 没有真正持久化 source candidate map。
断点 B：Map Editor 默认不读取 cold-start/source candidate 结果。
```

---

## 1. 现状证据

## 1.1 cold_start_job 只记录路径，不写文件

当前 `cold_start_job.py` 在 candidate 阶段会做：

```text
build_map_candidate_from_canonical_facts(...)
state.counts.candidate_table_count = ...
state.candidate_refs = ...
state.partial_outputs["candidate_map_path"] = str(get_project_candidate_map_path(project_root))
```

但没有把 `candidate_result` 或 `candidate_result.map` 写入：

```text
project/maps/candidate/latest.json
```

因此 job JSON 里会出现：

```json
"candidate_map_path": ".../project/maps/candidate/latest.json"
```

但该文件实际不存在。

这导致：

```text
job succeeded 只是“计算成功”
不是“可消费产物成功”
```

---

## 1.2 Map Editor 默认读取 release candidate 和 formal map

Map Editor 的 `FormalMapWorkspace` 初始化会加载：

```text
GET /agents/{agentId}/game/knowledge/map/candidate
GET /agents/{agentId}/game/knowledge/map
```

其中：

```text
GET /game/knowledge/map/candidate
```

当前后端实现是：

```text
build_map_candidate_result_from_release(project_root, release_id=release_id)
```

也就是：

```text
基于 current release 构造 candidate
```

如果没有 current release，就返回：

```text
404: No current knowledge release is set
```

而冷启动场景天然是：

```text
无 formal map
无 current release
有 source/canonical candidate
```

所以 Map Editor 默认读取路径一定拿不到 cold-start job 结果。

---

## 2. 修复目标

本次修复要实现：

```text
Rule-only 冷启动 job succeeded
必须意味着：
1. candidate map 已真实持久化
2. candidate diff review 已真实持久化
3. 后端有稳定接口可读取 latest source candidate
4. Map Editor 在无 current release 时能展示 latest source candidate
5. 用户可以从这个 candidate 保存 Formal Map
```

修复完成后的闭环：

```text
Rule-only Cold-start Job
→ writes project/maps/candidate/latest.json
→ Map Editor reads latest source candidate
→ user sees HeroTable
→ Save Formal Map
→ Build Release
→ Publish Current
→ RAG can answer HeroTable
```

---

## 3. 设计原则

### 3.1 不改变 Release Candidate 的语义

保留现有接口：

```text
GET /game/knowledge/map/candidate
```

继续表示：

```text
release snapshot candidate
```

不要偷偷改变它的语义，否则会影响已有 release review 逻辑。

---

### 3.2 新增 source candidate 读取接口

新增接口：

```text
GET /game/knowledge/map/candidate/source-latest
```

语义明确：

```text
读取最近一次 source/canonical cold-start candidate。
```

---

### 3.3 cold_start_job 的成功态必须以“产物写出”为准

如果 candidate map 计算成功，但写盘失败：

```text
job 不能 succeeded
必须 failed
stage = persisting_candidate_map
next_action = retry_cold_start_job
```

---

### 3.4 不自动保存 Formal Map

即使 source candidate 已落盘，也不能自动保存 Formal Map。

仍然保持：

```text
Candidate Map = 待审核
Formal Map = 管理员显式保存
Release = 管理员显式 Build
Current Release = 管理员显式 Publish
```

---

## 4. 推荐文件结构

使用现有路径定义：

```text
project/maps/candidate/latest.json
project/maps/candidate/history/<timestamp>-<job_id>.json
project/maps/diffs/latest_diff.json
project/maps/diffs/history/<timestamp>-<job_id>.json
```

如果当前没有 history helper，可以先只做：

```text
project/maps/candidate/latest.json
project/maps/diffs/latest_diff.json
```

但建议 history 一起做，方便追踪。

---

## 5. Candidate latest.json 数据结构

建议写入完整 `KnowledgeMapCandidateResult`，而不是只写 `KnowledgeMap`。

文件：

```text
project/maps/candidate/latest.json
```

内容：

```json
{
  "version": "1.0",
  "job_id": "map-cold-start-xxx",
  "created_at": "2026-05-15T...",
  "candidate": {
    "mode": "candidate_map",
    "map": {},
    "release_id": null,
    "candidate_source": "source_canonical",
    "is_formal_map": false,
    "source_release_id": null,
    "uses_existing_formal_map_as_hint": false,
    "warnings": [],
    "diff_review": {}
  },
  "candidate_table_count": 1,
  "candidate_refs": ["table:HeroTable"]
}
```

为什么写完整 result：

```text
Map Editor 需要 map
Review 页面需要 diff_review
UI 需要 mode/candidate_source/warnings
后续调试需要 job_id/created_at
```

---

## 6. 后端施工清单

# Slice A：新增 source candidate store

## A1. 新增文件

```text
src/ltclaw_gy_x/game/knowledge_source_candidate_store.py
```

## A2. 新增函数

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import KnowledgeMapCandidateResult
from .paths import (
    get_project_candidate_map_path,
    get_project_candidate_map_history_dir,
    get_project_latest_map_diff_path,
)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

def _safe_job_id(job_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in str(job_id or "")).strip("-") or "job"

def _candidate_refs(candidate: KnowledgeMapCandidateResult) -> list[str]:
    if candidate.map is None:
        return []
    refs: list[str] = []
    refs.extend(f"table:{table.table_id}" for table in candidate.map.tables)
    refs.extend(f"doc:{doc.doc_id}" for doc in candidate.map.docs)
    refs.extend(f"script:{script.script_id}" for script in candidate.map.scripts)
    return refs

def save_latest_source_candidate(
    project_root: Path,
    candidate: KnowledgeMapCandidateResult,
    *,
    job_id: str,
) -> Path:
    if candidate.map is None:
        raise ValueError("candidate.map is required")

    payload = {
        "version": "1.0",
        "job_id": job_id,
        "created_at": _now_iso(),
        "candidate": candidate.model_dump(mode="json"),
        "candidate_table_count": len(candidate.map.tables),
        "candidate_refs": _candidate_refs(candidate),
    }

    content = json.dumps(payload, indent=2, ensure_ascii=False)
    latest_path = get_project_candidate_map_path(project_root)
    _write_text_atomic(latest_path, content)

    history_dir = get_project_candidate_map_history_dir(project_root)
    history_path = history_dir / f"{_now_iso().replace(':', '-')}-{_safe_job_id(job_id)}.json"
    _write_text_atomic(history_path, content)

    if candidate.diff_review is not None:
        _write_text_atomic(
            get_project_latest_map_diff_path(project_root),
            candidate.diff_review.model_dump_json(indent=2),
        )

    return latest_path

def load_latest_source_candidate(project_root: Path) -> KnowledgeMapCandidateResult | None:
    path = get_project_candidate_map_path(project_root)
    if not path.exists() or not path.is_file():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    candidate_payload = payload.get("candidate")
    if candidate_payload is None:
        return None
    return KnowledgeMapCandidateResult.model_validate(candidate_payload)
```

## A3. 注意点

- [ ] 写 `latest.json` 必须 atomic。
- [ ] `candidate.map is None` 时不能保存。
- [ ] 保存失败必须抛异常。
- [ ] `load_latest_source_candidate()` 读不到时返回 None。
- [ ] 不要把 source candidate 保存成 Formal Map。

---

# Slice B：cold_start_job 持久化 candidate map

## B1. 修改文件

```text
src/ltclaw_gy_x/game/cold_start_job.py
```

## B2. 引入 store

```python
from .knowledge_source_candidate_store import save_latest_source_candidate
```

## B3. 调整 candidate 阶段逻辑

当前 candidate 阶段：

```python
candidate_result = build_map_candidate_from_canonical_facts(...)
state.partial_outputs["candidate_map_path"] = str(get_project_candidate_map_path(project_root))
...
save_cold_start_job(project_root, state)
```

要改成：

1. 先计算 candidate。
2. 如果 candidate 无 map，失败。
3. 生成 diff review。
4. 把 diff review 写回 candidate_result。
5. 保存 latest source candidate。
6. 保存成功后才 job succeeded。

推荐把 `generating_diff_review` 和 `persisting_candidate_map` 串起来：

```python
candidate_result = build_map_candidate_from_canonical_facts(...)

if candidate_result.map is None or candidate_result.mode == "no_canonical_facts":
    fail...

# generating_diff_review
diff_base, base_map_source = resolve_map_diff_base(...)
diff_review = build_map_diff_review(...)
candidate_result.diff_review = diff_review

# persisting_candidate_map
candidate_path = save_latest_source_candidate(project_root, candidate_result, job_id=job_id)

state.partial_outputs["candidate_map_path"] = str(candidate_path)
state.partial_outputs["diff_review"] = diff_review.model_dump(mode="json")
state.partial_outputs["candidate_mode"] = candidate_result.mode

# succeeded only after save succeeds
```

## B4. 新增 stage

建议新增 stage：

```text
persisting_candidate_map
```

进度：

```text
95
```

message：

```text
Persisting source candidate map.
```

## B5. 失败行为

如果写盘失败：

```text
status = failed
stage = persisting_candidate_map
message = "Persisting source candidate map failed."
next_action = retry_cold_start_job
errors += exception
```

不能 succeeded。

---

# Slice C：新增 source-latest 读取接口

## C1. 修改文件

```text
src/ltclaw_gy_x/app/routers/game_knowledge_map.py
```

## C2. 引入

```python
from ...game.knowledge_source_candidate_store import load_latest_source_candidate
```

## C3. 新增 route

必须放在：

```text
@router.get('/candidate/source-latest')
```

注意：要放在 `@router.get('/candidate')` 之前或之后都可以，因为路径更具体，一般 FastAPI 可区分；为了清晰，建议放在 `/candidate` 前。

```python
@router.get('/candidate/source-latest', response_model=SourceCandidateResponse)
async def get_latest_source_candidate(request: Request) -> SourceCandidateResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.read')
    project_root = _project_root_or_400(_game_service_or_404(workspace))

    candidate = load_latest_source_candidate(project_root)
    if candidate is None:
        raise HTTPException(status_code=404, detail='No source candidate map is available')

    readiness = _build_readiness_payload(project_root)
    diagnostics = CandidateDiagnostics(
        raw_table_index_count=readiness.raw_table_index_count,
        canonical_table_count=readiness.canonical_table_count,
        canonical_tables_dir=readiness.canonical_tables_dir or '',
        blocking_reason=readiness.blocking_reason,
        next_action=readiness.next_action,
    )
    return _serialize_source_candidate_response(candidate, diagnostics=diagnostics)
```

## C4. 不要修改 `/candidate`

保留原语义：

```text
release snapshot candidate
```

---

# Slice D：Map Editor 读取 latest source candidate

## D1. 修改 API 模块

文件：

```text
console/src/api/modules/gameKnowledgeRelease.ts
```

新增：

```ts
async getLatestSourceCandidate(agentId: string): Promise<KnowledgeMapCandidateResponse> {
  return request<KnowledgeMapCandidateResponse>(
    `/agents/${agentId}/game/knowledge/map/candidate/source-latest`,
  );
}
```

---

## D2. 修改 FormalMapWorkspace

文件：

```text
console/src/pages/Game/components/FormalMapWorkspace.tsx
```

当前初始化只会：

```text
fetchReleaseSnapshot()
fetchFormalMap()
```

需要新增：

```text
fetchLatestSourceCandidate()
```

建议状态：

```ts
const [sourceCandidateResult, setSourceCandidateResult] = useState<KnowledgeMapCandidateResponse | null>(null);
const [sourceCandidateLoading, setSourceCandidateLoading] = useState(false);
const [sourceCandidateError, setSourceCandidateError] = useState<string | null>(null);
```

已有 `sourceCandidateResult` 是按钮 build source candidate 用的状态，可以复用，但要注意：

```text
初始 latest source candidate
和
手动 build source candidate
都进入同一个 sourceCandidateResult
```

## D3. 加载策略

在 `fetchMapReviewData(agentId)` 中：

```text
1. fetchFormalMap(agentId)
2. fetchReleaseSnapshot(agentId)
3. fetchLatestSourceCandidate(agentId)
```

但建议逻辑：

- 有 current release 时，release snapshot candidate 可显示。
- 无 current release 时，release snapshot candidate 404 不应阻塞。
- latest source candidate 存在时，应显示在 Source Candidate Review 区域。
- formal map 仍按原逻辑加载。

最小实现：

```ts
if (!hasExplicitCapabilityContext || canReadCandidate) {
  tasks.push(fetchReleaseSnapshot(agentId));
  tasks.push(fetchLatestSourceCandidate(agentId));
}
```

`fetchLatestSourceCandidate` 处理 404：

```text
No source candidate map is available
```

不作为红色错误，显示为空状态即可。

## D4. UI 展示文案

如果有 latest source candidate：

```text
Latest Source Candidate
来自最近一次 Rule-only Cold-start / Source Canonical 构建
```

显示：

```text
candidate_source = source_canonical
candidate_table_count = 1
candidate_refs = table:HeroTable
diff_review.added_refs = table:HeroTable
```

按钮：

```text
Save Formal Map
```

保存时使用：

```ts
sourceCandidateResult.map
```

---

# Slice E：测试补齐

## E1. cold_start_job_pipeline 测试补强

文件：

```text
tests/unit/game/test_cold_start_job_pipeline.py
```

新增断言：

```python
from ltclaw_gy_x.game.paths import get_project_candidate_map_path, get_project_latest_map_diff_path
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate

candidate_path = get_project_candidate_map_path(project_root)
assert candidate_path.exists()

loaded = load_latest_source_candidate(project_root)
assert loaded is not None
assert loaded.map is not None
assert len(loaded.map.tables) == 1
assert loaded.map.tables[0].table_id == "HeroTable"
assert loaded.diff_review is not None
assert "table:HeroTable" in loaded.diff_review.added_refs

assert get_project_latest_map_diff_path(project_root).exists()
```

这条测试是关键。没有它，仍可能再次出现：

```text
job succeeded 但无 candidate latest.json
```

---

## E2. 新增 source-latest router 测试

文件：

```text
tests/unit/routers/test_game_knowledge_map_source_latest_router.py
```

测试 1：没有 candidate 时 404

```text
GET /candidate/source-latest
→ 404 No source candidate map is available
```

测试 2：job 成功后可读取

```text
运行 cold-start job
GET /candidate/source-latest
→ 200
mode = candidate_map
candidate_source = source_canonical
candidate_table_count = 1
candidate_refs = ["table:HeroTable"]
```

---

## E3. 前端测试

文件：

```text
console/src/pages/Game/components/FormalMapWorkspace.test.tsx
```

或已有测试文件中补。

测试目标：

```text
当 release snapshot 返回 no current release
且 source-latest 返回 candidate
Map Editor 显示 source candidate
Save Formal Map 按钮可用
```

如果前端测试成本太高，本轮至少人工烟测覆盖。

---

# 7. 人工验收流程

## 7.1 冷启动构建

1. 打开 Project Setup。
2. 配置 `examples/minimal_project`。
3. Source Discovery 发现 `HeroTable.csv`。
4. 点击 Rule-only 冷启动。
5. 等 Job succeeded。

检查文件：

```text
project/maps/candidate/latest.json
project/maps/diffs/latest_diff.json
```

必须存在。

---

## 7.2 Map Editor

进入 Map Editor。

期望：

```text
Formal Map: no_formal_map
Release Snapshot Candidate: no current release / empty
Latest Source Candidate: candidate_map
```

必须看到：

```text
table:HeroTable
candidate_source = source_canonical
candidate_table_count = 1
```

---

## 7.3 保存 Formal Map

点击：

```text
Save Formal Map
```

期望：

```text
Formal Map 保存成功
Formal Map 包含 HeroTable
```

---

## 7.4 后续 Release / RAG

在 Formal Map 保存成功后，再继续：

```text
Build Release
Publish Current
RAG 查询 HeroTable
```

---

# 8. 成功判定

这次修完后，Milestone 1 的成功标准应升级为：

```text
CSV Cold-start E2E Ready
```

必须满足：

- [ ] cold-start job succeeded
- [ ] `project/maps/candidate/latest.json` 存在
- [ ] `project/maps/diffs/latest_diff.json` 存在
- [ ] `GET /candidate/source-latest` 返回 candidate_map
- [ ] Map Editor 无 current release 时仍能显示 source candidate
- [ ] 用户能从 source candidate 保存 Formal Map
- [ ] Formal Map 保存后可 Build Release
- [ ] Publish Current 后 RAG 可用

---

# 9. 不建议的修法

## 9.1 不建议修改 `/candidate` 直接 fallback source candidate

原因：

```text
/candidate 现在语义是 release snapshot candidate
直接 fallback 会混淆 release candidate 和 source candidate
后续调试会更乱
```

除非你决定重新定义接口，否则建议保留语义，新增：

```text
/candidate/source-latest
```

---

## 9.2 不建议让 cold_start_job 自动保存 Formal Map

原因：

```text
Candidate Map 仍然需要管理员确认。
```

自动保存会破坏：

```text
Candidate → Review → Formal Map
```

这个治理边界。

---

## 9.3 不建议让 Map Editor 初始化时自动 POST candidate/from-source

原因：

```text
页面打开不应触发构建型写操作。
```

Map Editor 应该读现有 candidate，而不是隐式重新构建。

---

# 10. 给 Agent 的精确执行口令

```text
当前问题不是 capability，也不是前端单点，而是 cold_start_job 成功态与 Map Editor 默认读取契约不一致。

请执行以下修复：

1. 新增 knowledge_source_candidate_store.py
   - save_latest_source_candidate(project_root, candidate, job_id)
   - load_latest_source_candidate(project_root)
   - 写 project/maps/candidate/latest.json
   - 写 project/maps/candidate/history/*.json
   - 写 project/maps/diffs/latest_diff.json

2. 修改 cold_start_job.py
   - candidate_result 计算后，先生成 diff_review
   - candidate_result.diff_review = diff_review
   - 调 save_latest_source_candidate()
   - 只有保存成功后 job 才能 succeeded
   - 保存失败则 job failed，stage=persisting_candidate_map

3. 修改 game_knowledge_map.py
   - 新增 GET /game/knowledge/map/candidate/source-latest
   - 返回 SourceCandidateResponse
   - 没有 latest 时返回 404 No source candidate map is available
   - 不改变 GET /candidate 的 release snapshot 语义

4. 修改 gameKnowledgeRelease.ts
   - 新增 getLatestSourceCandidate()

5. 修改 FormalMapWorkspace.tsx
   - 初始化时读取 latest source candidate
   - 无 current release 时不阻塞
   - 有 source candidate 时显示并允许 Save Formal Map

6. 补测试
   - cold_start_job_pipeline 断言 latest.json 存在并可 load
   - router 测试 source-latest 404 / 200
   - 视情况补前端测试或人工烟测

禁止：
- 不自动保存 Formal Map
- 不自动 Build Release
- 不自动 Publish Current
- 不恢复 KB
- 不恢复 SVN watcher
- 不把 /candidate 改成含糊 fallback
- 不让 Map Editor 打开时自动 POST 构建

验收：
Rule-only cold-start job succeeded 后，Map Editor 必须能看到 table:HeroTable source candidate，并能保存 Formal Map。
```
