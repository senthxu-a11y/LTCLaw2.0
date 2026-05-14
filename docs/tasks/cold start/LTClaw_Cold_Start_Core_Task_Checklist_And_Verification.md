# LTClaw Map 冷启动核心功能最快落地 Checklist + 验证方案

## 0. 本轮目标

本轮只追求一个结果：

```text
用户可以在 UI 中配置本地项目路径和表路径；
用 1 张小表 rule-only 跑通：
Source Discovery → Raw Index → Canonical Facts → Candidate Map；
构建过程有进度条；
切换页面不打断；
失败能显示阶段、原因、路径、下一步。
```

不做复杂增强，不做大范围重构。

---

## 1. 最小验收样例

### 1.1 本地样例目录

必须提供一个最小项目：

```text
examples/minimal_project/
  Tables/
    HeroTable.csv
```

### 1.2 HeroTable.csv 内容

```csv
ID,Name,HP,Attack
1,HeroA,100,20
```

### 1.3 最终成功标准

UI 或 API 必须返回：

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

---

# Phase 1：Project Setup UI 最小闭环

## 1.1 目标

用户必须能在一个明确入口完成：

```text
Local Project Root
Tables Root
Include Patterns
Source Discovery
```

不要再让用户找隐藏配置、YAML、SVN Root 或 Advanced 页面。

---

## 1.2 后端任务

### Task 1：新增 Project Setup 状态接口

接口：

```text
GET /game/project/setup-status
```

返回字段：

```json
{
  "project_root": "E:/test_project",
  "project_root_exists": true,
  "project_bundle_root": "...",
  "project_key": "...",
  "tables_config": {
    "roots": ["Tables"],
    "include": ["**/*.csv", "**/*.xlsx", "**/*.txt"],
    "exclude": ["**/~$*", "**/.backup/**"],
    "header_row": 1,
    "primary_key_candidates": ["ID", "Id", "id"]
  },
  "discovery": {
    "discovered_table_count": 0,
    "unsupported_table_count": 0,
    "excluded_table_count": 0,
    "error_count": 0
  },
  "build_readiness": {
    "blocking_reason": "no_table_sources_found",
    "next_action": "configure_tables_source"
  }
}
```

Checklist：

- [ ] 能读取当前 project_root。
- [ ] 能判断 project_root 是否存在。
- [ ] 能返回 project_bundle_root。
- [ ] 能返回 project_key。
- [ ] 能返回当前 tables 配置。
- [ ] 没有配置时返回默认 tables 配置。
- [ ] 能返回当前 discovery 概览。
- [ ] 能返回 blocking_reason。
- [ ] 能返回 next_action。

验证：

- [ ] 未配置 project_root 时，返回 `project_root_exists=false`。
- [ ] 配置合法 project_root 后，返回 `project_root_exists=true`。
- [ ] project_bundle_root 不为空。
- [ ] 默认 tables include 包含 `**/*.csv`。

---

### Task 2：新增保存 Local Project Root 接口

接口：

```text
PUT /game/project/root
```

请求：

```json
{
  "project_root": "E:/test_project"
}
```

Checklist：

- [ ] 校验 project_root 不能为空。
- [ ] 校验必须是本地路径。
- [ ] 拒绝 `svn://`。
- [ ] 拒绝 `http://`。
- [ ] 拒绝 `https://`。
- [ ] 校验路径存在。
- [ ] 保存到明确配置位置。
- [ ] 返回 project_key。
- [ ] 返回 project_bundle_root。
- [ ] 返回 setup-status。

验证：

- [ ] 传空路径返回 400。
- [ ] 传不存在路径返回 400。
- [ ] 传 `svn://xxx` 返回 400。
- [ ] 传真实路径成功。
- [ ] 成功后重新 GET setup-status，project_root 保持一致。

---

### Task 3：新增保存 Tables Source 配置接口

接口：

```text
PUT /game/project/sources/tables
```

请求：

```json
{
  "roots": ["Tables"],
  "include": ["**/*.csv", "**/*.xlsx", "**/*.txt"],
  "exclude": ["**/~$*", "**/.backup/**"],
  "header_row": 1,
  "primary_key_candidates": ["ID", "Id", "id"]
}
```

Checklist：

