# R-6 写回闭环任务清单（P0）

> 目标：让用户在控制台/Agent 里把"读"配置升级为"读+改+审+提交"。  
> 项目：`e:\LTClaw2.0\LTclaw2.0`，包名 `ltclaw_gy_x`，venv `e:\LTClaw2.0\.venv`  
> 基线：单元测试 1852 passed / 0 failed，服务可启动，6 条 game 路由可达。

---

## 0. 全局约束（每个 agent 必读）

### 0.1 DLP 写入协议（强制）
- 本机有 TSD 风格 DLP，**禁止用 VS Code `replace_string_in_file` 工具直接编辑 `.py`**（会触发文件加密为 `%TSD-Header-###%` 格式）。
- 所有 `.py` 创建/修改必须用 PowerShell 脚本：
  ```powershell
  $enc = [Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($path, $content, $enc)
  ```
- 完成写入后立即验证文件未被加密：
  ```powershell
  $b = [IO.File]::ReadAllBytes($path)
  [Text.Encoding]::ASCII.GetString($b[0..15])  # 不应等于 "%TSD-Header-###%"
  ```

### 0.2 编码与运行时约束
- Python 3.12.7（64-bit），venv: `e:\LTClaw2.0\.venv`
- Pydantic v2 → 序列化用 `model_dump(mode="json")`
- 同步阻塞 IO 必须包 `asyncio.to_thread`
- 文件 IO 走 utf-8 BOM-less

### 0.3 不动核心装配链
- `app/_app.py` lifespan 主链
- `app/multi_agent_manager.py`
- `app/workspace/*` 主流程
- `auth.py` `_PUBLIC_PATHS`（不要把新 API 加进公开列表）
- `agents/react_agent.py` 主类（仅在工具映射 dict 加条目）

### 0.4 测试与运行命令
```powershell
# 单元测试
cd e:\LTClaw2.0\LTclaw2.0
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest <path> --no-cov -q

# 服务冒烟
$env:QWENPAW_WORKING_DIR = "$env:TEMP\ltclaw_smoke_$(Get-Random)"
& e:\LTClaw2.0\.venv\Scripts\python.exe -m ltclaw_gy_x app --port 18080 --log-level error
```

### 0.5 现有 game 包接口快照
- `game.service.GameService`（property: `project_config / user_config / svn / table_indexer / dependency_resolver / index_committer / svn_watcher / query_router`）
- `game.svn_client.SvnClient` 现有：`info / status / update / log / diff_paths / add / commit / check_installed`（**Task 3 需要补 `revert`**）
- `game.paths` 现有：`get_workspace_game_dir / get_index_dir / get_tables_dir / get_chroma_dir / get_llm_cache_dir / get_svn_cache_dir / get_user_config_path / get_project_config_path`（**Task 1 需要补 `get_proposals_dir`**）
- `game.models.ChangeSet/FieldInfo/TableIndex/DependencyEdge` 等已存在
- `game.table_indexer.TableIndexer` 内有 `_read_excel_file / _read_csv_file`，可参考其编码探测逻辑

### 0.6 错误类约定
- 所有自定义异常继承 `Exception`，定义在所属模块顶部
- 命名 `<Domain>Error`（参考 `SvnError`）
- Router 层把领域异常转为 `HTTPException(status_code=...)`

---

## Task 1 — `change_proposal.py` 数据模型 + Store

**新增文件**：`src/ltclaw_gy_x/game/change_proposal.py`  
**改动文件**：`src/ltclaw_gy_x/game/paths.py`（加 `get_proposals_dir`）

### 1.1 数据模型
```python
class ChangeOp(BaseModel):
    op: Literal["update_cell", "insert_row", "delete_row"]
    table: str
    row_id: str | int
    field: str | None = None       # update_cell 必填
    old_value: Any | None = None   # 可选，仅作记录
    new_value: Any | None = None   # update_cell / insert_row 必填

class ChangeProposal(BaseModel):
    schema_version: Literal["change-proposal.v1"] = "change-proposal.v1"
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    description: str = ""
    ops: list[ChangeOp]
    status: Literal[
        "draft", "approved", "applied",
        "committed", "rejected", "reverted"
    ] = "draft"
    author: str = "agent"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    applied_revision: int | None = None   # apply 后保留 svn_revision，便于追溯
    commit_revision: int | None = None
    error: str | None = None
```

