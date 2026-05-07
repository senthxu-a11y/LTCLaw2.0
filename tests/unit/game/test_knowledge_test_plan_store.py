from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from ltclaw_gy_x.game.knowledge_test_plan_store import (
    KnowledgeTestPlanRecordError,
    KnowledgeTestPlanValidationError,
    append_test_plan,
    list_test_plans,
)
from ltclaw_gy_x.game.models import WorkbenchTestPlan, WorkbenchTestPlanChange
from ltclaw_gy_x.game.paths import get_pending_test_plans_path, get_release_dir


def _plan(plan_id: str = 'plan-001') -> WorkbenchTestPlan:
    return WorkbenchTestPlan(
        id=plan_id,
        status='draft',
        title='Damage tuning',
        changes=[
            WorkbenchTestPlanChange(
                table='SkillTable',
                primary_key={'field': 'ID', 'value': '1029'},
                field='Damage',
                before='100',
                after='120',
                source_path='Tables/SkillTable.xlsx',
            )
        ],
        created_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        created_by='planner',
    )


def test_append_and_list_test_plans_roundtrip(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    saved = append_test_plan(project_root, _plan())
    listed = list_test_plans(project_root)

    assert saved.project_key
    assert saved.release_scope == 'not_in_release'
    assert saved.test_scope == 'local_workbench'
    assert saved.source_refs == ['Tables/SkillTable.xlsx']
    assert len(listed) == 1
    assert listed[0].id == 'plan-001'
    assert listed[0].source_refs == ['Tables/SkillTable.xlsx']
    payload = get_pending_test_plans_path(project_root).read_text(encoding='utf-8').strip().splitlines()
    assert len(payload) == 1
    record = json.loads(payload[0])
    assert record['project_key'] == saved.project_key
    assert record['release_scope'] == 'not_in_release'
    assert record['test_scope'] == 'local_workbench'


def test_list_test_plans_returns_empty_when_missing(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    assert list_test_plans(project_root) == []


@pytest.mark.parametrize(
    'source_path',
    ['../Secrets.xlsx', '..\\Secrets.xlsx', 'C:/abs/path.xlsx', 'C:\\abs\\path.xlsx', '/abs/path.xlsx'],
)
def test_append_rejects_source_path_escape(monkeypatch, tmp_path, source_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    plan = _plan()
    plan.changes[0].source_path = source_path

    with pytest.raises(KnowledgeTestPlanValidationError, match='Invalid source path'):
        append_test_plan(project_root, plan)


def test_append_writes_only_pending_store(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    append_test_plan(project_root, _plan())

    assert get_pending_test_plans_path(project_root).exists()
    assert not get_release_dir(project_root, 'release-001').exists()
    assert not (project_root / '.svn').exists()


def test_list_fails_clearly_on_bad_jsonl_line(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    target = get_pending_test_plans_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{bad json}\n', encoding='utf-8')

    with pytest.raises(KnowledgeTestPlanRecordError, match='Invalid test plan record at line 1'):
        list_test_plans(project_root)
