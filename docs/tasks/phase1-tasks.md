# LTCLAW-GY.X · 游戏策划工作台 · 阶段一任务清单

本文是阶段一的可分发任务卡集合。每张卡片可独立交给一个新会话执行，完成后回到主会话由复查清单核验。

---

## 公共上下文（每个任务的会话开头都贴这段）

```
项目：LTCLAW-GY.X v2.0（包名 ltclaw_gy_x）
仓库根：e:\LTClaw2.0\LTclaw2.0
环境前缀：QWENPAW_*（兼容 COPAW_*）
WORKING_DIR：~/.ltclaw_gy_x
工作区路径：~/.ltclaw_gy_x/workspaces/<agent_id>/

【强约束】
1. 不修改以下文件主体（只能在扩展点新增）：
   - src/ltclaw_gy_x/app/_app.py
   - src/ltclaw_gy_x/app/multi_agent_manager.py
   - src/ltclaw_gy_x/app/workspace/workspace.py（仅在 register 处加 1 个 ServiceDescriptor）
   - src/ltclaw_gy_x/providers/provider_manager.py
   - src/ltclaw_gy_x/agents/react_agent.py（仅在 tool_functions dict 追加项）
   - src/ltclaw_gy_x/security/secret_store.py
   - src/ltclaw_gy_x/app/auth.py（_PUBLIC_PATHS 不能动）

2. 全部新增包：src/ltclaw_gy_x/game/
   全部新增 router：src/ltclaw_gy_x/app/routers/game_*.py（在 routers/__init__.py 的两处 include 都要加）
   前端全部新增：console/src/pages/{SvnSync,IndexMap,Settings/GameProject}/, console/src/api/modules/game.ts, console/src/stores/game.ts

3. 同步阻塞 IO 走 asyncio.to_thread（参考 service_manager._get_or_create_service）

4. 新增依赖必须写进 pyproject.toml（openpyxl / chromadb / python-frontmatter 已存在则复用）

5. 测试放 tests/unit/game/ 或 tests/integration/

【架构关键】
- ServiceManager 优先级：10 runner / 20 memory|context|mcp|chat / 25 runner_start / 30 channel / 40 cron / 50 watcher
  → GameService 用 priority=60（最后启动，依赖前面都就绪）
- agent_scoped router 在 /api/agents/{aid}/ 下
- 所有 agent 数据隔离在各自 workspace_dir

【数据契约（已定）】
- SVN 工作副本根: 用户在 project_config 里填，不预设
- 索引输出根:    <svn-root>/.ltclaw_index/
- 本地缓存根:    <workspace_dir>/game_index/
- 配置文件:      <svn-root>/.ltclaw_index/project_config.yaml
- 表索引:        <svn-root>/.ltclaw_index/tables/<TableName>.json
- 用户级配置:    ~/.ltclaw_gy_x/game_user.yaml（不进 SVN）
```

---

## 任务 1.1 · ProjectConfig pydantic 模型与 IO

**目标**：建立 `game/paths.py` 与 `game/config.py`，实现 ProjectConfig pydantic 类、加载/保存/校验。

**新建文件**：
- `src/ltclaw_gy_x/game/__init__.py`
- `src/ltclaw_gy_x/game/paths.py`
- `src/ltclaw_gy_x/game/config.py`

**接口签名（必须严格遵守）**：
```python
# game/paths.py
def get_index_dir(svn_root: Path) -> Path           # <svn>/.ltclaw_index
def get_tables_dir(svn_root: Path) -> Path
def get_docs_dir(svn_root: Path) -> Path
def get_project_config_path(svn_root: Path) -> Path
def get_user_config_path() -> Path                   # ~/.ltclaw_gy_x/game_user.yaml
def get_workspace_game_dir(workspace_dir: Path) -> Path  # <ws>/game_index
def get_chroma_dir(workspace_dir: Path) -> Path
def get_llm_cache_dir(workspace_dir: Path) -> Path
def get_svn_cache_dir(workspace_dir: Path) -> Path

# game/config.py
class ProjectMeta(BaseModel): name, engine, language
class SvnConfig(BaseModel): root: str, poll_interval_seconds: int=300, jitter_seconds: int=30
class PathRule(BaseModel): path: str, semantic: Literal["table","doc","template"], system: str|None=None
class FilterConfig(BaseModel): include_ext: list[str], exclude_glob: list[str]
class IDRange(BaseModel): type: str, start: int, end: int
class TableConvention(BaseModel): header_row: int=1, comment_row: int|None=None, primary_key_field: str="ID", id_ranges: list[IDRange]=[]
class ModelSlotRef(BaseModel): provider_id: str, model_id: str
class ProjectConfig(BaseModel):
    schema_version: Literal["project-config.v1"]="project-config.v1"
    project: ProjectMeta
    svn: SvnConfig
    paths: list[PathRule]
    filters: FilterConfig
    table_convention: TableConvention
    doc_templates: dict[str, str]
    models: dict[str, ModelSlotRef]

class UserGameConfig(BaseModel):
    my_role: Literal["maintainer","consumer"]="consumer"
    svn_local_root: str|None=None
    svn_username: str|None=None

class ValidationIssue(BaseModel): severity: Literal["error","warning"], path: str, message: str

def load_project_config(svn_root: Path) -> ProjectConfig | None  # 不存在返 None
def save_project_config(svn_root: Path, cfg: ProjectConfig) -> None  # 原子写 yaml
def validate_project_config(cfg: ProjectConfig) -> list[ValidationIssue]
def load_user_config() -> UserGameConfig
def save_user_config(cfg: UserGameConfig) -> None
```

**依赖**：`pyyaml`（已在 pyproject）、`pydantic` v2（已用）

**测试**：`tests/unit/game/test_config.py` —— round-trip yaml、缺字段校验、id_range 重叠 warning。

**验收**：
- `pytest tests/unit/game/test_config.py` 全绿
- 手动建一个最小 yaml，能 load 出 ProjectConfig

---

## 任务 1.2 · 业务模型 dataclass

**目标**：建立 `game/models.py`，定义所有跨模块流转的数据结构。

**新建文件**：`src/ltclaw_gy_x/game/models.py`

