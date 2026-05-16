#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import (
    ProjectDocsSourceConfig,
    ProjectScriptsSourceConfig,
    ProjectTablesSourceConfig,
    save_project_docs_source_config,
    save_project_scripts_source_config,
    save_project_tables_source_config,
)
from ltclaw_gy_x.game.doc_source_discovery import discover_document_sources
from ltclaw_gy_x.game.knowledge_formal_map_store import save_formal_knowledge_map
from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer
from ltclaw_gy_x.game.knowledge_rag_context import build_current_release_context
from ltclaw_gy_x.game.knowledge_release_service import build_knowledge_release_from_current_indexes
from ltclaw_gy_x.game.knowledge_release_store import set_current_release
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate
from ltclaw_gy_x.game.script_source_discovery import discover_script_sources
from ltclaw_gy_x.game.source_discovery import discover_table_sources


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run multi-source cold start smoke flow in rule-only mode.')
    parser.add_argument('--project', required=True, help='Project path, e.g. examples/multi_source_project')
    parser.add_argument('--tables-root', default='Tables', help='Tables root relative to project root')
    parser.add_argument('--docs-root', default='Docs', help='Docs root relative to project root')
    parser.add_argument('--scripts-root', default='Scripts', help='Scripts root relative to project root')
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

    with tempfile.TemporaryDirectory(prefix='ltclaw-multi-source-smoke-') as temp_dir:
        os.environ['LTCLAW_WORKING_DIR'] = temp_dir
        try:
            yield Path(temp_dir)
        finally:
            os.environ.pop('LTCLAW_WORKING_DIR', None)


def _release_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    return f'multi-source-smoke-{timestamp}'


def _citation_refs(payload: dict) -> list[str]:
    return sorted({str(citation.get('ref') or '') for citation in list(payload.get('citations') or []) if citation.get('ref')})


async def _run(project_root: Path, tables_root: str, docs_root: str, scripts_root: str, rule_only: bool) -> dict:
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

    tables_config = ProjectTablesSourceConfig(
        roots=[tables_root],
        include=['**/*.csv', '**/*.xlsx', '**/*.txt'],
        exclude=[],
        header_row=1,
        primary_key_candidates=['ID'],
    )
    docs_config = ProjectDocsSourceConfig(
        roots=[docs_root],
        include=['**/*.md', '**/*.txt', '**/*.docx'],
        exclude=[],
    )
    scripts_config = ProjectScriptsSourceConfig(
        roots=[scripts_root],
        include=['**/*.cs', '**/*.lua', '**/*.py'],
        exclude=[],
    )
    save_project_tables_source_config(project_root, tables_config)
    save_project_docs_source_config(project_root, docs_config)
    save_project_scripts_source_config(project_root, scripts_config)

    table_discovery = discover_table_sources(project_root, tables_config)
    doc_discovery = discover_document_sources(project_root, docs_config)
    script_discovery = discover_script_sources(project_root, scripts_config)

    available_table_count = int(table_discovery['summary']['available_table_count'])
    available_doc_count = int(doc_discovery['summary']['available_doc_count'])
    available_script_count = int(script_discovery['summary']['available_script_count'])
    if available_table_count <= 0 or available_doc_count <= 0 or available_script_count <= 0:
        return _failure(
            'source_discovery',
            'multi_source_discovery_incomplete',
            path=str(project_root),
            next_action='configure_sources',
            diagnostics={
                'table_summary': table_discovery['summary'],
                'doc_summary': doc_discovery['summary'],
                'script_summary': script_discovery['summary'],
            },
        )

    job, _ = create_or_get_cold_start_job(project_root, timeout_seconds=60)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = load_cold_start_job(project_root, job.job_id)
        if state is None:
            await asyncio.sleep(0.05)
            continue
        if state.status in {'succeeded', 'failed', 'cancelled'}:
            break
        await asyncio.sleep(0.05)
    else:
        return _failure(
            'cold_start_job',
            'cold_start_job_timeout',
            path=str(project_root),
            next_action='inspect_cold_start_job',
        )

    assert state is not None
    if state.status != 'succeeded':
        return _failure(
            'cold_start_job',
            str(state.status),
            path=str(project_root),
            next_action=str(state.next_action or 'inspect_cold_start_job'),
            diagnostics={
                'stage': state.stage,
                'message': state.message,
                'errors': [item.model_dump(mode='json') for item in state.errors],
                'warnings': list(state.warnings),
                'counts': state.counts.model_dump(mode='json'),
                'candidate_refs': list(state.candidate_refs),
            },
        )

    candidate = load_latest_source_candidate(project_root)
    if candidate is None or candidate.map is None:
        return _failure(
            'candidate_from_source',
            'candidate_map_missing',
            path=str(project_root),
            next_action='inspect_candidate_builder',
        )

    save_formal_knowledge_map(project_root, candidate.map, updated_by='smoke-script')
    release = build_knowledge_release_from_current_indexes(
        project_root,
        REPO_ROOT,
        _release_id(),
    )
    set_current_release(project_root, release.manifest.release_id)

    table_query = 'HeroTable 这张表有哪些字段？主键是什么？'
    doc_query = 'BattleSystem 文档如何描述伤害公式？'
    script_query = 'DamageCalculator 使用了哪些表格字段？'
    table_context = build_current_release_context(
        project_root,
        table_query,
        max_chunks=8,
        max_chars=4000,
        focus_refs=['table:HeroTable'],
    )
    doc_context = build_current_release_context(
        project_root,
        doc_query,
        max_chunks=8,
        max_chars=4000,
        focus_refs=['doc:BattleSystem'],
    )
    script_context = build_current_release_context(
        project_root,
        script_query,
        max_chunks=8,
        max_chars=4000,
        focus_refs=['script:DamageCalculator'],
    )
    table_answer = build_rag_answer(table_query, table_context)
    doc_answer = build_rag_answer(doc_query, doc_context)
    script_answer = build_rag_answer(script_query, script_context)

    return {
        'success': True,
        'discovery': {
            'available_table_count': available_table_count,
            'available_doc_count': available_doc_count,
            'available_script_count': available_script_count,
        },
        'cold_start_job': {
            'status': state.status,
            'counts': state.counts.model_dump(mode='json'),
            'candidate_refs': list(state.candidate_refs),
        },
        'formal_map_saved': True,
        'release_id': release.manifest.release_id,
        'release_artifacts': {
            'table_schema': release.artifacts['table_schema'].count,
            'doc_knowledge': release.artifacts['doc_knowledge'].count,
            'script_evidence': release.artifacts['script_evidence'].count,
        },
        'rag_checks': {
            'table': {
                'mode': table_answer['mode'],
                'refs': _citation_refs(table_answer),
            },
            'doc': {
                'mode': doc_answer['mode'],
                'refs': _citation_refs(doc_answer),
            },
            'script': {
                'mode': script_answer['mode'],
                'refs': _citation_refs(script_answer),
            },
        },
        'llm_used': False,
    }


def main() -> int:
    args = _parse_args()
    project_root = _resolve_project_path(args.project)
    with _temporary_working_root():
        payload = asyncio.run(
            _run(
                project_root,
                args.tables_root,
                args.docs_root,
                args.scripts_root,
                args.rule_only,
            )
        )
    return _emit(payload)


if __name__ == '__main__':
    raise SystemExit(main())
