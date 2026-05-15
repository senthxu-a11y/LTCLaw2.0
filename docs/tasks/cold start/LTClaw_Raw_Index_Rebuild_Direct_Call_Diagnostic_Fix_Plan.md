# LTClaw raw_index_rebuild 直接调用诊断修复方案

## 0. 问题定义

当前 Milestone 1 主链路已经基本具备：

```text
CSV Rule-only:
Source Discovery → Raw Index → Canonical Facts → Candidate Map
```

但还有一个非阻塞风险：

```text
如果绕过 UI / cold-start job，直接调用 rebuild_raw_table_indexes()
且项目中只有 xlsx/txt，没有 csv，
函数可能返回 success=false、raw_table_index_count=0，
但 errors 不够明确。
```

这会导致 agent / 调试者误判：

```text
Raw Index 构建失败，但不知道是没有 CSV、格式不支持、路径错，还是内部异常。
```

本方案目标：

```text
给 raw_index_rebuild 增加明确诊断：
当前 Rule-only cold-start 只支持 CSV；
如果没有可用 CSV，必须明确返回 no_csv_table_files_available_for_rule_only_cold_start。
```

---

## 1. 修复原则

### 1.1 不扩大 Milestone 1 范围

本次不做：

```text
不支持 Excel
不支持 TXT
不支持多 sheet
不改 TableIndexer
不改 Canonical
不改 Candidate Map
不改 Release
不改 RAG
```

### 1.2 只补诊断和防误判

修复目标是：

```text
让直接调用 raw_index_rebuild 时也能得到清楚错误。
```

正常 UI / cold-start job 路径不应改变。

---

## 2. 当前源码行为

`source_discovery.py` 当前已经把冷启动支持格式限定为 CSV：

```python
COLD_START_SUPPORTED_FORMATS = frozenset({"csv"})
```

并且会给每个 discovered table file 增加：

```text
cold_start_supported
cold_start_reason
```

CSV 会是：

```text
status=available
cold_start_supported=true
```

XLSX / TXT 会是：

```text
status=recognized
cold_start_supported=false
```

`raw_index_rebuild.py` 当前逻辑是：

```python
for item in discovery['table_files']:
    if status != 'available':
        continue
    if fmt != 'csv':
        errors.append(...)
        continue
```

如果全部文件都是 xlsx/txt：

```text
status 都是 recognized
循环全部 continue
errors 为空
indexed_tables 为空
最终 success=false
```

问题就在这里。

---

## 3. 推荐最小修复

## 3.1 修改文件

只修改：

```text
src/ltclaw_gy_x/game/raw_index_rebuild.py
tests/unit/game/test_raw_index_rebuild.py
```

如果 `test_raw_index_rebuild.py` 已存在，则补测试；如果不存在，则新建。

---

## 3.2 后端代码修复

### Step 1：新增 helper

在 `raw_index_rebuild.py` 中加入：

```python
def _is_rule_only_available_csv(item: dict) -> bool:
    return (
        item.get("status") == "available"
        and item.get("format") == "csv"
        and item.get("cold_start_supported", True) is True
    )


def _recognized_but_not_supported_entries(discovery: dict) -> list[dict]:
    entries = []
    for item in discovery.get("table_files", []):
        if _is_rule_only_available_csv(item):
            continue
        status = item.get("status")
        fmt = item.get("format")
        source_path = item.get("source_path")
        if status in {"recognized", "available"} and fmt != "csv":
            entries.append(
                _error_entry(
                    source_path,
                    item.get("cold_start_reason")
                    or "rule_only_cold_start_currently_supports_csv",
                )
            )
    return entries
```

说明：

```text
- CSV available 继续进入 Raw Index。
- XLSX/TXT recognized 进入 diagnostic errors。
- XLS 不属于 recognized，仍由 unsupported_files 或 discovery 结果处理。
```

---

### Step 2：在 discovery 之后立刻判断是否有 CSV

在 `rebuild_raw_table_indexes()` 中，找到：

```python
if not discovery['table_files']:
    ...
```

在这段之后，`effective_config = ...` 之前，加入：

