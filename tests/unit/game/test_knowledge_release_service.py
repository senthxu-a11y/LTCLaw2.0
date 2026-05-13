from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ltclaw_gy_x.game.knowledge_formal_map_store import save_formal_knowledge_map
from ltclaw_gy_x.game.knowledge_release_builders import build_minimal_map, compute_map_hash
from ltclaw_gy_x.game.knowledge_release_candidate_store import append_release_candidate
from ltclaw_gy_x.game.knowledge_release_service import (
    KnowledgeProjectRootNotFoundError,
    KnowledgeReleasePrerequisiteError,
    build_knowledge_release,
    build_knowledge_release_from_current_indexes,
)
from ltclaw_gy_x.game.knowledge_release_store import get_current_release, set_current_release
from ltclaw_gy_x.game.models import (
    CodeFileIndex,
    CodeSymbol,
    CodeSymbolReference,
    DocIndex,
    FieldConfidence,
    FieldInfo,
    KnowledgeDocRef,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeTableRef,
    ReleaseCandidate,
    TableIndex,
)
from ltclaw_gy_x.game.paths import (
    get_code_index_dir,
    get_formal_map_path,
    get_project_store_dir,
    get_release_dir,
    get_table_indexes_path,
)
from ltclaw_gy_x.knowledge_base.kb_store import get_kb_store


def _write_source(project_root: Path, relative_path: str, content: str) -> None:
    target = project_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


