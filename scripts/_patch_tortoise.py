"""
Append TortoiseSVN fallback to SvnClient.
\u5728 _run_cmd \u4e0d\u53ef\u7528\u65f6\uff0c\u81ea\u52a8\u68c0\u6d4b TortoiseSVN \u5e76\u5207\u6362\u5230\u5b83\u3002
"""
from pathlib import Path

p = Path(r"e:\LTClaw2.0\LTclaw2.0\src\ltclaw_gy_x\game\svn_client.py")
src = p.read_text(encoding="utf-8")

# 1. \u5728 imports \u540e\u52a0\u8f85\u52a9\u51fd\u6570 + Tortoise \u8def\u5f84\u8bc6\u522b
old_imports = '''from .models import ChangeSet


class SvnError(Exception):'''
new_imports = '''import os
import re
import shutil
from .models import ChangeSet


_TORTOISE_CANDIDATES = [
    r"C:\\Program Files\\TortoiseSVN\\bin",
    r"C:\\Program Files (x86)\\TortoiseSVN\\bin",
]


def _find_tortoise_dir() -> Path | None:
    for c in _TORTOISE_CANDIDATES:
        d = Path(c)
        if (d / "TortoiseProc.exe").exists() and (d / "SubWCRev.exe").exists():
            return d
    return None


def _has_svn_cli() -> bool:
    return shutil.which("svn") is not None


class SvnError(Exception):'''
assert old_imports in src
src = src.replace(old_imports, new_imports, 1)

# 2. \u6539 __init__ \uff1a\u68c0\u6d4b mode + Tortoise \u8def\u5f84
old_init = '''    def __init__(self, working_copy: Path, username: Union[str, None] = None, password: Union[str, None] = None):
        self.working_copy = Path(working_copy)
        self.username = username
        self.password = password
        self._encoding = self._get_encoding()'''
new_init = '''    def __init__(self, working_copy: Path, username: Union[str, None] = None, password: Union[str, None] = None):
        self.working_copy = Path(working_copy)
        self.username = username
        self.password = password
        self._encoding = self._get_encoding()
        # \u6a21\u5f0f\u63a2\u6d4b\uff1a\u4f18\u5148 svn CLI\uff1b\u5426\u5219\u56de\u9000 TortoiseSVN
        self._mode = "cli" if _has_svn_cli() else None
        self._tortoise_dir: Path | None = None
        if self._mode is None:
            tdir = _find_tortoise_dir()
            if tdir is not None:
                self._mode = "tortoise"
                self._tortoise_dir = tdir
            else:
                self._mode = "cli"  # \u4ecd\u8bbe cli\uff0c\u8c03\u7528\u65f6\u62a5 SvnNotInstalledError'''
assert old_init in src
src = src.replace(old_init, new_init, 1)

# 3. \u91cd\u5199 update() \u548c info() \u52a0 Tortoise \u5206\u652f\uff0c\u5176\u4ed6\u9ad8\u7ea7\u64cd\u4f5c\u4e0d\u53ef\u7528\u65f6\u62a5\u9519
old_update = '''    async def update(self) -> int:
        cmd = self._build_cmd(["update"], xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            target = root.find("target")
            if target is not None:
                return int(target.get("revision", 0))
            return 0
        except ET.ParseError as e:
            raise SvnError(f"\u89e3\u6790SVN update XML\u5931\u8d25: {e}")'''
new_update = '''    async def update(self) -> int:
        if self._mode == "tortoise":
            return await self._tortoise_update()
        cmd = self._build_cmd(["update"], xml_output=True)
        output = await self._run_cmd(cmd)
        try:
            root = ET.fromstring(output)
            target = root.find("target")
            if target is not None:
                return int(target.get("revision", 0))
            return 0
        except ET.ParseError as e:
            raise SvnError(f"\u89e3\u6790SVN update XML\u5931\u8d25: {e}")

    async def _tortoise_update(self) -> int:
        """\u7528 TortoiseProc \u89e6\u53d1 update\uff0c\u63a5\u7740\u7528 SubWCRev \u8bfb\u65b0 revision\u3002"""
        tproc = self._tortoise_dir / "TortoiseProc.exe"
        cmd = [str(tproc), "/command:update", f"/path:{self.working_copy}", "/closeonend:1", "/notempfile"]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        # TortoiseProc \u8fd4\u56de 0 \u8868\u793a\u7528\u6237\u70b9\u4e86 OK\uff1b/closeonend:1 \u540e\u65e0\u9519\u4f1a\u81ea\u5173
        if process.returncode not in (0, None):
            raise SvnError(f"TortoiseProc update \u9000\u51fa\u7801: {process.returncode}")
        info = await self.info()
        return int(info.get("revision", 0))'''