- [ ] 支持 roots。
- [ ] 支持 include。
- [ ] 支持 exclude。
- [ ] 支持 header_row。
- [ ] 支持 primary_key_candidates。
- [ ] 写入 `<project-bundle>/project/sources/tables.yaml`。
- [ ] 返回 effective_config。
- [ ] 返回 setup-status。
- [ ] 不要求用户手写 YAML。

验证：

- [ ] 保存 `roots=["Tables"]` 成功。
- [ ] 文件 `tables.yaml` 存在。
- [ ] 再次读取 setup-status 能看到保存的配置。
- [ ] header_row 小于 1 时返回 400。

---

## 1.3 前端任务

### Task 4：新增 / 改造 Project Setup 页面

入口建议：

```text
Game → Project Setup
```

页面分区：

```text
1. Local Project Root
2. Tables Source
3. Source Discovery
4. Build Pipeline Status
```

Checklist：

- [ ] 第一屏能看到 Local Project Root。
- [ ] 第一屏能看到 Tables Root。
- [ ] 有“保存路径”按钮。
- [ ] 有“保存表路径配置”按钮。
- [ ] 有“检查数据源”按钮。
- [ ] 显示 project_bundle_root。
- [ ] 显示 project_key。
- [ ] 显示 blocking_reason。
- [ ] 显示 next_action。
- [ ] 不再把 SVN Root 作为主配置名。

验证：

- [ ] 用户能从导航找到 Project Setup。
- [ ] 用户不用手写 YAML 也能配置 Tables。
- [ ] 配置后页面立即刷新 setup-status。
- [ ] 配置错误能看到明确错误。

---

# Phase 2：Source Discovery 最小闭环

## 2.1 目标

用户配置表路径后，必须立即知道系统有没有找到表。

---

## 2.2 后端任务

### Task 5：新增 Source Discovery 接口

接口：

```text
POST /game/project/sources/discover
```

返回：

```json
{
  "success": true,
  "project_root": "E:/test_project",
  "table_files": [
    {
      "source_path": "Tables/HeroTable.csv",
      "format": "csv",
      "status": "available",
      "reason": "matched include pattern"
    }
  ],
  "excluded_files": [],
  "unsupported_files": [],
  "errors": [],
  "summary": {
    "discovered_table_count": 1,
    "available_table_count": 1,
    "excluded_table_count": 0,
    "unsupported_table_count": 0,
    "error_count": 0
  },
  "next_action": "run_raw_index"
}
```

Checklist：

- [ ] 从 project_root 开始扫描。
- [ ] 根据 tables roots 扫描。
- [ ] 支持 include patterns。
- [ ] 支持 exclude patterns。
- [ ] 默认排除 `~$*.xlsx`。
- [ ] 支持 `.csv`。
- [ ] 支持 `.xlsx`。
- [ ] 支持 `.txt`。
- [ ] `.xls` 标记 unsupported。
- [ ] 返回每个文件状态。
- [ ] 返回 summary。
- [ ] 没找到表时返回 `next_action=configure_tables_source`。

验证：

- [ ] minimal_project 能发现 1 张 HeroTable.csv。
- [ ] `~$Temp.xlsx` 被 excluded。
- [ ] `OldTable.xls` 被 unsupported。
- [ ] include 不匹配时 discovered_table_count=0，且有明确 next_action。
- [ ] 中文路径下能扫描。

---

## 2.3 前端任务

### Task 6：Source Discovery 预览表

Checklist：

- [ ] 显示发现数量。
- [ ] 显示 available 文件列表。
- [ ] 显示 excluded 文件列表。
- [ ] 显示 unsupported 文件列表。
- [ ] 显示 errors。
- [ ] discovered_table_count=0 时禁用后续构建按钮。
- [ ] 支持“复制诊断信息”。

验证：

- [ ] HeroTable.csv 显示为 available。
- [ ] 无表时显示“没有发现表文件”。
- [ ] 不支持文件显示原因。

---

# Phase 3：Raw Index 最小闭环

## 3.1 目标

Source Discovery 找到表后，能生成 Raw TableIndex。

---

## 3.2 后端任务

### Task 7：新增 / 暴露 Raw Index Rebuild 接口

接口：

```text
POST /game/knowledge/raw-index/rebuild
```

请求：

```json
{
  "scope": "tables",
  "rule_only": true
}
```

返回：

