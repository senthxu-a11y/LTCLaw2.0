from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_release_builders import build_minimal_manifest, build_minimal_map
from ltclaw_gy_x.game.knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    KnowledgeReleaseNotFoundError,
    create_release,
    get_current_release,
    load_manifest,
    set_current_release,
)
from ltclaw_gy_x.game.models import KnowledgeDocRef, KnowledgeRelationship, KnowledgeScriptRef, KnowledgeSystem, KnowledgeTableRef
from ltclaw_gy_x.game.paths import (
    get_current_release_path,
    get_formal_map_path,
    get_pending_test_plans_path,
    get_release_candidates_path,
    get_release_dir,
)


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


def _create_release(monkeypatch, tmp_path, release_id: str):
    project_root, manifest, knowledge_map = _create_release_inputs(monkeypatch, tmp_path, release_id)
    release_dir = create_release(
        project_root,
        manifest,
        knowledge_map,
        indexes={
            'table_schema.jsonl': '{"table_name":"SkillTable","source_path":"Tables/SkillTable.xlsx","source_hash":"sha256:table"}\n',
            'doc_knowledge.jsonl': '{"title":"Combat Overview","source_path":"Docs/Combat.md","source_hash":"sha256:doc"}\n',
            'script_evidence.jsonl': '{"source_path":"Scripts/CombatResolver.cs","source_hash":"sha256:script"}\n',
        },
        release_notes='# release notes\n',
    )
    return project_root, release_dir, manifest


def _create_release_inputs(monkeypatch, tmp_path, release_id: str):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'table source\n')
    _write_source(project_root, 'Docs/Combat.md', 'doc source\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'script source\n')
    knowledge_map = _knowledge_map(release_id)
    manifest = _manifest(project_root, release_id, knowledge_map)
    return project_root, manifest, knowledge_map


def test_create_release_writes_app_owned_assets(monkeypatch, tmp_path):
    project_root, release_dir, manifest = _create_release(monkeypatch, tmp_path, 'release-001')

    assert release_dir == get_release_dir(project_root, 'release-001')
    assert (release_dir / 'manifest.json').exists()
    assert (release_dir / 'map.json').exists()
    assert (release_dir / 'release_notes.md').exists()
    assert (release_dir / 'indexes' / 'table_schema.jsonl').exists()
    assert (release_dir / 'indexes' / 'doc_knowledge.jsonl').exists()
    assert (release_dir / 'indexes' / 'script_evidence.jsonl').exists()
    assert not (release_dir / 'Tables' / 'SkillTable.xlsx').exists()
    assert not (release_dir / 'Docs' / 'Combat.md').exists()
    assert not (release_dir / 'Scripts' / 'CombatResolver.cs').exists()
    assert load_manifest(project_root, 'release-001').map_hash == manifest.map_hash
    assert load_manifest(project_root, 'release-001').indexes['candidate_evidence'].path == 'indexes/candidate_evidence.jsonl'
    assert load_manifest(project_root, 'release-001').indexes['candidate_evidence'].count == 0



def test_set_and_get_current_release_roundtrip(monkeypatch, tmp_path):
    project_root, _, _ = _create_release(monkeypatch, tmp_path, 'release-001')
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'table source\n')
    _write_source(project_root, 'Docs/Combat.md', 'doc source\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'script source\n')
    knowledge_map = _knowledge_map('release-002')
    manifest = _manifest(project_root, 'release-002', knowledge_map)
    create_release(project_root, manifest, knowledge_map, release_notes='# second release\n')

    pointer = set_current_release(project_root, 'release-002')

    assert pointer.release_id == 'release-002'
    assert get_current_release(project_root).release_id == 'release-002'
    current_payload = json.loads(get_current_release_path(project_root).read_text(encoding='utf-8'))
    assert current_payload['release_id'] == 'release-002'
    assert current_payload['manifest_path'] == 'manifest.json'
    assert current_payload['map_path'] == 'map.json'


def test_set_current_release_updates_only_current_pointer(monkeypatch, tmp_path):
    project_root, release_dir, _ = _create_release(monkeypatch, tmp_path, 'release-001')

    pending_test_plans_path = get_pending_test_plans_path(project_root)
    pending_test_plans_path.parent.mkdir(parents=True, exist_ok=True)
    pending_test_plans_path.write_text('{"plan":"unchanged"}\n', encoding='utf-8')

    release_candidates_path = get_release_candidates_path(project_root)
    release_candidates_path.write_text('{"candidate":"unchanged"}\n', encoding='utf-8')

    formal_map_path = get_formal_map_path(project_root)
    formal_map_path.parent.mkdir(parents=True, exist_ok=True)
    formal_map_path.write_text('{"mode":"formal_map"}\n', encoding='utf-8')

    manifest_path = release_dir / 'manifest.json'
    knowledge_map_path = release_dir / 'map.json'
    release_notes_path = release_dir / 'release_notes.md'

    before_manifest = manifest_path.read_text(encoding='utf-8')
    before_map = knowledge_map_path.read_text(encoding='utf-8')
    before_notes = release_notes_path.read_text(encoding='utf-8')
    before_test_plans = pending_test_plans_path.read_text(encoding='utf-8')
    before_candidates = release_candidates_path.read_text(encoding='utf-8')
    before_formal_map = formal_map_path.read_text(encoding='utf-8')

    pointer = set_current_release(project_root, 'release-001')

    assert pointer.release_id == 'release-001'
    assert manifest_path.read_text(encoding='utf-8') == before_manifest
    assert knowledge_map_path.read_text(encoding='utf-8') == before_map
    assert release_notes_path.read_text(encoding='utf-8') == before_notes
    assert pending_test_plans_path.read_text(encoding='utf-8') == before_test_plans
    assert release_candidates_path.read_text(encoding='utf-8') == before_candidates
    assert formal_map_path.read_text(encoding='utf-8') == before_formal_map


def test_set_current_release_missing_release_fails_without_writing_pointer(monkeypatch, tmp_path):
    project_root, _, _ = _create_release(monkeypatch, tmp_path, 'release-001')
    current_path = get_current_release_path(project_root)

    with pytest.raises(KnowledgeReleaseNotFoundError, match='Knowledge release manifest not found: release-missing'):
        set_current_release(project_root, 'release-missing')

    assert current_path.exists() is False



def test_get_current_release_fails_clearly_when_missing(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))

    with pytest.raises(CurrentKnowledgeReleaseNotSetError, match='No current knowledge release is set'):
        get_current_release(project_root)


@pytest.mark.parametrize('asset_path', ['../escape.jsonl', '..\\escape.jsonl', 'C:/abs/path.jsonl', '/abs/path.jsonl'])
def test_create_release_rejects_index_asset_path_escape(monkeypatch, tmp_path, asset_path):
    project_root, manifest, knowledge_map = _create_release_inputs(monkeypatch, tmp_path, 'release-asset-path')

    with pytest.raises(ValueError, match='Invalid release asset path'):
        create_release(project_root, manifest, knowledge_map, indexes={asset_path: '{}\n'})


@pytest.mark.parametrize('release_id', ['', '.', '..', '../escape', 'nested/id', 'nested\\id'])
def test_release_store_rejects_invalid_release_ids(monkeypatch, tmp_path, release_id):
    project_root, _, _ = _create_release(monkeypatch, tmp_path, 'release-base')

    with pytest.raises(ValueError):
        load_manifest(project_root, release_id)
