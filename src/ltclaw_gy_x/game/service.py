"""
游戏策划工作台服务
"""

import logging
from pathlib import Path
from typing import Union

from .config import (
    ProjectConfig,
    UserGameConfig,
    load_project_config,
    load_user_config,
)
from .change_applier import ChangeApplier
from .change_proposal import ProposalStore
from .svn_committer import SvnCommitter
from .svn_client import SvnClient, SvnNotInstalledError
from .paths import (
    get_workspace_game_dir,
    get_chroma_dir,
    get_llm_cache_dir,
    get_svn_cache_dir,
)
from .table_indexer import TableIndexer
from .dependency_resolver import DependencyResolver
from .index_committer import IndexCommitter
from .svn_watcher import SvnWatcher
from .query_router import QueryRouter

logger = logging.getLogger(__name__)


class GameService:
    def __init__(self, workspace_dir: Path, runner=None, channel_manager=None):
        self.workspace_dir = workspace_dir
        self.runner = runner
        self.channel_manager = channel_manager
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
        self._started = False
        get_workspace_game_dir(workspace_dir).mkdir(parents=True, exist_ok=True)

    @property
    def configured(self) -> bool:
        return self._project_config is not None

    @property
    def project_config(self):
        return self._project_config

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

    def _model_router(self):
        return getattr(self.runner, "model_router", None) if self.runner else None

    def _rebuild_runtime_components(self) -> None:
        self._proposal_store = ProposalStore(self.workspace_dir)
        self._change_applier = None
        self._svn_committer = None
        self._table_indexer = None
        self._dependency_resolver = None
        self._index_committer = None
        self._svn_watcher = None
        if self._project_config:
            svn_root = Path(self._project_config.svn.root)
            self._table_indexer = TableIndexer(
                project=self._project_config,
                model_router=self._model_router(),
                cache_dir=get_llm_cache_dir(self.workspace_dir),
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
                        )
                        await self._svn_client.check_installed()
                    except SvnNotInstalledError:
                        logger.warning("SVN未安装，部分功能将不可用")
                    except Exception as e:
                        logger.warning(f"SVN客户端初始化失败: {e}")
            get_chroma_dir(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            get_llm_cache_dir(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            get_svn_cache_dir(self.workspace_dir).mkdir(parents=True, exist_ok=True)
            try:
                self._rebuild_runtime_components()
            except Exception as e:
                logger.warning(f"核心组件初始化失败: {e}")
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
                        )
                    except Exception as e:
                        logger.warning(f"SVN客户端重新初始化失败: {e}")
                        self._svn_client = None
            self._rebuild_runtime_components()
        except Exception as e:
            logger.error(f"GameService 配置重新加载失败: {e}")
            raise

    async def resolve_dependencies(self, tables: list, prev_graph=None):
        if not self._dependency_resolver:
            raise RuntimeError("依赖关系解析器未初始化，请确保项目已正确配置")
        return await self._dependency_resolver.resolve(tables, prev_graph)

    async def index_tables(self, file_paths: list, svn_root: Path = None, svn_revision: int = 0):
        if not self._table_indexer:
            raise RuntimeError("表索引器未初始化")
        if svn_root is None and self._project_config:
            svn_root = Path(self._project_config.svn.root)
        return await self._table_indexer.index_batch(
            [Path(p) for p in file_paths],
            svn_root or Path("."),
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

    async def _handle_svn_change(self, changeset) -> None:
        try:
            if self._index_committer:
                await self._index_committer.save_changeset(changeset)
            modified = list(getattr(changeset, "modified", []) or []) + list(getattr(changeset, "added", []) or [])
            table_files = [f for f in modified if f.lower().endswith((".xlsx", ".xls", ".csv"))]
            if table_files and self._table_indexer:
                logger.info(f"检测到{len(table_files)}个表格文件变更")
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
