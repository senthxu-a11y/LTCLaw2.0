"""单元测试: SvnClient (mock subprocess)。"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ltclaw_gy_x.game.svn_client import SvnClient, SvnError, SvnNotInstalledError, TortoiseUiOnlyError


@pytest.fixture
def client(tmp_path):
    with patch("ltclaw_gy_x.game.svn_client._find_svn_cli", return_value="svn"), patch(
        "ltclaw_gy_x.game.svn_client._find_tortoise_dir", return_value=None
    ):
        return SvnClient(working_copy=tmp_path)


def test_build_cmd_appends_flags(tmp_path):
    with patch("ltclaw_gy_x.game.svn_client._find_svn_cli", return_value="svn"), patch(
        "ltclaw_gy_x.game.svn_client._find_tortoise_dir", return_value=None
    ):
        client = SvnClient(working_copy=tmp_path, username="u", password="p")
    cmd = client._build_cmd(["info"], xml_output=True)
    assert Path(cmd[0]).name.lower() == "svn.exe" or cmd[0] == "svn"
    assert "info" in cmd
    assert "--xml" in cmd
    assert "--username" in cmd and "u" in cmd
    assert "--password" in cmd and "p" in cmd
    assert "--non-interactive" in cmd


def test_build_cmd_uses_tortoise_cli_when_path_missing(tmp_path):
    fake_tortoise_dir = tmp_path / "TortoiseSVN" / "bin"
    fake_tortoise_dir.mkdir(parents=True)
    (fake_tortoise_dir / "TortoiseProc.exe").write_text("", encoding="utf-8")
    (fake_tortoise_dir / "SubWCRev.exe").write_text("", encoding="utf-8")
    (fake_tortoise_dir / "svn.exe").write_text("", encoding="utf-8")

    with patch("ltclaw_gy_x.game.svn_client.shutil.which", return_value=None), patch(
        "ltclaw_gy_x.game.svn_client._find_tortoise_dir", return_value=fake_tortoise_dir
    ):
        client = SvnClient(working_copy=tmp_path)
        cmd = client._build_cmd(["status"], xml_output=False)

    assert Path(cmd[0]) == fake_tortoise_dir / "svn.exe"


def test_build_cmd_raises_for_tortoise_gui_only_install(tmp_path):
    fake_tortoise_dir = tmp_path / "TortoiseSVN" / "bin"
    fake_tortoise_dir.mkdir(parents=True)
    (fake_tortoise_dir / "TortoiseProc.exe").write_text("", encoding="utf-8")
    (fake_tortoise_dir / "SubWCRev.exe").write_text("", encoding="utf-8")

    with patch("ltclaw_gy_x.game.svn_client.shutil.which", return_value=None), patch(
        "ltclaw_gy_x.game.svn_client._find_tortoise_dir", return_value=fake_tortoise_dir
    ):
        client = SvnClient(working_copy=tmp_path)
        with pytest.raises(TortoiseUiOnlyError):
            client._build_cmd(["commit", "-m", "msg"])


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
    fake = MagicMock()
    fake.returncode = 0
    fake.communicate = AsyncMock(return_value=(b"svn, version 1.14\n", b""))
    with patch("ltclaw_gy_x.game.svn_client._find_svn_cli", return_value="svn"), patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=fake)
    ):
        result = await client.check_installed()
    assert result == "svn, version 1.14"


@pytest.mark.asyncio
async def test_revert_builds_and_runs_command(client):
    with patch.object(client, "_run_cmd", AsyncMock()) as run_cmd:
        await client.revert([Path("tables/Hero.csv")])

    cmd = run_cmd.await_args_list[0].args[0]
    assert Path(cmd[0]).name.lower() == "svn.exe" or cmd[0] == "svn"
    assert cmd[1] == "revert"
    assert any(path.endswith("Hero.csv") for path in cmd[2:])