def _write_table_indexes(project_root: Path, tables: list[TableIndex]) -> None:
    target = get_table_indexes_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({'version': '1.0', 'tables': [table.model_dump(mode='json') for table in tables]}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def _write_code_indexes(workspace_dir: Path, project_root: Path, code_indexes: list[CodeFileIndex]) -> None:
    store = get_code_index_dir(workspace_dir, project_root)
    store.mkdir(parents=True, exist_ok=True)
    from ltclaw_gy_x.game.code_indexer import CodeIndexStore

    code_store = CodeIndexStore(store)
    for code_index in code_indexes:
        code_store.save(code_index)


def _add_approved_doc(workspace_dir: Path, source_path: str) -> None:
    get_kb_store(workspace_dir).add(
        title='Combat Approved',
        summary='combat loop summary',
        category='doc:design',
        source='doc_library',
        tags=['combat'],
        extra={'doc_path': source_path, 'doc_type': 'design'},
    )


def _table_index() -> TableIndex:
    return TableIndex(
        table_name='SkillTable',
        source_path='Tables/SkillTable.xlsx',
        source_hash='sha256:table',
        svn_revision=7,
        system='combat',
        row_count=2,
        primary_key='ID',
        ai_summary='skill schema',
        ai_summary_confidence=0.9,
        fields=[FieldInfo(name='ID', type='int', description='identifier', confidence=FieldConfidence.CONFIRMED)],
        last_indexed_at=datetime(2026, 1, 1, 12, 0, 0),
        indexer_model='test-model',
    )


def _doc_index() -> DocIndex:
    return DocIndex(
        source_path='Docs/Combat.md',
        source_hash='sha256:doc-index',
        svn_revision=18,
        doc_type='design',
        title='Combat Overview',
        summary='combat loop summary',
        related_tables=['SkillTable'],
        last_indexed_at=datetime(2026, 1, 1, 12, 0, 0),
    )


def _code_index() -> CodeFileIndex:
    return CodeFileIndex(
        source_path='Scripts/CombatResolver.cs',
        source_hash='sha256:script-index',
        svn_revision=31,
        namespace='Game.Combat',
        symbols=[
            CodeSymbol(
                name='CombatResolver',
                kind='class',
                signature='class CombatResolver',
                line_start=10,
                line_end=30,
                references=[
                    CodeSymbolReference(
                        target_kind='table',
                        target_table='SkillTable',
                        line=12,
                        snippet='SkillTable.Get(skillId)',
                        confidence='confirmed',
                    )
                ],
                summary='combat logic',
            )
        ],
        references=[
            CodeSymbolReference(
                target_kind='symbol',
                target_symbol='DamageFormula',
                line=18,
                snippet='DamageFormula.Calculate()',
                confidence='inferred',
            )
        ],
        indexer_version='regex.v1',
    )


def _knowledge_map(release_id: str):
    return build_minimal_map(
        release_id,
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
                title='Combat Approved',
                source_path='KB/CombatApproved.md',
                source_hash='sha256:approved',
                system_id='combat',
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id='combat-script',
                title='Combat Resolver',
                source_path='Scripts/CombatResolver.cs',
                source_hash='sha256:script-index',
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


def _release_candidate(
    *,
    candidate_id: str = 'candidate-accepted',
    status: str = 'accepted',
    selected: bool = True,
    source_refs: list[str] | None = None,
) -> ReleaseCandidate:
    return ReleaseCandidate(
        candidate_id=candidate_id,
        test_plan_id=f'{candidate_id}-plan',
        status=status,
        title=f'{candidate_id} title',
        source_refs=list(source_refs or ['Tables/SkillTable.xlsx', 'KB/CombatApproved.md']),
        source_hash=f'sha256:{candidate_id}',
        selected=selected,
        created_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )


def _prepare_safe_build(monkeypatch, tmp_path, baseline_id: str) -> tuple[Path, Path, Path]:
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'value=1\n')
    _write_source(project_root, 'Docs/Combat.md', '# combat\n')
    _write_source(project_root, 'KB/CombatApproved.md', 'approved doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'class CombatResolver {}\n')

    baseline = build_knowledge_release(
        project_root,
        baseline_id,
        _knowledge_map(baseline_id),
        table_indexes=[_table_index()],
        doc_indexes=[_doc_index()],
        code_indexes=[_code_index()],
        knowledge_docs=[
            KnowledgeDocRef(
                doc_id='combat-doc',
                title='Combat Approved',
                source_path='KB/CombatApproved.md',
                source_hash='sha256:approved',
                system_id='combat',
                status='active',
            )
        ],
    )
    set_current_release(project_root, baseline.manifest.release_id)
    _write_table_indexes(project_root, [_table_index()])
    _write_code_indexes(workspace_dir, project_root, [_code_index()])
    _add_approved_doc(workspace_dir, 'KB/CombatApproved.md')
    return working_root, workspace_dir, project_root


def test_build_knowledge_release_creates_release_from_existing_indexes(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'value=1\n')
    _write_source(project_root, 'Docs/Combat.md', '# combat\n')
    _write_source(project_root, 'KB/CombatApproved.md', 'approved doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'class CombatResolver {}\n')

    result = build_knowledge_release(
        project_root,
        'release-001',
        _knowledge_map('release-001'),
        table_indexes=[_table_index()],
        doc_indexes=[_doc_index()],
        code_indexes=[_code_index()],
        knowledge_docs=[
            KnowledgeDocRef(
                doc_id='kb-combat-approved',
                title='Approved Combat KB',
                source_path='KB/CombatApproved.md',
                source_hash='sha256:approved',
                system_id='combat',
                status='active',
            )
        ],
        created_by='admin',
        release_notes='# release-001\n',
    )

    assert result.release_dir.exists()
    assert result.artifacts['table_schema'].count == 1
    assert result.artifacts['doc_knowledge'].count == 2
    assert result.artifacts['script_evidence'].count == 1
    assert result.artifacts['candidate_evidence'].count == 0
    assert not (result.release_dir / 'indexes' / 'candidate_evidence.jsonl').exists()


def test_build_knowledge_release_rejects_missing_project_root(tmp_path):
    with pytest.raises(KnowledgeProjectRootNotFoundError, match='Project root not found'):
        build_knowledge_release(
            tmp_path / 'missing-root',
            'release-003',
            _knowledge_map('release-003'),
            table_indexes=[],
            doc_indexes=[],
            code_indexes=[],
            knowledge_docs=[],
        )


def test_build_knowledge_release_from_current_indexes_uses_server_side_sources(monkeypatch, tmp_path):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline')

    result = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-safe-001',
        release_notes='# safe build\n',
    )

    assert result.manifest.release_id == 'release-safe-001'
    assert result.artifacts['candidate_evidence'].count == 0
    assert result.knowledge_map.release_id == 'release-safe-001'


def test_build_knowledge_release_from_current_indexes_prefers_saved_formal_map(monkeypatch, tmp_path):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-formal-map')
    saved_map = build_minimal_map(
        'formal-working',
        tables=[
            KnowledgeTableRef(
                table_id='SkillTable',
                title='SkillTable Formal',
                source_path='Tables/SkillTable.xlsx',
                source_hash='sha256:table-formal',
                system_id='combat',
            )
        ],
        docs=[
            KnowledgeDocRef(
                doc_id='combat-doc',
                title='Combat Approved Formal',
                source_path='KB/CombatApproved.md',
                source_hash='sha256:approved-formal',
                system_id='combat',
            )
        ],
        scripts=[
            KnowledgeScriptRef(
                script_id='combat-script',
                title='Combat Resolver Formal',
                source_path='Scripts/CombatResolver.cs',
                source_hash='sha256:script-formal',
                system_id='combat',
            )
        ],
        relationships=[
            KnowledgeRelationship(
                relationship_id='rel-formal-working',
                from_ref='script:combat-script',
                to_ref='table:SkillTable',
                relation_type='references_table',
                source_hash='sha256:formal-relationship',
            )
        ],
    )
    saved_record = save_formal_knowledge_map(project_root, saved_map, updated_by='designer')
    formal_map_path = get_formal_map_path(project_root)
    working_payload_before = json.loads(formal_map_path.read_text(encoding='utf-8'))
    working_mtime_before = formal_map_path.stat().st_mtime_ns
    baseline_map_path = get_release_dir(project_root, 'release-baseline-formal-map') / 'map.json'
    baseline_map_before = baseline_map_path.read_text(encoding='utf-8')

    result = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-safe-formal-map',
    )

    release_map_path = result.release_dir / 'map.json'
    release_map = json.loads(release_map_path.read_text(encoding='utf-8'))
    assert result.knowledge_map.release_id == 'release-safe-formal-map'
    assert release_map['release_id'] == 'release-safe-formal-map'
    assert release_map['tables'][0]['title'] == 'SkillTable Formal'
    assert release_map['relationships'][0]['relation_type'] == 'references_table'
    assert result.manifest.map_hash == compute_map_hash(result.knowledge_map)
    assert result.manifest.map_hash == compute_map_hash(result.knowledge_map.__class__.model_validate(release_map))
    assert result.manifest.map_hash != saved_record.map_hash
    assert json.loads(formal_map_path.read_text(encoding='utf-8')) == working_payload_before
    assert formal_map_path.stat().st_mtime_ns == working_mtime_before
    assert baseline_map_path.read_text(encoding='utf-8') == baseline_map_before
    assert get_current_release(project_root).release_id == 'release-baseline-formal-map'


def test_build_knowledge_release_from_current_indexes_rewrites_saved_formal_map_release_id(monkeypatch, tmp_path):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-formal-mismatch')
    save_formal_knowledge_map(project_root, _knowledge_map('older-formal-release'))

    result = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-safe-rewritten-map',
    )

    release_map = json.loads((result.release_dir / 'map.json').read_text(encoding='utf-8'))
    assert result.knowledge_map.release_id == 'release-safe-rewritten-map'
    assert release_map['release_id'] == 'release-safe-rewritten-map'
    assert release_map['release_id'] != 'older-formal-release'


