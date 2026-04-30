"""SVN client wrapper with CLI/TortoiseSVN fallback."""

import asyncio
import random
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import ChangeSet


class SvnError(Exception):
    pass


class SvnNotInstalledError(SvnError):
    pass


class TortoiseUiOnlyError(SvnError):
    pass


def _find_tortoise_dir() -> Path | None:
    candidates = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / "TortoiseSVN" / "bin")
    candidates.append(Path(r"C:/Program Files/TortoiseSVN/bin"))
    candidates.append(Path(r"C:/Program Files (x86)/TortoiseSVN/bin"))
    for directory in candidates:
        if (directory / "TortoiseProc.exe").exists() and (directory / "SubWCRev.exe").exists():
            return directory
    return None


def _find_svn_cli() -> str | None:
    cli = shutil.which("svn")
    if cli:
        return cli
    tortoise_dir = _find_tortoise_dir()
    if tortoise_dir:
        svn_exe = tortoise_dir / "svn.exe"
        if svn_exe.exists():
            return str(svn_exe)
    return None


class SvnClient:
    def __init__(self, working_copy: Path, username: str | None = None,
                 password: str | None = None, trust_server_cert: bool = False):
        self.working_copy = Path(working_copy)
        self.username = username
        self.password = password
        self.trust_server_cert = trust_server_cert
        self._svn_executable = _find_svn_cli()
        self._tortoise_dir = _find_tortoise_dir()

    def _require_cli(self, operation: str) -> str:
        if self._svn_executable:
            return self._svn_executable
        if self._tortoise_dir:
            raise TortoiseUiOnlyError(
                f"{operation} not supported in TortoiseSVN GUI-only mode."
            )
        raise SvnNotInstalledError("SVN CLI not installed or not in PATH")

    def _build_cmd(self, args: list[str], xml_output: bool = False) -> list[str]:
        operation = args[0] if args else "svn"
        cmd = [self._require_cli(operation), *args]
        if xml_output:
            cmd.append("--xml")
        if self.username:
            cmd.extend(["--username", self.username])
        if self.password:
            cmd.extend(["--password", self.password])
        if self.trust_server_cert:
            cmd.append("--trust-server-cert")
        cmd.append("--non-interactive")
        return cmd

    async def _run_cmd(self, cmd: list[str]) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.working_copy),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode("utf-8", errors="ignore")
            error_msg = stderr.decode("utf-8", errors="ignore").strip()
            if process.returncode != 0:
                raise SvnError(f"SVN cmd failed: {' '.join(cmd)}\nstderr: {error_msg}\nstdout: {output}")
            return output
        except FileNotFoundError:
            raise SvnNotInstalledError("SVN CLI not installed or not in PATH")
        except Exception as e:
            if isinstance(e, SvnError):
                raise
            raise SvnError(f"Error executing SVN cmd: {e}")

    async def check_installed(self) -> str:
        cli = _find_svn_cli()
        if not cli:
            if _find_tortoise_dir():
                return "tortoise-gui-only"
            raise SvnNotInstalledError("SVN CLI not installed or not in PATH")
        process = await asyncio.create_subprocess_exec(
            cli,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise SvnNotInstalledError(stderr.decode("utf-8", errors="ignore").strip() or "SVN unavailable")
        return stdout.decode("utf-8", errors="ignore").strip()

    async def info(self) -> dict:
        if self._svn_executable:
            output = await self._run_cmd(self._build_cmd(["info"], xml_output=True))
            try:
                root = ET.fromstring(output)
                entry = root.find("entry")
                if entry is None:
                    raise SvnError("Cannot parse SVN info output")
                return {
                    "revision": int(entry.attrib.get("revision", "0")),
                    "url": entry.findtext("url", default=""),
                    "root": entry.findtext("repository/root", default=""),
                }
            except ET.ParseError as e:
                raise SvnError(f"Failed to parse SVN info XML: {e}")
        return await self._tortoise_info()

    async def status(self) -> list[dict]:
        output = await self._run_cmd(self._build_cmd(["status"], xml_output=True))
        try:
            root = ET.fromstring(output)
            items = []
            for entry in root.findall("target/entry"):
                path = entry.attrib.get("path", "")
                wc_status = entry.find("wc-status")
                items.append({
                    "path": path,
                    "item": wc_status.attrib.get("item", "") if wc_status is not None else "",
                })
            return items
        except ET.ParseError as e:
            raise SvnError(f"Failed to parse SVN status XML: {e}")

    async def update(self) -> int:
        if self._svn_executable:
            output = await self._run_cmd(self._build_cmd(["update"]))
            m = re.search(r"(?:At|Updated to) revision (\d+)", output)
            if m:
                return int(m.group(1))
            return int((await self.info()).get("revision", 0))
        return await self._tortoise_update()

    async def _tortoise_update(self) -> int:
        if not self._tortoise_dir:
            raise SvnNotInstalledError("TortoiseSVN not installed")
        tproc = self._tortoise_dir / "TortoiseProc.exe"
        process = await asyncio.create_subprocess_exec(
            str(tproc),
            "/command:update",
            f"/path:{self.working_copy}",
            "/closeonend:1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise SvnError(f"TortoiseProc update exit code: {process.returncode}")
        return int((await self.info()).get("revision", 0))

    async def _tortoise_info(self) -> dict:
        if not self._tortoise_dir:
            raise SvnNotInstalledError("TortoiseSVN not installed")
        subwc = self._tortoise_dir / "SubWCRev.exe"
        process = await asyncio.create_subprocess_exec(
            str(subwc),
            str(self.working_copy),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            err = stderr.decode("utf-8", errors="ignore").strip()
            raise SvnError(f"SubWCRev failed: {err}")
        text = stdout.decode("utf-8", errors="ignore")
        matches = re.findall(r"\d+", text)
        revision = int(matches[-1]) if matches else 0
        return {
            "revision": revision,
            "url": str(self.working_copy),
            "root": str(self.working_copy),
        }

    async def diff_paths(self, from_rev: int, to_rev: int) -> ChangeSet:
        output = await self._run_cmd(
            self._build_cmd(["log", "-v", "-r", f"{from_rev}:{to_rev}"], xml_output=True)
        )
        try:
            root = ET.fromstring(output)
            added: list[str] = []
            modified: list[str] = []
            deleted: list[str] = []
            for logentry in root.findall("logentry"):
                paths_node = logentry.find("paths")
                if paths_node is None:
                    continue
                for path_node in paths_node.findall("path"):
                    path_text = (path_node.text or "").lstrip("/")
                    action = path_node.attrib.get("action", "")
                    if action == "A":
                        added.append(path_text)
                    elif action == "M":
                        modified.append(path_text)
                    elif action == "D":
                        deleted.append(path_text)
            return ChangeSet(from_rev=from_rev, to_rev=to_rev, added=added, modified=modified, deleted=deleted)
        except ET.ParseError as e:
            raise SvnError(f"Failed to parse SVN log XML: {e}")

    async def add(self, paths: list[Path]) -> None:
        if not paths:
            return
        cmd = self._build_cmd(["add", *[str(path) for path in paths], "--force"])
        await self._run_cmd(cmd)

    async def commit(self, paths: list[Path], message: str) -> int:
        if not paths:
            raise SvnError("No paths to commit")
        output = await self._run_cmd(
            self._build_cmd(["commit", *[str(path) for path in paths], "-m", message])
        )
        m = re.search(r"Committed revision (\d+)", output)
        if m:
            return int(m.group(1))
        return int((await self.info()).get("revision", 0))

    async def revert(self, paths: list[Path]) -> None:
        if not self._svn_executable and self._tortoise_dir:
            raise TortoiseUiOnlyError("revert not supported in TortoiseSVN GUI-only mode.")
        if not paths:
            return
        cmd = self._build_cmd(["revert", *[str(path) for path in paths]])
        await self._run_cmd(cmd)


_CONFLICT_PATTERNS = (
    "out of date",
    "out-of-date",
    "conflict",
    "e155011",
    "e160028",
    "e170004",
    "txn-current-lock",
    "needs update",
)


def _looks_like_conflict(err: BaseException) -> bool:
    text = str(err).lower()
    return any(pat in text for pat in _CONFLICT_PATTERNS)


async def _svn_commit_with_retry(
    client: "SvnClient",
    paths: list[Path],
    message: str,
    *,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> int:
    last_err: BaseException | None = None
    for attempt in range(max_retries):
        try:
            return await client.commit(paths, message)
        except SvnError as exc:
            if not _looks_like_conflict(exc):
                raise
            last_err = exc
            if attempt + 1 >= max_retries:
                break
            try:
                await client.update()
            except SvnError:
                pass
            delay = base_delay * (2 ** attempt) * random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
    raise SvnError(f"commit_with_retry exhausted after {max_retries} attempts: {last_err}")


async def _commit_with_retry_method(
    self: "SvnClient",
    paths: list[Path],
    message: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> int:
    return await _svn_commit_with_retry(
        self, paths, message, max_retries=max_retries, base_delay=base_delay
    )


SvnClient.commit_with_retry = _commit_with_retry_method