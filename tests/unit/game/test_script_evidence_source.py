from __future__ import annotations

import time

from ltclaw_gy_x.game.cold_start_job import create_or_get_cold_start_job, load_cold_start_job
from ltclaw_gy_x.game.config import (
    ProjectScriptsSourceConfig,
    ProjectTablesSourceConfig,
    save_project_scripts_source_config,
    save_project_tables_source_config,
)
from ltclaw_gy_x.game.knowledge_formal_map_store import save_formal_knowledge_map
from ltclaw_gy_x.game.knowledge_rag_answer import build_rag_answer
from ltclaw_gy_x.game.knowledge_rag_context import build_current_release_context
from ltclaw_gy_x.game.knowledge_release_service import build_knowledge_release_from_current_indexes
from ltclaw_gy_x.game.knowledge_release_store import set_current_release
from ltclaw_gy_x.game.knowledge_source_candidate_store import load_latest_source_candidate
from ltclaw_gy_x.game.script_source_discovery import discover_script_sources


def _write_project_sources(project_root) -> None:
    tables_dir = project_root / 'Tables'
    scripts_dir = project_root / 'Scripts'
    tables_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )
    (tables_dir / 'WeaponConfig.csv').write_text(
        'ID,WeaponName,AttackBonus\n1001,IronSword,5\n',
        encoding='utf-8',
    )
    (scripts_dir / 'DamageCalculator.cs').write_text(
        'namespace Combat.Systems;\n\n'
        'public static class DamageCalculator\n'
        '{\n'
        '    public static int Calculate(int heroId, int weaponId)\n'
        '    {\n'
        '        return HeroTable.Attack + WeaponConfig.AttackBonus;\n'
        '    }\n'
        '}\n',
        encoding='utf-8',
    )
    (scripts_dir / 'CharacterGrowthService.lua').write_text(
        'local CharacterGrowthService = {}\n\n'
        'function CharacterGrowthService.apply_level(heroId, level)\n'
        '    return HeroTable.HP + level\n'
        'end\n\n'
        'return CharacterGrowthService\n',
        encoding='utf-8',
    )
    (scripts_dir / 'drop_formula.py').write_text(
        'def calculate_drop_rate(enemy_level: int) -> int:\n'
        '    return enemy_level + WeaponConfig.AttackBonus\n',
        encoding='utf-8',
    )


def test_discover_script_sources_marks_cs_lua_py_available(tmp_path):
    project_root = tmp_path / 'project-root'
    _write_project_sources(project_root)

    result = discover_script_sources(
        project_root,
        ProjectScriptsSourceConfig(
            roots=['Scripts'],
            include=['**/*.cs', '**/*.lua', '**/*.py'],
            exclude=[],
        ),
    )

    assert result['summary']['available_script_count'] == 3
    assert sorted(item['source_path'] for item in result['script_files']) == [
        'Scripts/CharacterGrowthService.lua',
        'Scripts/DamageCalculator.cs',
        'Scripts/drop_formula.py',
    ]
    assert {item['format'] for item in result['script_files']} == {'csharp', 'lua', 'python'}


def test_script_evidence_cold_start_candidate_release_and_rag(tmp_path, monkeypatch):
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
    save_project_scripts_source_config(
        project_root,
        ProjectScriptsSourceConfig(
            roots=['Scripts'],
            include=['**/*.cs', '**/*.lua', '**/*.py'],
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
    assert state.counts.canonical_script_count == 3
    assert state.counts.candidate_script_count == 3
    assert 'script:DamageCalculator' in state.candidate_refs
    assert 'script:CharacterGrowthService' in state.candidate_refs
    assert 'script:drop_formula' in state.candidate_refs

    candidate = load_latest_source_candidate(project_root)
    assert candidate is not None
    assert candidate.map is not None
    assert [script.script_id for script in candidate.map.scripts] == [
        'CharacterGrowthService',
        'DamageCalculator',
        'drop_formula',
    ]
    relationship_refs = {
        (relationship.from_ref, relationship.to_ref)
        for relationship in candidate.map.relationships
    }
    assert ('script:DamageCalculator', 'table:HeroTable') in relationship_refs
    assert ('script:DamageCalculator', 'table:WeaponConfig') in relationship_refs

    save_formal_knowledge_map(project_root, candidate.map, updated_by='maintainer')
    release = build_knowledge_release_from_current_indexes(
        project_root,
        workspace_dir,
        'release-script-001',
    )

    assert release.artifacts['script_evidence'].count == 3
    assert [script.script_id for script in release.knowledge_map.scripts] == [
        'CharacterGrowthService',
        'DamageCalculator',
        'drop_formula',
    ]

    set_current_release(project_root, release.manifest.release_id)
    context = build_current_release_context(
        project_root,
        'What does DamageCalculator use from WeaponConfig?',
        max_chunks=8,
        max_chars=4000,
    )

    assert context['mode'] == 'context'
    assert any(citation.get('ref') == 'script:DamageCalculator' for citation in context['citations'])
    assert any('WeaponConfig' in chunk.get('text', '') for chunk in context['chunks'])

    answer = build_rag_answer('What does DamageCalculator use from WeaponConfig?', context)

    assert answer['mode'] == 'answer'
    assert any(citation.get('ref') == 'script:DamageCalculator' for citation in answer['citations'])
    assert 'WeaponConfig' in answer['answer']