def test_build_knowledge_release_from_current_indexes_fails_on_invalid_saved_formal_map(monkeypatch, tmp_path):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-invalid-formal')
    formal_map_path = get_formal_map_path(project_root)
    formal_map_path.parent.mkdir(parents=True, exist_ok=True)
    formal_map_path.write_text(
        json.dumps(
            {
                'schema_version': 'formal-knowledge-map.v1',
                'map': {
                    'schema_version': 'knowledge-map.v1',
                    'release_id': 'bad-formal-release',
                    'tables': [
                        {
                            'schema_version': 'knowledge-table-ref.v1',
                            'table_id': 'SkillTable',
                            'title': 'SkillTable',
                            'source_path': '../escape.xlsx',
                            'source_hash': 'sha256:table',
                            'system_id': 'combat',
                            'status': 'active',
                        }
                    ],
                    'docs': [],
                    'scripts': [],
                    'systems': [],
                    'relationships': [],
                    'deprecated': [],
                    'source_hash': None,
                },
                'map_hash': 'sha256:not-real',
                'updated_at': datetime(2026, 5, 8, tzinfo=timezone.utc).isoformat(),
                'updated_by': 'designer',
            },
            ensure_ascii=False,
            indent=2,
        ) + '\n',
        encoding='utf-8',
    )

    with pytest.raises(KnowledgeReleasePrerequisiteError, match='Saved formal knowledge map is invalid'):
        build_knowledge_release_from_current_indexes(
            project_root,
            workspace_dir,
            'release-safe-invalid-formal',
        )

    assert not get_release_dir(project_root, 'release-safe-invalid-formal').exists()
    assert get_current_release(project_root).release_id == 'release-baseline-invalid-formal'