### 1.2 ProposalStore
- 落盘路径：`{workspace_dir}/game_index/proposals/<id>.json`
- 必须方法（async，对内部同步 IO 用 `asyncio.to_thread`）：
  - `create(proposal: ChangeProposal) -> ChangeProposal`
  - `get(id: str) -> ChangeProposal | None`
  - `list(status: str | None = None, limit: int = 50) -> list[ChangeProposal]`（按 created_at desc）
  - `update(proposal: ChangeProposal) -> ChangeProposal`（自动刷新 updated_at）
  - `delete(id: str) -> bool`
- **状态机**（在 `update` 中校验 `old.status -> new.status`）：
  - `draft → approved | rejected`
  - `approved → applied | rejected`
  - `applied → committed | reverted`
  - 其它任何转移 → raise `InvalidProposalState(f"{old}->{new}")`
- 原子写：写到 `<id>.json.tmp` → `os.replace(...)` 覆盖
- 自定义异常：`ProposalStoreError` / `InvalidProposalState`

### 1.3 单测 `tests/unit/game/test_change_proposal.py`
覆盖：
- 创建/读取/列表/删除往返
- 序列化反序列化（含 datetime / Literal）
- 非法状态转移 raise InvalidProposalState
- list 按 status 过滤、按 created_at desc 排序
- 并发占位：concurrent create 不会丢条目（用 `asyncio.gather`）

### 1.4 验收
```powershell
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit/game/test_change_proposal.py --no-cov -v
```
预期：≥ 8 个测试全部通过。

---

## Task 2 — `change_applier.py` 写回 csv/xlsx

**新增文件**：`src/ltclaw_gy_x/game/change_applier.py`  
**依赖**：Task 1 完成（导入 `ChangeProposal / ChangeOp`）

### 2.1 类签名
```python
class ApplyError(Exception):
    def __init__(self, op: ChangeOp, reason: str):
        self.op = op
        self.reason = reason
        super().__init__(f"{op.op} on {op.table}#{op.row_id}: {reason}")

class ChangeApplier:
    def __init__(self, project: ProjectConfig, svn_root: Path,
                 table_indexer: TableIndexer | None = None): ...

    async def dry_run(self, proposal: ChangeProposal) -> list[dict]: ...
    async def apply(self, proposal: ChangeProposal) -> dict: ...
```

### 2.2 主流程
1. 通过 `table_indexer` 或 project 配置定位每个 op 的源文件（绝对路径）。
2. 按文件分组 ops（同一文件多 op 合并）。
3. 对每个文件：
   - 读全量到二维 list（参考 `table_indexer._read_excel_file/_read_csv_file`）
   - 取 `header_row` 与 primary_key 列索引
   - 对每个 op 应用变更（update_cell / insert_row / delete_row）
   - 写到 `<source>.ltclaw_pending`：xlsx 用 `openpyxl`（`load_workbook` 后写值再保存）；csv 用原 delimiter+encoding
   - 校验：能重新打开读取头行 → `os.replace(<pending>, <source>)`
4. 任一文件失败：删除该文件的 `.ltclaw_pending`，已成功的文件**不回滚**（保留），但聚合 raise `ApplyError`
5. 返回 `{"changed_files": [rel_paths], "summary": "N updates / M inserts / K deletes"}`

### 2.3 dry_run
- 不写盘，对每个 op 返回：`{"op": <op_dict>, "before": <row_or_cell>, "after": <preview>, "ok": bool, "reason": str|None}`

### 2.4 边界
- `update_cell`：`row_id` 找不到 / `field` 不存在 → ApplyError
- `insert_row`：`new_value` 必须是 dict（field→value），且不允许 row_id 冲突
- `delete_row`：`row_id` 找不到 → ApplyError
- 类型推断：保留原 cell 类型（int 列写 int，字符串列写 str），转换失败 → ApplyError

