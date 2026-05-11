"""
游戏策划工作台服务
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

from .config import (
    ProjectConfig,
    UserGameConfig,
    load_project_config,
    load_user_config,
)
from .change_applier import ChangeApplier
from .change_proposal import ProposalStore
from .svn_committer import SvnCommitter
from .svn_client import SvnClient, SvnNotInstalledError, TortoiseUiOnlyError
from .paths import (
    get_workspace_game_dir,
    get_chroma_dir,
    get_llm_cache_dir,
    get_svn_cache_dir,
    get_code_index_dir,
)
from .table_indexer import TableIndexer
from .dependency_resolver import DependencyResolver
from .index_committer import IndexCommitter
from .svn_watcher import SvnWatcher
from .query_router import QueryRouter
from .code_indexer import CodeIndexer, CodeIndexStore, index_cs_batch

logger = logging.getLogger(__name__)


class SimpleModelRouter:
    """轻量 LLM 调用桥接：把 game 子系统的 call_model(prompt, model_type)
    转发到 ProviderManager 当前激活的模型。失败时返回空字符串，由调用方走兜底。
    不在源码里出现任何凭据 / URL 字面量；一切走 ProviderManager 已存储的运行时配置。
    """

    def __init__(self, provider_manager: Any = None) -> None:
        self._pm = provider_manager

    def _resolve_active(self):
        if self._pm is None:
            return None, None
        active = getattr(self._pm, "active_model", None)
        if active is None:
            getter = getattr(self._pm, "get_active_model", None)
            if callable(getter):
                active = getter()
        if active is None:
            return None, None
        provider = self._pm.get_provider(active.provider_id)
        return provider, active

    async def call_model(self, prompt: str, model_type: str = "default") -> str:
        provider, active = self._resolve_active()
        if provider is None or active is None:
            logger.debug("SimpleModelRouter: no active model, returning empty")
            return ""
        model_id = getattr(active, "model_id", None) or getattr(active, "model", None)
        if not model_id:
            logger.warning("SimpleModelRouter: active model has no model id")
            return ""
        provider_type = type(provider).__name__
        try:
            if provider_type == "AnthropicProvider":
                client = provider._client(timeout=60)
                resp = await client.messages.create(
                    model=model_id,
                    max_tokens=16384,
                    messages=[{"role": "user", "content": prompt}],
                )
                parts = []
                for blk in (getattr(resp, "content", []) or []):
                    tx = getattr(blk, "text", None)
                    if tx:
                        parts.append(tx)
                return "".join(parts)
            base_url = getattr(provider, "base_url", None)
            api_key = getattr(provider, "api_key", None)
            if not (base_url and api_key):
                return ""
            try:
                from openai import AsyncOpenAI
            except Exception:
                return ""
            client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=60)
            resp = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            choice = resp.choices[0] if resp.choices else None
            if choice and choice.message and choice.message.content:
                return choice.message.content
            return ""
        except Exception as e:
            logger.warning(f"SimpleModelRouter.call_model failed ({model_type}, provider={provider_type}): {e}")
            return ""


class GameService:
    def __init__(self, workspace_dir: Path, runner=None, channel_manager=None):
        self.workspace_dir = workspace_dir
        self.runner = runner
        self.channel_manager = channel_manager
        self._config_generation = 0
        self._project_config: Union[ProjectConfig, None] = None
        self._user_config: UserGameConfig = UserGameConfig()
        self._svn_client: Union[SvnClient, None] = None
        self._table_indexer: Union[TableIndexer, None] = None
        self._dependency_resolver: Union[DependencyResolver, None] = None
        self._index_committer: Union[IndexCommitter, None] = None
        self._svn_watcher: Union[SvnWatcher, None] = None
        self._query_router: Union[QueryRouter, None] = None
        self._proposal_store: Union[ProposalStore, None] = None
        self._change_applier: Union[ChangeApplier, None] = None
        self._svn_committer: Union[SvnCommitter, None] = None
        self._code_indexer: Union[CodeIndexer, None] = None
        self._code_index_store: Union[CodeIndexStore, None] = None
        self._recent_changes_buffer: List[dict] = []
        self._started = False
        get_workspace_game_dir(workspace_dir).mkdir(parents=True, exist_ok=True)

    @property
    def configured(self) -> bool:
        return self._project_config is not None

    @property
    def project_config(self):
        return self._project_config

    @property
    def config(self):
        return self.project_config

    @property
    def config_generation(self) -> int:
        return self._config_generation

    @property
    def user_config(self):
        return self._user_config

    @property
    def svn(self):
        return self._svn_client

    @property
    def table_indexer(self):
        return self._table_indexer

    @property
    def dependency_resolver(self):
        return self._dependency_resolver

    @property
    def index_committer(self):
        return self._index_committer

    @property
    def svn_watcher(self):
        return self._svn_watcher

    @property
    def query_router(self):
        return self._query_router

    @property
    def proposal_store(self):
        return self._proposal_store

    @property
    def change_applier(self):
        return self._change_applier

    @property
    def svn_committer(self):
        return self._svn_committer

    @property
    def code_indexer(self):
        return self._code_indexer

    @property
    def code_index_store(self):
        return self._code_index_store

    @property
    def recent_changes(self) -> List[dict]:
        return list(self._recent_changes_buffer)

    def _runtime_svn_root(self) -> Path | None:
        candidate = getattr(self._user_config, "svn_local_root", None)
        if candidate:
            path = Path(candidate).expanduser()
            if path.exists():
                return path
        if self._project_config is not None:
            project_root = str(self._project_config.svn.root or "").strip()
            if project_root and "://" not in project_root:
                path = Path(project_root).expanduser()
                if path.exists():
                    return path
        return None

    def _model_router(self):
        if self.runner is not None:
            r = getattr(self.runner, "model_router", None)
            if r is not None:
                return r
        try:
            from ..providers.provider_manager import ProviderManager
            return SimpleModelRouter(ProviderManager.get_instance())
        except Exception as e:
            logger.debug(f"ProviderManager unavailable, using stub router: {e}")
            return SimpleModelRouter(None)

    def _rebuild_runtime_components(self) -> None:
        runtime_svn_root = self._runtime_svn_root()
        self._proposal_store = ProposalStore(self.workspace_dir, svn_root=runtime_svn_root)
        self._change_applier = None
        self._svn_committer = None
        self._table_indexer = None
        self._dependency_resolver = None
        self._index_committer = None
        self._svn_watcher = None
        self._code_indexer = None
        self._code_index_store = None
        if self._project_config:
            svn_root = Path(self._project_config.svn.root)
            self._table_indexer = TableIndexer(
                project=self._project_config,
                model_router=self._model_router(),
                cache_dir=get_llm_cache_dir(self.workspace_dir, runtime_svn_root),
            )
            self._dependency_resolver = DependencyResolver(
                project=self._project_config,
                model_router=self._model_router(),
            )
            self._change_applier = ChangeApplier(
                self._project_config,
                svn_root,
                self._table_indexer,
            )
            try:
                code_dir = get_code_index_dir(self.workspace_dir, runtime_svn_root)
                code_dir.mkdir(parents=True, exist_ok=True)
                self._code_indexer = CodeIndexer()
                self._code_index_store = CodeIndexStore(code_dir)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"初始化 code indexer 失败: {e}")
                self._code_indexer = None
                self._code_index_store = None
        if self._project_config and self._svn_client:
            self._index_committer = IndexCommitter(
                project=self._project_config,
                svn_client=self._svn_client,
                workspace_dir=self.workspace_dir,
            )
            self._svn_watcher = SvnWatcher(
                project=self._project_config,
                svn_client=self._svn_client,
                change_callback=self._handle_svn_change,
            )
            if self._user_config.my_role == "maintainer":
                self._svn_committer = SvnCommitter(
                    self._svn_client,
                    Path(self._project_config.svn.root),
                )
        self._query_router = QueryRouter(self)

    async def _maybe_start_watcher(self) -> None:
        if not self._svn_watcher:
            return
        if self._user_config.my_role != "maintainer":
            return
        try:
            await self._svn_watcher.start()
        except Exception as e:
            logger.warning(f"SVN watcher 启动失败: {e}")

    async def start(self) -> None:
        if self._started:
            return
        logger.info("GameService 正在启动...")
        try:
            self._user_config = load_user_config()
            if self._user_config.svn_local_root:
                svn_root = Path(self._user_config.svn_local_root)
                self._project_config = load_project_config(svn_root)
                if self._project_config and self._user_config.my_role == "maintainer":
                    try:
                        self._svn_client = SvnClient(
                            working_copy=svn_root,
                            username=self._user_config.svn_username,
                            password=self._user_config.svn_password,
                            trust_server_cert=self._user_config.svn_trust_cert,
                        )
                        await self._svn_client.check_installed()
                    except SvnNotInstalledError:
                        logger.warning("SVN未安装，部分功能将不可用")
                    except Exception as e:
                        logger.warning(f"SVN客户端初始化失败: {e}")
            runtime_svn_root = self._runtime_svn_root()
            get_chroma_dir(self.workspace_dir, runtime_svn_root).mkdir(parents=True, exist_ok=True)
            get_llm_cache_dir(self.workspace_dir, runtime_svn_root).mkdir(parents=True, exist_ok=True)
            get_svn_cache_dir(self.workspace_dir, runtime_svn_root).mkdir(parents=True, exist_ok=True)
            try:
                self._rebuild_runtime_components()
            except Exception as e:
                logger.warning(f"核心组件初始化失败: {e}")
            await self._maybe_start_watcher()
            self._started = True
            logger.info(
                f"GameService 启动完成: project={self._project_config.project.name if self._project_config else 'None'}, "
                f"role={self._user_config.my_role}, configured={self.configured}"
            )
        except Exception as e:
            logger.error(f"GameService 启动失败: {e}")
            raise

    async def stop(self) -> None:
        if not self._started:
            return
        try:
            if self._svn_watcher:
                await self._svn_watcher.stop()
            self._started = False
        except Exception as e:
            logger.error(f"GameService 停止时出错: {e}")

    async def reload_config(self) -> None:
        try:
            old = self._svn_watcher
            self._project_config = None
            self._svn_client = None
            self._table_indexer = None
            self._dependency_resolver = None
            self._index_committer = None
            self._svn_watcher = None
            self._proposal_store = None
            self._change_applier = None
            self._svn_committer = None
            self._code_indexer = None
            self._code_index_store = None
            if old:
                await old.stop()
            self._user_config = load_user_config()
            if self._user_config.svn_local_root:
                svn_root = Path(self._user_config.svn_local_root)
                self._project_config = load_project_config(svn_root)
                if self._project_config and self._user_config.my_role == "maintainer":
                    try:
                        self._svn_client = SvnClient(
                            working_copy=svn_root,
                            username=self._user_config.svn_username,
                            password=self._user_config.svn_password,
                            trust_server_cert=self._user_config.svn_trust_cert,
                        )
                    except Exception as e:
                        logger.warning(f"SVN客户端重新初始化失败: {e}")
                        self._svn_client = None
            self._rebuild_runtime_components()
            await self._maybe_start_watcher()
            self._config_generation += 1
        except Exception as e:
            logger.error(f"GameService 配置重新加载失败: {e}")
            raise

    async def resolve_dependencies(self, tables: list, prev_graph=None):
        if not self._dependency_resolver:
            raise RuntimeError("依赖关系解析器未初始化，请确保项目已正确配置")
        return await self._dependency_resolver.resolve(tables, prev_graph)

    async def index_tables(self, file_paths: list, svn_root: Path = None, svn_revision: int = 0):
        if not self._table_indexer:
            raise RuntimeError("table indexer not initialized")
        if svn_root is None and self._project_config:
            svn_root = Path(self._project_config.svn.root)
        root = svn_root or Path(".")
        resolved = []
        for p in file_paths:
            pp = Path(p)
            resolved.append(pp if pp.is_absolute() else (root / pp))
        return await self._table_indexer.index_batch(
            resolved,
            root,
            svn_revision,
        )

    async def commit_indexes(self, tables=None, graph=None, changeset=None,
                              commit_message=None):
        if not self._index_committer:
            raise RuntimeError("索引提交器未初始化，请确保项目和SVN已正确配置")
        if tables is not None and graph is not None and changeset is not None:
            return await self._index_committer.save_all(tables, graph, changeset, commit_message)
        success = True
        if tables is not None:
            success = success and await self._index_committer.save_table_indexes(tables, commit_message)
        if graph is not None:
            success = success and await self._index_committer.save_dependency_graph(graph, commit_message)
        if changeset is not None:
            success = success and await self._index_committer.save_changeset(changeset)
        return success

    def load_cached_indexes(self):
        if not self._index_committer:
            raise RuntimeError("索引提交器未初始化")
        return (
            self._index_committer.load_table_indexes(),
            self._index_committer.load_dependency_graph(),
            self._index_committer.load_changeset(),
        )

    def _path_passes_filter(self, p: str) -> bool:
        cfg = self._project_config
        if not cfg:
            return True
        include_ext = tuple(e.lower() for e in (cfg.filters.include_ext or []))
        if include_ext and not p.lower().endswith(include_ext):
            return False
        path_rules = list(cfg.paths or [])
        if path_rules:
            ok = False
            for rule in path_rules:
                pat = getattr(rule, "path", "") or ""
                if not pat:
                    continue
                if p.startswith(pat) or pat in p:
                    ok = True
                    break
            if not ok:
                return False
        return True

    async def _handle_svn_change(self, changeset) -> None:
        try:
            added = [p for p in (getattr(changeset, "added", []) or []) if self._path_passes_filter(p)]
            modified = [p for p in (getattr(changeset, "modified", []) or []) if self._path_passes_filter(p)]
            deleted = [p for p in (getattr(changeset, "deleted", []) or []) if self._path_passes_filter(p)]

            existing_tables: list = []
            prev_graph = None
            if self._index_committer:
                try:
                    existing_tables = self._index_committer.load_table_indexes() or []
                except Exception as e:
                    logger.warning(f"加载已有表索引失败: {e}")
                    existing_tables = []
                try:
                    prev_graph = self._index_committer.load_dependency_graph()
                except Exception as e:
                    logger.warning(f"加载已有依赖图失败: {e}")

            deleted_set = set(deleted)
            existing_tables = [t for t in existing_tables if getattr(t, "source_path", None) not in deleted_set]

            files_to_index = list(added) + list(modified)
            new_tables: list = []
            if files_to_index and self._table_indexer and self._project_config:
                svn_root = Path(self._project_config.svn.root)
                try:
                    new_tables = await self.index_tables(
                        files_to_index, svn_root, getattr(changeset, "to_rev", 0)
                    ) or []
                except Exception as e:
                    logger.warning(f"index_tables 失败: {e}")
                    new_tables = []

            merged: dict = {getattr(t, "table_name", None): t for t in existing_tables if getattr(t, "table_name", None)}
            for t in new_tables:
                key = getattr(t, "table_name", None)
                if key:
                    merged[key] = t
            all_tables = list(merged.values())

            # ── .cs 代码索引 (P2 #5) ──
            if self._code_indexer and self._code_index_store and self._project_config:
                svn_root = Path(self._project_config.svn.root)
                cs_added_modified = [
                    svn_root / p for p in (added + modified)
                    if p.lower().endswith(".cs")
                ]
                cs_deleted = [p for p in deleted if p.lower().endswith(".cs")]
                if cs_added_modified or cs_deleted:
                    known_tables_set = {
                        getattr(t, "table_name", "") for t in all_tables
                        if getattr(t, "table_name", None)
                    }
                    known_fields_map: dict[str, set[str]] = {}
                    for t in all_tables:
                        tname = getattr(t, "table_name", None)
                        fields = getattr(t, "fields", None) or []
                        if tname:
                            known_fields_map[tname] = {
                                getattr(f, "name", "") for f in fields
                                if getattr(f, "name", None)
                            }
                    try:
                        await index_cs_batch(
                            self._code_indexer,
                            self._code_index_store,
                            cs_added_modified,
                            svn_root,
                            svn_revision=getattr(changeset, "to_rev", 0),
                            known_tables=known_tables_set,
                            known_fields=known_fields_map,
                        )
                    except Exception as e:
                        logger.warning(f"index_cs_batch 失败: {e}")
                    for rel in cs_deleted:
                        try:
                            self._code_index_store.delete(rel)
                        except Exception:  # noqa: BLE001
                            continue

            graph = None
            if self._dependency_resolver:
                try:
                    graph = await self.resolve_dependencies(all_tables, prev_graph)
                except Exception as e:
                    logger.warning(f"resolve_dependencies 失败: {e}")

            to_rev = getattr(changeset, "to_rev", 0)
            msg = f"自动更新索引 r{to_rev}"
            try:
                await self.commit_indexes(
                    tables=all_tables, graph=graph, changeset=changeset, commit_message=msg
                )
            except TortoiseUiOnlyError:
                logger.warning("索引未提交至 SVN，需 GUI 提交")
            except Exception as e:
                logger.error(f"commit_indexes 失败: {e}")

            entry = {
                "revision": to_rev,
                "from_rev": getattr(changeset, "from_rev", 0),
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "indexed_tables": [getattr(t, "table_name", "") for t in new_tables],
                "timestamp": datetime.now().isoformat(),
            }
            self._recent_changes_buffer.insert(0, entry)
            if len(self._recent_changes_buffer) > 50:
                self._recent_changes_buffer = self._recent_changes_buffer[:50]
        except Exception as e:
            logger.error(f"处理SVN变更时出错: {e}")

    async def start_svn_monitoring(self) -> bool:
        if not self._svn_watcher:
            return False
        try:
            await self._svn_watcher.start()
            return True
        except Exception as e:
            logger.error(f"启动SVN监控失败: {e}")
            return False

    async def stop_svn_monitoring(self) -> bool:
        if not self._svn_watcher:
            return False
        try:
            await self._svn_watcher.stop()
            return True
        except Exception as e:
            logger.error(f"停止SVN监控失败: {e}")
            return False

    def get_svn_monitoring_status(self) -> dict:
        if not self._svn_watcher:
            return {"error": "SVN监控器未初始化"}
        return self._svn_watcher.get_status()

    async def force_full_rescan(self) -> dict:
        import fnmatch
        if not self._project_config:
            raise RuntimeError("project not configured")
        svn_root = Path(self._project_config.svn.root)
        if not svn_root.exists():
            raise RuntimeError(f"svn working copy missing: {svn_root}")
        current_rev = 0
        if self._svn_client is not None:
            try:
                info = await self._svn_client.info()
                current_rev = int(info.get("revision") or 0)
            except Exception as e:
                logger.warning(f"read svn revision failed: {e}")
        include_ext = tuple(e.lower() for e in (self._project_config.filters.include_ext or []))
        exclude_glob = list(self._project_config.filters.exclude_glob or [])
        scanned = []
        for f in svn_root.rglob("*"):
            if not f.is_file():
                continue
            try:
                rel = f.relative_to(svn_root).as_posix()
            except ValueError:
                continue
            if include_ext and f.suffix.lower() not in include_ext:
                continue
            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(f.name, pat) for pat in exclude_glob):
                continue
            scanned.append(rel)
        from .models import ChangeSet
        cs = ChangeSet(
            from_rev=0,
            to_rev=current_rev,
            added=[],
            modified=scanned,
            deleted=[],
        )
        await self._handle_svn_change(cs)
        last = self._recent_changes_buffer[0] if self._recent_changes_buffer else {}
        return {
            "revision": current_rev,
            "scanned_files": scanned,
            "indexed": len(last.get("indexed_tables", [])),
        }