```json
{
  "success": true,
  "raw_table_index_count": 1,
  "indexed_tables": [
    {
      "table_id": "HeroTable",
      "source_path": "Tables/HeroTable.csv",
      "row_count": 1,
      "field_count": 4,
      "primary_key": "ID"
    }
  ],
  "errors": [],
  "next_action": "run_canonical_rebuild"
}
```

Checklist：

- [ ] 支持 scope=tables。
- [ ] 使用 Source Discovery 的文件列表。
- [ ] 生成 TableIndex。
- [ ] 写入 `project/indexes/tables/*.json`。
- [ ] 写入 `project/indexes/table_indexes.json`。
- [ ] 返回 raw_table_index_count。
- [ ] 返回 indexed_tables。
- [ ] 单表失败不阻断其他表。
- [ ] CSV UTF-8 支持。
- [ ] CSV UTF-8 BOM 支持。
- [ ] 表头为空返回文件级错误。
- [ ] header_row 配错返回文件级错误。

验证：

- [ ] HeroTable.csv 生成 1 个 TableIndex。
- [ ] row_count=1。
- [ ] field_count=4。
- [ ] primary_key=ID。
- [ ] 输出目录存在 table index 文件。
- [ ] header_row 错误时返回明确错误。

---

# Phase 4：Canonical Facts 最小闭环

## 4.1 目标

Raw TableIndex 生成后，必须能生成 CanonicalTableSchema。

---

## 4.2 后端任务

### Task 8：新增 Canonical Facts Committer

新增文件建议：

```text
src/ltclaw_gy_x/game/canonical_facts_committer.py
```

Checklist：

- [ ] 读取 TableIndex。
- [ ] 调用 `build_canonical_table_schema(table_index)`。
- [ ] 写入 `get_project_canonical_table_schema_path(project_root, table_id)`。
- [ ] atomic write。
- [ ] 目录不存在时创建。
- [ ] 单表失败不阻断其他表。
- [ ] 返回 written 列表。
- [ ] 返回 errors。
- [ ] 不依赖 LLM。

验证：

- [ ] 给一个 TableIndex，生成一个 CanonicalTableSchema JSON。
- [ ] JSON 能被 `CanonicalTableSchema.model_validate()` 读取。
- [ ] canonical_header 正常归一化。
- [ ] primary key semantic_type=id。
- [ ] source=raw_index_rule。

---

### Task 9：新增 Canonical Rebuild 接口

接口：

```text
POST /game/knowledge/canonical/rebuild
```

请求：

```json
{
  "scope": "tables",
  "rule_only": true,
  "force": false
}
```

返回：

```json
{
  "success": true,
  "raw_table_index_count": 1,
  "canonical_table_count": 1,
  "written": ["HeroTable.json"],
  "errors": [],
  "warnings": [],
  "next_action": "build_candidate_from_source"
}
```

Checklist：

- [ ] 支持 scope=tables。
- [ ] 从 raw table indexes 读取。
- [ ] 生成 canonical table schemas。
- [ ] rule_only=true 时不调用 LLM。
- [ ] LLM 不可用时也能 fallback。
- [ ] 返回 canonical_table_count。
- [ ] 返回 next_action。

验证：

- [ ] HeroTable raw index 能生成 HeroTable canonical。
- [ ] 关闭模型仍然成功。
- [ ] canonical_table_count=1。
- [ ] canonical 文件路径正确。

---

# Phase 5：Build Readiness + Candidate Map

## 5.1 目标

系统能判断当前是否可以构建 Candidate Map，并能真正生成 Candidate Map。

---

## 5.2 后端任务

### Task 10：新增 Build Readiness 接口

接口：

```text
GET /game/knowledge/map/build-readiness
```

Checklist：

- [ ] 返回 project_root。
- [ ] 返回 project_bundle_root。
- [ ] 返回 source_config_exists。
- [ ] 返回 tables_config_exists。
- [ ] 返回 discovered_table_count。
- [ ] 返回 raw_table_index_count。
- [ ] 返回 canonical_table_count。
- [ ] 返回 has_formal_map。
- [ ] 返回 has_current_release。
- [ ] 返回 blocking_reason。
- [ ] 返回 next_action。
- [ ] 返回 raw_tables_dir。
- [ ] 返回 canonical_tables_dir。
- [ ] 返回 candidate_read_dir。
- [ ] 返回 same_project_bundle。

blocking_reason：

