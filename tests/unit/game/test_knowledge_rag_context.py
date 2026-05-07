from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_rag_context import (
    KnowledgeReleaseContextPathError,
    build_current_release_context,
)
from ltclaw_gy_x.game.knowledge_release_builders import build_minimal_manifest, build_minimal_map
from ltclaw_gy_x.game.knowledge_release_query import query_current_release
from ltclaw_gy_x.game.knowledge_release_store import create_release, set_current_release
from ltclaw_gy_x.game.models import KnowledgeDocRef, KnowledgeRelationship, KnowledgeScriptRef, KnowledgeSystem, KnowledgeTableRef
from ltclaw_gy_x.game.paths import get_current_release_path, get_pending_test_plans_path, get_release_candidates_path, get_release_dir


def _write_source(project_root: Path, relative_path: str, content: str) -> None:
    target = project_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


def _knowledge_map(release_id: str):
    return build_minimal_map(
        release_id,
        systems=[KnowledgeSystem(system_id='combat', title='Combat System')],
        tables=[
            KnowledgeTableRef(
                table_id='SkillTable',
                title='SkillTable',
                source_path='Tables/SkillTable.xlsx',
                source_hash='sha256:table',
                system_id='combat',
            )
        ],
        docs=[
            KnowledgeDocRef(
                doc_id='combat-doc',
                title='Combat Overview',
                source_path='Docs/Combat.md',
                source_hash='sha256:doc',
                system_id='combat',
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id='combat-script',
                title='CombatResolver',
                source_path='Scripts/CombatResolver.cs',
                source_hash='sha256:script',
                system_id='combat',
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id=f'rel-{release_id}',
                from_ref='table:SkillTable',
                to_ref='doc:combat-doc',
                relation_type='documented_by',
                source_hash='sha256:relationship',
            )
        ],
    )


