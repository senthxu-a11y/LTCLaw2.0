from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ltclaw_gy_x.game.cold_start_job import (
    ColdStartJobState,
    cancel_cold_start_job,
    create_or_get_cold_start_job,
    load_cold_start_job,
    save_cold_start_job,
)
from ltclaw_gy_x.game.paths import get_project_key, get_project_runtime_build_job_path, get_project_runtime_build_jobs_dir


@pytest.fixture(autouse=True)
def _isolated_working_dir(monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'working-root'))
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job._ACTIVE_JOB_HANDLES', {})


def test_create_get_and_persist_cold_start_job(tmp_path, monkeypatch):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.start', lambda self: None)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.is_alive', lambda self: True)

    job, reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    loaded = load_cold_start_job(project_root, job.job_id)

    assert reused is False
    assert loaded is not None
    assert loaded.job_id == job.job_id
    assert loaded.project_key == get_project_key(project_root)
    assert get_project_runtime_build_job_path(project_root, job.job_id).exists()


def test_reuses_existing_running_job_for_same_project(tmp_path, monkeypatch):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.start', lambda self: None)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.is_alive', lambda self: True)

    first, first_reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    second, second_reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)

    assert first_reused is False
    assert second_reused is True
    assert second.job_id == first.job_id


def test_active_job_is_isolated_by_project_key(tmp_path, monkeypatch):
    project_a = tmp_path / 'project-a'
    project_b = tmp_path / 'project-b'
    project_a.mkdir(parents=True)
    project_b.mkdir(parents=True)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.start', lambda self: None)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.is_alive', lambda self: True)

    job_a, _ = create_or_get_cold_start_job(project_a, timeout_seconds=30)
    job_b, reused_b = create_or_get_cold_start_job(project_b, timeout_seconds=30)

    assert reused_b is False
    assert job_a.job_id != job_b.job_id
    assert job_a.project_key != job_b.project_key


def test_cancel_persists_cancelled_state(tmp_path, monkeypatch):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.start', lambda self: None)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.is_alive', lambda self: True)

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    cancelled = cancel_cold_start_job(project_root, job.job_id)
    reloaded = load_cold_start_job(project_root, job.job_id)

    assert cancelled is not None
    assert cancelled.status == 'cancelled'
    assert cancelled.stage == 'cancelled'
    assert reloaded is not None
    assert reloaded.status == 'cancelled'


def test_terminal_states_remain_readable_after_refresh(tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)

    for status, stage in [('succeeded', 'done'), ('failed', 'failed'), ('cancelled', 'cancelled')]:
        state = ColdStartJobState(
            job_id=f'{status}-job',
            project_key=get_project_key(project_root),
            project_root=str(project_root),
            status=status,
            stage=stage,
            progress=100 if status == 'succeeded' else 20,
            message=status,
            finished_at=datetime.now(timezone.utc),
        )
        save_cold_start_job(project_root, state)
        loaded = load_cold_start_job(project_root, state.job_id)
        assert loaded is not None
        assert loaded.status == status


def test_prunes_to_latest_twenty_jobs(tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    base_time = datetime(2026, 5, 14, tzinfo=timezone.utc)

    for index in range(22):
        save_cold_start_job(
            project_root,
            ColdStartJobState(
                job_id=f'job-{index:02d}',
                project_key=get_project_key(project_root),
                project_root=str(project_root),
                status='succeeded',
                stage='done',
                progress=100,
                message='finished',
                created_at=base_time + timedelta(seconds=index),
                updated_at=base_time + timedelta(seconds=index),
                finished_at=base_time + timedelta(seconds=index),
            ),
        )

    remaining = sorted(path.name for path in get_project_runtime_build_jobs_dir(project_root).glob('*.json'))
    assert len(remaining) == 20
    assert 'job-00.json' not in remaining
    assert 'job-01.json' not in remaining
    assert 'job-21.json' in remaining