```python
available_csv_items = [
    item
    for item in discovery["table_files"]
    if _is_rule_only_available_csv(item)
]

if not available_csv_items:
    recognized_errors = _recognized_but_not_supported_entries(discovery)
    unsupported_errors = [
        _error_entry(item.get("source_path"), item.get("reason", "unsupported_table_format"))
        for item in discovery.get("unsupported_files", [])
    ]
    discovery_errors = [
        _error_entry(item.get("source_path"), item.get("reason", "source_discovery_error"))
        for item in discovery.get("errors", [])
    ]

    errors = [*discovery_errors, *recognized_errors, *unsupported_errors]
    if not errors:
        errors = [_error_entry(None, "no_csv_table_files_available_for_rule_only_cold_start")]

    result.update(
        {
            "success": False,
            "raw_table_index_count": 0,
            "indexed_tables": [],
            "errors": errors,
            "next_action": "configure_csv_tables_source",
            "discovery_summary": discovery.get("summary", {}),
        }
    )
    return result
```

---

### Step 3：循环只处理 available_csv_items

把：

```python
for item in discovery['table_files']:
```

改为：

```python
for item in available_csv_items:
```

然后这段可以简化：

```python
status = item['status']
if status != 'available':
    continue
if fmt != 'csv':
    errors.append(...)
    continue
```

建议改成防御断言式：

```python
fmt = item["format"]
if fmt != "csv":
    errors.append(_error_entry(item.get("source_path"), "rule_only_raw_index_currently_supports_csv"))
    continue
```

完整建议：

```python
for item in available_csv_items:
    source_path = item["source_path"]
    fmt = item["format"]
    if fmt != "csv":
        errors.append(_error_entry(source_path, "rule_only_raw_index_currently_supports_csv"))
        continue

    source_file = project_root / source_path
    try:
        ...
```

---

## 4. 期望返回行为

### Case A：有 CSV

输入：

```text
Tables/HeroTable.csv
```

返回：

```json
{
  "success": true,
  "raw_table_index_count": 1,
  "indexed_tables": [
    {
      "table_id": "HeroTable",
      "source_path": "Tables/HeroTable.csv"
    }
  ],
  "errors": [],
  "next_action": "run_canonical_rebuild"
}
```

---

### Case B：只有 XLSX

输入：

```text
Tables/HeroTable.xlsx
```

返回：

```json
{
  "success": false,
  "raw_table_index_count": 0,
  "indexed_tables": [],
  "errors": [
    {
      "source_path": "Tables/HeroTable.xlsx",
      "error": "rule_only_cold_start_not_supported_for_xlsx"
    }
  ],
  "next_action": "configure_csv_tables_source"
}
```

---

### Case C：只有 TXT

输入：

```text
Tables/HeroTable.txt
```

返回：

```json
{
  "success": false,
  "raw_table_index_count": 0,
  "indexed_tables": [],
  "errors": [
    {
      "source_path": "Tables/HeroTable.txt",
      "error": "rule_only_cold_start_not_supported_for_txt"
    }
  ],
  "next_action": "configure_csv_tables_source"
}
```

---

### Case D：没有任何表

返回：

```json
{
  "success": false,
  "raw_table_index_count": 0,
  "errors": [
    {
      "error": "no_available_table_files"
    }
  ],
  "next_action": "configure_tables_source"
}
```

这里可以保持原逻辑，也可以把 next_action 改得更准确。

---

## 5. 测试方案

## 5.1 新增 / 修改测试文件

```text
tests/unit/game/test_raw_index_rebuild.py
```

---

## 5.2 测试 1：CSV 成功

```python
import asyncio

from ltclaw_gy_x.game.config import ProjectTablesSourceConfig
from ltclaw_gy_x.game.raw_index_rebuild import rebuild_raw_table_indexes


def test_rebuild_raw_table_indexes_succeeds_for_csv(tmp_path):
    project_root = tmp_path / "project-root"
    tables_dir = project_root / "Tables"
    tables_dir.mkdir(parents=True)
    (tables_dir / "HeroTable.csv").write_text(
        "ID,Name,HP,Attack\n1,HeroA,100,20\n",
        encoding="utf-8",
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=["Tables"],
                include=["**/*.csv"],
                exclude=[],
                header_row=1,
                primary_key_candidates=["ID"],
            ),
        )
    )

    assert result["success"] is True
    assert result["raw_table_index_count"] == 1
    assert result["indexed_tables"][0]["table_id"] == "HeroTable"
    assert result["errors"] == []
```

---

## 5.3 测试 2：只有 XLSX 时明确失败

