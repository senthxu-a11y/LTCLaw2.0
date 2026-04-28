"""
SVN CLI 薄封装
"""

import asyncio
import locale
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union

from .models import ChangeSet


class SvnError(Exception):
    pass


class SvnNotInstalledError(SvnError):
    pass


class SvnClient:
    def __init__(self, working_copy: Path, username: Union[str, None] = None, password: Union[str, None] = None):
        self.working_copy = Path(working_copy)
        self.username = username
        self.password = password
        self._encoding = self._get_encoding()

    def _get_encoding(self) -> str:
        try:
            return locale.getpreferredencoding(False)
        except Exception:
            return "utf-8"

    def _build_cmd(self, args: list[str], xml_output: bool = False) -> list[str]:
        cmd = ["svn"] + args
        if xml_output:
            cmd.append("--xml")
        if self.username:
            cmd.extend(["--username", self.username])
        if self.password:
            cmd.extend(["--password", self.password])
        cmd.append("--non-interactive")
        cmd.append("--trust-server-cert")
        return cmd

    async def _run_cmd(self, cmd: list[str]) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_copy,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                error_msg = stderr.decode(self._encoding, errors="replace").strip()
                raise SvnError(f"SVN命令失败: {' '.join(cmd)}\n错误: {error_msg}")
            return stdout.decode(self._encoding, errors="replace")
        except FileNotFoundError:
            raise SvnNotInstalledError("SVN命令行工具未安装或未在PATH中")
        except Exception as e:
            if isinstance(e, SvnError):
                raise
            raise SvnError(f"执行SVN命令时出错: {e}")

    async def info(self) -> dict:
        cmd = self._build_cmd(["info"], xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            entry = root.find("entry")
            if entry is None:
                raise SvnError("无法解析SVN info输出")
            revision = int(entry.get("revision", 0))
            url = entry.find("url")
            repository = entry.find("repository")
            return {
                "revision": revision,
                "url": url.text if url is not None else "",
                "root": repository.find("root").text if repository is not None and repository.find("root") is not None else "",
            }
        except ET.ParseError as e:
            raise SvnError(f"解析SVN info XML失败: {e}")

    async def status(self, paths: Union[list[Path], None] = None) -> list[dict]:
        cmd_args = ["status"]
        if paths:
            cmd_args.extend([str(p) for p in paths])
        cmd = self._build_cmd(cmd_args, xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            result = []
            for target in root.findall("target"):
                for entry in target.findall("entry"):
                    path = entry.get("path", "")
                    wc_status = entry.find("wc-status")
                    if wc_status is not None:
                        status = wc_status.get("item", "unknown")
                        result.append({"path": path, "status": status})
            return result
        except ET.ParseError as e:
            raise SvnError(f"解析SVN status XML失败: {e}")

    async def update(self) -> int:
        cmd = self._build_cmd(["update"], xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            target = root.find("target")
            if target is not None:
                return int(target.get("revision", 0))
            return 0
        except ET.ParseError as e:
            raise SvnError(f"解析SVN update XML失败: {e}")

    async def log(self, from_rev: int, to_rev: Union[int, str] = "HEAD",
                  paths: Union[list[Path], None] = None) -> list[dict]:
        cmd_args = ["log", f"-r{from_rev}:{to_rev}"]
        if paths:
            cmd_args.extend([str(p) for p in paths])
        cmd = self._build_cmd(cmd_args, xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            result = []
            for logentry in root.findall("logentry"):
                revision = int(logentry.get("revision", 0))
                author = logentry.find("author")
                date = logentry.find("date")
                msg = logentry.find("msg")
                result.append({
                    "revision": revision,
                    "author": author.text if author is not None else "",
                    "date": date.text if date is not None else "",
                    "message": msg.text if msg is not None else "",
                })
            return result
        except ET.ParseError as e:
            raise SvnError(f"解析SVN log XML失败: {e}")

    async def diff_paths(self, from_rev: int, to_rev: int) -> ChangeSet:
        cmd = self._build_cmd(["diff", "--summarize", f"-r{from_rev}:{to_rev}"])
        output = await self._run_cmd(cmd)
        added: list[str] = []
        modified: list[str] = []
        deleted: list[str] = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            status, path = parts
            rel_path = Path(path).relative_to(self.working_copy) if Path(path).is_absolute() else Path(path)
            rel_path_str = str(rel_path).replace("\\", "/")
            if status == "A":
                added.append(rel_path_str)
            elif status == "M":
                modified.append(rel_path_str)
            elif status == "D":
                deleted.append(rel_path_str)
        return ChangeSet(from_rev=from_rev, to_rev=to_rev, added=added, modified=modified, deleted=deleted)

    async def add(self, paths: list[Path]) -> None:
        if not paths:
            return
        status_list = await self.status(paths)
        status_map = {item["path"]: item["status"] for item in status_list}
        to_add = []
        for path in paths:
            rel_path = str(path.relative_to(self.working_copy) if path.is_absolute() else path)
            rel_path = rel_path.replace("\\", "/")
            if status_map.get(rel_path, "unversioned") == "unversioned":
                to_add.append(str(path))
        if to_add:
            cmd = self._build_cmd(["add"] + to_add)
            await self._run_cmd(cmd)

    async def commit(self, paths: list[Path], message: str) -> int:
        if not paths:
            raise SvnError("没有文件需要提交")
        cmd = self._build_cmd(["commit", "-m", message] + [str(p) for p in paths], xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            commit = root.find("commit")
            if commit is not None:
                return int(commit.get("revision", 0))
            info = await self.info()
            return info["revision"]
        except ET.ParseError as e:
            raise SvnError(f"解析SVN commit XML失败: {e}")

    async def revert(self, paths: list[Path]) -> None:
        if not paths:
            return
        cmd = self._build_cmd(["revert"] + [str(p) for p in paths])
        await self._run_cmd(cmd)

    @classmethod
    async def check_installed(cls) -> Union[str, None]:
        try:
            process = await asyncio.create_subprocess_exec(
                "svn", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                output = stdout.decode("utf-8", errors="replace")
                for line in output.split("\n"):
                    if "svn, version" in line.lower():
                        return line.strip()
                return "SVN已安装"
            return None
        except FileNotFoundError:
            return None
        except Exception:
            return None
