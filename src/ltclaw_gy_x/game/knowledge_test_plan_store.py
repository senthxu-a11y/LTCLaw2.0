from __future__ import annotations

import json
from pathlib import Path

from .models import WorkbenchTestPlan
from .paths import get_pending_test_plans_path, get_project_store_dir


DEFAULT_RELEASE_SCOPE = 'not_in_release'
DEFAULT_TEST_SCOPE = 'local_workbench'


class KnowledgeTestPlanStoreError(RuntimeError):
    pass


class KnowledgeTestPlanValidationError(KnowledgeTestPlanStoreError):
    pass


class KnowledgeTestPlanRecordError(KnowledgeTestPlanStoreError):
    pass


def append_test_plan(project_root: Path, plan: WorkbenchTestPlan) -> WorkbenchTestPlan:
    normalized = _normalize_test_plan(project_root, plan)
    target = get_pending_test_plans_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(normalized.model_dump(mode='json'), ensure_ascii=False) + '\n')
    return normalized


def list_test_plans(project_root: Path) -> list[WorkbenchTestPlan]:
    target = get_pending_test_plans_path(project_root)
    if not target.exists() or target.stat().st_size == 0:
        return []

    plans: list[WorkbenchTestPlan] = []
    with target.open('r', encoding='utf-8') as handle:
        for line_no, line in enumerate(handle, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                plan = WorkbenchTestPlan.model_validate(json.loads(payload))
                plans.append(_normalize_test_plan(project_root, plan))
            except Exception as exc:  # noqa: BLE001
                raise KnowledgeTestPlanRecordError(f'Invalid test plan record at line {line_no}') from exc
    return plans


def get_test_plan(project_root: Path, plan_id: str) -> WorkbenchTestPlan | None:
    normalized_plan_id = str(plan_id or '').strip()
    if not normalized_plan_id:
        raise KnowledgeTestPlanValidationError('Test plan id is required')
    for plan in list_test_plans(project_root):
        if plan.id == normalized_plan_id:
            return plan
    return None


def _normalize_test_plan(project_root: Path, plan: WorkbenchTestPlan) -> WorkbenchTestPlan:
    normalized_id = str(plan.id or '').strip()
    if not normalized_id:
        raise KnowledgeTestPlanValidationError('Test plan id is required')

    normalized_changes = []
    derived_source_refs: list[str] = []
    for change in plan.changes:
        normalized_source_path = _normalize_relative_path(change.source_path)
        normalized_changes.append(change.model_copy(update={'source_path': normalized_source_path}))
        if normalized_source_path not in derived_source_refs:
            derived_source_refs.append(normalized_source_path)

    normalized_source_refs: list[str] = []
    for source_ref in [*plan.source_refs, *derived_source_refs]:
        normalized_source_ref = _normalize_relative_path(source_ref)
        if normalized_source_ref not in normalized_source_refs:
            normalized_source_refs.append(normalized_source_ref)

    return plan.model_copy(
        update={
            'id': normalized_id,
            'project_key': plan.project_key or get_project_store_dir(project_root).name,
            'release_scope': plan.release_scope or DEFAULT_RELEASE_SCOPE,
            'test_scope': plan.test_scope or DEFAULT_TEST_SCOPE,
            'source_refs': normalized_source_refs,
            'changes': normalized_changes,
        }
    )


def _normalize_relative_path(value: str) -> str:
    raw_value = str(value or '').strip()
    candidate = Path(raw_value)
    if not candidate.parts or candidate.is_absolute() or raw_value.startswith(('/', '\\')):
        raise KnowledgeTestPlanValidationError(f'Invalid source path: {value!r}')
    normalized_parts = [part for part in candidate.parts if part not in ('', '.')]
    if not normalized_parts or any(part == '..' for part in normalized_parts):
        raise KnowledgeTestPlanValidationError(f'Invalid source path: {value!r}')
    return Path(*normalized_parts).as_posix()
