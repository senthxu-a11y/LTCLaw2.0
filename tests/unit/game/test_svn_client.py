"""单元测试: SvnClient (mock subprocess)。"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ltclaw_gy_x.game.svn_client import SvnClient, SvnError, SvnNotInstalledError


@pytest.fixture
def client(tmp_path):
    return SvnClient(working_copy=tmp_path)


def test_build_cmd_appends_flags(tmp_path):
    c = SvnClient(working_copy=tmp_path, username="u", password="p")
    cmd = c._build_cmd(["info"], xml_output=True)
    assert cmd[0] == "svn"
    assert "info" in cmd
    assert "--xml" in cmd
    assert "--username" in cmd and "u" in cmd
    assert "--password" in cmd and "p" in cmd
    assert "--non-interactive" in cmd


@pytest.mark.asyncio
async def test_run_cmd_raises_not_installed(client):
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
        with pytest.raises(SvnNotInstalledError):
            await client._run_cmd(["svn", "info"])


@pytest.mark.asyncio
async def test_run_cmd_raises_on_nonzero(client):
    fake = MagicMock()
    fake.returncode = 1
    fake.communicate = AsyncMock(return_value=(b"", b"boom"))
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake)):
        with pytest.raises(SvnError):
            await client._run_cmd(["svn", "info"])


@pytest.mark.asyncio
async def test_info_parses_revision(client):
    xml = (
        '<?xml version="1.0"?>'
        '<info>'
        '<entry revision="42">'
        '<url>svn://test/repo</url>'
        '<repository><root>svn://test/repo</root></repository>'
        '</entry>'
        '</info>'
    )
    with patch.object(client, "_run_cmd", AsyncMock(return_value=xml)):
        info = await client.info()
    assert info["revision"] == 42
    assert info["url"] == "svn://test/repo"


@pytest.mark.asyncio
async def test_info_invalid_xml_raises(client):
    with patch.object(client, "_run_cmd", AsyncMock(return_value="not xml")):
        with pytest.raises(SvnError):
            await client.info()


@pytest.mark.asyncio
async def test_check_installed_passthrough(client):
    if not hasattr(client, "check_installed"):
        pytest.skip("check_installed not present")
    with patch.object(client, "_run_cmd", AsyncMock(return_value="svn 1.14")):
        await client.check_installed()


@pytest.mark.asyncio
async def test_revert_builds_and_runs_command(client):
    with patch.object(client, "_run_cmd", AsyncMock()) as run_cmd:
        await client.revert([Path("tables/Hero.csv")])

    cmd = run_cmd.await_args_list[0].args[0]
    assert cmd[:2] == ["svn", "revert"]
    assert any(path.endswith("Hero.csv") for path in cmd[2:])