**必须定义**：
```python
class FieldConfidence(str, Enum):
    CONFIRMED = "confirmed"
    HIGH_AI = "high_ai"
    LOW_AI = "low_ai"

class FieldInfo(BaseModel):
    name: str
    type: str
    description: str
    confidence: FieldConfidence
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    ai_raw_description: str | None = None
    references: list[str] = []
    tags: list[str] = []

class TableIndex(BaseModel):
    schema_version: Literal["table-index.v1"] = "table-index.v1"
    table_name: str
    source_path: str           # 相对 svn_root
    source_hash: str           # sha256:xxx
    svn_revision: int
    system: str | None = None
    row_count: int
    header_row: int = 1
    primary_key: str = "ID"
    ai_summary: str
    ai_summary_confidence: float
    fields: list[FieldInfo]
    id_ranges: list[dict]
    last_indexed_at: datetime
    indexer_model: str

class DocIndex(BaseModel):
    schema_version: Literal["doc-index.v1"] = "doc-index.v1"
    source_path: str
    source_hash: str
    svn_revision: int
    doc_type: str              # gdd / requirement / design_change / changelog / small_change / unknown
    title: str
    summary: str
    related_tables: list[str]
    last_indexed_at: datetime

class DependencyEdge(BaseModel):
    from_table: str
    from_field: str
    to_table: str
    to_field: str
    confidence: FieldConfidence
    inferred_by: Literal["rule","llm","manual"]

class DependencyGraph(BaseModel):
    schema_version: Literal["dep-graph.v1"] = "dep-graph.v1"
    edges: list[DependencyEdge]
    last_updated: datetime

class SystemGroup(BaseModel):
    name: str
    tables: list[str]
    description: str | None = None
    source: Literal["config","ai","manual"]

class ChangeSet(BaseModel):
    from_rev: int
    to_rev: int
    added: list[str]            # 相对 svn_root
    modified: list[str]
    deleted: list[str]

class CommitResult(BaseModel):
    revision: int | None
    files_committed: int
    skipped_reason: str | None  # 例如 "not maintainer"

class FieldPatch(BaseModel):
    description: str | None = None
    confidence: FieldConfidence | None = None
    confirmed_by: str | None = None
```

**测试**：`tests/unit/game/test_models.py` —— 序列化/反序列化往返。

**验收**：所有 model `.model_dump_json()` 可逆、字段类型严格。

---

## 任务 1.3 · SVN CLI 薄封装

**目标**：`game/svn_client.py`，封装本机 `svn` 命令，处理中文路径。

**新建文件**：`src/ltclaw_gy_x/game/svn_client.py`

**接口**：
```python
class SvnError(Exception): pass
class SvnNotInstalledError(SvnError): pass

class SvnClient:
    def __init__(self, working_copy: Path, username: str|None=None, password: str|None=None): ...

    async def info(self) -> dict   # {"revision": int, "url": str, "root": str}
    async def status(self, paths: list[Path]|None=None) -> list[dict]  # [{"path","status"}]
    async def update(self) -> int  # 返回更新后 revision
    async def log(self, from_rev: int, to_rev: int|str="HEAD", paths: list[Path]|None=None) -> list[dict]
    async def diff_paths(self, from_rev: int, to_rev: int) -> ChangeSet  # 用 svn diff --summarize -r
    async def add(self, paths: list[Path]) -> None  # 自动跳过已 versioned
    async def commit(self, paths: list[Path], message: str) -> int  # 返回新 revision
    @classmethod
    async def check_installed(cls) -> str | None  # 返回版本号字符串或 None
```

**实现要点**：
- 用 `asyncio.create_subprocess_exec("svn", ..., stdout=PIPE, stderr=PIPE)`
- Windows 下 `subprocess` 用 `cwd=working_copy`，编码用 `locale.getpreferredencoding(False)` 兜底 `utf-8 errors=replace`
- XML 输出用 `--xml`，stdlib `xml.etree.ElementTree` 解析
- 所有方法 async，但内部是 subprocess（已经是异步 IO）

**测试**：`tests/unit/game/test_svn_client.py` —— mock subprocess，覆盖 info/status/diff_paths/commit；至少一个集成测试（标 `@pytest.mark.skipif(not have_svn)`）。

**验收**：在装了 svn CLI 的机器上，`SvnClient(<workspace>).info()` 能返回真实 revision。

---

## 任务 1.4 · GameService 生命周期骨架

**目标**：`game/service.py`，提供启停入口；此时只是空壳，挂上 logger，方便 1.5 注入验证。

**新建文件**：`src/ltclaw_gy_x/game/service.py`

**接口**：
```python
class GameService:
    def __init__(self, workspace_dir: Path, runner, channel_manager): ...
    async def start(self) -> None:
        # 1. 加载 user_config 和 project_config（项目配未配都要能启动）
        # 2. 若已配置且 my_role==maintainer，准备 SvnClient（先不启 watcher）
        # 3. 准备 chroma 目录（lazy）
        # 4. logger.info("GameService started: project=%s role=%s", ...)
    async def stop(self) -> None: ...

    @property
    def configured(self) -> bool: ...   # project_config 是否存在且合法
    @property
    def project_config(self) -> ProjectConfig | None: ...
    @property
    def user_config(self) -> UserGameConfig: ...
    @property
    def svn(self) -> SvnClient | None: ...   # 未配置返 None

    # 给 router 用的方法（先抛 NotImplementedError）
    async def reload_config(self) -> None: ...
```

**测试**：`tests/unit/game/test_service.py` —— start/stop 不抛异常；configured 状态正确。

**验收**：单测全绿；后续任务只在此类内继续填肉。

---

## 任务 1.5 · Workspace ServiceDescriptor 注入

**目标**：让每个 Workspace 启动时附带一个 GameService（按 priority=60，conditional 启动）。

**修改文件**（仅扩展点）：
- `src/ltclaw_gy_x/app/workspace/service_factories.py`：新增 `create_game_service(ws)` 工厂
- `src/ltclaw_gy_x/app/workspace/workspace.py`：在 register 处追加 1 个 ServiceDescriptor

