#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ltclaw_gy_x.game.canonical_facts_committer import CanonicalFactsCommitter
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.knowledge_map_candidate import build_map_candidate_from_canonical_facts
from ltclaw_gy_x.game.raw_index_rebuild import rebuild_raw_table_indexes
from ltclaw_gy_x.game.source_discovery import discover_table_sources


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run cold start map smoke flow in rule-only mode.')
    parser.add_argument('--project', required=True, help='Project path, e.g. examples/minimal_project')
    parser.add_argument('--tables-root', default='Tables', help='Tables root relative to project root')
    parser.add_argument('--rule-only', action='store_true', help='Run strictly in rule-only mode')
    return parser.parse_args()


def _resolve_project_path(value: str) -> Path:
    project_path = Path(value).expanduser()
    if not project_path.is_absolute():
        project_path = (REPO_ROOT / project_path).resolve()
    return project_path


def _emit(payload: dict) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get('success') else 1


def _failure(
    stage: str,
    reason: str,
    *,
    path: str | None = None,
    next_action: str | None = None,
    diagnostics: dict | None = None,
) -> dict:
    payload = {
        'success': False,
        'stage': stage,
        'reason': reason,
        'path': path,
        'next_action': next_action,
        'llm_used': False,
    }
    if diagnostics:
        payload['diagnostics'] = diagnostics
    return payload


@contextlib.contextmanager
def _temporary_working_root() -> Iterator[Path]:
    existing = os.environ.get('LTCLAW_WORKING_DIR')
    if existing:
        yield Path(existing)
        return

    with tempfile.TemporaryDirectory(prefix='ltclaw-cold-start-smoke-') as temp_dir:
        os.environ['LTCLAW_WORKING_DIR'] = temp_dir
        try:
            yield Path(temp_dir)
        finally:
            os.environ.pop('LTCLAW_WORKING_DIR', None)


async def _run(project_root: Path, tables_root: str, rule_only: bool) -> dict:
    if not rule_only:
        return _failure(
            'argument_validation',
            'rule_only_required',
            next_action='rerun_with_rule_only',
        )

    if not project_root.exists() or not project_root.is_dir():
        return _failure(
            'project_root_setup',
            'project_root_missing',
            path=str(project_root),
            next_action='pass_existing_project_root',
        )

    tables_config = ProjectTablesSourceConfig(roots=[tables_root])
    save_project_tables_source_config(project_root, tables_config)

    discovery = discover_table_sources(project_root, tables_config)
    discovered_table_count = int(discovery['summary']['discovered_table_count'])
    available_table_count = int(discovery['summary']['available_table_count'])
    if available_table_count <= 0:
        first_error = discovery['errors'][0] if discovery['errors'] else {}
        return _failure(
            'source_discovery',
            str(first_error.get('reason') or 'no_table_sources_found'),
            path=first_error.get('source_path') or str(project_root / tables_root),
            next_action=str(discovery.get('next_action') or 'configure_tables_source'),
            diagnostics=discovery['summary'],
        )

    raw_result = await rebuild_raw_table_indexes(project_root, tables_config)
    if int(raw_result.get('raw_table_index_count', 0)) <= 0:
        first_error = raw_result['errors'][0] if raw_result.get('errors') else {}
        return _failure(
            'raw_index_rebuild',
            str(first_error.get('error') or 'no_raw_indexes'),
            path=first_error.get('source_path') or str(project_root),
            next_action=str(raw_result.get('next_action') or 'run_canonical_rebuild'),
            diagnostics=raw_result,
        )

    canonical_result = CanonicalFactsCommitter(project_root).rebuild_tables(force=False)
    if canonical_result.canonical_table_count <= 0:
        first_error = canonical_result.errors[0] if canonical_result.errors else None
        return _failure(
            'canonical_facts_rebuild',
            str(first_error.error if first_error else 'no_canonical_facts'),
            path=(first_error.raw_index_file if first_error else str(project_root)),
            next_action='build_candidate_from_source',
            diagnostics={
                'raw_table_index_count': canonical_result.raw_table_index_count,
                'canonical_table_count': canonical_result.canonical_table_count,
                'warnings': list(canonical_result.warnings),
            },
        )

    candidate_result = build_map_candidate_from_canonical_facts(project_root)
    if candidate_result.mode != 'candidate_map' or candidate_result.map is None:
        return _failure(
            'candidate_from_source',
            candidate_result.mode,
            path=str(project_root),
            next_action='run_canonical_rebuild' if candidate_result.mode == 'no_canonical_facts' else 'inspect_candidate_builder',
            diagnostics={
                'warnings': list(candidate_result.warnings),
                'candidate_source': candidate_result.candidate_source,
            },
        )

    candidate_refs = sorted(f'table:{table.table_id}' for table in candidate_result.map.tables)
    return {
        'success': True,
        'discovered_table_count': discovered_table_count,
        'raw_table_index_count': int(raw_result['raw_table_index_count']),
        'canonical_table_count': int(canonical_result.canonical_table_count),
        'candidate_table_count': len(candidate_result.map.tables),
        'candidate_refs': candidate_refs,
        'llm_used': False,
    }


def main() -> int:
    args = _parse_args()
    project_root = _resolve_project_path(args.project)
    with _temporary_working_root():
        payload = asyncio.run(_run(project_root, args.tables_root, args.rule_only))
    return _emit(payload)


if __name__ == '__main__':
    raise SystemExit(main())