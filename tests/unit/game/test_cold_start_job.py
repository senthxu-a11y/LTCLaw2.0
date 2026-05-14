from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ltclaw_gy_x.game.cold_start_job import ColdStartJobState, save_cold_start_job
from ltclaw_gy_x.game.paths import get_project_runtime_build_jobs_dir


def test_save_cold_start_job_keeps_only_latest_twenty(tmp_path):
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