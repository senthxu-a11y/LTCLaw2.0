"""单元测试: SvnWatcher 启停与轮询参数。"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.svn_watcher import SvnWatcher


def _project(poll=120):
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="svn://x", poll_interval_seconds=poll, jitter_seconds=10),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


def _make_svn_mock(revision=10):
    m = MagicMock()
    m.info = AsyncMock(return_value={"revision": revision, "url": "svn://x"})
    return m


def test_poll_interval_from_project():
    w = SvnWatcher(project=_project(poll=200), svn_client=_make_svn_mock())
    assert w.poll_interval == 200


def test_poll_interval_explicit_overrides_project():
    w = SvnWatcher(project=_project(poll=200), svn_client=_make_svn_mock(), poll_interval=33)
    assert w.poll_interval == 33


def test_initial_state_not_running():
    w = SvnWatcher(project=_project(), svn_client=_make_svn_mock())
    assert w._running is False
    assert w._task is None
    assert w._last_checked_revision is None


@pytest.mark.asyncio
async def test_start_then_stop_idempotent():
    svn = _make_svn_mock(revision=5)
    w = SvnWatcher(project=_project(poll=999999), svn_client=svn)
    await w.start()
    assert w._running is True
    assert w._last_checked_revision == 5
    await w.start()
    await w.stop()
    assert w._running is False
    await w.stop()


@pytest.mark.asyncio
async def test_start_with_failing_initial_revision_falls_back_to_zero():
    svn = MagicMock()
    svn.info = AsyncMock(side_effect=RuntimeError("boom"))
    w = SvnWatcher(project=_project(poll=999999), svn_client=svn)
    await w.start()
    try:
        assert w._last_checked_revision == 0
    finally:
        await w.stop()