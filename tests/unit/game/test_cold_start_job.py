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
def _isolate_working_dir(monkeypatch, tmp_path):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'working-root'))


def test_save_cold_start_job_keeps_only_latest_twenty(tmp_path):
    # This test uses local project bundle paths and must not read a machine-level workspace pointer.
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    base_time = datetime(2026, 5, 14, tzinfo=timezone.utc)

    for index in range(22):
        state = ColdStartJobState(
            job_id=f'job-{index:02d}',
            project_key='demo-project',
            project_root=str(project_root),
            status='succeeded',
            stage='done',
            progress=100,
            message='finished',
            created_at=base_time + timedelta(seconds=index),
            updated_at=base_time + timedelta(seconds=index),
            finished_at=base_time + timedelta(seconds=index),
        )
        save_cold_start_job(project_root, state)

    jobs_dir = get_project_runtime_build_jobs_dir(project_root)
    remaining = sorted(path.name for path in jobs_dir.glob('*.json'))

    assert len(remaining) == 20
    assert 'job-00.json' not in remaining
    assert 'job-01.json' not in remaining
    assert 'job-21.json' in remaining


def test_cold_start_job_persists_and_reuses_running_job(tmp_path, monkeypatch):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.start', lambda self: None)
    monkeypatch.setattr('ltclaw_gy_x.game.cold_start_job.threading.Thread.is_alive', lambda self: True)

    job, reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    second, second_reused = create_or_get_cold_start_job(project_root, timeout_seconds=30)

    assert reused is False
    assert second_reused is True
    assert second.job_id == job.job_id
    assert get_project_runtime_build_job_path(project_root, job.job_id).exists()
    assert load_cold_start_job(project_root, job.job_id).job_id == job.job_id
    assert job.project_key == get_project_key(project_root)


def test_cancel_cold_start_job_persists_cancelled_state(tmp_path, monkeypatch):
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
