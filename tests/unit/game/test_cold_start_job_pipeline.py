from __future__ import annotations

import time
from pathlib import Path

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.paths import (
    get_project_canonical_table_schema_path,
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_raw_table_index_path,
)


def _write_minimal_hero_table(project_root: Path) -> None:
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )


def test_cold_start_job_pipeline_succeeds_for_single_csv_rule_only(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_minimal_hero_table(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.csv'],
            exclude=[],
            header_row=1,
            primary_key_candidates=['ID'],
        ),
    )

    job, reused_existing = create_or_get_cold_start_job(project_root, timeout_seconds=30)

    assert reused_existing is False

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        state = load_cold_start_job(project_root, job.job_id)
        assert state is not None
        if state.status in {'succeeded', 'failed', 'cancelled'}:
            break
        time.sleep(0.05)
    else:
        raise AssertionError('cold-start job did not reach terminal state in time')

    assert state.status == 'succeeded'
    assert state.stage == 'done'
    assert state.progress == 100
    assert state.counts.discovered_table_count == 1
    assert state.counts.raw_table_index_count == 1
    assert state.counts.canonical_table_count == 1
    assert state.counts.candidate_table_count == 1
    assert state.candidate_refs == ['table:HeroTable']

    assert get_project_raw_table_index_path(project_root, 'HeroTable').exists()
    assert get_project_canonical_table_schema_path(project_root, 'HeroTable').exists()
    assert not get_project_formal_map_canonical_path(project_root).exists()
    assert not get_project_current_release_path(project_root).exists()