```text
project_root_missing
tables_source_missing
no_table_sources_found
no_raw_indexes
no_canonical_facts
candidate_ready
formal_map_missing
release_missing
ready
path_mismatch
```

验证：

- [ ] 无 project_root → project_root_missing。
- [ ] 有表但无 raw index → no_raw_indexes。
- [ ] 有 raw index 无 canonical → no_canonical_facts。
- [ ] 有 canonical → candidate_ready。
- [ ] 目录不一致 → path_mismatch。

---

### Task 11：增强 candidate/from-source 诊断

Checklist：

- [ ] no_canonical_facts 时返回 diagnostics。
- [ ] diagnostics 包含 raw_table_index_count。
- [ ] diagnostics 包含 canonical_table_count。
- [ ] diagnostics 包含 canonical_tables_dir。
- [ ] diagnostics 包含 blocking_reason。
- [ ] diagnostics 包含 next_action。
- [ ] candidate 成功时返回 candidate_table_count。
- [ ] candidate 成功时返回 candidate_refs。

验证：

- [ ] canonical 为空时，前端能显示“请先生成 Canonical Facts”。
- [ ] canonical 有 1 张表时，candidate map 有 1 个 table ref。
- [ ] Candidate Map 不自动保存 Formal Map。
- [ ] Candidate Map 不自动 Build Release。

---

# Phase 6：后台 Job + 进度条

## 6.1 目标

构建不能被切换界面打断。前端只订阅 Job 状态。

---

## 6.2 后端任务

### Task 12：新增 Cold-start Job 接口

接口：

```text
POST /game/knowledge/map/cold-start-jobs
GET  /game/knowledge/map/cold-start-jobs/{job_id}
POST /game/knowledge/map/cold-start-jobs/{job_id}/cancel
```

Job 字段：

```json
{
  "job_id": "map-cold-start-001",
  "status": "running",
  "stage": "building_canonical_facts",
  "progress": 60,
  "message": "正在生成 Canonical Facts：HeroTable.csv",
  "current_file": "Tables/HeroTable.csv",
  "counts": {
    "discovered_table_count": 1,
    "raw_table_index_count": 1,
    "canonical_table_count": 0,
    "candidate_table_count": 0
  },
  "warnings": [],
  "errors": [],
  "next_action": null
}
```

Checklist：

- [ ] POST 创建 job。
- [ ] GET 查询 job 状态。
- [ ] cancel 取消 job。
- [ ] job 状态写入 `runtime/build_jobs/<job_id>.json`。
- [ ] 保留最近 20 条 job。
- [ ] 同项目已有 running job 时，不重复创建。
- [ ] 切换页面不取消 job。
- [ ] 刷新浏览器可恢复 job。
- [ ] 支持 timeout。
- [ ] 支持 partial_outputs 标记。
- [ ] 成功后返回 candidate result。

stage：

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

验证：

- [ ] 点击构建后切换页面，job 继续。
- [ ] 回到页面能恢复进度。
- [ ] 刷新浏览器能恢复状态。
- [ ] 重复点击不会启动两个 job。
- [ ] 取消后 status=cancelled。
- [ ] 失败时有 stage/error/next_action。

---

## 6.3 前端任务

### Task 13：构建进度条和说明信息

Checklist：

- [ ] 显示 progress。
- [ ] 显示 stage。
- [ ] 显示 message。
- [ ] 显示 current_file。
- [ ] 显示 counts。
- [ ] 显示 warnings。
- [ ] 显示 errors。
- [ ] 显示 next_action。
- [ ] 支持取消。
- [ ] 支持重试。
- [ ] 支持复制诊断信息。
- [ ] 页面切换后恢复 active_job_id。
- [ ] 浏览器刷新后恢复 active_job_id。

验证：

- [ ] 构建中切换页面再回来，进度仍在。
- [ ] 构建完成显示“查看 Candidate Map”。
- [ ] 构建失败显示失败阶段和下一步。
- [ ] 进度条不会一直卡 0%。

---

# Phase 7：前端一步跑通按钮

## 7.1 目标

提供一个最快测试按钮：

```text
[Rule-only 冷启动构建]
```

它内部执行：

```text
Source Discovery
→ Raw Index
→ Canonical Facts
→ Candidate Map
```

不自动：

```text
Save Formal Map
Build Release
Publish Current
```

Checklist：