def _manifest(project_root: Path, release_id: str, knowledge_map):
    return build_minimal_manifest(
        project_root,
        release_id,
        knowledge_map,
        source_paths=[
            'Tables/SkillTable.xlsx',
            'Docs/Combat.md',
            'Scripts/CombatResolver.cs',
        ],
        created_by='admin',
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _create_release(project_root: Path, release_id: str) -> None:
    knowledge_map = _knowledge_map(release_id)
    manifest = _manifest(project_root, release_id, knowledge_map)
    create_release(
        project_root,
        manifest,
        knowledge_map,
        indexes={
            'table_schema.jsonl': (
                '{"table_name":"SkillTable","system":"combat","summary":"combat skill damage schema",'
                '"source_path":"Tables/SkillTable.xlsx","source_hash":"sha256:table","primary_key":"ID",'
                '"row_count":7,"fields":[{"name":"Damage","type":"int","description":"combat damage value"}]}'
                '\n'
            ),
            'doc_knowledge.jsonl': (
                '{"title":"Combat Overview","summary":"combat damage formula design",'
                '"category":"design","tags":["combat"],"source_path":"Docs/Combat.md",'
                '"related_tables":["SkillTable"],"source_hash":"sha256:doc"}'
                '\n'
            ),
            'script_evidence.jsonl': (
                '{"source_path":"Scripts/CombatResolver.cs","source_hash":"sha256:script","language":"csharp",'
                '"kind":"code_index","summary":"combat damage resolver logic","symbols":[{"name":"CombatResolver"}],'
                '"references":[{"target_symbol":"DamageFormula"},{"target_table":"SkillTable"}]}'
                '\n'
            ),
            'candidate_evidence.jsonl': (
                '{"candidate_id":"candidate-1","title":"pending combat candidate","source_refs":["Tables/SkillTable.xlsx"],'
                '"source_hash":"sha256:candidate"}'
                '\n'
            ),
        },
    )


def test_build_current_release_context_returns_no_current_release(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    payload = build_current_release_context(project_root, 'combat damage')

    assert payload == {
        'mode': 'no_current_release',
        'query': 'combat damage',
        'release_id': None,
        'built_at': None,
        'chunks': [],
        'citations': [],
    }


def test_build_current_release_context_reads_only_current_release_artifacts(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _write_source(project_root, '.svn/entries', 'svn metadata should not be read\n')

    _create_release(project_root, 'release-old')
    _create_release(project_root, 'release-current')
    set_current_release(project_root, 'release-current')

    pending_test_plans = get_pending_test_plans_path(project_root)
    pending_test_plans.parent.mkdir(parents=True, exist_ok=True)
    pending_test_plans.write_text('{"title":"pending combat damage"}\n', encoding='utf-8')
    pending_release_candidates = get_release_candidates_path(project_root)
    pending_release_candidates.write_text('{"title":"pending release candidate combat"}\n', encoding='utf-8')

    old_release_dir = get_release_dir(project_root, 'release-old')
    current_release_dir = get_release_dir(project_root, 'release-current')
    candidate_evidence_path = current_release_dir / 'indexes' / 'candidate_evidence.jsonl'
    assert candidate_evidence_path.exists()

    (project_root / 'Tables' / 'SkillTable.xlsx').unlink()
    (project_root / 'Docs' / 'Combat.md').unlink()
    (project_root / 'Scripts' / 'CombatResolver.cs').unlink()

    read_paths: list[Path] = []
    original_read_text = Path.read_text

    def _spy_read_text(self: Path, *args, **kwargs):
        read_paths.append(self.resolve(strict=False))
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', _spy_read_text)

    payload = build_current_release_context(project_root, 'combat damage formula skilltable', max_chunks=8, max_chars=12000)

    assert payload['mode'] == 'context'
    assert payload['release_id'] == 'release-current'
    assert payload['chunks']
    assert {chunk['source_type'] for chunk in payload['chunks']}.issubset(
        {'manifest', 'map', 'table_schema', 'doc_knowledge', 'script_evidence'}
    )
    assert {'table_schema', 'doc_knowledge', 'script_evidence'}.issubset(
        {chunk['source_type'] for chunk in payload['chunks']}
    )
    assert all(citation['release_id'] == 'release-current' for citation in payload['citations'])

    normalized_reads = {path.resolve(strict=False) for path in read_paths}
    assert old_release_dir.resolve(strict=False) / 'manifest.json' not in normalized_reads
    assert candidate_evidence_path.resolve(strict=False) not in normalized_reads
    assert pending_test_plans.resolve(strict=False) not in normalized_reads
    assert pending_release_candidates.resolve(strict=False) not in normalized_reads
    assert (project_root / '.svn' / 'entries').resolve(strict=False) not in normalized_reads
    assert (project_root / 'Tables' / 'SkillTable.xlsx').resolve(strict=False) not in normalized_reads
    assert (project_root / 'Docs' / 'Combat.md').resolve(strict=False) not in normalized_reads
    assert (project_root / 'Scripts' / 'CombatResolver.cs').resolve(strict=False) not in normalized_reads


@pytest.mark.parametrize('index_path', ['../outside-doc.jsonl', '..\\outside-doc.jsonl', 'C:/outside-doc.jsonl'])
def test_build_current_release_context_rejects_manifest_index_path_escape(monkeypatch, tmp_path, index_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-escape')
    set_current_release(project_root, 'release-escape')

    manifest_path = get_release_dir(project_root, 'release-escape') / 'manifest.json'
    manifest_payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest_payload['indexes']['doc_knowledge']['path'] = index_path
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    with pytest.raises(KnowledgeReleaseContextPathError, match='Invalid release artifact path'):
        build_current_release_context(project_root, 'combat damage')


def test_build_current_release_context_honors_max_chunks(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-max-chunks')
    set_current_release(project_root, 'release-max-chunks')

    payload = build_current_release_context(project_root, 'combat skill damage formula', max_chunks=2)

    assert len(payload['chunks']) == 2
    assert len(payload['citations']) == 2
    assert [chunk['rank'] for chunk in payload['chunks']] == [1, 2]


def test_build_current_release_context_honors_max_chars(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-max-chars')
    set_current_release(project_root, 'release-max-chars')

    payload = build_current_release_context(project_root, 'combat skill damage formula', max_chunks=8, max_chars=120)

    assert payload['chunks']
    assert sum(len(chunk['text']) for chunk in payload['chunks']) <= 120
    assert any(chunk['text'].endswith('...') or len(chunk['text']) < 120 for chunk in payload['chunks'])


def test_build_current_release_context_citations_include_release_and_reference(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-citations')
    set_current_release(project_root, 'release-citations')

    payload = build_current_release_context(project_root, 'combat skill damage formula', max_chunks=8)

    assert payload['citations']
    assert {citation['citation_id'] for citation in payload['citations']} == {
        chunk['citation_id'] for chunk in payload['chunks']
    }
    for citation in payload['citations']:
        assert citation['release_id'] == 'release-citations'
        assert citation['artifact_path'] or citation['source_path']
        if citation['source_type'] in {'table_schema', 'doc_knowledge', 'script_evidence'}:
            assert citation['source_path']


def test_build_current_release_context_is_read_only_and_does_not_change_current_release(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-read-only')
    set_current_release(project_root, 'release-read-only')

    current_path = get_current_release_path(project_root)
    manifest_path = get_release_dir(project_root, 'release-read-only') / 'manifest.json'
    before_current = current_path.read_text(encoding='utf-8')
    before_manifest = manifest_path.read_text(encoding='utf-8')

    def _forbid_write(*args, **kwargs):
        raise AssertionError('context builder must be read-only')

    monkeypatch.setattr(Path, 'write_text', _forbid_write)
    monkeypatch.setattr(Path, 'write_bytes', _forbid_write)

    payload = build_current_release_context(project_root, 'combat skill damage formula', max_chunks=8)

    assert payload['release_id'] == 'release-read-only'
    assert current_path.read_text(encoding='utf-8') == before_current
    assert manifest_path.read_text(encoding='utf-8') == before_manifest


def test_query_current_release_still_remains_keyword_only(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-query-regression')
    set_current_release(project_root, 'release-query-regression')

    payload = query_current_release(project_root, 'damage', top_k=10)

    assert payload['mode'] == 'current_release_keyword'
    assert payload['count'] == 3
    assert {item['source_type'] for item in payload['results']} == {
        'doc_knowledge',
        'script_evidence',
        'table_schema',
    }
