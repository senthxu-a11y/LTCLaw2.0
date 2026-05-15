from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import KnowledgeMapCandidateResult
from .paths import (
    get_project_candidate_map_history_dir,
    get_project_candidate_map_path,
    get_project_latest_map_diff_path,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + '.tmp')
    temp_path.write_text(content, encoding='utf-8')
    temp_path.replace(path)


def _safe_job_id(job_id: str) -> str:
    safe = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '-' for ch in str(job_id or ''))
    return safe.strip('-') or 'job'


def _candidate_refs(candidate: KnowledgeMapCandidateResult) -> list[str]:
    if candidate.map is None:
        return []
    return sorted(f'table:{table.table_id}' for table in candidate.map.tables)


def save_latest_source_candidate(
    project_root: Path,
    candidate: KnowledgeMapCandidateResult,
    *,
    job_id: str,
) -> Path:
    if candidate.map is None:
        raise ValueError('candidate.map is required')

    now_iso = _now_iso()
    payload = {
        'version': '1.0',
        'job_id': job_id,
        'created_at': now_iso,
        'candidate': candidate.model_dump(mode='json'),
        'candidate_table_count': len(candidate.map.tables),
        'candidate_refs': _candidate_refs(candidate),
    }
    content = json.dumps(payload, indent=2, ensure_ascii=False)

    latest_path = get_project_candidate_map_path(project_root)
    _write_text_atomic(latest_path, content)

    history_path = get_project_candidate_map_history_dir(project_root) / f"{now_iso.replace(':', '-')}-{_safe_job_id(job_id)}.json"
    _write_text_atomic(history_path, content)

    if candidate.diff_review is not None:
        _write_text_atomic(
            get_project_latest_map_diff_path(project_root),
            candidate.diff_review.model_dump_json(indent=2),
        )

    return latest_path


def load_latest_source_candidate(project_root: Path) -> KnowledgeMapCandidateResult | None:
    path = get_project_candidate_map_path(project_root)
    if not path.exists() or not path.is_file():
        return None

    payload = json.loads(path.read_text(encoding='utf-8'))
    candidate_payload = payload.get('candidate')
    if candidate_payload is None:
        return None
    return KnowledgeMapCandidateResult.model_validate(candidate_payload)