**关键代码**：
```python
# service_factories.py
def create_game_service(ws):
    from ltclaw_gy_x.game.service import GameService
    return GameService(
        workspace_dir=ws.workspace_dir,
        runner=ws.runner,
        channel_manager=ws.channel_manager,
    )

# workspace.py 在已有 register 末尾追加：
self.service_manager.register(ServiceDescriptor(
    name="game_service",
    service_class=create_game_service,
    init_args=lambda: {},
    start_method="start",
    stop_method="stop",
    reusable=False,
    priority=60,
    concurrent_init=False,
))
```

**注意**：
- GameService 对没配置项目的 agent 也要能正常 start（内部判断），不能阻塞 workspace 启动
- 暴露方式：`ws.game_service` 或 `ws.service_manager.get("game_service")`

**验收**：
- `python -m ltclaw_gy_x app --port=free` 能正常启动，logs 里看到 `GameService started`
- 即使 project_config 不存在，启动也不报错

---

## 任务 1.6 · ProjectConfig HTTP API

**目标**：暴露 GET / PUT / COMMIT 三个接口给前端。

**新建文件**：`src/ltclaw_gy_x/app/routers/game_project.py`

**接口**：
```
GET  /api/agents/{aid}/game/project/config        → ProjectConfig | null
PUT  /api/agents/{aid}/game/project/config        body: ProjectConfig
POST /api/agents/{aid}/game/project/config/commit body: {message?: str} → CommitResult
GET  /api/agents/{aid}/game/project/user_config   → UserGameConfig
PUT  /api/agents/{aid}/game/project/user_config   body: UserGameConfig
GET  /api/agents/{aid}/game/project/validate      → list[ValidationIssue]
```

**修改文件**：`src/ltclaw_gy_x/app/routers/__init__.py`（在 agent_scoped 函数中 include 这个 router）。

**实现要点**：
- 通过 `Depends(get_agent_for_request)` 拿 Workspace
- 调 `ws.game_service` 操作
- PUT 后调用 `service.reload_config()`
- COMMIT 仅 maintainer 可用，否则 403
- 不加进 `_PUBLIC_PATHS`（必须登录）

**测试**：`tests/integration/test_game_project_api.py`（用 TestClient，覆盖 GET/PUT/COMMIT 链路；commit 用 monkeypatch 跳过真实 svn 调用）。

**验收**：
- 通过 curl/前端 POST 一份 config，磁盘上能看到 `<svn-root>/.ltclaw_index/project_config.yaml`
- consumer 角色 POST commit → 403

---

## 任务 1.7 · 单元测试基础设施

**目标**：建立 `tests/unit/game/` 测试目录，提供共享 fixture。

**新建文件**：
- `tests/unit/game/__init__.py`
- `tests/unit/game/conftest.py`

**conftest 必须提供 fixture**：
```python
@pytest.fixture
def fake_svn_root(tmp_path) -> Path: ...   # 创建 .ltclaw_index/ 子目录

@pytest.fixture
def sample_project_config() -> ProjectConfig: ...

@pytest.fixture
def fake_workspace_dir(tmp_path) -> Path: ...

@pytest.fixture
def mock_svn_client(monkeypatch): ...      # SvnClient 全 mock，无需真实 svn
```

**验收**：1.1~1.6 的所有测试都用这些 fixture，能独立 `pytest tests/unit/game/` 全绿。

---

## 任务 2.1 · TableIndexer（xlsx/csv → TableIndex）

**目标**：`game/table_indexer.py`，从一张表生成 TableIndex，含 LLM 字段描述与 hash 缓存。

**新建文件**：`src/ltclaw_gy_x/game/table_indexer.py`

**依赖**：`openpyxl`（写进 pyproject.toml）

**接口**：
```python
class TableIndexer:
    def __init__(self, project: ProjectConfig, model_router, cache_dir: Path):
        # model_router: 调用 provider_manager 中 "field_describer" slot 的接口
        # cache_dir: <workspace>/game_index/llm_cache/

    async def index_one(self, source: Path, svn_root: Path, svn_revision: int,
                        prev: TableIndex | None) -> TableIndex:
        # 1. 计算 source 的 sha256
        # 2. 若 prev 存在且 source_hash 相同 → 直接返回 prev（仅更新 svn_revision）
        # 3. 用 openpyxl 读 header_row → 字段列表 + 类型推断（int/float/str/bool/list）
        # 4. 行数计数
        # 5. 字段描述：批量 prompt → LLM 一次返回所有字段
        #    缓存 key = sha256(table_name + field_name + field_type + sample_values_hash)
        # 6. id_ranges: 扫主键列，落到 project.table_convention.id_ranges 哪个段
        # 7. system: 通过 source path 匹配 project.paths 找出 system
        # 8. ai_summary: 单独一次 LLM 调用，输入 fields + 部分 sample
        # 9. 组装并返回 TableIndex

    async def index_batch(self, sources: list[Path], svn_root: Path, svn_revision: int) -> list[TableIndex]:
        # 并发 limit=3，调用 index_one
```

**LLM 调用约定**：
- 通过 `provider_manager.get_instance().get_provider_by_slot("field_describer")` 拿 provider
- prompt 模板：中文优先，要求结构化 JSON 输出
- 失败 → confidence=LOW_AI，description 写 fallback "<待补充>"

**测试**：
- 准备 fixture xlsx（用 openpyxl 程序生成）
- mock model_router 返回固定 JSON
- 验证 hash 缓存命中跳过 LLM
- 验证 id_range 落段正确

**验收**：单测全绿；用真实 xlsx + ollama qwen2.5:7b 跑一遍能产出合理描述。

---

## 任务 2.2 · DependencyResolver

**目标**：`game/dependency_resolver.py`，从所有 TableIndex 推断跨表外键。

**新建文件**：`src/ltclaw_gy_x/game/dependency_resolver.py`

**接口**：
```python
class DependencyResolver:
    def __init__(self, project: ProjectConfig, model_router): ...

    async def resolve(self, tables: list[TableIndex],
                      prev_graph: DependencyGraph | None) -> DependencyGraph:
        # 1. 规则层：
        #    - 字段名匹配：FooID 字段 → 找 FooTable 表（不分大小写）
        #    - 已 confirmed 的边直接保留
        # 2. LLM 兜底：对规则没匹配上的、形似外键的字段，
        #    一次调用问 LLM 给候选目标表（only when ambiguous）
        # 3. 合并 prev_graph 中 inferred_by="manual" 的边（人工修正不能丢）
```