### 2.5 单测 `tests/unit/game/test_change_applier.py`
fixture：`tmp_path` + 内置 `ProjectConfig` + 准备 1 个 csv + 1 个 xlsx 测试表。
覆盖：
- update_cell 成功（csv + xlsx 各一）
- insert_row + delete_row 各一
- dry_run 返回正确 before/after
- row_id 找不到 → ApplyError
- field 不存在 → ApplyError
- 部分失败时已写入文件保留、未写入临时文件被清理

### 2.6 验收
```powershell
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit/game/test_change_applier.py --no-cov -v
```
预期：≥ 8 个测试全部通过。

---

## Task 3 — `svn_committer.py` 提交封装

**新增文件**：`src/ltclaw_gy_x/game/svn_committer.py`  
**改动文件**：`src/ltclaw_gy_x/game/svn_client.py`（加 `revert` 方法）

### 3.1 SvnClient.revert（新增）
```python
async def revert(self, paths: list[Path]) -> None:
    if not paths:
        return
    cmd = self._build_cmd(["revert"] + [str(p) for p in paths])
    await self._run_cmd(cmd)
```

### 3.2 SvnCommitter
```python
class CommitError(Exception): ...

class SvnCommitter:
    def __init__(self, svn_client: SvnClient, svn_root: Path): ...

    async def commit_proposal(
        self,
        proposal: ChangeProposal,
        changed_files: list[str],          # 相对 svn_root 的路径
        message_template: str | None = None,
    ) -> int: ...

    async def revert_local_changes(self, paths: list[Path]) -> None: ...
```

主流程：
1. `changed_files` 转绝对路径
2. `svn add`（对 unversioned）
3. message：默认 `[ltclaw][proposal:{id[:8]}] {title}\n\n{description}`
4. `svn_client.commit(paths, message)` → 返回 revision
5. 任一步异常 → raise `CommitError(原因)`

`revert_local_changes`：直接转发到 `svn_client.revert(paths)`。

### 3.3 单测 `tests/unit/game/test_svn_committer.py`
mock `SvnClient`：
- 验证 commit_proposal 调用顺序：先 `add` 再 `commit`
- message 格式正确（含 proposal id 前 8 位）
- 路径相对→绝对转换正确
- commit 失败时抛 CommitError 并保留原异常 chain
- revert 直接转发

### 3.4 验收
```powershell
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit/game/test_svn_committer.py --no-cov -v
```
预期：≥ 5 个测试全部通过。

---

## Task 4 — `GameService` 集成 ProposalStore / ChangeApplier / SvnCommitter

**改动文件**：`src/ltclaw_gy_x/game/service.py`  
**依赖**：Task 1/2/3 完成

### 4.1 改动点
1. `__init__` 增字段：
   ```python
   self._proposal_store: ProposalStore | None = None
   self._change_applier: ChangeApplier | None = None
   self._svn_committer: SvnCommitter | None = None
   ```
2. `start()` 内：
   - 无条件创建 `self._proposal_store = ProposalStore(self.workspace_dir)`
   - 当 `self._project_config` 存在：`self._change_applier = ChangeApplier(self._project_config, svn_root, self._table_indexer)`
   - 当 `self._project_config + self._svn_client + role==maintainer`：`self._svn_committer = SvnCommitter(self._svn_client, svn_root)`
3. `reload_config()` 同步重建（参考现有 `_table_indexer` 重建分支）
4. 加 3 个 property：`proposal_store / change_applier / svn_committer`

### 4.2 回归
```powershell
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit/game/test_service.py --no-cov -q
```
预期：现有测试全部仍然通过；如需，可补 1-2 个 service 集成测试验证 3 个 property 在不同 role 下的可用性。

---

## Task 5 — Router `/game/change/*`

**新增文件**：`src/ltclaw_gy_x/app/routers/game_change.py`  
**改动文件**：`src/ltclaw_gy_x/app/routers/agent_scoped.py`（注册）

### 5.1 端点（前缀 `/game/change`，tags=["game-change"]）

