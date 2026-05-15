# LTClaw 冷启动 Milestone 1：GPT-5.4 精准执行版施工单

## 0. 使用方式

这份文档是给 GPT-5.4 / coding agent 执行的低自由度施工单。

目标不是让 agent 重新设计，而是让它按指定文件、指定字段、指定验收方式完成最小修复。

本轮只追求：

```text
CSV Rule-only 冷启动一次跑通。
```

不要扩大范围。

---

## 1. 总目标

基于当前提交：

```text
a4084f685188ece1bee87cd1eaae82a824001106
complete cold start core flow
```

完成 Milestone 1：

```text
Milestone 1: CSV Cold-start Core Path Ready
```

必须保证：

```text
examples/minimal_project/Tables/HeroTable.csv
→ Source Discovery
→ Raw TableIndex
→ CanonicalTableSchema
→ Candidate Map
→ Cold-start Job succeeded
```

最终 smoke 命令必须成功：

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

期望输出：

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

---

## 2. 绝对禁止事项

本轮禁止：

- [ ] 不支持 Excel 作为 cold-start P0。
- [ ] 不支持 TXT 作为 cold-start P0。
- [ ] 不做 XLSX 多 sheet。
- [ ] 不做 JSON / YAML / TSV。
- [ ] 不自动保存 Formal Map。
- [ ] 不自动 Build Release。
- [ ] 不自动 Publish Current。
- [ ] 不恢复 KB。
- [ ] 不恢复 SVN watcher。
- [ ] 不做 LLM 生成脚本。
- [ ] 不做 MCP。
- [ ] 不重构架构。
- [ ] 不把 source-write、RAG、Release、KB 链路重新改动。
- [ ] 不把当前冷启动流程改成依赖 LLM。

---

# 3. 任务切片总览

只做 5 个切片：

```text
Slice 1：CSV-only cold-start 格式边界
Slice 2：setup-status discovery not_scanned 语义
Slice 3：running job stale 防护
Slice 4：完整 cold-start job pipeline 测试
Slice 5：smoke + UI 人工验收说明更新
```

执行顺序必须是：

```text
Slice 1 → Slice 2 → Slice 3 → Slice 4 → Slice 5
```

---

# Slice 1：CSV-only cold-start 格式边界

## 目标

当前 `source_discovery.py` 会把 `.csv / .xlsx / .txt` 都作为 available，但 `raw_index_rebuild.py` 只支持 CSV。  
这会误导 UI 用户。

本切片目标：

```text
Rule-only cold-start P0 只支持 CSV。
XLSX/TXT 可被发现，但不得显示为“可一键冷启动”。
```

## 允许修改文件

```text
src/ltclaw_gy_x/game/source_discovery.py
console/src/api/types/game.ts
console/src/pages/Game/components/projectSetupHelpers.ts
console/src/pages/Game/GameProject.tsx
```

如果实际前端文件名略有不同，可以只改对应 Project Setup 页面和类型文件。

## 禁止修改文件

```text
src/ltclaw_gy_x/game/table_indexer.py
src/ltclaw_gy_x/game/raw_index_rebuild.py
src/ltclaw_gy_x/game/canonical_facts_committer.py
src/ltclaw_gy_x/game/cold_start_job.py
```

本切片不改 raw index 逻辑，只修“发现与 UI 可构建状态”的语义。

---

## 后端精确改法

文件：

```text
src/ltclaw_gy_x/game/source_discovery.py
```

### 1. 新增常量

加入：

```python
RULE_ONLY_COLD_START_FORMATS = {"csv"}
```

### 2. 修改 `_entry`

当前：

```python
def _entry(source_path: str, fmt: str, status: str, reason: str) -> dict:
    return {
        "source_path": _normalize_path_for_match(source_path),
        "format": fmt,
        "status": status,
        "reason": reason,
    }
```

改为：

```python
def _entry(
    source_path: str,
    fmt: str,
    status: str,
    reason: str,
    *,
    cold_start_supported: bool | None = None,
    cold_start_reason: str | None = None,
) -> dict:
    payload = {
        "source_path": _normalize_path_for_match(source_path),
        "format": fmt,
        "status": status,
        "reason": reason,
    }
    if cold_start_supported is not None:
        payload["cold_start_supported"] = cold_start_supported
    if cold_start_reason:
        payload["cold_start_reason"] = cold_start_reason
    return payload
```

