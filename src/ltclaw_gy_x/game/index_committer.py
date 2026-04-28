"""
索引提交器: 负责索引文件的本地缓存与可选 SVN 提交。
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import ProjectConfig
from .models import TableIndex, DependencyGraph, ChangeSet
from .svn_client import SvnClient
from .paths import get_svn_cache_dir

logger = logging.getLogger(__name__)


class IndexCommitter:
    def __init__(self, project: ProjectConfig, svn_client: SvnClient, workspace_dir: Path,
                 index_output_dir: str = ".ltclaw_index"):
        self.project = project
        self.svn = svn_client
        self.workspace_dir = workspace_dir
        self.index_output_dir = index_output_dir
        self.cache_dir = get_svn_cache_dir(workspace_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tables_index_file = self.cache_dir / "table_indexes.json"
        self.dependency_graph_file = self.cache_dir / "dependency_graph.json"
        self.changeset_file = self.cache_dir / "latest_changeset.json"
        self.svn_tables_file: Optional[Path] = None
        self.svn_dependency_file: Optional[Path] = None
        self._setup_svn_paths()

    def _setup_svn_paths(self):
        if not self.index_output_dir or not self.svn:
            return
        try:
            svn_root = Path(self.svn.working_copy)
            output_dir = svn_root / self.index_output_dir
            self.svn_tables_file = output_dir / "table_indexes.json"
            self.svn_dependency_file = output_dir / "dependency_graph.json"
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"setup svn paths failed: {e}")

    def _serialize_table_indexes(self, tables: List[TableIndex]) -> str:
        data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "tables": [t.model_dump(mode="json") for t in tables],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _deserialize_table_indexes(self, s: str) -> List[TableIndex]:
        try:
            data = json.loads(s)
            return [TableIndex.model_validate(t) for t in data.get("tables", [])]
        except Exception as e:
            logger.error(f"反序列化表索引失败: {e}")
            return []

    def _serialize_dependency_graph(self, g: DependencyGraph) -> str:
        d = g.model_dump(mode="json")
        d["version"] = "1.0"
        return json.dumps(d, indent=2, ensure_ascii=False)

    def _deserialize_dependency_graph(self, s: str) -> Optional[DependencyGraph]:
        try:
            data = json.loads(s)
            data.pop("version", None)
            return DependencyGraph.model_validate(data)
        except Exception as e:
            logger.error(f"反序列化依赖图失败: {e}")
            return None

    def _serialize_changeset(self, c: ChangeSet) -> str:
        d = c.model_dump(mode="json")
        d["version"] = "1.0"
        return json.dumps(d, indent=2, ensure_ascii=False)

    def _deserialize_changeset(self, s: str) -> Optional[ChangeSet]:
        try:
            data = json.loads(s)
            data.pop("version", None)
            return ChangeSet.model_validate(data)
        except Exception as e:
            logger.error(f"反序列化变更集失败: {e}")
            return None

    async def save_table_indexes(self, tables: List[TableIndex],
                                  commit_message: Optional[str] = None) -> bool:
        try:
            content = self._serialize_table_indexes(tables)
            self.tables_index_file.write_text(content, encoding="utf-8")
            if self.svn_tables_file:
                self.svn_tables_file.write_text(content, encoding="utf-8")
                msg = commit_message or f"更新表索引 ({len(tables)} tables)"
                if not await self._commit_to_svn([self.svn_tables_file], msg):
                    return False
            return True
        except Exception as e:
            logger.error(f"保存表索引失败: {e}")
            return False

    async def save_dependency_graph(self, graph: DependencyGraph,
                                     commit_message: Optional[str] = None) -> bool:
        try:
            content = self._serialize_dependency_graph(graph)
            self.dependency_graph_file.write_text(content, encoding="utf-8")
            if self.svn_dependency_file:
                self.svn_dependency_file.write_text(content, encoding="utf-8")
                msg = commit_message or f"更新依赖关系图 ({len(graph.edges)} dependencies)"
                if not await self._commit_to_svn([self.svn_dependency_file], msg):
                    return False
            return True
        except Exception as e:
            logger.error(f"保存依赖图失败: {e}")
            return False

    async def save_changeset(self, changeset: ChangeSet) -> bool:
        try:
            content = self._serialize_changeset(changeset)
            self.changeset_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"保存变更集失败: {e}")
            return False

    async def save_all(self, tables: List[TableIndex], graph: DependencyGraph,
                       changeset: ChangeSet, commit_message: Optional[str] = None) -> bool:
        try:
            tj = self._serialize_table_indexes(tables)
            gj = self._serialize_dependency_graph(graph)
            cj = self._serialize_changeset(changeset)
            self.tables_index_file.write_text(tj, encoding="utf-8")
            self.dependency_graph_file.write_text(gj, encoding="utf-8")
            self.changeset_file.write_text(cj, encoding="utf-8")
            files = []
            if self.svn_tables_file:
                self.svn_tables_file.write_text(tj, encoding="utf-8")
                files.append(self.svn_tables_file)
            if self.svn_dependency_file:
                self.svn_dependency_file.write_text(gj, encoding="utf-8")
                files.append(self.svn_dependency_file)
            if files:
                msg = commit_message or f"批量更新索引数据 ({len(tables)} tables, {len(graph.edges)} dependencies)"
                if not await self._commit_to_svn(files, msg):
                    return False
            return True
        except Exception as e:
            logger.error(f"批量保存失败: {e}")
            return False

    async def _commit_to_svn(self, files: List[Path], message: str) -> bool:
        try:
            if not self.svn:
                return False
            existing = [f for f in files if f.exists()]
            if not existing:
                return False
            try:
                await self.svn.add(existing)
            except Exception as e:
                logger.warning(f"svn add 警告: {e}")
            await self.svn.commit(existing, message)
            return True
        except Exception as e:
            logger.error(f"SVN提交失败: {e}")
            return False

    def load_table_indexes(self) -> List[TableIndex]:
        try:
            if self.tables_index_file.exists():
                return self._deserialize_table_indexes(self.tables_index_file.read_text(encoding="utf-8"))
            return []
        except Exception as e:
            logger.error(f"加载表索引失败: {e}")
            return []

    def load_dependency_graph(self) -> Optional[DependencyGraph]:
        try:
            if self.dependency_graph_file.exists():
                return self._deserialize_dependency_graph(self.dependency_graph_file.read_text(encoding="utf-8"))
            return None
        except Exception as e:
            logger.error(f"加载依赖图失败: {e}")
            return None

    def load_changeset(self) -> Optional[ChangeSet]:
        try:
            if self.changeset_file.exists():
                return self._deserialize_changeset(self.changeset_file.read_text(encoding="utf-8"))
            return None
        except Exception as e:
            logger.error(f"加载变更集失败: {e}")
            return None

    async def create_backup(self, backup_dir: Optional[Path] = None) -> bool:
        try:
            if backup_dir is None:
                backup_dir = self.cache_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            for fp in [self.tables_index_file, self.dependency_graph_file, self.changeset_file]:
                if fp.exists():
                    shutil.copy2(fp, backup_dir / fp.name)
            return True
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False

    async def restore_from_backup(self, backup_dir: Path) -> bool:
        try:
            if not backup_dir.exists():
                return False
            mapping = [
                ("table_indexes.json", self.tables_index_file),
                ("dependency_graph.json", self.dependency_graph_file),
                ("latest_changeset.json", self.changeset_file),
            ]
            for name, target in mapping:
                src = backup_dir / name
                if src.exists():
                    shutil.copy2(src, target)
            return True
        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")
            return False

    def get_index_stats(self) -> dict:
        def info(p: Path) -> dict:
            return {
                "exists": p.exists(),
                "size": p.stat().st_size if p.exists() else 0,
                "modified": p.stat().st_mtime if p.exists() else None,
            }
        return {
            "cache_dir": str(self.cache_dir),
            "tables_index_file": info(self.tables_index_file),
            "dependency_graph_file": info(self.dependency_graph_file),
            "changeset_file": info(self.changeset_file),
        }