**测试**：构造 3 张 fake TableIndex，验证规则层匹配；mock LLM 验证兜底。

**验收**：单测全绿。

---

## 任务 2.3 · IndexCommitter

**目标**：`game/index_committer.py`，把 TableIndex/DocIndex/Graph 写到磁盘并 commit。

**新建文件**：`src/ltclaw_gy_x/game/index_committer.py`

**接口**：
```python
class IndexCommitter:
    def __init__(self, svn_root: Path, svn: SvnClient, is_maintainer: bool): ...

    def write_table(self, idx: TableIndex) -> Path:
        # 写 <svn_root>/.ltclaw_index/tables/<TableName>.json
        # JSON 格式: indent=2, sort_keys=True, ensure_ascii=False
        # 原子写：先写 .tmp 再 rename

    def write_doc(self, idx: DocIndex) -> Path: ...
    def write_dependencies(self, graph: DependencyGraph) -> Path: ...
    def write_systems(self, groups: list[SystemGroup]) -> Path: ...
    def write_manifest(self, manifest: dict) -> Path: ...

    async def commit_round(self, message: str, written_files: list[Path]) -> CommitResult:
        # 非 maintainer → 返回 CommitResult(revision=None, skipped_reason="not maintainer")
        # 是 maintainer →
        #   1. svn add（已 versioned 自动跳过）
        #   2. svn commit
        #   3. 返回 CommitResult
```

**测试**：mock SvnClient，验证 write_* 落盘正确；commit_round 行为按角色分支。

**验收**：能在 fake_svn_root 上跑通"写 + commit"流程。

---

## 任务 2.4 · SvnWatcher 轮询调度

**目标**：`game/svn_watcher.py`，定时拉取 SVN 变更并触发回调。

**新建文件**：`src/ltclaw_gy_x/game/svn_watcher.py`

**接口**：
```python
class SvnWatcher:
    def __init__(self, svn: SvnClient, project: ProjectConfig,
                 on_change: Callable[[ChangeSet], Awaitable[None]],
                 log_emit: Callable[[dict], Awaitable[None]] | None = None): ...

    async def start(self) -> None:
        # 启动后台 task 循环
    async def stop(self) -> None:
        # 取消 task，等其结束
    async def trigger_now(self) -> ChangeSet:
        # 立刻执行一次（不等下个周期）
    @property
    def status(self) -> dict:
        # {"current_rev","last_polled_at","next_poll_at","running","my_role"}
```

**实现要点**：
- 循环：`update → diff_paths(prev_rev, new_rev) → 应用 filters → 调 on_change(ChangeSet)`
- jitter：每轮 sleep 时间 = `interval + random(0, jitter_seconds)`，避免多机同时 commit
- 异常不传播（log + 继续下一轮）
- log_emit 用于 SSE 推送

**集成到 GameService**：在 `service.start()` 中，若 configured 且 maintainer，构造 SvnWatcher 并 start。
on_change 回调里串起 TableIndexer + DependencyResolver + IndexCommitter（这部分逻辑写在 service.py 内）。

**测试**：
- mock SvnClient.update 模拟 r1→r2 变更
- 验证 on_change 被调用、ChangeSet 内容正确
- 验证 stop 后不再轮询

**验收**：跑一个最小 e2e（fake svn）能看到 watcher 触发 → indexer 执行 → committer 写入。

---

## 任务 3.1 · 前端：GameProject 配置页

**目标**：`console/src/pages/Settings/GameProject/`，完整表单 + 保存 + 提交 SVN。

**新建文件**：
- `console/src/api/modules/game.ts`（API 客户端）
- `console/src/stores/game.ts`（Zustand store：projectConfig / userConfig / svnStatus）
- `console/src/pages/Settings/GameProject/index.tsx`
- `console/src/pages/Settings/GameProject/index.less`
- `console/src/pages/Settings/GameProject/components/PathRulesEditor.tsx`
- `console/src/pages/Settings/GameProject/components/IDRangesEditor.tsx`
- `console/src/pages/Settings/GameProject/components/ModelSlotsEditor.tsx`

**修改文件**：
- `console/src/layouts/constants.ts`：加 `'game-project': '/settings/game-project'` 到 KEY_TO_PATH 与 KEY_TO_LABEL
- `console/src/layouts/Sidebar.tsx`：settings-group 末尾追加 `game-project` 菜单项
- `console/src/App.tsx` 路由表：加 `<Route path="/settings/game-project" element={<GameProject/>}/>`

**API client（game.ts）**：
```typescript
export const gameApi = {
  getProjectConfig: (agentId) => http.get<ProjectConfig|null>(`/api/agents/${agentId}/game/project/config`),
  saveProjectConfig: (agentId, cfg) => http.put(`/api/agents/${agentId}/game/project/config`, cfg),
  commitProjectConfig: (agentId, message?) => http.post<CommitResult>(`/api/agents/${agentId}/game/project/config/commit`, {message}),
  getUserConfig: (agentId) => http.get<UserGameConfig>(...),
  saveUserConfig: (agentId, cfg) => http.put(...),
  validate: (agentId) => http.get<ValidationIssue[]>(...),

  getSvnStatus: (agentId) => http.get<SvnStatus>(...),
  triggerSync: (agentId) => http.post(...),
  subscribeSvnLog: (agentId, onMsg) => /* EventSource */,

  listSystems: (agentId) => http.get<SystemGroup[]>(...),
  listTables: (agentId, params) => http.get<TablePage>(...),
  getTable: (agentId, name) => http.get<TableIndex>(...),
  patchField: (agentId, table, field, patch) => http.patch(...),
  getDependencies: (agentId, table) => http.get<DependencySnapshot>(...),
};
```

**UI 复用**：AntD `Form / Input / Select / Table / Tag / Button`，目录语义/ID段用 AntD `Table` 行内编辑模式；样式 less 复用 `Settings/Models/index.less` 的 layout。

