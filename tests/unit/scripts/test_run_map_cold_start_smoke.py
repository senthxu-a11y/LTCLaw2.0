from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ltclaw_gy_x.game.paths import (
    get_project_canonical_tables_dir,
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_raw_table_indexes_path,
    get_project_raw_tables_dir,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _project_root() -> Path:
    return _repo_root() / 'examples' / 'minimal_project'


def _script_path() -> Path:
    return _repo_root() / 'scripts' / 'run_map_cold_start_smoke.py'


def _run_smoke(workdir: Path, project: str = 'examples/minimal_project') -> tuple[subprocess.CompletedProcess[str], dict]:
    env = os.environ.copy()
    env['LTCLAW_WORKING_DIR'] = str(workdir)
    env['PYTHONPATH'] = str(_repo_root() / 'src') + os.pathsep + env.get('PYTHONPATH', '')
    command = [
        sys.executable,
        str(_script_path()),
        '--project',
        project,
        '--rule-only',
    ]
    result = subprocess.run(
        command,
        cwd=_repo_root(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    return result, payload


def test_smoke_script_succeeds_in_clean_environment(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    result, payload = _run_smoke(workdir)

    assert result.returncode == 0, result.stderr
    assert payload == {
        'success': True,
        'discovered_table_count': 1,
        'raw_table_index_count': 1,
        'canonical_table_count': 1,
        'candidate_table_count': 1,
        'candidate_refs': ['table:HeroTable'],
        'llm_used': False,
    }
    assert not get_project_formal_map_canonical_path(_project_root()).exists()
    assert not get_project_current_release_path(_project_root()).exists()


def test_smoke_script_succeeds_without_model_configuration(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    result, payload = _run_smoke(workdir)

    assert result.returncode == 0, result.stderr
    assert payload['success'] is True
    assert payload['llm_used'] is False


def test_smoke_script_succeeds_after_deleting_canonical_outputs(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    first_result, first_payload = _run_smoke(workdir)
    assert first_result.returncode == 0, first_result.stderr
    assert first_payload['success'] is True

    canonical_dir = get_project_canonical_tables_dir(_project_root())
    for candidate in canonical_dir.glob('*.json'):
        candidate.unlink()

    second_result, second_payload = _run_smoke(workdir)
    assert second_result.returncode == 0, second_result.stderr
    assert second_payload['success'] is True
    assert second_payload['canonical_table_count'] == 1


def test_smoke_script_succeeds_after_deleting_raw_outputs(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    first_result, first_payload = _run_smoke(workdir)
    assert first_result.returncode == 0, first_result.stderr
    assert first_payload['success'] is True

    raw_indexes_path = get_project_raw_table_indexes_path(_project_root())
    if raw_indexes_path.exists():
        raw_indexes_path.unlink()
    raw_tables_dir = get_project_raw_tables_dir(_project_root())
    for candidate in raw_tables_dir.glob('*.json'):
        candidate.unlink()

    second_result, second_payload = _run_smoke(workdir)
    assert second_result.returncode == 0, second_result.stderr
    assert second_payload['success'] is True
    assert second_payload['raw_table_index_count'] == 1


def test_smoke_script_prints_failure_diagnostics(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    result, payload = _run_smoke(workdir, project='examples/does-not-exist')

    assert result.returncode == 1
    assert payload == {
        'success': False,
        'stage': 'project_root_setup',
        'reason': 'project_root_missing',
        'path': str(_repo_root() / 'examples' / 'does-not-exist'),
        'next_action': 'pass_existing_project_root',
        'llm_used': False,
    }