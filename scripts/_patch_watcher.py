# -*- coding: utf-8 -*-
"""Patch SvnWatcher.trigger_now + game_svn router fallback."""
from pathlib import Path

# 1. Add trigger_now to SvnWatcher
p1 = Path(r"e:\LTClaw2.0\LTclaw2.0\src\ltclaw_gy_x\game\svn_watcher.py")
src1 = p1.read_text(encoding="utf-8")
old1 = "    async def force_check(self) -> Optional[ChangeSet]:"
inject = '''    async def trigger_now(self) -> Optional[ChangeSet]:
        """\u624b\u52a8\u89e6\u53d1\u4e00\u6b21\u5b8c\u6574\u540c\u6b65: svn update -> diff -> \u8fd4\u56de ChangeSet"""
        from_rev = self._last_checked_revision
        try:
            await self.svn.update()
        except Exception as e:
            logger.error(f"svn update \u5931\u8d25: {e}")
            self._error_count += 1
            raise
        try:
            current_revision = await self._get_current_revision()
        except Exception as e:
            logger.error(f"\u83b7\u53d6\u5f53\u524drevision\u5931\u8d25: {e}")
            self._error_count += 1
            raise
        cs: Optional[ChangeSet] = None
        if from_rev is not None and current_revision > from_rev:
            try:
                cs = await self.svn.diff_paths(from_rev + 1, current_revision)
                cs = self._filter_changeset(cs)
                if cs and self.change_callback:
                    await self._trigger_change_callback(cs)
                    self._change_count += 1
            except Exception as e:
                logger.error(f"\u83b7\u53d6\u53d8\u66f4\u96c6\u5931\u8d25: {e}")
        self._last_checked_revision = current_revision
        self._last_check_time = datetime.now()
        self._check_count += 1
        if cs is None:
            from .models import ChangeSet as _CS
            cs = _CS(from_rev=from_rev or current_revision, to_rev=current_revision,
                     added=[], modified=[], deleted=[])
        return cs

'''
assert old1 in src1, "force_check not found"
src1 = src1.replace(old1, inject + old1, 1)
p1.write_bytes(src1.encode("utf-8"))
print("svn_watcher.py patched, size=", len(src1))

# 2. Add fallback to router
p2 = Path(r"e:\LTClaw2.0\LTclaw2.0\src\ltclaw_gy_x\app\routers\game_svn.py")
src2 = p2.read_text(encoding="utf-8")
old2 = '''    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is None:
        raise HTTPException(status_code=400, detail="SVN watcher not available")
    changeset = await svn_watcher.trigger_now()
    if hasattr(changeset, "model_dump"):
        return changeset.model_dump(mode="json")
    return changeset'''
new2 = '''    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is not None and hasattr(svn_watcher, "trigger_now"):
        changeset = await svn_watcher.trigger_now()
        if hasattr(changeset, "model_dump"):
            return changeset.model_dump(mode="json")
        return changeset
    # Fallback: \u76f4\u63a5\u7528 svn_client \u505a\u4e00\u6b21 update + info
    svn_client = getattr(game_service, "svn", None)
    if svn_client is None:
        raise HTTPException(
            status_code=400,
            detail=f"SVN watcher \u4e0d\u53ef\u7528\u4e14 svn_client \u672a\u521d\u59cb\u5316\u3002role={game_service.user_config.my_role}, configured={game_service.configured}",
        )
    try:
        await svn_client.update()
        info = await svn_client.info()
        rev = int(info.get("revision", 0)) if isinstance(info, dict) else 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"svn update \u5931\u8d25: {e}")
    return {"from_rev": rev, "to_rev": rev, "added": [], "modified": [], "deleted": [], "fallback": True}'''
assert old2 in src2, "router block not found"
src2 = src2.replace(old2, new2, 1)
p2.write_bytes(src2.encode("utf-8"))
print("game_svn.py patched, size=", len(src2))