**验收**：
- 访问 `/settings/game-project` 能填表单
- 保存后磁盘上 `.ltclaw_index/project_config.yaml` 内容与表单一致
- 切换"我的角色"为 maintainer 后，commit 按钮可点
- 点 commit 后 toast 显示新 revision

---

## 任务 3.2 · 前端：SvnSync 状态页

**目标**：`console/src/pages/SvnSync/`，状态卡片 + 实时日志 SSE。

**新建文件**：
- `console/src/pages/SvnSync/index.tsx`
- `console/src/pages/SvnSync/index.less`
- `console/src/pages/SvnSync/components/StatusCards.tsx`
- `console/src/pages/SvnSync/components/LogStream.tsx`

**修改文件**：
- `constants.ts` + `Sidebar.tsx`：control-group 末尾追加 `svn-sync`
- `App.tsx`：加 `/svn-sync` 路由

**LogStream 实现要点**：
- 用 `gameApi.subscribeSvnLog(agentId, onMsg)` 拿 EventSource
- 维护一个 ring buffer（最多 1000 条）
- 自动滚到底，用户向上滚动时停止 auto-scroll（标识"暂停跟随"）
- 颜色：INFO=灰、LLM=蓝、WARN=黄、✓=绿、ERROR=红

**StatusCards**：4 张卡片用 AntD `Statistic`，每 5 秒 poll `getSvnStatus`。

**验收**：
- 后端打日志 SSE → 前端实时看到
- 点"立即同步"按钮 → 后端立刻触发 → 日志流可见

---

## 任务 3.3 · 前端：IndexMap 列表视图

**目标**：`console/src/pages/IndexMap/`，左侧系统树 + 右上单表概览 + 右下字段表格。

**新建文件**：
- `console/src/pages/IndexMap/index.tsx`
- `console/src/pages/IndexMap/index.less`
- `console/src/pages/IndexMap/components/SystemTree.tsx`
- `console/src/pages/IndexMap/components/TableOverview.tsx`
- `console/src/pages/IndexMap/components/FieldsTable.tsx`
- `console/src/pages/IndexMap/components/DependencyPanel.tsx`
- `console/src/components/Game/FieldConfidenceTag.tsx`（共享）

**关键交互**：
- 左侧 AntD `Tree`，节点带 `count` 后缀
- 顶部 `Input.Search` 全局搜表/字段
- 字段表格右侧"置信度"列，点击 → AntD `Popover` 三选项（确认/编辑/标记有误）
- 编辑后调 `gameApi.patchField`，乐观更新 + 失败回滚

**Sidebar/路由**：
- 新增 `game-group` 整组（条件渲染：useGameStore().projectConfigured 才显示）
- `/game/index-map` 路由

**验收**：
- 全表能从左树选到右边
- 字段编辑能改、能持久（刷新页面后还在）
- 修改触发后端 SVN commit（控制台日志可见）

---

## 任务 3.4 · QueryRouter（精确 + 关联）

**目标**：`game/query_router.py`，提供两层查询（语义层 P2 推迟）。

**新建文件**：`src/ltclaw_gy_x/game/query_router.py`

**接口**：
```python
class QueryRouter:
    def __init__(self, svc: GameService): ...

    async def fields_of_table(self, table: str) -> list[FieldInfo]: ...
    async def find_field(self, field_name: str) -> list[tuple[str, FieldInfo]]:
        # 返回 [(table_name, field_info)]
    async def dependencies_of(self, table: str) -> dict:
        # {"upstream": [...], "downstream": [...]}
    async def list_tables(self, system: str|None=None, query: str|None=None,
                          page: int=1, size: int=50) -> dict: ...
    async def query(self, q: str, mode: str="auto") -> dict:
        # mode auto: 优先精确（完整字段名/表名），其次模糊
        # 语义层留 stub（NotImplementedError 或返回空）
```

**实现要点**：
- 全部基于已落盘的 `.ltclaw_index/*.json` 读取（用 file mtime 缓存）
- 不查 chroma（P2）
- 暴露给 router 层和 gamedev_tools

**新 router**：`src/ltclaw_gy_x/app/routers/game_index.py` —— 把 `find_field` / `list_tables` / `getTable` / `dependencies_of` / `patchField` 全部接出来；在 routers/__init__.py 注册。

**测试**：构造 fake 索引目录，验证查询结果。

**验收**：
- API 测试覆盖每个端点
- 与 3.3 前端联调可用

---

## 任务 3.5 · gamedev_tools 注入 ReActAgent

**目标**：让 AI 在 Chat 里能直接查表查字段。

**新建文件**：`src/ltclaw_gy_x/agents/tools/gamedev_tools.py`

**修改文件（仅扩展点）**：`src/ltclaw_gy_x/agents/react_agent.py`，在 `tool_functions` dict 末尾追加 5 项；默认开关在 `agent_config.tools.builtin_tools.game_*.enabled`（默认 false，需配置项目后用户在 agent 配置里开）。

**工具签名**（用 agentscope 的 tool 装饰器风格）：
```python
async def game_query_tables(query: str, mode: str = "auto") -> dict:
    """搜索表/字段/系统。query 可以是表名、字段名或自然语句。"""

async def game_describe_field(table: str, field: str) -> dict:
    """获取某张表某个字段的完整描述（含 AI 描述、置信度、引用关系）。"""

async def game_table_dependencies(table: str) -> dict:
    """获取某张表的上下游依赖（哪些表引用它，它引用哪些表）。"""

async def game_search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """从知识库检索（P2 stub，先返回空）。"""

async def game_list_systems() -> list[dict]:
    """列出所有系统分组及表数。"""
```

**实现**：每个工具内部从 `request.app.state.multi_agent_manager` → 当前 workspace.game_service.query 调用。

**新增 skills**（用于触发器，让 AI 在合适时机用对路子）：
- `src/ltclaw_gy_x/agents/skills/game_query-zh/SKILL.md`
- `src/ltclaw_gy_x/agents/skills/game_query-en/SKILL.md`

skill frontmatter 必填：
```yaml
---
name: game_query
language: zh
triggers: ["哪张表", "字段什么意思", "依赖", "引用", "外键"]
require_tools: ["game_query_tables", "game_describe_field", "game_table_dependencies"]
---
```
SKILL.md 正文写一段教 AI 何时用这些工具的指引（5~10 行）。

