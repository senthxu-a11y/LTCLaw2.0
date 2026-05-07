from __future__ import annotations

from pathlib import Path
from typing import Any


def normalize_local_project_relative_path(value: Any, *, error_label: str = 'local project relative path') -> str:
    raw_value = str(value or '').strip()
    if not raw_value or raw_value.startswith(('/', '\\')) or _has_windows_drive_prefix(raw_value):
        raise ValueError(f'Invalid {error_label}: {value!r}')

    candidate = Path(raw_value.replace('\\', '/'))
    if not candidate.parts or candidate.is_absolute():
        raise ValueError(f'Invalid {error_label}: {value!r}')

    normalized_parts = [part for part in candidate.parts if part not in ('', '.')]
    if not normalized_parts or any(part == '..' for part in normalized_parts):
        raise ValueError(f'Invalid {error_label}: {value!r}')
    return Path(*normalized_parts).as_posix()


def _has_windows_drive_prefix(value: str) -> bool:
    return len(value) >= 2 and value[0].isalpha() and value[1] == ':'