### 3. CSV available entry

在 `status == "available"` 分支里改成：

```python
if status == "available" and fmt is not None:
    if fmt in RULE_ONLY_COLD_START_FORMATS:
        table_files.append(
            _entry(
                normalized_path,
                fmt,
                "available",
                "matched_supported_format",
                cold_start_supported=True,
            )
        )
    else:
        unsupported_entry = _entry(
            normalized_path,
            fmt,
            "unsupported_for_cold_start",
            "rule_only_cold_start_currently_supports_csv",
            cold_start_supported=False,
            cold_start_reason="rule_only_cold_start_currently_supports_csv",
        )
        table_files.append(unsupported_entry)
        unsupported_files.append(unsupported_entry)
    seen_paths.add(normalized_path)
    continue
```

### 4. available_count 只能统计 cold_start_supported

当前：

```python
available_count = sum(1 for item in table_files if item["status"] == "available")
```

改为：

```python
available_count = sum(
    1
    for item in table_files
    if item.get("status") == "available" and item.get("cold_start_supported") is True
)
```

### 5. discovered_table_count 仍可表示发现数量

保留：

```python
"discovered_table_count": len(table_files)
```

但 UI 启动构建必须看 `available_table_count` 或 `cold_start_supported`。

---

## 前端精确改法

### 1. 更新类型

文件：

```text
console/src/api/types/game.ts
```

在 table source discovery item 类型中增加：

```ts
cold_start_supported?: boolean;
cold_start_reason?: string;
```

如果已有类型名不同，找到对应 `table_files` item 类型加字段。

### 2. 一键构建按钮条件

找到 helper：

```text
canStartRuleOnlyColdStartBuild(...)
```

或者等价逻辑。

要求改为：

```ts
const availableColdStartTables = discovery.table_files.filter(
  item => item.status === "available" && item.cold_start_supported === true
);

return setup.project_root_exists === true
  && availableColdStartTables.length > 0
  && !runningJob;
```

不能用：

```ts
discovered_table_count > 0
```

作为构建条件。

### 3. UI 文案

CSV：

```text
可用于 Rule-only 冷启动
```

XLSX/TXT：

```text
已识别，但当前 Rule-only 冷启动仅支持 CSV
```

---

## Slice 1 验收

### 自动/人工验证

在 `examples/minimal_project/Tables` 下临时增加：

```text
HeroTable.xlsx
HeroTable.txt
OldTable.xls
```

预期：

- [ ] CSV: `status=available`, `cold_start_supported=true`
- [ ] XLSX: `status=unsupported_for_cold_start`, `cold_start_supported=false`
- [ ] TXT: `status=unsupported_for_cold_start`, `cold_start_supported=false`
- [ ] XLS: `status=unsupported`
- [ ] Rule-only 构建按钮仍对 CSV 启用
- [ ] 如果只有 XLSX/TXT，没有 CSV，Rule-only 构建按钮禁用

---

# Slice 2：setup-status discovery not_scanned 语义

## 目标

当前 setup-status 默认 discovery count 为 0，会误导用户以为系统已经扫描但没找到表。

本切片目标：

```text
未执行 Source Discovery 时显示 not_scanned，而不是 0 张表。
```

## 允许修改文件

```text
src/ltclaw_gy_x/app/routers/game_project.py
console/src/api/types/game.ts
console/src/pages/Game/GameProject.tsx
console/src/pages/Game/components/projectSetupHelpers.ts
```

## 后端精确改法

文件：

```text
src/ltclaw_gy_x/app/routers/game_project.py
```

在 `_build_setup_status()` 里的 discovery 增加 status：

当前：

```python
"discovery": {
    "discovered_table_count": 0,
    "unsupported_table_count": 0,
    "excluded_table_count": 0,
    "error_count": 0,
},
```

改为：

```python
"discovery": {
    "status": "not_scanned",
    "discovered_table_count": 0,
    "available_table_count": 0,
    "unsupported_table_count": 0,
    "excluded_table_count": 0,
    "error_count": 0,
},
```

注意：不要在 setup-status 里自动扫描，避免接口变慢。

## 前端精确改法

### 类型

在 setup-status discovery 类型加：

```ts
status?: "not_scanned" | "scanned";
available_table_count?: number;
```

### UI