| Method | Path | 说明 | 权限 |
|---|---|---|---|
| POST | `/proposals` | 创建草稿（body: `{title, description, ops}`） | 任何用户 |
| GET | `/proposals` | 列表，query `status?`、`limit=50` | 任何用户 |
| GET | `/proposals/{id}` | 详情 | 任何用户 |
| POST | `/proposals/{id}/dry_run` | 预览 | 任何用户 |
| POST | `/proposals/{id}/approve` | draft→approved | maintainer |
| POST | `/proposals/{id}/apply` | approved→applied，写盘 | maintainer |
| POST | `/proposals/{id}/commit` | applied→committed，提交 SVN | maintainer |
| POST | `/proposals/{id}/reject` | draft/approved → rejected | maintainer |
| POST | `/proposals/{id}/revert` | applied → reverted（仅本地 `svn revert`） | maintainer |

### 5.2 实现要点
- 仿照 `app/routers/game_index.py` 的 `_get(workspace)` 模式取 service
- 错误处理：
  - service 不可用 → 404
  - proposal 不存在 → 404
  - 状态机非法 → 409 Conflict
  - role≠maintainer → 403
  - applier/committer 不可用（未配置 SVN 等）→ 412 Precondition Failed
- approve/apply/commit/reject/revert 后立刻 `proposal_store.update(updated)` 把状态写回

### 5.3 注册
在 `agent_scoped.py` 中：
```python
from .game_change import router as game_change_router
...
router.include_router(game_change_router)
```

### 5.4 单测 `tests/unit/routers/test_game_change_router.py`
用 FastAPI `TestClient` + monkeypatched `Workspace`：
- 列表/详情/创建 happy path
- 状态机非法转移 → 409
- 非 maintainer 调 approve → 403
- service 缺失 → 404

### 5.5 验收
```powershell
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit/routers/test_game_change_router.py --no-cov -v
```

---

## Task 6 — 3 个 Agent 工具

**改动文件**：
- `src/ltclaw_gy_x/agents/tools/gamedev_tools.py`
- `src/ltclaw_gy_x/agents/react_agent.py`（仅在 import 区 + tool_functions dict 加条目）

### 6.1 新增工具
```python
async def game_propose_change(
    title: str,
    description: str,
    ops: list[dict],
) -> Dict[str, Any]: ...

async def game_apply_proposal(
    proposal_id: str,
    dry_run: bool = True,
) -> Dict[str, Any]: ...

async def game_commit_proposal(
    proposal_id: str,
) -> Dict[str, Any]: ...
```

### 6.2 实现要点
- 都通过 `_get_game_service()` 拿 service（仿现有 `game_query_tables`）
- `game_propose_change`：构造 `ChangeProposal(status="draft")` → `store.create()` → 返回 `{id, status, ops_count}`
- `game_apply_proposal`：
  - dry_run=True → applier.dry_run()
  - dry_run=False → 检查 status=approved → applier.apply() → store.update(status=applied)
- `game_commit_proposal`：检查 status=applied + role=maintainer → committer.commit_proposal() → store.update(status=committed, commit_revision=N)
- 返回值都是 dict（不直接返 Pydantic 对象）

### 6.3 react_agent 注册
- import 区（参考第 61-63 行）加 3 个名字
- `tool_functions` dict（参考第 286-287 行）加 3 个键值
- 不需要改 `agent_config.tools.builtin_tools` 默认值（继承现有 game 工具的 enabled 策略）

### 6.4 验收
- 跑 `tests/unit/agents/` 全部通过
- 在服务冒烟时通过 react agent 可调用（手动验证）

---

## Task 7 — 前端：SvnSync 加 changelog tab

**改动文件**：
- `console/src/api/modules/`（新增 `gameChange.ts` 或扩展现有 game 相关模块）
- `console/src/pages/Game/SvnSync.tsx` + `.module.less`
- `console/src/locales/{zh,en,ja,ru}.json`

### 7.1 API 模块
```ts
export const gameChangeApi = {
  list: (agentId: string, status?: string) => http.get(...),
  get: (agentId: string, id: string) => http.get(...),
  create: (agentId: string, body: ChangeProposalCreate) => http.post(...),
  dryRun: (agentId: string, id: string) => http.post(...),
  approve / apply / commit / reject / revert
};
```

### 7.2 UI 改造
- 在 `SvnSync.tsx` 顶部用 antd `Tabs`：
  - Tab 1 "同步状态"：保留现有 SVN 状态/日志
  - Tab 2 "变更草稿"：新增 changelog 列表