**验收**：
- 在 Chat 里问"DmgCoeff 是什么意思" → AI 调用 `game_describe_field` → 给出准确答案
- 问"哪些表引用 BuffTable" → AI 调用 `game_table_dependencies`

---

## 复查清单（全部任务完成后由主会话执行）

```
□ 包结构正确：src/ltclaw_gy_x/game/{paths,config,models,svn_client,
    table_indexer,dependency_resolver,index_committer,svn_watcher,
    query_router,service}.py 全部存在
□ 所有接口签名与本文档一致（参数名、返回类型）
□ pyproject.toml 已添加 openpyxl 依赖
□ workspace.py 仅在 register 处增加 1 个 ServiceDescriptor，
    没有改动其它逻辑
□ react_agent.py 仅在 tool_functions dict 追加项
□ routers/__init__.py 在 agent_scoped 中 include 了 game_project /
    game_svn / game_index 三个 router
□ auth.py _PUBLIC_PATHS 未被修改
□ 前端 Sidebar 条件渲染：projectConfigured 才显示 game-group
□ 测试：tests/unit/game/ 全绿；tests/integration/test_game_*.py 全绿
□ pytest 整体覆盖率 >=30%（不能因新代码拖低）
□ 启动 python -m ltclaw_gy_x app 不报错
□ 端到端冒烟：
    1. 通过 API 写 project_config
    2. 在 svn_root 改一张 xlsx
    3. 触发 trigger_now → 看到 .ltclaw_index/tables/X.json
    4. 前端 IndexMap 能查到该字段
    5. Chat 工具问字段含义能正确返回
```

---

## 使用方式

1. 给每个新会话只贴：**"公共上下文"段 + 1 个任务卡**
2. 完成后让那个会话给出最终改动文件清单
3. 全部 15 个完成后，回到主会话说"复查"，按复查清单逐条核验代码

---

# 阶段一 · 复查后修补任务（P0，5 张卡可全部并行）

> 上一轮 15 个任务复查后发现：测试文件全部 UTF-16 带 null 字节（pytest 直接挂）、`query_router.py`/`gamedev_tools.py`/`game_svn.py`/`game_index.py` 完全缺失、前端 API 路径 100% 写错。下面 5 张卡修复。每张可独立分发。

---

## 任务 R-1 · 修复测试文件编码（UTF-16 → UTF-8）

**问题**：`tests/unit/game/` 下全部 10 个 .py 文件是 UTF-16 LE BOM，每个文件含约 4000 个 null 字节，pytest 直接报 `SyntaxError: source code string cannot contain null bytes`。

**任务范围**：
- `tests/unit/game/__init__.py`
- `tests/unit/game/conftest.py`
- `tests/unit/game/test_config.py`
- `tests/unit/game/test_models.py`
- `tests/unit/game/test_svn_client.py`
- `tests/unit/game/test_service.py`
- `tests/unit/game/test_table_indexer.py`
- `tests/unit/game/test_dependency_resolver.py`
- `tests/unit/game/test_index_committer.py`
- `tests/unit/game/test_svn_watcher.py`

**操作步骤**：
1. 对每个文件：用 Python 读取（指定 utf-16 / utf-16-le / 自动 BOM 探测），strip 掉 null 字节，重新以 **UTF-8 无 BOM** 写出
2. 推荐脚本：
   ```python
   from pathlib import Path
   for p in Path("tests/unit/game").glob("*.py"):
       raw = p.read_bytes()
       # 试 utf-16 → utf-8 → 兜底 latin-1 strip null
       for enc in ("utf-16", "utf-16-le", "utf-8-sig"):
           try:
               text = raw.decode(enc)
               break
           except UnicodeDecodeError:
               continue
       else:
           text = raw.decode("latin-1")
       text = text.replace("\x00", "")
       p.write_text(text, encoding="utf-8", newline="\n")
   ```
3. 写完后跑 `pytest tests/unit/game/ -v --tb=short` 看真实通过率
4. **修真正暴露的逻辑 bug**（不是编码问题）直到全绿

**验收**：
- `python -c "open(p,'rb').read().count(b'\x00')"` 全部为 0
- `pytest tests/unit/game/ -v` 0 个 SyntaxError
- 真实测试通过率 ≥ 80%（剩余的 fail 列出来给主会话）

---

## 任务 R-2 · QueryRouter + game_index router

**目标**：补齐缺失的查询层，让 IndexMap 页和 AI 工具有数据可拿。

**新建文件**：
- `src/ltclaw_gy_x/game/query_router.py`
- `src/ltclaw_gy_x/app/routers/game_index.py`

**接口**：
```python
# game/query_router.py
class QueryRouter:
    def __init__(self, svc: "GameService"): ...

    async def list_systems(self) -> list[SystemGroup]: ...
    async def list_tables(self, system: str|None=None, query: str|None=None,
                          page: int=1, size: int=50) -> dict:
        # {"items": [...], "total": int, "page": int, "size": int}
    async def get_table(self, name: str) -> TableIndex | None: ...
    async def fields_of_table(self, table: str) -> list[FieldInfo]: ...
    async def find_field(self, field_name: str) -> list[tuple[str, FieldInfo]]: ...
    async def dependencies_of(self, table: str) -> dict:
        # {"upstream": [...], "downstream": [...]}
    async def patch_field(self, table: str, field: str, patch: FieldPatch) -> FieldInfo:
        # 1. 读 .ltclaw_index/tables/<table>.json
        # 2. 找到 field，应用 patch
        # 3. 原子写回，触发 IndexCommitter.commit_round
        # 4. 返回更新后的 FieldInfo
    async def query(self, q: str, mode: str="auto") -> dict:
        # 自动判定: 完整字段名/表名 → 精确; 否则模糊
        # 语义层 stub: return {"mode":"semantic_stub","results":[]}
```

**实现要点**：
- 全部基于已落盘 `.ltclaw_index/*.json` 读取（按 file mtime 缓存 + 全量重读）
- 不查 chroma（P2）
- 文件路径常量统一从 `game/paths.py` 拿

