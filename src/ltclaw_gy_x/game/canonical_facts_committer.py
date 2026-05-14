from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .canonical_facts import build_canonical_table_schema
from .models import CanonicalTableSchema, TableIndex
from .paths import (
    get_project_canonical_table_schema_path,
    get_project_canonical_tables_dir,
    get_project_raw_table_indexes_path,
)


@dataclass(slots=True)
class CanonicalCommitError:
    raw_index_file: str
    error: str
    table_id: str | None = None


@dataclass(slots=True)
class CanonicalTablesCommitResult:
    raw_table_index_count: int
    canonical_table_count: int
    written: list[str] = field(default_factory=list)
    errors: list[CanonicalCommitError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CanonicalFactsCommitter:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).expanduser()

    def rebuild_tables(self, *, force: bool = False) -> CanonicalTablesCommitResult:
        raw_table_indexes_path = get_project_raw_table_indexes_path(self.project_root)
        canonical_tables_dir = get_project_canonical_tables_dir(self.project_root)

        result = CanonicalTablesCommitResult(
            raw_table_index_count=0,
            canonical_table_count=0,
        )

        table_entries = self._load_raw_table_index_entries(raw_table_indexes_path, result)
        result.raw_table_index_count = len(table_entries)
        if result.errors:
            return result
        if not table_entries:
            result.errors.append(
                CanonicalCommitError(
                    raw_index_file=raw_table_indexes_path.name,
                    error=f'No raw table indexes found: {raw_table_indexes_path}',
                )
            )
            return result

        canonical_tables_dir.mkdir(parents=True, exist_ok=True)

        for entry in table_entries:
            raw_index_file_name = self._raw_index_file_name(entry)
            try:
                table_index = TableIndex.model_validate(entry)
                canonical_schema = build_canonical_table_schema(table_index)
                target_path = get_project_canonical_table_schema_path(self.project_root, canonical_schema.table_id)
                if not force and self._is_up_to_date(target_path, canonical_schema.source_hash):
                    continue
                self._write_json_atomic(target_path, canonical_schema.model_dump(mode='json'))
                result.written.append(target_path.name)
            except Exception as exc:
                result.errors.append(
                    CanonicalCommitError(
                        raw_index_file=raw_index_file_name,
                        table_id=self._safe_table_id(entry),
                        error=str(exc),
                    )
                )

        result.canonical_table_count = self._count_valid_canonical_tables(canonical_tables_dir)
        return result

    def _is_up_to_date(self, target_path: Path, source_hash: str) -> bool:
        if not target_path.exists():
            return False
        try:
            current = CanonicalTableSchema.model_validate_json(target_path.read_text(encoding='utf-8'))
        except Exception:
            return False
        return current.source_hash == source_hash

    def _count_valid_canonical_tables(self, canonical_tables_dir: Path) -> int:
        count = 0
        for file_path in canonical_tables_dir.glob('*.json'):
            try:
                CanonicalTableSchema.model_validate_json(file_path.read_text(encoding='utf-8'))
            except Exception:
                continue
            count += 1
        return count

    def _write_json_atomic(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            handle.write(text)
            tmp_path = Path(handle.name)
        try:
            tmp_path.replace(path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

    def _load_raw_table_index_entries(
        self,
        raw_table_indexes_path: Path,
        result: CanonicalTablesCommitResult,
    ) -> list[dict[str, Any]]:
        if not raw_table_indexes_path.exists():
            result.errors.append(
                CanonicalCommitError(
                    raw_index_file=raw_table_indexes_path.name,
                    error=f'Raw table indexes file does not exist: {raw_table_indexes_path}',
                )
            )
            return []
        try:
            payload = json.loads(raw_table_indexes_path.read_text(encoding='utf-8'))
        except Exception as exc:
            result.errors.append(
                CanonicalCommitError(
                    raw_index_file=raw_table_indexes_path.name,
                    error=f'Failed to parse raw table indexes: {exc}',
                )
            )
            return []
        table_entries = payload.get('tables') if isinstance(payload, dict) else None
        if not isinstance(table_entries, list):
            result.errors.append(
                CanonicalCommitError(
                    raw_index_file=raw_table_indexes_path.name,
                    error=f'Invalid raw table indexes payload: {raw_table_indexes_path}',
                )
            )
            return []
        normalized_entries: list[dict[str, Any]] = []
        for entry in table_entries:
            if isinstance(entry, dict):
                normalized_entries.append(entry)
            else:
                normalized_entries.append({'table_name': None, '__invalid_entry__': entry})
        return normalized_entries

    def _raw_index_file_name(self, raw_entry: dict[str, Any]) -> str:
        table_id = self._safe_table_id(raw_entry)
        return f'{table_id}.json' if table_id else 'unknown.json'

    def _safe_table_id(self, raw_entry: dict[str, Any]) -> str | None:
        try:
            table_name = raw_entry.get('table_name') if isinstance(raw_entry, dict) else None
        except Exception:
            return None
        return str(table_name).strip() or None