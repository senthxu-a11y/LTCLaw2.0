from __future__ import annotations

from datetime import datetime, timezone

from ltclaw_gy_x.game.cold_start_job import (
    ColdStartJobState,
    load_cold_start_job_with_stale_check,
    save_cold_start_job,
)


def test_load_cold_start_job_with_stale_check_marks_orphaned_running_job_failed(tmp_path):
    project_root = tmp_path / 'project-root'
    project_root.mkdir(parents=True)
    state = ColdStartJobState(
        job_id='job-stale',
        project_key='demo-project',
        project_root=str(project_root),
        status='running',
        stage='building_candidate_map',
        progress=80,
        message='Still running',
        next_action='build_candidate_from_source',
        created_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
    )
    save_cold_start_job(project_root, state)

    stale_state = load_cold_start_job_with_stale_check(project_root, 'job-stale')

    assert stale_state is not None
    assert stale_state.status == 'failed'
    assert stale_state.stage == 'stale'
    assert stale_state.next_action == 'retry_cold_start_job'
    assert stale_state.finished_at is not None
    assert stale_state.errors[-1].stage == 'stale'
    assert stale_state.errors[-1].error == 'cold_start_job_handle_missing'