未扫描时显示：

```text
尚未检查数据源
```

不要显示：

```text
发现 0 张表
```

当用户点击 `/sources/discover` 后，前端把 discoveryResult 视为：

```ts
status: "scanned"
```

保存 Project Root 或 Tables Source 后，前端清空 discoveryResult，回到 not_scanned。

## Slice 2 验收

- [ ] 打开 Project Setup，未扫描时显示“尚未检查数据源”。
- [ ] 不显示“发现 0 张表”。
- [ ] 点击检查数据源后显示真实数量。
- [ ] 修改 Tables Source 后回到“尚未检查数据源”。
- [ ] 修改 Project Root 后回到“尚未检查数据源”。

---

# Slice 3：running job stale 防护

## 目标

后端重启后，旧 job 文件可能仍是 running，但线程已不存在。必须防止前端永久显示 running。

## 允许修改文件

```text
src/ltclaw_gy_x/game/cold_start_job.py
src/ltclaw_gy_x/app/routers/game_knowledge_map.py
tests/unit/game/test_cold_start_job_stale.py
```

---

## 后端精确改法

文件：

```text
src/ltclaw_gy_x/game/cold_start_job.py
```

### 1. 新增函数

添加：

```python
def load_cold_start_job_with_stale_check(project_root: Path, job_id: str) -> ColdStartJobState | None:
    state = load_cold_start_job(project_root, job_id)
    if state is None:
        return None

    if state.status in _ACTIVE_JOB_STATUSES:
        handle = _active_handle(state.project_key)
        if handle is None or handle.job_id != job_id:
            state.status = "failed"
            state.stage = "stale"
            state.message = "Cold-start job was interrupted or server restarted."
            state.next_action = "retry_cold_start_job"
            state.finished_at = _now()
            save_cold_start_job(project_root, state)

    return state
```

说明：本轮不要做复杂超时窗口，直接无 handle 判 stale。这样更稳定。

### 2. 修改 GET job route

文件：

```text
src/ltclaw_gy_x/app/routers/game_knowledge_map.py
```

导入：

```python
load_cold_start_job_with_stale_check
```

把：

```python
job = load_cold_start_job(project_root, job_id)
```

改为：

```python
job = load_cold_start_job_with_stale_check(project_root, job_id)
```

`cancel` route 可以继续用 `load_cold_start_job` 或也使用 stale check，建议保持简单。

---

## 测试

新增：

```text
tests/unit/game/test_cold_start_job_stale.py
```

测试内容：

```python
from datetime import datetime, timezone
from ltclaw_gy_x.game.cold_start_job import (
    ColdStartJobState,
    save_cold_start_job,
    load_cold_start_job_with_stale_check,
)

def test_running_job_without_active_handle_becomes_stale(tmp_path):
    project_root = tmp_path / "project-root"
    project_root.mkdir(parents=True)

    state = ColdStartJobState(
        job_id="job-stale",
        project_key="demo-project",
        project_root=str(project_root),
        status="running",
        stage="building_raw_index",
        progress=40,
        message="Running",
        created_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
        started_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )
    save_cold_start_job(project_root, state)

    loaded = load_cold_start_job_with_stale_check(project_root, "job-stale")

    assert loaded is not None
    assert loaded.status == "failed"
    assert loaded.stage == "stale"
    assert loaded.next_action == "retry_cold_start_job"
```

## Slice 3 验收

- [ ] 测试通过。
- [ ] 旧 running job 不再永久 running。
- [ ] UI 可显示 retry。

---

# Slice 4：完整 cold-start job pipeline 测试

## 目标

补上最关键自动化测试：

```text
HeroTable.csv → job succeeded → counts 全部为 1
```

## 允许修改文件

```text
tests/unit/game/test_cold_start_job_pipeline.py
```

如有必要，允许小幅修改：

```text
src/ltclaw_gy_x/game/cold_start_job.py
```

但不允许改业务行为绕测试。

---

## 测试代码要求

新增：

```text
tests/unit/game/test_cold_start_job_pipeline.py
```

建议结构：

