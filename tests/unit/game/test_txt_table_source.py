from __future__ import annotations

import time

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.source_discovery import discover_table_sources
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate


def _write_txt_sources(project_root) -> None:
    tables_dir = project_root / 'Tables'
    docs_dir = project_root / 'Docs'
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'EnemyConfig.txt').write_text(
        '# Enemy config table\n\n'
        '// generated from design sheet\n'
        'ID\tName\tHP\tAttack\n'
        '2001\tSlime\t30\t5\n'
        '\n'
        '2002\tGoblin\t50\t8\n',
        encoding='utf-8',
    )
    (docs_dir / 'CharacterGrowth.txt').write_text(
        'Character Growth Design\n\nOverview\nCharacters grow by increasing level.\n',
        encoding='utf-8',
    )


def test_discover_table_sources_marks_txt_available_for_rule_only(tmp_path):
    project_root = tmp_path / 'project-root'
    _write_txt_sources(project_root)

    result = discover_table_sources(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.txt'],
            exclude=[],
            header_row=1,
            primary_key_candidates=['ID'],
        ),
    )

    assert result['table_files'] == [
        {
            'source_path': 'Tables/EnemyConfig.txt',
            'format': 'txt',
            'status': 'available',
            'reason': 'matched_supported_format',
            'cold_start_supported': True,
            'cold_start_reason': 'rule_only_supported_txt',
        }
    ]
    assert result['summary']['available_table_count'] == 1
    assert result['next_action'] == 'run_raw_index'


def test_txt_document_is_not_discovered_as_table_when_tables_root_is_explicit(tmp_path):
    project_root = tmp_path / 'project-root'
    _write_txt_sources(project_root)

    table_discovery = discover_table_sources(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.txt'],
            exclude=[],
            header_row=1,
            primary_key_candidates=['ID'],
        ),
    )

    assert [item['source_path'] for item in table_discovery['table_files']] == ['Tables/EnemyConfig.txt']
    assert all(item['source_path'] != 'Docs/CharacterGrowth.txt' for item in table_discovery['table_files'])


def test_txt_table_cold_start_pipeline_builds_candidate(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_txt_sources(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.txt'],
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
    assert state.counts.discovered_table_count == 1
    assert state.counts.raw_table_index_count == 1
    assert state.counts.canonical_table_count == 1
    assert state.counts.candidate_table_count == 1
    assert state.candidate_refs == ['table:EnemyConfig']

    candidate = load_latest_source_candidate(project_root)
    assert candidate is not None
    assert candidate.map is not None
    assert [table.table_id for table in candidate.map.tables] == ['EnemyConfig']