- 草稿列表用 antd `Table`：columns = title / status (badge) / author / created_at / actions
- actions 用 `Dropdown.Button`：dry_run / approve / apply / commit / reject / revert（按 status 灰化）
- 详情用 `Drawer`：展示 ops 表格（op type / table / row_id / field / old → new）
- dry_run 结果用简易 before/after 双列展示（不强求 diff 库）

### 7.3 i18n
- 加 `game.proposal.*` 命名空间，含状态名/操作按钮文案/错误提示
- 4 个语言全部补齐（保持与现有键风格一致）

### 7.4 验收
- `npm run build` / `pnpm build` 通过（看 console/package.json 实际包管理器）
- 手动操作流：创建 → dry_run → approve → apply → commit 链路在 UI 跑通

---

## Task 8 — 全量回归 + 服务冒烟（收尾）

### 8.1 单元回归
```powershell
cd e:\LTClaw2.0\LTclaw2.0
& e:\LTClaw2.0\.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q
```
- 基线：1852 passed, 3 skipped
- 完工目标：≥ 1880 passed（新增 ~30 个测试）、0 failed

### 8.2 服务冒烟脚本
```powershell
$env:QWENPAW_WORKING_DIR = "$env:TEMP\ltclaw_smoke_p0_$(Get-Random)"
& e:\LTClaw2.0\.venv\Scripts\python.exe -m ltclaw_gy_x app --port 18080 --log-level error
```
另一终端验证：
```powershell
# 1. version
Invoke-WebRequest 'http://127.0.0.1:18080/api/version'

# 2. 创建 proposal
$body = @{
  title = "smoke test"
  description = "P0 smoke"
  ops = @(@{ op="update_cell"; table="X"; row_id=1; field="hp"; new_value=100 })
} | ConvertTo-Json -Depth 5

$r = Invoke-WebRequest -Uri 'http://127.0.0.1:18080/api/agents/default/game/change/proposals' `
     -Method POST -Body $body -ContentType 'application/json'
$id = ($r.Content | ConvertFrom-Json).id
"id=$id"

# 3. 列表
(Invoke-WebRequest 'http://127.0.0.1:18080/api/agents/default/game/change/proposals').Content

# 4. dry_run
(Invoke-WebRequest "http://127.0.0.1:18080/api/agents/default/game/change/proposals/$id/dry_run" -Method POST).Content
```
- 全部 200 通过即为冒烟成功
- approve/apply/commit 在没有真实 SVN repo 时预期 412/403，不强求

### 8.3 完工标准
- [ ] 1852 → ≥ 1880 单测全部绿
- [ ] `/api/agents/default/game/change/proposals` GET/POST 200
- [ ] `/api/agents/default/game/change/proposals/{id}` GET 200
- [ ] dry_run 200 + 返回结构合理
- [ ] 前端 SvnSync changelog tab 渲染无错
- [ ] 用户级 memory `/memories/ltclaw-mvp-plan.md` 更新一段"R-6 完工"记录

---

## 推荐分发模式

| Agent 编号 | 任务 | 起步条件 |
|---|---|---|
| A | Task 1（含 paths 改动）+ Task 4 中 ProposalStore 部分 | 立即开工 |
| B | Task 2 | 等 Task 1 类型定义就绪（可先用桩签名） |
| C | Task 3（含 svn_client.revert） | 立即开工（mock SvnClient） |
| D | Task 4 收尾 + Task 5 + Task 6 | 等 1/2/3 完成 |
| E | Task 7 前端 | 等 Task 5 路由稳定（可先用 mock 数据） |
| F | Task 8 验证收尾 | 全部完成后 |

---

## 验证人 checklist（我负责）

- [ ] Task 1 文件未被 DLP 加密 + 单测通过
- [ ] Task 2 文件未被 DLP 加密 + 单测通过
- [ ] Task 3 文件未被 DLP 加密 + 单测通过
- [ ] Task 4 service 集成不破现有测试
- [ ] Task 5 router 单测通过 + agent_scoped 正确注册
- [ ] Task 6 工具在 react_agent 工具映射中正确出现
- [ ] Task 7 前端 build 通过 + tab 渲染
- [ ] Task 8 全量回归 + 冒烟全过 + memory 更新