assert old_update in src
src = src.replace(old_update, new_update, 1)

# 4. \u91cd\u5199 info() \u52a0 Tortoise \u5206\u652f
old_info = '''    async def info(self) -> dict:
        cmd = self._build_cmd(["info"], xml_output=True)
        output = await self._run_cmd(cmd)'''
new_info = '''    async def info(self) -> dict:
        if self._mode == "tortoise":
            return await self._tortoise_info()
        cmd = self._build_cmd(["info"], xml_output=True)
        output = await self._run_cmd(cmd)'''
assert old_info in src
src = src.replace(old_info, new_info, 1)

# 5. \u5728\u7c7b\u672b\u5c3e\uff08\u7528 revert \u4f5c\u4e3a\u951a\u70b9\uff09\u540e\u9762\u63d2\u5165 _tortoise_info \u548c \u5176\u4ed6\u4e0d\u652f\u6301\u63d0\u793a
old_tail = '''    async def revert(self, paths: list[Path]) -> None:
        if not paths:
            return
        cmd = self._build_cmd(["revert"] + [str(p) for p in paths])
        await self._run_cmd(cmd)'''
new_tail = '''    async def revert(self, paths: list[Path]) -> None:
        if not paths:
            return
        if self._mode == "tortoise":
            raise SvnError("revert \u5728 TortoiseSVN \u56de\u9000\u6a21\u5f0f\u4e0b\u4e0d\u652f\u6301\uff0c\u8bf7\u4f7f\u7528 TortoiseSVN GUI\u3002")
        cmd = self._build_cmd(["revert"] + [str(p) for p in paths])
        await self._run_cmd(cmd)

    async def _tortoise_info(self) -> dict:
        """\u7528 SubWCRev \u8bfb working copy revision \u4e0e URL\u3002"""
        subwc = self._tortoise_dir / "SubWCRev.exe"
        process = await asyncio.create_subprocess_exec(
            str(subwc), str(self.working_copy),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            err = stderr.decode(self._encoding, errors="replace").strip()
            raise SvnError(f"SubWCRev \u5931\u8d25: {err}")
        text = stdout.decode(self._encoding, errors="replace")
        # \u793a\u4f8b\u8f93\u51fa\uff1a"Last committed at revision 12345" \u4e0e "Updated to revision 12345"
        rev = 0
        m = re.search(r"Updated to revision\s+(\d+)", text)
        if m:
            rev = int(m.group(1))
        else:
            m = re.search(r"Last committed at revision\s+(\d+)", text)
            if m:
                rev = int(m.group(1))
        # SubWCRev \u4e0d\u8f93\u51fa URL\uff0c\u4ece .svn/wc.db \u8bfb\u4e00\u4e0b\uff1b\u672a\u5b9e\u73b0\u65f6\u8fd4 ""
        url = self._read_url_from_wc()
        return {"revision": rev, "url": url, "root": ""}

    def _read_url_from_wc(self) -> str:
        """\u5c1d\u8bd5\u4ece .svn/wc.db (sqlite) \u8bfb URL\uff0c\u5931\u8d25\u8fd4\u7a7a\u5b57\u7b26\u4e32\u3002"""
        try:
            import sqlite3
            db = self.working_copy / ".svn" / "wc.db"
            if not db.exists():
                return ""
            conn = sqlite3.connect(str(db))
            try:
                cur = conn.execute("SELECT root FROM REPOSITORY LIMIT 1")
                row = cur.fetchone()
                return row[0] if row else ""
            finally:
                conn.close()
        except Exception:
            return ""'''
assert old_tail in src
src = src.replace(old_tail, new_tail, 1)

# 6. \u5728 _run_cmd \u91cc\u63d0\u793a\u66f4\u53cb\u597d\uff1a\u5982\u679c mode==tortoise \u4f46\u6709\u4eba\u8c03\u4e0d\u652f\u6301\u7684\u9ad8\u7ea7 cmd\uff0c\u4e0d\u52a8 (\u8d70\u539f FileNotFoundError \u8def\u5f84)
# \u4fdd\u6301\u539f\u72b6\u3002

p.write_bytes(src.encode("utf-8"))
print("svn_client.py patched, size=", len(src))

# \u9a8c\u8bc1\u8bed\u6cd5
import py_compile
py_compile.compile(str(p), doraise=True)
print("syntax OK")