**`routers/game_index.py` HTTP 路由**：
```
GET   /game/index/systems
GET   /game/index/tables                  ?system=&query=&page=&size=
GET   /game/index/tables/{name}
PATCH /game/index/tables/{name}/fields/{field}    body: FieldPatch
GET   /game/index/dependencies/{table}
GET   /game/index/find_field?name=xxx
POST  /game/index/query                   body: {"q":"...","mode":"auto"}
```

**注册**：在 `routers/agent_scoped.py` 中 import + include `game_index_router`。

**测试**：`tests/integration/test_game_index_api.py`
- 准备 fake `.ltclaw_index/tables/SkillTable.json`
- 验证 GET 列表/详情、PATCH field 后磁盘文件被改、find_field 跨表搜索

**验收**：
- 全部端点 200 OK
- 单测通过

---

## 任务 R-3 · game_svn router（SvnSync 页面后端）

**目标**：让前端 `/svn-sync` 页面可用：状态卡片 + 实时日志 SSE + 立即同步。

**新建文件**：`src/ltclaw_gy_x/app/routers/game_svn.py`

**HTTP 路由**：
```
GET  /game/svn/status              → {current_rev, last_polled_at, next_poll_at,
                                       running, my_role, configured}
POST /game/svn/sync                立即触发一轮，返回 ChangeSet
GET  /game/svn/log/stream          (SSE) 实时日志流
GET  /game/svn/log/recent?limit=200  最近 N 条历史日志（页面加载时回填）
```

**实现要点**：
- 状态来自 `workspace.service_manager.get("game_service").svn_watcher.status`
- SSE 用 `sse_starlette.EventSourceResponse`（项目已有依赖，参考其它 SSE router）
- `GameService` 内维护一个 `asyncio.Queue` 作为日志总线，多消费者订阅；订阅断开自动清理
- 推送事件结构：`{"ts": "...", "level": "INFO|LLM|WARN|ERROR|OK", "msg": "..."}`
- consumer 角色访问 `/sync` → 返回 `409 {"detail":"not maintainer, sync skipped"}`

**SvnWatcher 改造**：在原 `log_emit` 回调里把消息塞进 GameService 的日志总线（如果还没接通的话）。

**注册**：`routers/agent_scoped.py` include `game_svn_router`。

**测试**：`tests/integration/test_game_svn_api.py`
- mock SvnWatcher，验证 status/sync 返回
- 启动 SSE 客户端读 3 条事件后关闭，验证不泄漏 task

**验收**：
- 前端打开 `/svn-sync` 看到 4 张卡有数据
- 后端 `await game_service._log_bus.put({...})` 后前端立即收到

---

## 任务 R-4 · 前端 API 路径全部对齐 + 配置页 API 修补

**问题**：`console/src/api/modules/game.ts` 全部 endpoint 路径错误：
- 写成 `/api/game-project/config`，正确是 `/api/agents/{agentId}/game/project/config`
- snake/kebab 不一致（`/user_config` vs `/user-config`）
- 缺 svn / index / knowledge 全部 endpoint
- 缺 `/validate` GET 和 `/config` DELETE 的后端实现

**任务范围**：

### 4.1 后端补 2 个端点（修改 `routers/game_project.py`）
```python
@router.get("/validate", response_model=list[ValidationIssue])
async def validate_config(workspace=Depends(get_agent_for_request)):
    cfg = workspace.service_manager.get("game_service").project_config
    if cfg is None: return []
    return validate_project_config(cfg)

@router.delete("/config")
async def delete_project_config(workspace=Depends(get_agent_for_request)):
    # 仅删除磁盘 yaml；需要 maintainer 权限
    ...
```

### 4.2 前端 `console/src/api/modules/game.ts` 整体重写
**所有 endpoint 必须**：
- 加 agent 前缀：`/api/agents/${agentId}/...`
- snake_case 与后端对齐（`/user_config` 不是 `/user-config`）
- 第一个参数始终是 `agentId: string`

完整签名（必须严格遵守）：
```typescript
export const gameApi = {
  // project
  getProjectConfig: (agentId) => GET  `/api/agents/${agentId}/game/project/config`,
  saveProjectConfig: (agentId, cfg) => PUT `/api/agents/${agentId}/game/project/config`,
  deleteProjectConfig: (agentId) => DELETE `/api/agents/${agentId}/game/project/config`,
  commitProjectConfig: (agentId, message?) => POST `/api/agents/${agentId}/game/project/config/commit`,
  validateProjectConfig: (agentId) => GET `/api/agents/${agentId}/game/project/validate`,
  getUserConfig: (agentId) => GET `/api/agents/${agentId}/game/project/user_config`,
  saveUserConfig: (agentId, cfg) => PUT `/api/agents/${agentId}/game/project/user_config`,

  // svn
  getSvnStatus: (agentId) => GET `/api/agents/${agentId}/game/svn/status`,
  triggerSync: (agentId) => POST `/api/agents/${agentId}/game/svn/sync`,
  getSvnLogRecent: (agentId, limit=200) => GET `/api/agents/${agentId}/game/svn/log/recent`,
  subscribeSvnLog: (agentId, onMsg) => new EventSource(`/api/agents/${agentId}/game/svn/log/stream`),

  // index
  listSystems: (agentId) => GET `/api/agents/${agentId}/game/index/systems`,
  listTables: (agentId, params) => GET `/api/agents/${agentId}/game/index/tables`,
  getTable: (agentId, name) => GET `/api/agents/${agentId}/game/index/tables/${name}`,
  patchField: (agentId, table, field, patch) => PATCH `/api/agents/${agentId}/game/index/tables/${table}/fields/${field}`,
  getDependencies: (agentId, table) => GET `/api/agents/${agentId}/game/index/dependencies/${table}`,
  findField: (agentId, name) => GET `/api/agents/${agentId}/game/index/find_field`,
  query: (agentId, q, mode) => POST `/api/agents/${agentId}/game/index/query`,
};
```

### 4.3 调用方 agentId 来源
- 所有页面用 `useCurrentAgent()` hook 拿 agentId（项目已有，参考其它 page）
- 改 `pages/Game/GameProject.tsx` 等三个页面：先 `const agentId = useCurrentAgent()`，再传给 `gameApi.xxx(agentId, ...)`

