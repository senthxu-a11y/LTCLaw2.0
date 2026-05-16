from __future__ import annotations

import time

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import (
    ProjectDocsSourceConfig,
    ProjectTablesSourceConfig,
    save_project_docs_source_config,
    save_project_tables_source_config,
)
from ltclaw_gy_x.game.doc_source_discovery import discover_document_sources
from ltclaw_gy_x.game.knowledge_formal_map_store import save_formal_knowledge_map
from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer
from ltclaw_gy_x.game.knowledge_rag_context import build_current_release_context
from ltclaw_gy_x.game.knowledge_release_service import build_knowledge_release_from_current_indexes
from ltclaw_gy_x.game.knowledge_release_store import set_current_release
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate


def _write_project_sources(project_root) -> None:
    tables_dir = project_root / 'Tables'
    docs_dir = project_root / 'Docs'
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )
    (tables_dir / 'WeaponConfig.csv').write_text(
        'ID,WeaponName,AttackBonus\n1001,IronSword,5\n',
        encoding='utf-8',
    )
    (docs_dir / 'BattleSystem.md').write_text(
        '# Battle System\n\n'
        '## Damage Formula\n\n'
        'Damage is calculated as Attack * SkillMultiplier + WeaponConfig bonus.\n\n'
        '## Related Data\n\n'
        'HeroTable stores the base attack value. WeaponConfig stores weapon bonus metadata.\n',
        encoding='utf-8',
    )


def test_discover_document_sources_marks_markdown_available(tmp_path):
    project_root = tmp_path / 'project-root'
    _write_project_sources(project_root)

    result = discover_document_sources(
        project_root,
        ProjectDocsSourceConfig(
            roots=['Docs'],
            include=['**/*.md'],
            exclude=[],
        ),
    )

    assert result['summary']['available_doc_count'] == 1
    assert result['doc_files'] == [
        {
            'source_path': 'Docs/BattleSystem.md',
            'format': 'md',
            'status': 'available',
            'reason': 'matched_supported_format',
            'cold_start_supported': True,
            'cold_start_reason': 'rule_only_supported_md',
        }
    ]


def test_markdown_doc_cold_start_candidate_release_and_rag(tmp_path, monkeypatch):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_project_sources(project_root)
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
    save_project_docs_source_config(
        project_root,
        ProjectDocsSourceConfig(
            roots=['Docs'],
            include=['**/*.md'],
            exclude=[],
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
    assert state.counts.canonical_doc_count == 1
    assert state.counts.candidate_doc_count == 1
    assert 'doc:BattleSystem' in state.candidate_refs

    candidate = load_latest_source_candidate(project_root)
    assert candidate is not None
    assert candidate.map is not None
    assert [doc.doc_id for doc in candidate.map.docs] == ['BattleSystem']
    relationship_refs = {
        (relationship.from_ref, relationship.to_ref)
        for relationship in candidate.map.relationships
    }
    assert ('doc:BattleSystem', 'table:HeroTable') in relationship_refs
    assert ('doc:BattleSystem', 'table:WeaponConfig') in relationship_refs

    save_formal_knowledge_map(project_root, candidate.map, updated_by='maintainer')
    release = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-doc-001',
    )

    assert release.artifacts['doc_knowledge'].count == 1
    assert [doc.doc_id for doc in release.knowledge_map.docs] == ['BattleSystem']

    set_current_release(project_root, release.manifest.release_id)
    context = build_current_release_context(
        project_root,
        'What does BattleSystem say about the damage formula?',
        max_chunks=8,
        max_chars=4000,
    )

    assert context['mode'] == 'context'
    assert any(citation.get('ref') == 'doc:BattleSystem' for citation in context['citations'])
    assert any('Attack * SkillMultiplier' in chunk.get('text', '') for chunk in context['chunks'])

    answer = build_rag_answer('What does BattleSystem say about the damage formula?', context)

    assert answer['mode'] == 'answer'
    assert any(citation.get('ref') == 'doc:BattleSystem' for citation in answer['citations'])
    assert 'Attack * SkillMultiplier + WeaponConfig bonus' in answer['answer']
