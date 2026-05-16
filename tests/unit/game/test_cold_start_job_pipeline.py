from __future__ import annotations

import time
from pathlib import Path

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import (
    ProjectDocsSourceConfig,
    ProjectScriptsSourceConfig,
    ProjectTablesSourceConfig,
    save_project_docs_source_config,
    save_project_scripts_source_config,
    save_project_tables_source_config,
)
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate
from ltclaw_gy_x.game.paths import (
    get_project_candidate_map_path,
    get_project_canonical_table_schema_path,
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_latest_map_diff_path,
    get_project_raw_table_index_path,
)


def _write_minimal_hero_table(project_root: Path) -> None:
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )


def _await_terminal_state(project_root: Path, job_id: str):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        state = load_cold_start_job(project_root, job_id)
        assert state is not None
        if state.status in {'succeeded', 'failed', 'cancelled'}:
            return state
        time.sleep(0.05)
    raise AssertionError('cold-start job did not reach terminal state in time')


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

    state = _await_terminal_state(project_root, job.job_id)

    assert state.status == 'succeeded'
    assert state.stage == 'done'
    assert state.progress == 100
    assert state.counts.discovered_table_count == 1
    assert state.counts.discovered_doc_count == 0
    assert state.counts.discovered_script_count == 0
    assert state.counts.raw_table_index_count == 1
    assert state.counts.canonical_table_count == 1
    assert state.counts.candidate_table_count == 1
    assert state.candidate_refs == ['table:HeroTable']

    assert get_project_raw_table_index_path(project_root, 'HeroTable').exists()
    assert get_project_canonical_table_schema_path(project_root, 'HeroTable').exists()
    assert get_project_candidate_map_path(project_root).exists()
    assert get_project_latest_map_diff_path(project_root).exists()

    loaded_candidate = load_latest_source_candidate(project_root)
    assert loaded_candidate is not None
    assert loaded_candidate.map is not None
    assert len(loaded_candidate.map.tables) == 1
    assert loaded_candidate.map.tables[0].table_id == 'HeroTable'
    assert loaded_candidate.diff_review is not None
    assert 'table:HeroTable' in loaded_candidate.diff_review.added_refs

    assert not get_project_formal_map_canonical_path(project_root).exists()
    assert not get_project_current_release_path(project_root).exists()


def test_cold_start_job_succeeds_with_warning_when_docs_root_missing(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_minimal_hero_table(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv'], exclude=[]),
    )
    save_project_docs_source_config(project_root, ProjectDocsSourceConfig(roots=['Docs']))

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    state = _await_terminal_state(project_root, job.job_id)

    assert state.status == 'succeeded'
    assert state.counts.discovered_table_count == 1
    assert state.counts.discovered_doc_count == 0
    assert state.counts.raw_table_index_count == 1
    assert state.counts.canonical_table_count == 1
    assert state.counts.candidate_table_count == 1
    assert any(item.startswith('docs_skipped_missing_root:Docs') for item in state.warnings)
    assert 'docs_skipped_no_available_sources' in state.warnings


def test_cold_start_job_succeeds_with_warning_when_docs_have_no_available_files(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    docs_dir = project_root / 'Docs'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_minimal_hero_table(project_root)
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / 'notes.bin').write_text('noop', encoding='utf-8')
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv'], exclude=[]),
    )
    save_project_docs_source_config(project_root, ProjectDocsSourceConfig(roots=['Docs'], include=['**/*.md']))

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    state = _await_terminal_state(project_root, job.job_id)

    assert state.status == 'succeeded'
    assert state.counts.discovered_doc_count == 0
    assert state.counts.discovered_table_count == 1
    assert 'docs_skipped_no_available_sources' in state.warnings


def test_cold_start_job_succeeds_with_warning_when_scripts_root_missing(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_minimal_hero_table(project_root)
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv'], exclude=[]),
    )
    save_project_scripts_source_config(project_root, ProjectScriptsSourceConfig(roots=['Scripts']))

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    state = _await_terminal_state(project_root, job.job_id)

    assert state.status == 'succeeded'
    assert state.counts.discovered_script_count == 0
    assert state.counts.discovered_table_count == 1
    assert state.counts.raw_table_index_count == 1
    assert state.counts.canonical_table_count == 1
    assert state.counts.candidate_table_count == 1
    assert any(item.startswith('scripts_skipped_missing_root:Scripts') for item in state.warnings)
    assert 'scripts_skipped_no_available_sources' in state.warnings


def test_cold_start_job_succeeds_with_warning_when_scripts_have_no_available_files(tmp_path, monkeypatch):
    working_root = tmp_path / 'working-root'
    project_root = tmp_path / 'project-root'
    scripts_dir = project_root / 'Scripts'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_minimal_hero_table(project_root)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / 'readme.md').write_text('noop', encoding='utf-8')
    save_project_tables_source_config(
        project_root,
        ProjectTablesSourceConfig(roots=['Tables'], include=['**/*.csv'], exclude=[]),
    )
    save_project_scripts_source_config(project_root, ProjectScriptsSourceConfig(roots=['Scripts'], include=['**/*.py']))

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=30)
    state = _await_terminal_state(project_root, job.job_id)

    assert state.status == 'succeeded'
    assert state.counts.discovered_script_count == 0
    assert state.counts.discovered_table_count == 1
    assert 'scripts_skipped_no_available_sources' in state.warnings