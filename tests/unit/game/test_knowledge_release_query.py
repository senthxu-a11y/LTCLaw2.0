from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from ltclaw_gy_x.game.knowledge_release_builders import build_minimal_manifest, build_minimal_map
from ltclaw_gy_x.game.knowledge_release_query import query_current_release
from ltclaw_gy_x.game.knowledge_release_store import create_release, set_current_release
from ltclaw_gy_x.game.paths import get_release_dir
from ltclaw_gy_x.game.models import KnowledgeDocRef, KnowledgeRelationship, KnowledgeScriptRef, KnowledgeSystem, KnowledgeTableRef


def _write_source(project_root: Path, relative_path: str, content: str) -> None:
    target = project_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


def _knowledge_map(release_id: str):
    return build_minimal_map(
        release_id,
        systems=[KnowledgeSystem(system_id='combat', title='Combat')],
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


def test_query_current_release_reads_only_release_jsonl(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')

    knowledge_map = _knowledge_map('release-001')
    manifest = _manifest(project_root, 'release-001', knowledge_map)
    create_release(
        project_root,
        manifest,
        knowledge_map,
        indexes={
            'table_schema.jsonl': (
                '{"table_name":"SkillTable","system":"combat","summary":"skill damage values",'
                '"source_path":"Tables/SkillTable.xlsx","source_hash":"sha256:table","primary_key":"ID",'
                '"row_count":7,"fields":[{"name":"Damage","type":"int","description":"skill damage"}]}'
                '\n'
            ),
            'doc_knowledge.jsonl': (
                '{"title":"Combat Overview","summary":"damage formula design","category":"design",'
                '"tags":["combat"],"source_path":"Docs/Combat.md","related_tables":["SkillTable"],'
                '"source_hash":"sha256:doc"}'
                '\n'
            ),
            'script_evidence.jsonl': (
                '{"source_path":"Scripts/CombatResolver.cs","source_hash":"sha256:script","language":"csharp",'
                '"kind":"code_index","summary":"damage resolver logic","symbols":[{"name":"CombatResolver"}],'
                '"references":[{"target_symbol":"DamageFormula"}]}'
                '\n'
            ),
        },
    )
    set_current_release(project_root, 'release-001')

    (project_root / 'Tables' / 'SkillTable.xlsx').unlink()
    (project_root / 'Docs' / 'Combat.md').unlink()
    (project_root / 'Scripts' / 'CombatResolver.cs').unlink()

    payload = query_current_release(project_root, 'damage', top_k=10)

    assert payload['mode'] == 'current_release_keyword'
    assert payload['release_id'] == 'release-001'
    assert payload['count'] == 3
    assert {item['source_type'] for item in payload['results']} == {
        'doc_knowledge',
        'script_evidence',
        'table_schema',
    }
    for item in payload['results']:
        assert item['source_path']
        assert item['release_id'] == 'release-001'
        assert item['built_at'] == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_query_current_release_returns_no_current_release(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    payload = query_current_release(project_root, 'damage')

    assert payload == {
        'mode': 'no_current_release',
        'query': 'damage',
        'top_k': 10,
        'release_id': None,
        'built_at': None,
        'results': [],
        'count': 0,
    }


def test_query_current_release_ignores_manifest_index_path_escape(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    _write_source(project_root, 'Tables/SkillTable.xlsx', 'source-only table\n')
    _write_source(project_root, 'Docs/Combat.md', 'source-only doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'source-only code\n')
    knowledge_map = _knowledge_map('release-002')
    manifest = _manifest(project_root, 'release-002', knowledge_map)
    create_release(
        project_root,
        manifest,
        knowledge_map,
        indexes={
            'table_schema.jsonl': '{"table_name":"SkillTable","source_path":"Tables/SkillTable.xlsx","source_hash":"sha256:table"}\n',
        },
    )
    set_current_release(project_root, 'release-002')

    outside_path = get_release_dir(project_root, 'release-002').parent / 'outside-doc.jsonl'
    outside_path.write_text(
        '{"title":"Outside Doc","summary":"damage outside release","source_path":"Docs/Outside.md","source_hash":"sha256:outside"}\n',
        encoding='utf-8',
    )
    manifest_path = get_release_dir(project_root, 'release-002') / 'manifest.json'
    manifest_payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest_payload['indexes']['doc_knowledge']['path'] = '../outside-doc.jsonl'
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    payload = query_current_release(project_root, 'damage')

    assert payload['mode'] == 'current_release_keyword'
    assert payload['results'] == []
    assert payload['count'] == 0