```python
from __future__ import annotations

import time
from pathlib import Path

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.paths import (
    get_project_canonical_table_schema_path,
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_raw_table_index_path,
)

def _write_hero_table(project_root: Path) -> None:
    table_dir = project_root / "Tables"
    table_dir.mkdir(parents=True)
    (table_dir / "HeroTable.csv").write_text(
        "ID,Name,HP,Attack\n1,HeroA,100,20\n",
        encoding="utf-8",
    )

def _wait_for_terminal(project_root: Path, job_id: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = load_cold_start_job(project_root, job_id)
        if state and state.status in {"succeeded", "failed", "cancelled"}:
            return state
        time.sleep(0.05)
    raise AssertionError("cold-start job did not finish in time")

def test_cold_start_job_pipeline_succeeds_for_minimal_csv(tmp_path):
    project_root = tmp_path / "project-root"
    project_root.mkdir(parents=True)
    _write_hero_table(project_root)

    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(
            roots=["Tables"],
            include=["**/*.csv"],
            exclude=["**/~$*", "**/.backup/**"],
            header_row=1,
            primary_key_candidates=["ID", "Id", "id"],
        ),
    )

    created, reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    assert reused is False

    finished = _wait_for_terminal(project_root, created.job_id)

    assert finished.status == "succeeded"
    assert finished.stage == "done"
    assert finished.progress == 100
    assert finished.counts.discovered_table_count == 1
    assert finished.counts.raw_table_index_count == 1
    assert finished.counts.canonical_table_count == 1
    assert finished.counts.candidate_table_count == 1
    assert finished.candidate_refs == ["table:HeroTable"]
    assert "diff_review" in finished.partial_outputs

    assert get_project_raw_table_index_path(project_root, "HeroTable").exists()
    assert get_project_canonical_table_schema_path(project_root, "HeroTable").exists()

    assert not get_project_formal_map_canonical_path(project_root).exists()
    assert not get_project_current_release_path(project_root).exists()
```

如果 `create_or_get_cold_start_job` 返回顺序是 `(state, reused)`，按实际源码修正变量名。当前源码是：

```python
return state, False
```

所以测试里应该写：

```python
created, reused = create_or_get_cold_start_job(...)
```

## Slice 4 验收

- [ ] 新测试通过。
- [ ] 不依赖 LLM。
- [ ] 不依赖 SVN。
- [ ] 不依赖 KB。
- [ ] 不自动 Formal Map。
- [ ] 不自动 Release。

---

# Slice 5：smoke + UI 人工验收说明更新

## 目标

确保 agent 施工后能直接证明 Milestone 1 成功。

## 允许修改文件

```text
docs/tasks/cold start/...
README 或开发文档
```

不强制修改代码。

## 必须执行命令

### 后端 smoke

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

### 后端测试

```bash
pytest tests/unit/game/test_canonical_facts_committer.py
pytest tests/unit/game/test_cold_start_job.py
pytest tests/unit/game/test_cold_start_job_stale.py
pytest tests/unit/game/test_cold_start_job_pipeline.py
```

### 前端测试

按项目实际命令执行，至少：

```bash
cd console
npm test -- coldStartJobHelpers
```

如果项目使用其他命令，执行等价命令，并记录实际命令。

## UI 人工验收

必须人工跑：

```text
1. 打开 Project Setup
2. 配置 Local Project Root = examples/minimal_project
3. 配置 Tables Root = Tables
4. Include = **/*.csv
5. 点击检查数据源
6. 确认 HeroTable.csv available
7. 点击 Rule-only 冷启动构建
8. 观察进度条
9. 构建中切换页面再回来
10. 刷新页面恢复 job
11. 看到 succeeded
12. candidate_refs = table:HeroTable
```

## Milestone 1 最终归档备注

- 当前结论已成立：Milestone 1 已达到既定目标，CSV Rule-only 冷启动核心路径已通过 smoke、自动化测试和人工 UI 验收。
- 本次出现的 `Missing capability: knowledge.candidate.write` 属于本地运行环境配置问题，不是 cold-start 代码缺陷。
- 根因是新隔离 `LTCLAW_WORKING_DIR` 下缺少本地用户配置，UI 请求会回落到 viewer capability，并在写入路由被正确拦截。
- 最小处理方式是在当前 `LTCLAW_WORKING_DIR` 对应目录补 `game_data/user/game_user.yaml`，并设置：`my_role: maintainer`。
- 补完本地用户配置后，必须在同一 `LTCLAW_WORKING_DIR` 下重启后端，再继续做 UI 验收。
- 本轮最终 UI 验收结果应以修正后的同一 working dir 为准，不需要修改权限系统实现，也不需要修改 cold-start 业务逻辑。