def test_build_knowledge_release_from_current_indexes_does_not_touch_svn(monkeypatch, tmp_path):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-no-svn')
    svn_dir = project_root / '.svn'
    svn_dir.mkdir(parents=True, exist_ok=True)
    svn_marker = svn_dir / 'entries'
    svn_marker.write_text('svn metadata\n', encoding='utf-8')

    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes
    original_write_text = Path.write_text
    original_write_bytes = Path.write_bytes

    def _guard_read_text(self: Path, *args, **kwargs):
        if '.svn' in self.parts:
            raise AssertionError('safe build must not read svn state')
        return original_read_text(self, *args, **kwargs)

    def _guard_read_bytes(self: Path, *args, **kwargs):
        if '.svn' in self.parts:
            raise AssertionError('safe build must not read svn state')
        return original_read_bytes(self, *args, **kwargs)

    def _guard_write_text(self: Path, *args, **kwargs):
        if '.svn' in self.parts:
            raise AssertionError('safe build must not write svn state')
        return original_write_text(self, *args, **kwargs)

    def _guard_write_bytes(self: Path, *args, **kwargs):
        if '.svn' in self.parts:
            raise AssertionError('safe build must not write svn state')
        return original_write_bytes(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', _guard_read_text)
    monkeypatch.setattr(Path, 'read_bytes', _guard_read_bytes)
    monkeypatch.setattr(Path, 'write_text', _guard_write_text)
    monkeypatch.setattr(Path, 'write_bytes', _guard_write_bytes)

    result = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-safe-no-svn',
    )

    assert result.manifest.release_id == 'release-safe-no-svn'
    assert original_read_text(svn_marker, encoding='utf-8') == 'svn metadata\n'


