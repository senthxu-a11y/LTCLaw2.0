from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from .config import DEFAULT_SCRIPTS_EXCLUDE_PATTERNS, ProjectScriptsSourceConfig


AVAILABLE_SCRIPT_FORMATS: dict[str, str] = {
    '.cs': 'csharp',
    '.lua': 'lua',
    '.py': 'python',
}

COLD_START_SUPPORTED_SCRIPT_FORMATS: frozenset[str] = frozenset({'csharp', 'lua', 'python'})


def _normalize_path_for_match(path: str) -> str:
    return path.replace('\\', '/').strip('/')


def _matches_any(path: str, patterns: list[str]) -> bool:
    normalized = _normalize_path_for_match(path).lower()
    return any(fnmatch(normalized, _normalize_path_for_match(pattern).lower()) for pattern in patterns)


def _entry(source_path: str, fmt: str, status: str, reason: str) -> dict:
    cold_start_supported = fmt in COLD_START_SUPPORTED_SCRIPT_FORMATS and status == 'available'
    cold_start_reason = (
        f'rule_only_supported_{fmt}'
        if cold_start_supported
        else f'rule_only_cold_start_not_supported_for_{fmt}'
    )
    return {
        'source_path': _normalize_path_for_match(source_path),
        'format': fmt,
        'status': status,
        'reason': reason,
        'cold_start_supported': cold_start_supported,
        'cold_start_reason': cold_start_reason,
    }


def discover_script_sources(project_root: Path | None, scripts_config: ProjectScriptsSourceConfig | None) -> dict:
    project_root_value = str(project_root) if project_root is not None else None
    empty_payload = {
        'success': False,
        'project_root': project_root_value,
        'script_files': [],
        'excluded_files': [],
        'unsupported_files': [],
        'errors': [],
        'summary': {
            'discovered_script_count': 0,
            'available_script_count': 0,
            'excluded_script_count': 0,
            'unsupported_script_count': 0,
            'error_count': 0,
        },
        'next_action': 'configure_scripts_source',
    }
    if project_root is None:
        empty_payload['errors'].append({'reason': 'project_root_not_configured'})
        empty_payload['summary']['error_count'] = len(empty_payload['errors'])
        return empty_payload
    if not project_root.exists():
        empty_payload['errors'].append({'source_path': str(project_root), 'reason': 'project_root_missing'})
        empty_payload['summary']['error_count'] = len(empty_payload['errors'])
        return empty_payload

    effective_config = scripts_config or ProjectScriptsSourceConfig()
    if not effective_config.roots:
        empty_payload['errors'].append({'reason': 'scripts_roots_not_configured'})
        empty_payload['summary']['error_count'] = len(empty_payload['errors'])
        return empty_payload

    include_patterns = [pattern.strip() for pattern in effective_config.include if pattern.strip()]
    exclude_patterns = list(dict.fromkeys([*DEFAULT_SCRIPTS_EXCLUDE_PATTERNS, *effective_config.exclude]))

    script_files: list[dict] = []
    excluded_files: list[dict] = []
    errors: list[dict] = []
    seen_paths: set[str] = set()

    for configured_root in effective_config.roots:
        root_value = str(configured_root or '').strip()
        if not root_value:
            continue
        normalized_root_value = root_value.replace('\\', '/')
        root_path = Path(normalized_root_value).expanduser()
        if not root_path.is_absolute():
            root_path = project_root / normalized_root_value
        if not root_path.exists():
            errors.append({'source_path': _normalize_path_for_match(root_value), 'reason': 'source_root_missing'})
            continue
        if not root_path.is_dir():
            errors.append({'source_path': _normalize_path_for_match(root_value), 'reason': 'source_root_not_directory'})
            continue

        for file_path in root_path.rglob('*'):
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
                excluded_files.append(
                    _entry(normalized_path, file_path.suffix.lower().lstrip('.') or 'unknown', 'excluded', 'matched_exclude_pattern')
                )
                seen_paths.add(normalized_path)
                continue
            if include_patterns and not _matches_any(normalized_path, include_patterns):
                continue
            suffix = file_path.suffix.lower()
            fmt = AVAILABLE_SCRIPT_FORMATS.get(suffix)
            if fmt is None:
                continue
            script_files.append(_entry(normalized_path, fmt, 'available', 'matched_supported_format'))
            seen_paths.add(normalized_path)

    available_count = sum(1 for item in script_files if item['cold_start_supported'])
    return {
        'success': len(errors) == 0,
        'project_root': str(project_root),
        'script_files': script_files,
        'excluded_files': excluded_files,
        'unsupported_files': [],
        'errors': errors,
        'summary': {
            'discovered_script_count': len(script_files),
            'available_script_count': available_count,
            'excluded_script_count': len(excluded_files),
            'unsupported_script_count': 0,
            'error_count': len(errors),
        },
        'next_action': 'run_script_index' if available_count > 0 else 'configure_scripts_source',
    }
