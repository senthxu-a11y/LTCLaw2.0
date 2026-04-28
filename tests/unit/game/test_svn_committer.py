from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from ltclaw_gy_x.game.change_proposal import ChangeProposal
from ltclaw_gy_x.game.svn_committer import CommitError, SvnCommitter


class _StubSvnClient:
    def __init__(self):
        self.add = AsyncMock()
        self.commit = AsyncMock(return_value=123)
        self.revert = AsyncMock()


@pytest.fixture
def proposal():
    return ChangeProposal(
        id="12345678abcdef00",
        title="Buff hero hp",
        description="Increase hero base hp.",
        ops=[],
        status="applied",
    )


@pytest.fixture
def svn_client():
    return _StubSvnClient()


@pytest.fixture
def committer(tmp_path, svn_client):
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    return SvnCommitter(svn_client, svn_root)


@pytest.mark.asyncio
async def test_commit_proposal_calls_add_before_commit(committer, svn_client, proposal):
    revision = await committer.commit_proposal(proposal, ["tables/Hero.csv"])

    assert revision == 123
    assert svn_client.add.await_count == 1
    assert svn_client.commit.await_count == 1
    assert svn_client.add.await_args_list[0].args[0] == [committer.svn_root / "tables/Hero.csv"]
    assert svn_client.commit.await_args_list[0].args[0] == [committer.svn_root / "tables/Hero.csv"]


@pytest.mark.asyncio
async def test_commit_proposal_formats_default_message(committer, svn_client, proposal):
    await committer.commit_proposal(proposal, ["tables/Hero.csv"])

    message = svn_client.commit.await_args_list[0].args[1]
    assert "[ltclaw][proposal:12345678] Buff hero hp" in message
    assert "Increase hero base hp." in message


@pytest.mark.asyncio
async def test_commit_proposal_converts_relative_paths_to_absolute(committer, svn_client, proposal):
    await committer.commit_proposal(proposal, ["tables/Hero.csv", "tables/Item.xlsx"])

    assert svn_client.add.await_args_list[0].args[0] == [
        committer.svn_root / "tables/Hero.csv",
        committer.svn_root / "tables/Item.xlsx",
    ]


@pytest.mark.asyncio
async def test_commit_proposal_wraps_commit_error(committer, svn_client, proposal):
    svn_client.commit.side_effect = RuntimeError("svn boom")

    with pytest.raises(CommitError) as exc_info:
        await committer.commit_proposal(proposal, ["tables/Hero.csv"])

    assert "svn boom" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, RuntimeError)


@pytest.mark.asyncio
async def test_revert_local_changes_forwards_to_client(committer, svn_client):
    paths = [Path("tables/Hero.csv")]

    await committer.revert_local_changes(paths)

    svn_client.revert.assert_awaited_once_with(paths)