def test_build_knowledge_release_from_current_indexes_includes_selected_candidates(monkeypatch, tmp_path):
    working_root, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-candidate')
    append_release_candidate(project_root, _release_candidate())

    result = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-safe-with-candidate',
        candidate_ids=['candidate-accepted'],
    )

    evidence_path = result.release_dir / 'indexes' / 'candidate_evidence.jsonl'
    evidence_payload = [json.loads(line) for line in evidence_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert result.artifacts['candidate_evidence'].path == 'indexes/candidate_evidence.jsonl'
    assert result.artifacts['candidate_evidence'].count == 1
    assert evidence_payload == [
        {
            'candidate_id': 'candidate-accepted',
            'created_at': '2026-01-02T12:00:00Z',
            'project_key': get_project_store_dir(project_root).name,
            'schema_version': 'candidate-evidence-record.v1',
            'selected': True,
            'source_hash': 'sha256:candidate-accepted',
            'source_refs': ['KB/CombatApproved.md', 'Tables/SkillTable.xlsx'],
            'status': 'accepted',
            'test_plan_id': 'candidate-accepted-plan',
            'title': 'candidate-accepted title',
        }
    ]
    assert get_current_release(project_root).release_id == 'release-baseline-candidate'
    assert not (result.release_dir / 'Tables' / 'SkillTable.xlsx').exists()
    assert not (result.release_dir / 'KB' / 'CombatApproved.md').exists()


@pytest.mark.parametrize(
    ('candidate', 'candidate_ids', 'message'),
    [
        (None, ['missing-candidate'], 'Release candidate not found: missing-candidate'),
        (_release_candidate(candidate_id='candidate-pending', status='pending'), ['candidate-pending'], r'Release candidate must be accepted: candidate-pending \(pending\)'),
        (_release_candidate(candidate_id='candidate-rejected', status='rejected'), ['candidate-rejected'], r'Release candidate must be accepted: candidate-rejected \(rejected\)'),
        (_release_candidate(candidate_id='candidate-unselected', selected=False), ['candidate-unselected'], 'Release candidate must be selected for build: candidate-unselected'),
    ],
)
def test_build_knowledge_release_from_current_indexes_rejects_invalid_candidates(
    monkeypatch,
    tmp_path,
    candidate,
    candidate_ids,
    message,
):
    _, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-invalid-candidate')
    if candidate is not None:
        append_release_candidate(project_root, candidate)

    with pytest.raises(KnowledgeReleasePrerequisiteError, match=message):
        build_knowledge_release_from_current_indexes(
            project_root,
            workspace_dir,
            'release-safe-invalid-candidate',
            candidate_ids=candidate_ids,
        )


def test_build_knowledge_release_from_current_indexes_rejects_candidate_source_ref_escape(monkeypatch, tmp_path):
    working_root, workspace_dir, project_root = _prepare_safe_build(monkeypatch, tmp_path, 'release-baseline-invalid-path')
    release_candidates_path = working_root / 'game_data' / 'projects' / get_project_store_dir(project_root).name / 'project' / 'pending' / 'release_candidates.jsonl'
    release_candidates_path.parent.mkdir(parents=True, exist_ok=True)
    release_candidates_path.write_text(
        json.dumps(_release_candidate(candidate_id='candidate-bad-path', source_refs=['../Secrets.txt']).model_dump(mode='json'), ensure_ascii=False) + '\n',
        encoding='utf-8',
    )

    with pytest.raises(KnowledgeReleasePrerequisiteError, match=r"Invalid release candidate record at line 1: Invalid source path: '\.\./Secrets\.txt'"):
        build_knowledge_release_from_current_indexes(
            project_root,
            workspace_dir,
            'release-safe-invalid-path',
            candidate_ids=['candidate-bad-path'],
        )


def test_build_knowledge_release_from_current_indexes_requires_approved_docs(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'value=1\n')
    _write_source(project_root, 'Docs/Combat.md', '# combat\n')
    _write_source(project_root, 'KB/CombatApproved.md', 'approved doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'class CombatResolver {}\n')

    baseline = build_knowledge_release(
        project_root,
        'release-baseline-doc-check',
        _knowledge_map('release-baseline-doc-check'),
        table_indexes=[_table_index()],
        doc_indexes=[_doc_index()],
        code_indexes=[_code_index()],
        knowledge_docs=[
            KnowledgeDocRef(
                doc_id='combat-doc',
                title='Combat Approved',
                source_path='KB/CombatApproved.md',
                source_hash='sha256:approved',
                system_id='combat',
                status='active',
            )
        ],
    )
    set_current_release(project_root, baseline.manifest.release_id)
    _write_table_indexes(project_root, [_table_index()])
    _write_code_indexes(workspace_dir, project_root, [_code_index()])

    with pytest.raises(KnowledgeReleasePrerequisiteError, match='Approved docs are missing'):
        build_knowledge_release_from_current_indexes(project_root, workspace_dir, 'release-safe-002')


def test_build_knowledge_release_from_current_indexes_bootstraps_first_release_from_current_indexes(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'value=1\n')
    _write_source(project_root, 'KB/CombatApproved.md', 'approved doc\n')
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'class CombatResolver {}\n')
    _write_table_indexes(project_root, [_table_index()])
    _write_code_indexes(workspace_dir, project_root, [_code_index()])
    _add_approved_doc(workspace_dir, 'KB/CombatApproved.md')

    result = build_knowledge_release_from_current_indexes(project_root, workspace_dir, 'release-safe-003')

    assert result.manifest.release_id == 'release-safe-003'
    assert result.knowledge_map.release_id == 'release-safe-003'
    assert [table.table_id for table in result.knowledge_map.tables] == ['SkillTable']
    assert [doc.source_path for doc in result.knowledge_map.docs] == ['KB/CombatApproved.md']
    assert [script.source_path for script in result.knowledge_map.scripts] == ['Scripts/CombatResolver.cs']
    assert result.artifacts['table_schema'].count == 1
    assert result.artifacts['script_evidence'].count == 1
    assert result.artifacts['doc_knowledge'].count == 2


def test_build_knowledge_release_from_current_indexes_requires_current_indexes_for_first_release(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(
        KnowledgeReleasePrerequisiteError,
        match='Current table indexes are required to build the first knowledge release',
    ):
        build_knowledge_release_from_current_indexes(project_root, workspace_dir, 'release-safe-004')


def test_build_knowledge_release_from_current_indexes_requires_table_indexes_for_code_only_bootstrap(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)
    _write_source(project_root, 'Scripts/CombatResolver.cs', 'class CombatResolver {}\n')
    _write_code_indexes(workspace_dir, project_root, [_code_index()])

    with pytest.raises(
        KnowledgeReleasePrerequisiteError,
        match='Current table indexes are required to build the first knowledge release',
    ):
        build_knowledge_release_from_current_indexes(project_root, workspace_dir, 'release-safe-code-only')


def test_build_knowledge_release_from_current_indexes_rejects_approved_doc_path_escape(monkeypatch, tmp_path):
    working_root = tmp_path / 'ltclaw-data'
    workspace_dir = tmp_path / 'workspace'
    project_root = tmp_path / 'project-root'
    outside_secret = tmp_path / 'Secrets.txt'
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(working_root))
    project_root.mkdir(parents=True, exist_ok=True)
    _write_source(project_root, 'Tables/SkillTable.xlsx', 'value=1\n')
    _write_table_indexes(project_root, [_table_index()])
    outside_secret.write_text('top-secret\n', encoding='utf-8')
    _add_approved_doc(workspace_dir, '../Secrets.txt')

    original_read_bytes = Path.read_bytes

    def _guard_read_bytes(self: Path, *args, **kwargs):
        if self.resolve(strict=False) == outside_secret.resolve(strict=False):
            raise AssertionError('safe build must not read approved docs outside the project root')
        return original_read_bytes(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_bytes', _guard_read_bytes)

    with pytest.raises(KnowledgeReleasePrerequisiteError, match=r"Invalid approved doc path: '\.\./Secrets\.txt'"):
        build_knowledge_release_from_current_indexes(project_root, workspace_dir, 'release-safe-escaped-doc')