```python
def test_rebuild_raw_table_indexes_reports_no_csv_for_xlsx_only(tmp_path):
    project_root = tmp_path / "project-root"
    tables_dir = project_root / "Tables"
    tables_dir.mkdir(parents=True)
    (tables_dir / "HeroTable.xlsx").write_text("fake", encoding="utf-8")

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=["Tables"],
                include=["**/*.xlsx"],
                exclude=[],
                header_row=1,
                primary_key_candidates=["ID"],
            ),
        )
    )

    assert result["success"] is False
    assert result["raw_table_index_count"] == 0
    assert result["next_action"] == "configure_csv_tables_source"
    assert result["errors"]
    assert result["errors"][0]["source_path"] == "Tables/HeroTable.xlsx"
    assert "csv" in result["errors"][0]["error"]
```

注意：

```text
这里用假 xlsx 文件也可以，因为测试目标不是 Excel 读取，而是确认 raw index rebuild 在没有 CSV 时提前退出。
```

---

## 5.4 测试 3：只有 TXT 时明确失败

```python
def test_rebuild_raw_table_indexes_reports_no_csv_for_txt_only(tmp_path):
    project_root = tmp_path / "project-root"
    tables_dir = project_root / "Tables"
    tables_dir.mkdir(parents=True)
    (tables_dir / "HeroTable.txt").write_text(
        "ID\tName\tHP\tAttack\n1\tHeroA\t100\t20\n",
        encoding="utf-8",
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=["Tables"],
                include=["**/*.txt"],
                exclude=[],
                header_row=1,
                primary_key_candidates=["ID"],
            ),
        )
    )

    assert result["success"] is False
    assert result["raw_table_index_count"] == 0
    assert result["next_action"] == "configure_csv_tables_source"
    assert result["errors"]
    assert result["errors"][0]["source_path"] == "Tables/HeroTable.txt"
    assert "csv" in result["errors"][0]["error"]
```

---

## 5.5 测试 4：CSV + XLSX 时只处理 CSV

```python
def test_rebuild_raw_table_indexes_ignores_non_csv_when_csv_exists(tmp_path):
    project_root = tmp_path / "project-root"
    tables_dir = project_root / "Tables"
    tables_dir.mkdir(parents=True)
    (tables_dir / "HeroTable.csv").write_text(
        "ID,Name,HP,Attack\n1,HeroA,100,20\n",
        encoding="utf-8",
    )
    (tables_dir / "OtherTable.xlsx").write_text("fake", encoding="utf-8")

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=["Tables"],
                include=["**/*.csv", "**/*.xlsx"],
                exclude=[],
                header_row=1,
                primary_key_candidates=["ID"],
            ),
        )
    )

    assert result["success"] is True
    assert result["raw_table_index_count"] == 1
    assert result["indexed_tables"][0]["table_id"] == "HeroTable"
```

是否把 xlsx 作为 warning 记录，可以不强制。  
建议不记录 warning，避免污染成功链路。

---

## 6. 验收命令

执行：

```bash
pytest tests/unit/game/test_raw_index_rebuild.py
pytest tests/unit/game/test_cold_start_job_pipeline.py
pytest tests/unit/game/test_cold_start_job_stale.py
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

必须保证：

```text
CSV smoke 不受影响
cold-start job pipeline 不受影响
xlsx/txt-only raw rebuild 有明确失败原因
```

---

## 7. 是否阻塞 Milestone 1

判断：

```text
不阻塞。
```

原因：

```text
UI 已经按 cold_start_supported 控制按钮。
cold-start job 已经按 status=available 过滤 available_tables。
这个问题只影响直接调用 raw_index_rebuild 的调试路径。
```

但是建议在宣布 Milestone 1 前顺手补掉，因为改动很小，能减少后续误判。

---

## 8. 给 agent 的执行口令

```text
请只修 raw_index_rebuild 直接调用诊断问题，不扩大冷启动格式范围。

目标：
当项目中只有 xlsx/txt，没有 csv 时，rebuild_raw_table_indexes() 必须明确返回：
success=false
raw_table_index_count=0
next_action=configure_csv_tables_source
errors 中说明 rule_only cold-start 当前只支持 CSV。

允许修改：
src/ltclaw_gy_x/game/raw_index_rebuild.py
tests/unit/game/test_raw_index_rebuild.py

禁止：
不支持 Excel
不支持 TXT
不改 TableIndexer
不改 Canonical
不改 Candidate Map
不改 UI
不改 Release/RAG/KB

必须测试：
CSV 成功
只有 XLSX 明确失败
只有 TXT 明确失败
CSV + XLSX 只处理 CSV
smoke 脚本仍成功
```
