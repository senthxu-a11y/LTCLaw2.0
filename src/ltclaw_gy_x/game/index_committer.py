"""
索引提交器: 负责索引文件的本地缓存与可选 SVN 提交。
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import ProjectConfig
from .history_archiver import diff_and_archive
from .models import ChangeSet, DependencyGraph, TableIndex
from .paths import get_svn_cache_dir, get_tables_dir, get_workspace_game_dir
from .svn_client import SvnClient

logger = logging.getLogger(__name__)


class IndexCommitter:
    def __init__(
        self,
        project: ProjectConfig,
        svn_client: SvnClient,
        workspace_dir: Path,
        index_output_dir: str = ".ltclaw_index",
    ):
        self.project = project
        self.svn = svn_client
        self.workspace_dir = workspace_dir
        self.index_output_dir = index_output_dir
        self.cache_dir = get_svn_cache_dir(workspace_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_tables_dir = get_workspace_game_dir(workspace_dir) / "tables"
        self.workspace_tables_dir.mkdir(parents=True, exist_ok=True)
        self.tables_index_file = self.cache_dir / "table_indexes.json"
        self.dependency_graph_file = self.cache_dir / "dependency_graph.json"
        self.changeset_file = self.cache_dir / "latest_changeset.json"
        self.registry_file = self.cache_dir / "registry.json"
        self.history_dir = self.cache_dir / "history"
        self.svn_tables_dir: Optional[Path] = None
        self.svn_tables_file: Optional[Path] = None
        self.svn_dependency_file: Optional[Path] = None
        self.svn_registry_file: Optional[Path] = None
        self._setup_svn_paths()

    def _setup_svn_paths(self):
        if not self.index_output_dir or not self.svn:
            return
        try:
            svn_root = Path(self.svn.working_copy)
            output_dir = svn_root / self.index_output_dir
            self.svn_tables_dir = get_tables_dir(svn_root)
            self.svn_tables_file = output_dir / "table_indexes.json"
            self.svn_dependency_file = output_dir / "dependency_graph.json"
            self.svn_registry_file = output_dir / "registry.json"
            output_dir.mkdir(parents=True, exist_ok=True)
            self.svn_tables_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"setup paths failed: {e}")

    def _serialize_table_indexes(self, tables: List[TableIndex]) -> str:
        data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "tables": [t.model_dump(mode="json") for t in tables],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _serialize_single_table_index(self, table: TableIndex) -> str:
        data = table.model_dump(mode="json")
        data["file"] = table.source_path
        data["summary"] = table.ai_summary
        data["generated_at"] = data.get("last_indexed_at") or datetime.now().isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _write_text_atomic(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)

    def _write_per_table_indexes(self, tables: List[TableIndex]) -> None:
        target_dirs = [self.workspace_tables_dir]
        if self.svn_tables_dir is not None:
            target_dirs.append(self.svn_tables_dir)
        for target_dir in target_dirs:
            target_dir.mkdir(parents=True, exist_ok=True)
            existing = {path.stem for path in target_dir.glob("*.json")}
            current = set()
            for table in tables:
                current.add(table.table_name)
                content = self._serialize_single_table_index(table)
                self._write_text_atomic(target_dir / f"{table.table_name}.json", content)
            for stale in existing - current:
                try:
                    (target_dir / f"{stale}.json").unlink()
                except FileNotFoundError:
                    pass

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

    def _serialize_registry(self, tables: List[TableIndex], graph: DependencyGraph) -> str:
        tables_json = self._serialize_table_indexes(tables)
        graph_json = self._serialize_dependency_graph(graph)
        tables_sha = hashlib.sha256(tables_json.encode("utf-8")).hexdigest()
        graph_sha = hashlib.sha256(graph_json.encode("utf-8")).hexdigest()
        entries = []
        for t in tables:
            indexed_at = t.last_indexed_at
            entries.append(
                {
                    "name": t.table_name,
                    "path": t.source_path,
                    "hash": t.source_hash,
                    "row_count": t.row_count,
                    "system": t.system,
                    "svn_revision": t.svn_revision,
                    "indexed_at": indexed_at.isoformat() if hasattr(indexed_at, "isoformat") else str(indexed_at),
                }
            )
        data = {
            "schema_version": "registry.v1",
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "tables": entries,
            "dependencies_count": len(graph.edges),
            "integrity": {
                "table_indexes_sha256": tables_sha,
                "dependency_graph_sha256": graph_sha,
            },
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _deserialize_registry(self, s: str) -> Optional[dict]:
        try:
            return json.loads(s)
        except Exception as e:
            logger.error(f"反序列化清单失败: {e}")
            return None

    async def save_table_indexes(
        self,
        tables: List[TableIndex],
        commit_message: Optional[str] = None,
    ) -> bool:
        try:
            content = self._serialize_table_indexes(tables)
            self._write_text_atomic(self.tables_index_file, content)
            self._write_per_table_indexes(tables)
            if self.svn_tables_file:
                self._write_text_atomic(self.svn_tables_file, content)
                msg = commit_message or f"更新表索引 ({len(tables)} tables)"
                if not await self._commit_to_svn([self.svn_tables_file], msg):
                    return False
            return True
        except Exception as e:
            logger.error(f"保存表索引失败: {e}")
            return False

    async def save_dependency_graph(
        self,
        graph: DependencyGraph,
        commit_message: Optional[str] = None,
    ) -> bool:
        try:
            content = self._serialize_dependency_graph(graph)
            self._write_text_atomic(self.dependency_graph_file, content)
            if self.svn_dependency_file:
                self._write_text_atomic(self.svn_dependency_file, content)
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
            self._write_text_atomic(self.changeset_file, content)
            return True
        except Exception as e:
            logger.error(f"保存变更集失败: {e}")
            return False

    async def save_all(
        self,
        tables: List[TableIndex],
        graph: DependencyGraph,
        changeset: ChangeSet,
        commit_message: Optional[str] = None,
    ) -> bool:
        try:
            prev_tables = self.load_table_indexes()
            tj = self._serialize_table_indexes(tables)
            gj = self._serialize_dependency_graph(graph)
            cj = self._serialize_changeset(changeset)
            rj = self._serialize_registry(tables, graph)
            self._write_text_atomic(self.tables_index_file, tj)
            self._write_text_atomic(self.dependency_graph_file, gj)
            self._write_text_atomic(self.changeset_file, cj)
            self._write_text_atomic(self.registry_file, rj)
            self._write_per_table_indexes(tables)
            try:
                diff_and_archive(prev_tables, tables, self.history_dir)
            except Exception as e:
                logger.warning(f"归档历史失败: {e}")
            files = []
            if self.svn_tables_file:
                self._write_text_atomic(self.svn_tables_file, tj)
                files.append(self.svn_tables_file)
            if self.svn_dependency_file:
                self._write_text_atomic(self.svn_dependency_file, gj)
                files.append(self.svn_dependency_file)
            if self.svn_registry_file:
                self._write_text_atomic(self.svn_registry_file, rj)
                files.append(self.svn_registry_file)
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
                logger.warning(f"add 警告: {e}")
            await self.svn.commit(existing, message)
            return True
        except Exception as e:
            logger.error(f"提交失败: {e}")
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

    def load_registry(self) -> Optional[dict]:
        try:
            if self.registry_file.exists():
                return self._deserialize_registry(self.registry_file.read_text(encoding="utf-8"))
            return None
        except Exception as e:
            logger.error(f"加载清单失败: {e}")
            return None
