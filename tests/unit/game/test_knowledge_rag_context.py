from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ltclaw_gy_x.game import retrieval as retrieval_module
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
        'allowed_refs': [],
        'map_hash': None,
        'map_source_hash': None,
        'reason': 'no_current_release',
        'requested_focus_refs': [],
        'active_focus_refs': [],
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
        {'table_schema', 'doc_knowledge', 'script_evidence'}
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
        assert citation['ref']
        if citation['source_type'] in {'table_schema', 'doc_knowledge', 'script_evidence'}:
            assert citation['source_path']


def test_build_current_release_context_citations_preserve_locator_fields(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-citation-locators')
    set_current_release(project_root, 'release-citation-locators')

    payload = build_current_release_context(project_root, 'combat damage formula skilltable', max_chunks=8)

    citations_by_ref = {citation['ref']: citation for citation in payload['citations']}
    assert citations_by_ref['table:SkillTable'] == {
        'citation_id': citations_by_ref['table:SkillTable']['citation_id'],
        'release_id': 'release-citation-locators',
        'source_type': 'table_schema',
        'table': 'SkillTable',
        'artifact_path': 'indexes/table_schema.jsonl',
        'source_path': 'Tables/SkillTable.xlsx',
        'title': 'SkillTable',
        'row': 1,
        'field': 'Damage',
        'source_hash': 'sha256:table',
        'ref': 'table:SkillTable',
    }
    assert citations_by_ref['doc:combat-doc'] == {
        'citation_id': citations_by_ref['doc:combat-doc']['citation_id'],
        'release_id': 'release-citation-locators',
        'source_type': 'doc_knowledge',
        'table': None,
        'artifact_path': 'indexes/doc_knowledge.jsonl',
        'source_path': 'Docs/Combat.md',
        'title': 'Combat Overview',
        'row': 1,
        'field': None,
        'source_hash': 'sha256:doc',
        'ref': 'doc:combat-doc',
    }
    assert citations_by_ref['script:combat-script'] == {
        'citation_id': citations_by_ref['script:combat-script']['citation_id'],
        'release_id': 'release-citation-locators',
        'source_type': 'script_evidence',
        'table': None,
        'artifact_path': 'indexes/script_evidence.jsonl',
        'source_path': 'Scripts/CombatResolver.cs',
        'title': 'CombatResolver.cs',
        'row': 1,
        'field': None,
        'source_hash': 'sha256:script',
        'ref': 'script:combat-script',
    }


def test_build_current_release_context_routes_through_map_router(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-routed')
    set_current_release(project_root, 'release-routed')

    import ltclaw_gy_x.game.knowledge_rag_context as context_module

    captured = {}
    original_route = context_module.route_release_map_refs

    def _route(query, current_release, knowledge_map, *, focus_refs=None):
        captured['query'] = query
        captured['release_id'] = current_release.release_id
        captured['focus_refs'] = list(focus_refs or [])
        return original_route(query, current_release, knowledge_map, focus_refs=focus_refs)

    monkeypatch.setattr(context_module, 'route_release_map_refs', _route)

    payload = build_current_release_context(project_root, 'combat damage', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'context'
    assert captured == {
        'query': 'combat damage',
        'release_id': 'release-routed',
        'focus_refs': ['doc:combat-doc'],
    }


def test_build_current_release_context_reads_only_allowed_ref_artifacts(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-focus-doc')
    set_current_release(project_root, 'release-focus-doc')

    release_dir = get_release_dir(project_root, 'release-focus-doc')
    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'context'
    assert payload['allowed_refs'] == ['doc:combat-doc']
    assert {chunk['source_type'] for chunk in payload['chunks']} == {'doc_knowledge'}

    normalized = {path.resolve(strict=False) for path in opened_paths}
    assert release_dir.resolve(strict=False) / 'indexes' / 'doc_knowledge.jsonl' in normalized
    assert release_dir.resolve(strict=False) / 'indexes' / 'table_schema.jsonl' not in normalized
    assert release_dir.resolve(strict=False) / 'indexes' / 'script_evidence.jsonl' not in normalized
    assert release_dir.resolve(strict=False) / 'indexes' / 'candidate_evidence.jsonl' not in normalized


def test_build_current_release_context_stops_reading_rows_after_allowed_refs_are_satisfied(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-row-stop')
    set_current_release(project_root, 'release-row-stop')

    doc_path = get_release_dir(project_root, 'release-row-stop') / 'indexes' / 'doc_knowledge.jsonl'
    doc_path.write_text(
        '\n'.join(
            [
                '{"title":"Combat Overview","summary":"combat damage formula design","category":"design","tags":["combat"],"source_path":"Docs/Combat.md","related_tables":["SkillTable"],"source_hash":"sha256:doc"}',
                '{"title":"Noise 1","summary":"should never be read","category":"design","tags":[],"source_path":"Docs/Noise1.md","source_hash":"sha256:noise-1"}',
                '{"title":"Noise 2","summary":"should never be read","category":"design","tags":[],"source_path":"Docs/Noise2.md","source_hash":"sha256:noise-2"}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    import ltclaw_gy_x.game.knowledge_rag_context as context_module

    original_loads = context_module.json.loads
    seen_titles: list[str] = []

    def _spy_loads(line: str, *args, **kwargs):
        record = original_loads(line, *args, **kwargs)
        if isinstance(record, dict) and record.get('title'):
            seen_titles.append(str(record['title']))
        return record

    monkeypatch.setattr(context_module.json, 'loads', _spy_loads)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'context'
    assert payload['allowed_refs'] == ['doc:combat-doc']
    assert seen_titles == ['Combat Overview']


def test_build_current_release_context_excludes_ignored_and_deprecated_refs(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')

    knowledge_map = _knowledge_map('release-filtered').model_copy(
        update={
            'docs': [
                KnowledgeDocRef(
                    doc_id='combat-doc',
                    title='Combat Overview',
                    source_path='Docs/Combat.md',
                    source_hash='sha256:doc',
                    system_id='combat',
                    status='ignored',
                )
            ],
            'scripts': [
                KnowledgeScriptRef(
                    script_id='combat-script',
                    title='CombatResolver',
                    source_path='Scripts/CombatResolver.cs',
                    source_hash='sha256:script',
                    system_id='combat',
                    status='active',
                )
            ],
            'deprecated': ['script:combat-script'],
        }
    )
    manifest = _manifest(project_root, 'release-filtered', knowledge_map)
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
        },
    )
    set_current_release(project_root, 'release-filtered')

    payload = build_current_release_context(project_root, 'combat damage formula')

    assert payload['mode'] == 'context'
    assert payload['allowed_refs'] == ['table:SkillTable']
    assert {chunk['source_type'] for chunk in payload['chunks']} == {'table_schema'}
    assert all(citation['ref'] == 'table:SkillTable' for citation in payload['citations'])


def test_build_current_release_context_returns_insufficient_context_when_no_allowed_refs(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-no-allowed')
    set_current_release(project_root, 'release-no-allowed')

    payload = build_current_release_context(project_root, 'completely unmatched signal')

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'no_allowed_refs'
    assert payload['allowed_refs'] == []
    assert payload['requested_focus_refs'] == []
    assert payload['active_focus_refs'] == []
    assert payload['chunks'] == []
    assert payload['citations'] == []


def test_build_current_release_context_returns_insufficient_context_when_allowed_refs_have_no_evidence(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-no-evidence')
    set_current_release(project_root, 'release-no-evidence')

    doc_path = get_release_dir(project_root, 'release-no-evidence') / 'indexes' / 'doc_knowledge.jsonl'
    doc_path.write_text(
        '{"title":"Another Doc","summary":"something else","category":"design","tags":[],"source_path":"Docs/Other.md","related_tables":[],"source_hash":"sha256:other"}\n',
        encoding='utf-8',
    )

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'allowed_refs_without_evidence'
    assert payload['allowed_refs'] == ['doc:combat-doc']
    assert payload['requested_focus_refs'] == ['doc:combat-doc']
    assert payload['active_focus_refs'] == ['doc:combat-doc']
    assert payload['chunks'] == []


def test_build_current_release_context_unknown_focus_refs_fail_closed(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-unknown-focus')
    set_current_release(project_root, 'release-unknown-focus')

    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:unknown'])

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'no_active_focus_refs'
    assert payload['allowed_refs'] == []
    assert payload['requested_focus_refs'] == ['doc:unknown']
    assert payload['active_focus_refs'] == []
    assert payload['chunks'] == []
    assert payload['citations'] == []
    assert all('indexes' not in path.as_posix() for path in opened_paths)


def test_build_current_release_context_unknown_prefix_focus_refs_fail_closed(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-unknown-prefix-focus')
    set_current_release(project_root, 'release-unknown-prefix-focus')

    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['kb:combat-doc'])

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'no_active_focus_refs'
    assert payload['allowed_refs'] == []
    assert payload['requested_focus_refs'] == ['kb:combat-doc']
    assert payload['active_focus_refs'] == []
    assert payload['chunks'] == []
    assert payload['citations'] == []
    assert all('indexes' not in path.as_posix() for path in opened_paths)


def test_build_current_release_context_ignored_focus_refs_fail_closed(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')

    knowledge_map = _knowledge_map('release-ignored-focus').model_copy(
        update={
            'docs': [
                KnowledgeDocRef(
                    doc_id='combat-doc',
                    title='Combat Overview',
                    source_path='Docs/Combat.md',
                    source_hash='sha256:doc',
                    system_id='combat',
                    status='ignored',
                )
            ]
        }
    )
    manifest = _manifest(project_root, 'release-ignored-focus', knowledge_map)
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
        },
    )
    set_current_release(project_root, 'release-ignored-focus')

    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'no_active_focus_refs'
    assert payload['allowed_refs'] == []
    assert payload['requested_focus_refs'] == ['doc:combat-doc']
    assert payload['active_focus_refs'] == []
    assert payload['chunks'] == []
    assert payload['citations'] == []
    assert all('indexes' not in path.as_posix() for path in opened_paths)


def test_build_current_release_context_deprecated_focus_refs_fail_closed(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')

    knowledge_map = _knowledge_map('release-deprecated-focus').model_copy(
        update={
            'deprecated': ['doc:combat-doc']
        }
    )
    manifest = _manifest(project_root, 'release-deprecated-focus', knowledge_map)
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
        },
    )
    set_current_release(project_root, 'release-deprecated-focus')

    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(project_root, 'combat damage formula', focus_refs=['doc:combat-doc'])

    assert payload['mode'] == 'insufficient_context'
    assert payload['reason'] == 'no_active_focus_refs'
    assert payload['allowed_refs'] == []
    assert payload['requested_focus_refs'] == ['doc:combat-doc']
    assert payload['active_focus_refs'] == []
    assert payload['chunks'] == []
    assert payload['citations'] == []
    assert all('indexes' not in path.as_posix() for path in opened_paths)


def test_build_current_release_context_mixed_focus_refs_reads_only_active_focus(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-mixed-focus')
    set_current_release(project_root, 'release-mixed-focus')

    release_dir = get_release_dir(project_root, 'release-mixed-focus')
    opened_paths: list[Path] = []
    original_open = Path.open

    def _spy_open(self: Path, *args, **kwargs):
        opened_paths.append(self.resolve(strict=False))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', _spy_open)

    payload = build_current_release_context(
        project_root,
        'combat damage formula',
        focus_refs=['doc:combat-doc', 'doc:unknown'],
    )

    assert payload['mode'] == 'context'
    assert payload['allowed_refs'] == ['doc:combat-doc']
    assert payload['requested_focus_refs'] == ['doc:combat-doc', 'doc:unknown']
    assert payload['active_focus_refs'] == ['doc:combat-doc']
    assert {chunk['source_type'] for chunk in payload['chunks']} == {'doc_knowledge'}
    normalized = {path.resolve(strict=False) for path in opened_paths}
    assert release_dir.resolve(strict=False) / 'indexes' / 'doc_knowledge.jsonl' in normalized
    assert release_dir.resolve(strict=False) / 'indexes' / 'table_schema.jsonl' not in normalized
    assert release_dir.resolve(strict=False) / 'indexes' / 'script_evidence.jsonl' not in normalized


def test_build_current_release_context_does_not_call_legacy_retrieval_or_kb(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-no-retrieval')
    set_current_release(project_root, 'release-no-retrieval')

    monkeypatch.setattr(retrieval_module, 'get_kb_store', lambda *args, **kwargs: pytest.fail('formal RAG must not call KB'))
    monkeypatch.setattr(retrieval_module, '_retrieval_dir', lambda *args, **kwargs: pytest.fail('formal RAG must not call retrieval'))

    payload = build_current_release_context(project_root, 'combat damage formula')

    assert payload['mode'] == 'context'
    assert payload['chunks']


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


def test_query_current_release_uses_restored_current_release_after_rollback(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-old')
    _create_release(project_root, 'release-current')

    (get_release_dir(project_root, 'release-old') / 'indexes' / 'doc_knowledge.jsonl').write_text(
        '{"title":"Legacy Combat","summary":"zetaoldsignal","category":"design","tags":["legacy"],"source_path":"Docs/Combat.md","source_hash":"sha256:legacy"}\n',
        encoding='utf-8',
    )
    (get_release_dir(project_root, 'release-current') / 'indexes' / 'doc_knowledge.jsonl').write_text(
        '{"title":"Current Combat","summary":"omegacurrentsignal","category":"design","tags":["current"],"source_path":"Docs/Combat.md","source_hash":"sha256:current"}\n',
        encoding='utf-8',
    )

    set_current_release(project_root, 'release-current')
    before_payload = query_current_release(project_root, 'zetaoldsignal', top_k=10)
    set_current_release(project_root, 'release-old')
    after_payload = query_current_release(project_root, 'zetaoldsignal', top_k=10)

    assert before_payload['release_id'] == 'release-current'
    assert before_payload['count'] == 0
    assert after_payload['release_id'] == 'release-old'
    assert after_payload['count'] == 1
    assert after_payload['results'][0]['title'] == 'Legacy Combat'


def test_build_current_release_context_uses_restored_current_release_after_rollback(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    _create_release(project_root, 'release-old')
    _create_release(project_root, 'release-current')

    (get_release_dir(project_root, 'release-old') / 'indexes' / 'doc_knowledge.jsonl').write_text(
        '{"title":"Legacy Combat","summary":"zetaoldsignal","category":"design","tags":["legacy"],"source_path":"Docs/Combat.md","source_hash":"sha256:legacy"}\n',
        encoding='utf-8',
    )
    (get_release_dir(project_root, 'release-current') / 'indexes' / 'doc_knowledge.jsonl').write_text(
        '{"title":"Current Combat","summary":"omegacurrentsignal","category":"design","tags":["current"],"source_path":"Docs/Combat.md","source_hash":"sha256:current"}\n',
        encoding='utf-8',
    )

    set_current_release(project_root, 'release-current')
    before_payload = build_current_release_context(project_root, 'zetaoldsignal', max_chunks=8, max_chars=12000)
    set_current_release(project_root, 'release-old')
    after_payload = build_current_release_context(project_root, 'zetaoldsignal', max_chunks=8, max_chars=12000)

    assert before_payload['release_id'] == 'release-current'
    assert before_payload['mode'] == 'insufficient_context'
    assert before_payload['chunks'] == []
    assert after_payload['release_id'] == 'release-old'
    assert after_payload['mode'] == 'insufficient_context'
    assert after_payload['chunks'] == []