---

# 4. 最终验收矩阵

## 4.1 自动验收

必须全部通过：

- [ ] `python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only`
- [ ] `pytest tests/unit/game/test_canonical_facts_committer.py`
- [ ] `pytest tests/unit/game/test_cold_start_job.py`
- [ ] `pytest tests/unit/game/test_cold_start_job_stale.py`
- [ ] `pytest tests/unit/game/test_cold_start_job_pipeline.py`
- [ ] 前端 coldStartJobHelpers 测试通过

## 4.2 人工验收

必须全部通过：

- [ ] 用户能找到 Project Setup。
- [ ] 用户能配置 Local Project Root。
- [ ] 用户能配置 Tables Root。
- [ ] 未扫描时显示“尚未检查数据源”。
- [ ] Source Discovery 发现 HeroTable.csv。
- [ ] Rule-only 构建按钮启用。
- [ ] 构建有进度条。
- [ ] 构建有阶段说明。
- [ ] 切换页面不打断。
- [ ] 刷新页面能恢复。
- [ ] Job succeeded。
- [ ] discovered/raw/canonical/candidate 都为 1。
- [ ] candidate_refs 显示 `table:HeroTable`。
- [ ] 不自动保存 Formal Map。
- [ ] 不自动 Build Release。
- [ ] 不自动 Publish Current。

## 4.3 失败验收

必须能正确失败：

- [ ] 不存在 project_root 返回清晰错误。
- [ ] 错误 tables root 返回 source_root_missing。
- [ ] 只有 xlsx/txt 时，Rule-only 构建按钮禁用，并说明 P0 仅 CSV。
- [ ] 后端重启后的 running job 不永久 running，而是 stale/failed。
- [ ] 失败状态显示 stage/error/next_action。

---

# 5. Agent 最终交付格式

GPT-5.4 执行完后，必须按以下格式回复。

```text
## 改动文件

- ...

## 完成的 Slice

- Slice 1：...
- Slice 2：...
- Slice 3：...
- Slice 4：...
- Slice 5：...

## 执行的命令

```bash
...
```

## 测试结果

- smoke：通过/失败
- pytest：通过/失败
- frontend test：通过/失败

## 人工验收结果

- Project Setup：通过/失败
- Source Discovery：通过/失败
- Cold-start Job：通过/失败
- 切换页面恢复：通过/失败
- 刷新恢复：通过/失败

## 未完成项

- ...

## 是否触碰禁止范围

- Excel/TXT 正式支持：否
- Formal Map 自动保存：否
- Release 自动 Build：否
- Current 自动 Publish：否
- KB：否
- SVN watcher：否

## 最终判断

Milestone 1: CSV Cold-start Core Path Ready
是 / 否
```

---

# 6. 给 GPT-5.4 的直接执行 Prompt

把下面这段直接发给 GPT-5.4：

```text
你要在 LTClaw2.0 仓库中执行冷启动 Milestone 1 修复。

基线提交：
a4084f685188ece1bee87cd1eaae82a824001106

目标：
只保证 CSV Rule-only 冷启动一次跑通。

必须完成 5 个 Slice：
1. CSV-only cold-start 格式边界：XLSX/TXT 不得显示为可一键 cold-start。
2. setup-status discovery 加 not_scanned/scanned 语义，避免默认 0 误导。
3. cold-start running job 加 stale 检测，后端重启后不能永久 running。
4. 增加完整 cold-start job pipeline 测试。
5. 执行 smoke 和自动化测试，并按指定格式报告。

禁止：
不做 Excel/TXT 正式支持。
不做多 sheet。
不自动保存 Formal Map。
不自动 Build Release。
不自动 Publish Current。
不恢复 KB。
不恢复 SVN watcher。
不做 LLM 生成脚本。
不做 MCP。

必须通过：
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only

必须新增测试：
tests/unit/game/test_cold_start_job_stale.py
tests/unit/game/test_cold_start_job_pipeline.py

最终判断标准：
如果 smoke 成功，pipeline 测试成功，UI 能完成 Project Setup → Source Discovery → Rule-only Job → Candidate Map，并且切换/刷新不打断，则宣布：
Milestone 1: CSV Cold-start Core Path Ready。
```
