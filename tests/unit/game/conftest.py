import pytest
from pathlib import Path
from ltclaw_gy_x.game.config import ProjectConfig, UserGameConfig, ProjectMeta, SvnConfig, FilterConfig, TableConvention


@pytest.fixture
def fake_svn_root(tmp_path):
    svn_root = tmp_path / "svn_root"
    svn_root.mkdir()
    index_dir = svn_root / ".ltclaw_index"
    index_dir.mkdir()
    (index_dir / "tables").mkdir()
    (index_dir / "docs").mkdir()
    return svn_root


@pytest.fixture
def sample_project_config():
    return ProjectConfig(
        project=ProjectMeta(
            name="Test Game",
            engine="Unity",
            language="zh-CN"
        ),
        svn=SvnConfig(
            root="svn://test.server/repo",
            poll_interval_seconds=300,
            jitter_seconds=30
        ),
        paths=[],
        filters=FilterConfig(
            include_ext=[".xlsx", ".csv"],
            exclude_glob=["~$*"]
        ),
        table_convention=TableConvention(),
        doc_templates={},
        models={}
    )


@pytest.fixture
def fake_workspace_dir(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "game_index").mkdir()
    return workspace_dir
