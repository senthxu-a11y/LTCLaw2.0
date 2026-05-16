from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _project_root() -> Path:
    return _repo_root() / 'examples' / 'multi_source_project'


def _script_path() -> Path:
    return _repo_root() / 'scripts' / 'run_multi_source_cold_start_smoke.py'


def _run_smoke(workdir: Path, project: str = 'examples/multi_source_project') -> tuple[subprocess.CompletedProcess[str], dict]:
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


def test_multi_source_smoke_script_succeeds_in_clean_environment(monkeypatch, tmp_path):
    workdir = tmp_path / 'ltclaw-working'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(workdir))

    result, payload = _run_smoke(workdir)

    assert result.returncode == 0, result.stderr
    assert payload['success'] is True
    assert payload['discovery'] == {
        'available_table_count': 3,
        'available_doc_count': 3,
        'available_script_count': 3,
    }
    assert payload['cold_start_job']['status'] == 'succeeded'
    assert payload['cold_start_job']['counts']['candidate_table_count'] == 3
    assert payload['cold_start_job']['counts']['candidate_doc_count'] == 3
    assert payload['cold_start_job']['counts']['candidate_script_count'] == 3
    assert 'table:HeroTable' in payload['cold_start_job']['candidate_refs']
    assert 'doc:BattleSystem' in payload['cold_start_job']['candidate_refs']
    assert 'script:DamageCalculator' in payload['cold_start_job']['candidate_refs']
    assert payload['formal_map_saved'] is True
    assert payload['release_id'].startswith('multi-source-smoke-')
    assert payload['release_artifacts'] == {
        'table_schema': 3,
        'doc_knowledge': 3,
        'script_evidence': 3,
    }
    assert payload['rag_checks']['table']['mode'] == 'answer'
    assert 'table:HeroTable' in payload['rag_checks']['table']['refs']
    assert payload['rag_checks']['doc']['mode'] == 'answer'
    assert 'doc:BattleSystem' in payload['rag_checks']['doc']['refs']
    assert payload['rag_checks']['script']['mode'] == 'answer'
    assert 'script:DamageCalculator' in payload['rag_checks']['script']['refs']
    assert payload['llm_used'] is False


def test_multi_source_smoke_script_prints_failure_diagnostics(monkeypatch, tmp_path):
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
