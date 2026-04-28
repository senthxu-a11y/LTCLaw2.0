"""单元测试: GameService 启停与未配置态。"""
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
    UserGameConfig,
)
from ltclaw_gy_x.game.service import GameService


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("QWENPAW_WORKING_DIR", str(tmp_path / "qpw"))
    yield tmp_path


@pytest.fixture
def service(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return GameService(workspace_dir=workspace, runner=None, channel_manager=None)


def test_initial_state_unconfigured(service):
    assert service.configured is False
    assert service.project_config is None
    assert service.svn is None
    assert service.table_indexer is None
    assert service.dependency_resolver is None
    assert service.index_committer is None
    assert service.svn_watcher is None
    assert service.query_router is None
    assert service.proposal_store is None
    assert service.change_applier is None
    assert service.svn_committer is None


def test_workspace_game_dir_created(service, tmp_path):
    assert (tmp_path / "workspace" / "game_index").exists()


@pytest.mark.asyncio
async def test_start_without_config_completes(service):
    await service.start()
    assert service._started is True
    assert service.configured is False
    assert service.query_router is not None
    assert service.proposal_store is not None
    assert service.change_applier is None
    assert service.svn_committer is None
    await service.stop()
    assert service._started is False


@pytest.mark.asyncio
async def test_double_start_is_idempotent(service):
    await service.start()
    started_at = service._started
    await service.start()
    assert service._started == started_at
    await service.stop()


@pytest.mark.asyncio
async def test_stop_without_start_is_safe(service):
    await service.stop()


@pytest.mark.asyncio
async def test_index_tables_raises_without_indexer(service):
    with pytest.raises(RuntimeError):
        await service.index_tables(["foo.xlsx"])


def _project_config(svn_root: Path) -> ProjectConfig:
    return ProjectConfig(
        project=ProjectMeta(name="Test Game", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root=str(svn_root), poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


@pytest.mark.asyncio
async def test_start_with_consumer_config_creates_proposal_store_and_change_applier(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch("ltclaw_gy_x.game.service.load_user_config", return_value=UserGameConfig(my_role="consumer", svn_local_root=str(svn_root))), \
         patch("ltclaw_gy_x.game.service.load_project_config", return_value=_project_config(svn_root)):
        await service.start()

    assert service.proposal_store is not None
    assert service.change_applier is not None
    assert service.svn_committer is None


@pytest.mark.asyncio
async def test_start_with_maintainer_config_creates_svn_committer(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch("ltclaw_gy_x.game.service.load_user_config", return_value=UserGameConfig(my_role="maintainer", svn_local_root=str(svn_root))), \
         patch("ltclaw_gy_x.game.service.load_project_config", return_value=_project_config(svn_root)), \
         patch("ltclaw_gy_x.game.service.SvnClient.check_installed", AsyncMock(return_value="svn")):
        await service.start()

    assert service.proposal_store is not None
    assert service.change_applier is not None
    assert service.svn_committer is not None
