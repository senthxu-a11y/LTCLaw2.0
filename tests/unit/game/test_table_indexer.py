"""单元测试: TableIndexer 工具方法。"""
import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.table_indexer import TableIndexer


def _project():
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="svn://x", poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


@pytest.fixture
def indexer(tmp_path):
    return TableIndexer(project=_project(), model_router=None, cache_dir=tmp_path / "cache")


def test_cache_dirs_created(indexer):
    assert indexer.cache_dir.exists()
    assert indexer.field_cache_dir.exists()
    assert indexer.summary_cache_dir.exists()


def test_calculate_file_hash_stable(indexer, tmp_path):
    f = tmp_path / "data.csv"
    f.write_bytes(b"hello,world\n")
    h1 = indexer._calculate_file_hash(f)
    h2 = indexer._calculate_file_hash(f)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_calculate_file_hash_changes_on_content(indexer, tmp_path):
    a = tmp_path / "a.csv"; a.write_bytes(b"a")
    b = tmp_path / "b.csv"; b.write_bytes(b"b")
    assert indexer._calculate_file_hash(a) != indexer._calculate_file_hash(b)


def test_infer_field_type_str_when_empty(indexer):
    assert indexer._infer_field_type([]) == "str"
    assert indexer._infer_field_type([None, ""]) == "str"


def test_infer_field_type_numeric(indexer):
    result = indexer._infer_field_type([1, 2, 3])
    assert isinstance(result, str)
    assert result != ""