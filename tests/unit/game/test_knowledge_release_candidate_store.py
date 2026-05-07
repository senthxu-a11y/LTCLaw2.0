from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from ltclaw_gy_x.game.knowledge_release_candidate_store import (
    KnowledgeReleaseCandidateRecordError,
    KnowledgeReleaseCandidateValidationError,
    append_release_candidate,
    list_release_candidates,
)
from ltclaw_gy_x.game.models import ReleaseCandidate
from ltclaw_gy_x.game.paths import (
    get_current_release_path,
    get_release_candidates_path,
    get_release_dir,
)


def _candidate(candidate_id: str = 'candidate-001') -> ReleaseCandidate:
    return ReleaseCandidate(
        candidate_id=candidate_id,
        test_plan_id='plan-001',
        status='pending',
        title='Damage tuning candidate',
        source_refs=['Tables/SkillTable.xlsx'],
        source_hash='sha256:test-plan',
        created_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
    )


def _append_candidates(project_root, *candidates: ReleaseCandidate) -> None:
    for candidate in candidates:
        append_release_candidate(project_root, candidate)


def test_append_and_list_release_candidates_roundtrip(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    saved = append_release_candidate(project_root, _candidate())
    listed = list_release_candidates(project_root)

    assert saved.project_key
    assert saved.status == 'pending'
    assert saved.source_refs == ['Tables/SkillTable.xlsx']
    assert len(listed) == 1
    assert listed[0].candidate_id == 'candidate-001'
    assert listed[0].test_plan_id == 'plan-001'
    payload = get_release_candidates_path(project_root).read_text(encoding='utf-8').strip().splitlines()
    assert len(payload) == 1
    record = json.loads(payload[0])
    assert record['project_key'] == saved.project_key
    assert record['status'] == 'pending'
    assert record['source_refs'] == ['Tables/SkillTable.xlsx']


def test_list_release_candidates_returns_empty_when_missing(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    assert list_release_candidates(project_root) == []


def test_list_release_candidates_supports_status_selected_and_test_plan_filters(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    accepted = _candidate('candidate-002').model_copy(
        update={
            'status': 'accepted',
            'selected': True,
            'test_plan_id': 'plan-002',
            'created_at': datetime(2026, 5, 8, tzinfo=timezone.utc),
        }
    )
    rejected = _candidate('candidate-003').model_copy(
        update={
            'status': 'rejected',
            'selected': False,
            'test_plan_id': 'plan-002',
            'created_at': datetime(2026, 5, 9, tzinfo=timezone.utc),
        }
    )
    pending_selected = _candidate('candidate-004').model_copy(
        update={
            'selected': True,
            'test_plan_id': 'plan-001',
            'created_at': datetime(2026, 5, 10, tzinfo=timezone.utc),
        }
    )
    _append_candidates(project_root, pending_selected, rejected, _candidate(), accepted)

    listed = list_release_candidates(project_root)
    pending_only = list_release_candidates(project_root, status='pending')
    selected_only = list_release_candidates(project_root, selected=True)
    plan_only = list_release_candidates(project_root, test_plan_id='plan-002')
    combined = list_release_candidates(project_root, status='accepted', selected=True, test_plan_id='plan-002')

    assert [candidate.candidate_id for candidate in listed] == [
        'candidate-001',
        'candidate-002',
        'candidate-003',
        'candidate-004',
    ]
    assert [candidate.candidate_id for candidate in pending_only] == ['candidate-001', 'candidate-004']
    assert [candidate.candidate_id for candidate in selected_only] == ['candidate-002', 'candidate-004']
    assert [candidate.candidate_id for candidate in plan_only] == ['candidate-002', 'candidate-003']
    assert [candidate.candidate_id for candidate in combined] == ['candidate-002']


def test_list_release_candidates_rejects_invalid_status_filter(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    with pytest.raises(KnowledgeReleaseCandidateValidationError, match='status must be one of'):
        list_release_candidates(project_root, status='draft')


def test_list_release_candidates_does_not_modify_pending_file_or_release_state(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _append_candidates(project_root, _candidate(), _candidate('candidate-002').model_copy(update={'selected': True}))

    target = get_release_candidates_path(project_root)
    before_payload = target.read_text(encoding='utf-8')
    before_mtime_ns = target.stat().st_mtime_ns

    listed = list_release_candidates(project_root, selected=True)

    assert [candidate.candidate_id for candidate in listed] == ['candidate-002']
    assert target.read_text(encoding='utf-8') == before_payload
    assert target.stat().st_mtime_ns == before_mtime_ns
    assert not get_current_release_path(project_root).exists()
    assert not get_release_dir(project_root, 'release-001').exists()
    assert not (project_root / '.svn').exists()


@pytest.mark.parametrize(
    'source_path',
    ['../Secrets.xlsx', '..\\Secrets.xlsx', 'C:/abs/path.xlsx', 'C:\\abs\\path.xlsx', '/abs/path.xlsx'],
)
def test_append_rejects_release_candidate_source_path_escape(monkeypatch, tmp_path, source_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    candidate = _candidate()
    candidate.source_refs = [source_path]

    with pytest.raises(KnowledgeReleaseCandidateValidationError, match='Invalid source path'):
        append_release_candidate(project_root, candidate)


def test_append_writes_only_pending_candidate_store(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    append_release_candidate(project_root, _candidate())

    assert get_release_candidates_path(project_root).exists()
    assert not get_release_dir(project_root, 'release-001').exists()
    assert not get_current_release_path(project_root).exists()
    assert not (project_root / '.svn').exists()


def test_list_release_candidates_fails_clearly_on_bad_jsonl_line(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    target = get_release_candidates_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{bad json}\n', encoding='utf-8')

    with pytest.raises(KnowledgeReleaseCandidateRecordError, match='Invalid release candidate record at line 1'):
        list_release_candidates(project_root)
