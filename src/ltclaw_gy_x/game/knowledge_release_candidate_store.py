from __future__ import annotations

import json
from pathlib import Path

from .local_project_paths import normalize_local_project_relative_path
from .models import ReleaseCandidate
from .paths import get_project_store_dir, get_release_candidates_path


VALID_RELEASE_CANDIDATE_STATUSES = ('pending', 'accepted', 'rejected')


class KnowledgeReleaseCandidateStoreError(RuntimeError):
    pass


class KnowledgeReleaseCandidateValidationError(KnowledgeReleaseCandidateStoreError):
    pass


class KnowledgeReleaseCandidateRecordError(KnowledgeReleaseCandidateStoreError):
    pass


def append_release_candidate(project_root: Path, candidate: ReleaseCandidate) -> ReleaseCandidate:
    normalized = _normalize_release_candidate(project_root, candidate)
    target = get_release_candidates_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(normalized.model_dump(mode='json'), ensure_ascii=False) + '\n')
    return normalized


def list_release_candidates(
    project_root: Path,
    *,
    status: str | None = None,
    selected: bool | None = None,
    test_plan_id: str | None = None,
) -> list[ReleaseCandidate]:
    normalized_status = _normalize_status_filter(status)
    normalized_test_plan_id = str(test_plan_id or '').strip() or None
    target = get_release_candidates_path(project_root)
    if not target.exists() or target.stat().st_size == 0:
        return []

    candidates: list[ReleaseCandidate] = []
    with target.open('r', encoding='utf-8') as handle:
        for line_no, line in enumerate(handle, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                candidate = ReleaseCandidate.model_validate(json.loads(payload))
                normalized_candidate = _normalize_release_candidate(project_root, candidate)
                if normalized_status is not None and normalized_candidate.status != normalized_status:
                    continue
                if selected is not None and normalized_candidate.selected is not selected:
                    continue
                if normalized_test_plan_id is not None and normalized_candidate.test_plan_id != normalized_test_plan_id:
                    continue
                candidates.append(normalized_candidate)
            except Exception as exc:  # noqa: BLE001
                raise KnowledgeReleaseCandidateRecordError(
                    f'Invalid release candidate record at line {line_no}: {exc}'
                ) from exc
    candidates.sort(key=lambda candidate: (candidate.created_at, candidate.candidate_id))
    return candidates


def _normalize_release_candidate(project_root: Path, candidate: ReleaseCandidate) -> ReleaseCandidate:
    normalized_candidate_id = str(candidate.candidate_id or '').strip()
    normalized_test_plan_id = str(candidate.test_plan_id or '').strip()
    normalized_title = str(candidate.title or '').strip()
    normalized_source_hash = str(candidate.source_hash or '').strip()

    if not normalized_candidate_id:
        raise KnowledgeReleaseCandidateValidationError('Release candidate id is required')
    if not normalized_test_plan_id:
        raise KnowledgeReleaseCandidateValidationError('Test plan id is required')
    if not normalized_title:
        raise KnowledgeReleaseCandidateValidationError('Release candidate title is required')
    if not normalized_source_hash:
        raise KnowledgeReleaseCandidateValidationError('Release candidate source hash is required')

    normalized_source_refs: list[str] = []
    for source_ref in candidate.source_refs:
        normalized_source_ref = _normalize_relative_path(source_ref)
        if normalized_source_ref not in normalized_source_refs:
            normalized_source_refs.append(normalized_source_ref)

    return candidate.model_copy(
        update={
            'candidate_id': normalized_candidate_id,
            'test_plan_id': normalized_test_plan_id,
            'title': normalized_title,
            'project_key': candidate.project_key or get_project_store_dir(project_root).name,
            'source_refs': normalized_source_refs,
            'source_hash': normalized_source_hash,
        }
    )


def _normalize_status_filter(value: str | None) -> str | None:
    normalized_value = str(value or '').strip()
    if not normalized_value:
        return None
    if normalized_value not in VALID_RELEASE_CANDIDATE_STATUSES:
        raise KnowledgeReleaseCandidateValidationError(
            'Release candidate status must be one of: pending, accepted, rejected'
        )
    return normalized_value


def _normalize_relative_path(value: str) -> str:
    try:
        return normalize_local_project_relative_path(value, error_label='source path')
    except ValueError as exc:
        raise KnowledgeReleaseCandidateValidationError(f'Invalid source path: {value!r}') from exc