### 4.4 `stores/game.ts` 同步改造
若已有 store，把所有 action 改为接受 `agentId`；若没 store 则跳过。

**验收**：
- 浏览器 DevTools Network 看请求路径全部带 `/api/agents/<aid>/`
- GameProject 配置页能成功 GET / PUT / commit
- SvnSync 页 SSE 连得上、日志流出现
- IndexMap 页能拉到表列表

---

## 任务 R-5 · gamedev_tools + 2 个 skill + react_agent 注册

**目标**：让 AI 在 Chat 里能用工具查表查字段。

**新建文件**：
- `src/ltclaw_gy_x/agents/tools/gamedev_tools.py`
- `src/ltclaw_gy_x/agents/skills/game_query-zh/SKILL.md`
- `src/ltclaw_gy_x/agents/skills/game_query-en/SKILL.md`

### R-5.1 工具实现 `gamedev_tools.py`

5 个工具，全部 async，返回 dict：
```python
async def game_query_tables(query: str, mode: str = "auto") -> dict:
    """按关键字搜表/字段/系统。query 可以是表名、字段名或自然语句。"""

async def game_describe_field(table: str, field: str) -> dict:
    """获取某张表某个字段的完整描述（AI 描述、置信度、引用关系）。"""

async def game_table_dependencies(table: str) -> dict:
    """获取某张表的上下游依赖（哪些表引用它，它引用哪些表）。"""

async def game_search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """从知识库检索（P2 stub，先返回空列表）。"""

async def game_list_systems() -> list[dict]:
    """列出所有系统分组及表数。"""
```

**实现约定**：
- 通过 `agent_context._current_agent_id` ContextVar 拿 agent_id（参考 `agents/tools/` 已有工具的模式）
- 从 `request.app.state.multi_agent_manager.get_agent(agent_id)` 拿 Workspace
- 调 `ws.service_manager.get("game_service").query` (R-2 中创建的 QueryRouter)
- 返回 dict 必须 JSON-serializable（pydantic 用 `.model_dump(mode="json")`）
- service 不存在或未配置 → 返回 `{"error": "game service not configured"}`

### R-5.2 在 `react_agent.py` 注册（仅追加，不动主体）

定位 `tool_functions` dict（搜 `tool_functions =`），在末尾追加 5 行：
```python
tool_functions["game_query_tables"]       = game_query_tables
tool_functions["game_describe_field"]     = game_describe_field
tool_functions["game_table_dependencies"] = game_table_dependencies
tool_functions["game_search_knowledge"]   = game_search_knowledge
tool_functions["game_list_systems"]       = game_list_systems
```

import 必须放文件顶部相邻其它 tool import 处。

**默认开关**：在 `agent_config.tools.builtin_tools` 默认配置（搜 `builtin_tools` 字段定义处）追加：
```python
"game_query_tables":       BuiltinToolConfig(enabled=False),
"game_describe_field":     BuiltinToolConfig(enabled=False),
"game_table_dependencies": BuiltinToolConfig(enabled=False),
"game_search_knowledge":   BuiltinToolConfig(enabled=False),
"game_list_systems":       BuiltinToolConfig(enabled=False),
```
默认 false，用户在 GameProject 配置完后到 agent 设置里手动启用。

### R-5.3 Skill 文件

`agents/skills/game_query-zh/SKILL.md`：
```markdown
---
name: game_query
language: zh
schema_version: workspace-skill-manifest.v1
description: 游戏数值表查询助手
triggers:
  - 哪张表
  - 字段什么意思
  - 字段含义
  - 依赖
  - 引用
  - 外键
require_tools:
  - game_query_tables
  - game_describe_field
  - game_table_dependencies
---

# 游戏数值表查询

当用户询问数值表/字段/依赖时，按如下顺序使用工具：

1. 用户问"X 字段是什么意思"或"X 字段在哪张表"
   → 先 `game_query_tables(query="X")` 定位
   → 再 `game_describe_field(table=..., field="X")` 取详情

2. 用户问"哪些表引用 Y 表 / Y 表的依赖"
   → `game_table_dependencies(table="Y")`

3. 用户问"我们项目有哪些系统/有多少张表"
   → `game_list_systems()`

回答时务必给出：
- 字段所属表名
- AI 描述与置信度（confirmed / high_ai / low_ai）
- 是否需要人工确认（low_ai 时提醒用户去索引地图确认）
```

`agents/skills/game_query-en/SKILL.md`：英文对照版（triggers 用英文：`which table`, `field meaning`, `dependency`, `reference`, `foreign key`）。

**测试**：手动验证（无单测要求）：
1. 开发环境配好 project_config 并跑通 svn 索引
2. 在 agent 配置里启用 5 个 game_* 工具
3. Chat 里问"DmgCoeff 是什么意思" → AI 应当调用 `game_query_tables` + `game_describe_field` 后给出答案

**验收**：
- 工具文件存在、类型正确
- `react_agent.py` git diff 只有追加，没有删改
- `python -m ltclaw_gy_x app` 能正常启动（不报 import 错）
- 默认 false 不影响现有 agent 行为

---

## P0 修补复查清单（5 张卡完成后由主会话执行）

```
□ tests/unit/game/*.py 全部 0 null 字节
□ pytest tests/unit/game/ 通过率 ≥ 80%
□ src/ltclaw_gy_x/game/query_router.py 存在且导出 QueryRouter
□ src/ltclaw_gy_x/app/routers/game_index.py 存在
□ src/ltclaw_gy_x/app/routers/game_svn.py 存在
□ routers/agent_scoped.py 已 include 三个 game_* router
□ console/src/api/modules/game.ts 全部路径含 /api/agents/${agentId}/
□ game_project.py 新增 GET /validate、DELETE /config
□ src/ltclaw_gy_x/agents/tools/gamedev_tools.py 存在 5 个 async 工具
□ react_agent.py tool_functions dict 追加 5 项（无主体改动）
□ agents/skills/game_query-{zh,en}/SKILL.md 存在
□ 启动 python -m ltclaw_gy_x app 不报错
□ 端到端冒烟（同主清单的 5 步）真正跑通
```

