from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from .config import DEFAULT_TABLES_EXCLUDE_PATTERNS, ProjectTablesSourceConfig


AVAILABLE_TABLE_FORMATS: dict[str, str] = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".txt": "txt",
}

COLD_START_SUPPORTED_FORMATS: frozenset[str] = frozenset({"csv"})

UNSUPPORTED_TABLE_FORMATS: dict[str, str] = {
    ".xls": "xls",
}


def _normalize_path_for_match(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _matches_any(path: str, patterns: list[str]) -> bool:
    normalized = _normalize_path_for_match(path).lower()
    return any(fnmatch(normalized, _normalize_path_for_match(pattern).lower()) for pattern in patterns)


def _classify_format(path: Path) -> tuple[str | None, str | None]:
    suffix = path.suffix.lower()
    if suffix in AVAILABLE_TABLE_FORMATS:
        return AVAILABLE_TABLE_FORMATS[suffix], "available"
    if suffix in UNSUPPORTED_TABLE_FORMATS:
        return UNSUPPORTED_TABLE_FORMATS[suffix], "unsupported"
    return None, None


def _entry(source_path: str, fmt: str, status: str, reason: str) -> dict:
    cold_start_supported = fmt in COLD_START_SUPPORTED_FORMATS and status == "available"
    cold_start_reason = "rule_only_supported_csv" if cold_start_supported else f"rule_only_cold_start_not_supported_for_{fmt}"
    return {
        "source_path": _normalize_path_for_match(source_path),
        "format": fmt,
        "status": status,
        "reason": reason,
        "cold_start_supported": cold_start_supported,
        "cold_start_reason": cold_start_reason,
    }


def discover_table_sources(project_root: Path | None, tables_config: ProjectTablesSourceConfig | None) -> dict:
    project_root_value = str(project_root) if project_root is not None else None
    empty_payload = {
        "success": False,
        "project_root": project_root_value,
        "roots": [],
        "table_files": [],
        "excluded_files": [],
        "unsupported_files": [],
        "errors": [],
        "summary": {
            "discovered_table_count": 0,
            "available_table_count": 0,
            "excluded_table_count": 0,
            "unsupported_table_count": 0,
            "error_count": 0,
        },
        "next_action": "configure_tables_source",
    }
    if project_root is None:
        empty_payload["errors"].append({"reason": "project_root_not_configured"})
        empty_payload["summary"]["error_count"] = len(empty_payload["errors"])
        return empty_payload
    if not project_root.exists():
        empty_payload["errors"].append({"source_path": str(project_root), "reason": "project_root_missing"})
        empty_payload["summary"]["error_count"] = len(empty_payload["errors"])
        return empty_payload

    effective_config = tables_config or ProjectTablesSourceConfig()
    if not effective_config.roots:
        empty_payload.update({"project_root": str(project_root)})
        empty_payload["errors"].append({"reason": "tables_roots_not_configured"})
        empty_payload["summary"]["error_count"] = len(empty_payload["errors"])
        return empty_payload

    include_patterns = [pattern.strip() for pattern in effective_config.include if pattern.strip()]
    exclude_patterns = list(dict.fromkeys([*DEFAULT_TABLES_EXCLUDE_PATTERNS, *effective_config.exclude]))

    table_files: list[dict] = []
    excluded_files: list[dict] = []
    unsupported_files: list[dict] = []
    errors: list[dict] = []
    root_entries: list[dict] = []
    seen_paths: set[str] = set()

    for configured_root in effective_config.roots:
        root_value = str(configured_root or "").strip()
        if not root_value:
            continue
        normalized_root_value = root_value.replace("\\", "/")
        root_path = Path(normalized_root_value).expanduser()
        if not root_path.is_absolute():
            root_path = project_root / normalized_root_value
        root_entries.append(
            {
                "configured_root": _normalize_path_for_match(root_value),
                "resolved_root": root_path.as_posix(),
                "exists": root_path.exists(),
                "is_directory": root_path.is_dir(),
            }
        )
        if not root_path.exists():
            errors.append({"source_path": _normalize_path_for_match(root_value), "reason": "source_root_missing"})
            continue
        if not root_path.is_dir():
            errors.append({"source_path": _normalize_path_for_match(root_value), "reason": "source_root_not_directory"})
            continue

        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                relative_path = file_path.relative_to(project_root).as_posix()
            except ValueError:
                relative_path = file_path.as_posix()
            normalized_path = _normalize_path_for_match(relative_path)
            if normalized_path in seen_paths:
                continue
            if _matches_any(normalized_path, exclude_patterns):
                fmt = file_path.suffix.lower().lstrip(".") or "unknown"
                excluded_files.append(_entry(normalized_path, fmt, "excluded", "matched_exclude_pattern"))
                seen_paths.add(normalized_path)
                continue
            if include_patterns and not _matches_any(normalized_path, include_patterns):
                continue

            fmt, status = _classify_format(file_path)
            if status == "available" and fmt is not None:
                table_status = "available" if fmt in COLD_START_SUPPORTED_FORMATS else "recognized"
                table_reason = "matched_supported_format" if table_status == "available" else "matched_recognized_format"
                table_files.append(_entry(normalized_path, fmt, table_status, table_reason))
                seen_paths.add(normalized_path)
                continue
            if status == "unsupported" and fmt is not None:
                unsupported_entry = _entry(normalized_path, fmt, "unsupported", "xls_format_not_supported")
                table_files.append(unsupported_entry)
                unsupported_files.append(unsupported_entry)
                seen_paths.add(normalized_path)

    available_count = sum(1 for item in table_files if item["cold_start_supported"])
    payload = {
        "success": len(errors) == 0,
        "project_root": str(project_root),
        "roots": root_entries,
        "table_files": table_files,
        "excluded_files": excluded_files,
        "unsupported_files": unsupported_files,
        "errors": errors,
        "summary": {
            "discovered_table_count": len(table_files),
            "available_table_count": available_count,
            "excluded_table_count": len(excluded_files),
            "unsupported_table_count": len(unsupported_files),
            "error_count": len(errors),
        },
        "next_action": "run_raw_index" if available_count > 0 else "configure_tables_source",
    }
    return payload