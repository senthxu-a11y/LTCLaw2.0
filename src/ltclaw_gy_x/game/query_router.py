"""
Query router for game development data
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from .models import (
    TableIndex, FieldInfo, DependencyGraph, SystemGroup,
    FieldPatch,
)
from .paths import (
    get_dependency_graph_path,
    get_project_raw_table_index_path,
    get_project_raw_tables_dir,
    get_tables_dir,
)


class QueryRouter:
    def __init__(self, svc):
        self.service = svc
        self._table_cache: dict = {}
        self._cache_timestamps: dict = {}

    def _has_project_root(self) -> bool:
        return self._project_root() is not None

    async def list_systems(self) -> List[SystemGroup]:
        if not self._has_project_root():
            return []
        return []

    async def list_tables(self, system: Optional[str] = None, query: Optional[str] = None,
                          page: int = 1, size: int = 50) -> Dict[str, Any]:
        if not self._has_project_root():
            return {"items": [], "total": 0, "page": page, "size": size}
        try:
            project_root = self._project_root()
            if project_root is None:
                return {"items": [], "total": 0, "page": page, "size": size}
            tables = []
            for table_file in self._table_index_files(project_root):
                try:
                    table_index = await self._load_table_from_file(table_file)
                    if table_index:
                        if system and table_index.system != system:
                            continue
                        if query and query.lower() not in table_index.table_name.lower():
                            continue
                        tables.append(table_index)
                except Exception:
                    continue
            tables.sort(key=lambda item: item.table_name)
            total = len(tables)
            start = (page - 1) * size
            end = start + size
            items = tables[start:end]
            return {
                "items": [item.model_dump(mode="json") for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except Exception as e:
            return {"items": [], "total": 0, "page": page, "size": size, "error": str(e)}

    async def get_table(self, name: str) -> Optional[TableIndex]:
        if not self._has_project_root():
            return None
        try:
            project_root = self._project_root()
            if project_root is None:
                return None
            table_file = get_tables_dir(project_root) / f"{name}.json"
            if table_file.exists():
                return await self._load_table_from_file(table_file)
            raw_table_file = get_project_raw_table_index_path(project_root, name)
            if raw_table_file.exists():
                return await self._load_table_from_file(raw_table_file)
            return None
        except Exception:
            return None

    async def fields_of_table(self, table: str) -> List[FieldInfo]:
        table_index = await self.get_table(table)
        return table_index.fields if table_index else []

    async def find_field(self, field_name: str) -> List[Tuple[str, FieldInfo]]:
        if not self._has_project_root():
            return []
        results = []
        try:
            project_root = self._project_root()
            if project_root is None:
                return []
            for table_file in self._table_index_files(project_root):
                try:
                    table_index = await self._load_table_from_file(table_file)
                    if table_index:
                        for field in table_index.fields:
                            if field_name.lower() in field.name.lower():
                                results.append((table_index.table_name, field))
                except Exception:
                    continue
        except Exception:
            pass
        return results

    async def dependencies_of(self, table: str) -> Dict[str, Any]:
        if not self._has_project_root():
            return {"upstream": [], "downstream": []}
        try:
            project_root = self._project_root()
            if project_root is None:
                return {"upstream": [], "downstream": []}
            dep_file = get_dependency_graph_path(project_root)
            if not dep_file.exists():
                return {"upstream": [], "downstream": []}
            with open(dep_file, "r", encoding="utf-8") as file_obj:
                dep_graph = DependencyGraph.model_validate_json(file_obj.read())
            upstream = []
            downstream = []
            for edge in dep_graph.edges:
                if edge.to_table == table:
                    upstream.append({
                        "table": edge.from_table,
                        "field": edge.from_field,
                        "target_field": edge.to_field,
                        "confidence": edge.confidence,
                    })
                elif edge.from_table == table:
                    downstream.append({
                        "table": edge.to_table,
                        "field": edge.to_field,
                        "source_field": edge.from_field,
                        "confidence": edge.confidence,
                    })
            return {"upstream": upstream, "downstream": downstream}
        except Exception:
            return {"upstream": [], "downstream": []}

    async def patch_field(self, table: str, field: str, patch: FieldPatch) -> Optional[FieldInfo]:
        if not self._has_project_root():
            return None
        try:
            project_root = self._project_root()
            if project_root is None:
                return None
            table_file = get_tables_dir(project_root) / f"{table}.json"
            if not table_file.exists():
                return None
            table_index = await self._load_table_from_file(table_file)
            if not table_index:
                return None
            field_found = None
            for field_info in table_index.fields:
                if field_info.name == field:
                    field_found = field_info
                    if patch.description is not None:
                        field_info.description = patch.description
                    if patch.confidence is not None:
                        field_info.confidence = patch.confidence
                    if patch.confirmed_by is not None:
                        field_info.confirmed_by = patch.confirmed_by
                        field_info.confirmed_at = datetime.now()
                    break
            if not field_found:
                return None
            temp_file = table_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as file_obj:
                file_obj.write(table_index.model_dump_json(indent=2))
            temp_file.replace(table_file)
            return field_found
        except Exception:
            return None

    async def query(self, q: str, mode: str = "auto") -> Dict[str, Any]:
        if not self._has_project_root():
            return {"mode": "not_configured", "results": []}
        if mode == "auto":
            table_results = await self.list_tables(query=q, page=1, size=10)
            if table_results["total"] > 0:
                return {"mode": "exact_table", "results": table_results["items"]}
            field_results = await self.find_field(q)
            if field_results:
                return {
                    "mode": "exact_field",
                    "results": [
                        {"table": table, "field": field.model_dump(mode="json")}
                        for table, field in field_results
                    ],
                }
        return {"mode": "semantic_stub", "results": []}

    async def _load_table_from_file(self, table_file: Path) -> Optional[TableIndex]:
        try:
            mtime = table_file.stat().st_mtime
            key = str(table_file)
            if (key in self._table_cache and key in self._cache_timestamps
                    and self._cache_timestamps[key] >= mtime):
                return self._table_cache[key]
            with open(table_file, "r", encoding="utf-8") as file_obj:
                table_index = TableIndex.model_validate_json(file_obj.read())
            self._table_cache[key] = table_index
            self._cache_timestamps[key] = mtime
            return table_index
        except Exception:
            return None

    def _project_root(self) -> Path | None:
        runtime_root = getattr(self.service, "_runtime_svn_root", None)
        if callable(runtime_root):
            resolved = runtime_root()
            if resolved is not None:
                return Path(resolved)

        user_config = getattr(self.service, "user_config", None)
        local_root = getattr(user_config, "svn_local_root", None)
        if local_root:
            return Path(local_root)

        project_config = getattr(self.service, "project_config", None)
        svn_config = getattr(project_config, "svn", None)
        svn_root = getattr(svn_config, "root", None)
        if svn_root:
            return Path(svn_root)
        return None

    def _table_index_files(self, project_root: Path) -> list[Path]:
        legacy_table_dir = get_tables_dir(project_root)
        legacy_files = sorted(legacy_table_dir.glob("*.json")) if legacy_table_dir.exists() else []
        if legacy_files:
            return legacy_files

        raw_tables_dir = get_project_raw_tables_dir(project_root)
        if not raw_tables_dir.exists():
            return []
        return sorted(raw_tables_dir.glob("*.json"))