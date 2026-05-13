from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from ltclaw_gy_x.cli import doctor_cmd as doctor_cmd_module
from ltclaw_gy_x.cli.main import cli


def test_build_windows_startup_doctor_report_flags_missing_table_indexes(monkeypatch, tmp_path):
    working_dir = tmp_path / 'working'
    console_static = tmp_path / 'console-static'
    project_root = tmp_path / 'project-root'
    working_dir.mkdir()
    console_static.mkdir()
    (console_static / 'index.html').write_text('<html></html>', encoding='utf-8')
    project_root.mkdir()

    monkeypatch.setenv('QWENPAW_WORKING_DIR', str(working_dir))
    monkeypatch.setenv('QWENPAW_CONSOLE_STATIC_DIR', str(console_static))
    monkeypatch.setattr(
        doctor_cmd_module,
        'load_user_config',
        lambda: type('Cfg', (), {'svn_local_root': str(project_root)})(),
    )
    monkeypatch.setattr(doctor_cmd_module, 'resolve_console_static_dir', lambda: str(console_static))
    monkeypatch.setattr(doctor_cmd_module, 'find_ltclaw_gy_x_source_repo_root', lambda: tmp_path)

    report = doctor_cmd_module.build_windows_startup_doctor_report(
        host='127.0.0.1',
        port=8092,
        agent_id='default',
        timeout=0.1,
    )

    assert report['env_paths']['QWENPAW_WORKING_DIR']['set'] is True
    assert report['env_paths']['QWENPAW_CONSOLE_STATIC_DIR']['exists'] is True
    assert report['local_project_dir']['configured'] is True
    assert report['knowledge_first_release']['current_table_indexes']['ready'] is False
    assert report['knowledge_first_release']['current_table_indexes']['detail'] == 'Current table indexes are required to build the first knowledge release'


def test_build_windows_startup_doctor_report_detects_table_indexes_ready(monkeypatch, tmp_path):
    working_dir = tmp_path / 'working'
    console_static = tmp_path / 'console-static'
    project_root = tmp_path / 'project-root'
    working_dir.mkdir()
    console_static.mkdir()
    (console_static / 'index.html').write_text('<html></html>', encoding='utf-8')
    project_root.mkdir()
    monkeypatch.setenv('QWENPAW_WORKING_DIR', str(working_dir))
    monkeypatch.setenv('QWENPAW_CONSOLE_STATIC_DIR', str(console_static))
    table_indexes_path = doctor_cmd_module.get_table_indexes_path(project_root)
    table_indexes_path.parent.mkdir(parents=True, exist_ok=True)
    table_indexes_path.write_text(
        json.dumps({'version': '1.0', 'tables': [{'table_name': 'SkillTable'}]}),
        encoding='utf-8',
    )

    monkeypatch.setattr(
        doctor_cmd_module,
        'load_user_config',
        lambda: type('Cfg', (), {'svn_local_root': str(project_root)})(),
    )
    monkeypatch.setattr(doctor_cmd_module, 'resolve_console_static_dir', lambda: str(console_static))
    monkeypatch.setattr(doctor_cmd_module, 'find_ltclaw_gy_x_source_repo_root', lambda: None)

    report = doctor_cmd_module.build_windows_startup_doctor_report(
        host='127.0.0.1',
        port=8092,
        agent_id='default',
        timeout=0.1,
    )

    assert report['knowledge_first_release']['current_table_indexes']['ready'] is True
    assert report['knowledge_first_release']['current_table_indexes']['count'] == 1


def test_doctor_windows_startup_help_is_available():
    result = CliRunner().invoke(cli, ['doctor', 'windows-startup', '--help'])

    assert result.exit_code == 0
    assert 'Focused Windows pilot startup preflight for operators.' in result.output
    assert '--host' in result.output
    assert '--port INTEGER' in result.output
    assert '--agent-id' in result.output


def test_doctor_windows_startup_accepts_subcommand_host_and_port(monkeypatch):
    captured = {}

    def _build_report(*, host, port, agent_id, timeout):
        captured['host'] = host
        captured['port'] = port
        captured['agent_id'] = agent_id
        captured['timeout'] = timeout
        return {'target': {'base_url': f'http://{host}:{port}', 'agent_id': agent_id}}

    monkeypatch.setattr(doctor_cmd_module, 'build_windows_startup_doctor_report', _build_report)
    monkeypatch.setattr(doctor_cmd_module, '_emit_windows_startup_doctor_report', lambda _report: False)

    result = CliRunner().invoke(
        cli,
        ['doctor', 'windows-startup', '--host', '127.0.0.1', '--port', '8092', '--agent-id', 'default'],
    )

    assert result.exit_code == 0
    assert captured['host'] == '127.0.0.1'
    assert captured['port'] == 8092
    assert captured['agent_id'] == 'default'


def test_doctor_windows_startup_subcommand_host_port_override_top_level(monkeypatch):
    captured = {}

    def _build_report(*, host, port, agent_id, timeout):
        captured['host'] = host
        captured['port'] = port
        return {'target': {'base_url': f'http://{host}:{port}', 'agent_id': agent_id}}

    monkeypatch.setattr(doctor_cmd_module, 'build_windows_startup_doctor_report', _build_report)
    monkeypatch.setattr(doctor_cmd_module, '_emit_windows_startup_doctor_report', lambda _report: False)

    result = CliRunner().invoke(
        cli,
        [
            '--host',
            '10.0.0.8',
            '--port',
            '8088',
            'doctor',
            'windows-startup',
            '--host',
            '127.0.0.1',
            '--port',
            '8092',
            '--agent-id',
            'default',
        ],
    )

    assert result.exit_code == 0
    assert captured['host'] == '127.0.0.1'
    assert captured['port'] == 8092