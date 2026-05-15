from __future__ import annotations

import time

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import ProjectTablesSourceConfig, save_project_tables_source_config
from ltclaw_gy_x.game.knowledge_formal_map_store import save_formal_knowledge_map
from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer
from ltclaw_gy_x.game.knowledge_rag_context import build_current_release_context
from ltclaw_gy_x.game.knowledge_release_service import build_knowledge_release_from_current_indexes
from ltclaw_gy_x.game.knowledge_release_store import set_current_release
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate


def _write_minimal_hero_table(project_root) -> None:
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )


def test_cold_start_candidate_to_release_and_rag_context(tmp_path, monkeypatch):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
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
    candidate = load_latest_source_candidate(project_root)
    assert candidate is not None
    assert candidate.map is not None
    assert [table.table_id for table in candidate.map.tables] == ['HeroTable']

    save_formal_knowledge_map(project_root, candidate.map, updated_by='maintainer')

    release = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-hero-001',
    )

    assert release.manifest.release_id == 'release-hero-001'
    assert release.map_source == 'formal_map'
    assert release.artifacts['table_schema'].count == 1
    assert [table.table_id for table in release.knowledge_map.tables] == ['HeroTable']

    set_current_release(project_root, release.manifest.release_id)

    context = build_current_release_context(
        project_root,
        'HeroTable 这张表有哪些字段？主键是什么？',
        max_chunks=8,
        max_chars=4000,
    )

    assert context['mode'] == 'context'
    assert context['release_id'] == 'release-hero-001'
    assert context['citations']
    assert any(citation.get('ref') == 'table:HeroTable' for citation in context['citations'])

    answer = build_rag_answer('HeroTable 这张表有哪些字段？主键是什么？', context)

    assert answer['mode'] == 'answer'
    assert answer['release_id'] == 'release-hero-001'
    assert answer['citations']
    assert any(citation.get('ref') == 'table:HeroTable' for citation in answer['citations'])