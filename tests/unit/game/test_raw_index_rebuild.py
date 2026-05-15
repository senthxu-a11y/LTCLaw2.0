from __future__ import annotations

import asyncio

from ltclaw_gy_x.game.config import ProjectTablesSourceConfig
from ltclaw_gy_x.game.raw_index_rebuild import rebuild_raw_table_indexes


def test_rebuild_raw_table_indexes_succeeds_for_csv(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.csv'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is True
    assert result['raw_table_index_count'] == 1
    assert result['indexed_tables'][0]['table_id'] == 'HeroTable'
    assert result['errors'] == []


def test_rebuild_raw_table_indexes_reports_csv_requirement_for_xlsx_only(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.xlsx').write_text('fake', encoding='utf-8')

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.xlsx'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is False
    assert result['raw_table_index_count'] == 0
    assert result['indexed_tables'] == []
    assert result['next_action'] == 'configure_csv_tables_source'
    assert result['errors']
    assert result['errors'][0]['error'] == 'no_csv_table_files_available_for_rule_only_cold_start'
    assert any(item.get('source_path') == 'Tables/HeroTable.xlsx' for item in result['errors'])


def test_rebuild_raw_table_indexes_reports_csv_requirement_for_txt_only(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.txt').write_text(
        'ID\tName\tHP\tAttack\n1\tHeroA\t100\t20\n',
        encoding='utf-8',
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.txt'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is False
    assert result['raw_table_index_count'] == 0
    assert result['indexed_tables'] == []
    assert result['next_action'] == 'configure_csv_tables_source'
    assert result['errors']
    assert result['errors'][0]['error'] == 'no_csv_table_files_available_for_rule_only_cold_start'
    assert any(item.get('source_path') == 'Tables/HeroTable.txt' for item in result['errors'])


def test_rebuild_raw_table_indexes_ignores_non_csv_when_csv_exists(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )
    (tables_dir / 'OtherTable.xlsx').write_text('fake', encoding='utf-8')

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.csv', '**/*.xlsx'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is True
    assert result['raw_table_index_count'] == 1
    assert result['indexed_tables'][0]['table_id'] == 'HeroTable'