- [ ] 按钮只在 Project Root 和 Tables Source 有效时可用。
- [ ] 默认 rule_only=true。
- [ ] 创建后台 job。
- [ ] 展示进度条。
- [ ] 成功后显示 candidate_table_count。
- [ ] 成功后显示 candidate_refs。
- [ ] 成功后提供“查看 Diff Review”。
- [ ] 成功后提供“保存 Formal Map”。

验证：

- [ ] minimal_project 一键成功。
- [ ] 成功后不自动保存 Formal Map。
- [ ] 成功后不自动 Build Release。
- [ ] 成功后不自动 Publish Current。

---

# Phase 8：Smoke Test

## 8.1 目标

仓库必须有一个命令验证核心链路。

---

## 8.2 后端任务

### Task 14：新增最小样例

目录：

```text
examples/minimal_project/Tables/HeroTable.csv
```

内容：

```csv
ID,Name,HP,Attack
1,HeroA,100,20
```

Checklist：

- [ ] 样例项目入库。
- [ ] HeroTable.csv 入库。
- [ ] 不依赖模型。
- [ ] 不依赖 SVN。
- [ ] 不依赖 KB。

---

### Task 15：新增 smoke 脚本

脚本：

```text
scripts/run_map_cold_start_smoke.py
```

命令：

```bash
python scripts/run_map_cold_start_smoke.py --project examples/minimal_project --rule-only
```

成功输出：

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

Checklist：

- [ ] 脚本配置 project_root。
- [ ] 脚本配置 tables root。
- [ ] 脚本执行 discovery。
- [ ] 脚本执行 raw index。
- [ ] 脚本执行 canonical rebuild。
- [ ] 脚本执行 candidate/from-source。
- [ ] 脚本断言结果。
- [ ] 失败时打印 diagnostics。

验证：

- [ ] 在干净环境运行一次成功。
- [ ] 关闭模型配置仍然成功。
- [ ] 删除 canonical 后重跑成功。
- [ ] 删除 raw index 后重跑成功。

---

# Phase 9：边界测试

## 9.1 Windows 路径测试

- [ ] `E:\\test_project`。
- [ ] 路径中包含空格。
- [ ] 路径中包含中文。
- [ ] 大小写扩展名 `.CSV`。
- [ ] 反斜杠路径保存后能正常解析。

## 9.2 CSV 编码测试

- [ ] UTF-8。
- [ ] UTF-8 BOM。
- [ ] 空文件。
- [ ] 空表头。
- [ ] header_row 错误。
- [ ] 缺主键时能 fallback 或明确 warning。

## 9.3 XLSX 测试

- [ ] 单 sheet。
- [ ] 多 sheet。
- [ ] 空 sheet 跳过。
- [ ] `~$Temp.xlsx` 排除。
- [ ] `.xls` 标记 unsupported。

---

# 最终交付验收

## 必须通过

- [ ] 用户能找到 Project Setup。
- [ ] 用户能设置 Local Project Root。
- [ ] 用户能设置 Tables Root。
- [ ] Source Discovery 能发现 HeroTable.csv。
- [ ] Raw Index 生成 1。
- [ ] Canonical Facts 生成 1。
- [ ] Candidate Map 生成 1。
- [ ] 构建有后台 job。
- [ ] 构建有进度条。
- [ ] 切换页面不打断。
- [ ] 刷新页面能恢复。
- [ ] 失败有 stage/error/next_action。
- [ ] Rule-only 不依赖 LLM。
- [ ] 不自动保存 Formal Map。
- [ ] 不自动 Build Release。
- [ ] 不自动 Publish Current。
- [ ] smoke 脚本一次通过。

## 可以宣布核心链路可用的条件

```text
examples/minimal_project 在 rule-only 模式下，
从 Project Setup UI 和 smoke 脚本两条路径都能一次跑通。
```

---

# Agent 执行顺序建议

最快看到效果的顺序：

```text
1. 后端 Source Discovery
2. 后端 Raw Index Rebuild
3. Canonical Facts Committer
4. Canonical Rebuild
5. Candidate from Source 诊断增强
6. Build Readiness
7. Smoke 脚本
8. Project Setup UI
9. 后台 Job
10. 前端进度条
11. Windows/CSV/XLSX 边界测试
```

如果人手有限，先做 1-7，可以先在命令行看到核心链路跑通。  
然后做 8-10，让 UI 可用。
