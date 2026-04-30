from pathlib import Path
p = Path(r"e:\LTClaw2.0\LTclaw2.0\src\ltclaw_gy_x\app\routers\game_svn.py")
src = p.read_text(encoding="utf-8")

# 1. Add SvnNotInstalledError import
old_import = "from ...app.agent_context import get_agent_for_request\nfrom ...app.workspace.workspace import Workspace"
new_import = "from ...app.agent_context import get_agent_for_request\nfrom ...app.workspace.workspace import Workspace\nfrom ...game.svn_client import SvnNotInstalledError"
assert old_import in src
src = src.replace(old_import, new_import, 1)

# 2. Wrap trigger_now with SvnNotInstalledError handler
old_block = '''    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is not None and hasattr(svn_watcher, "trigger_now"):
        changeset = await svn_watcher.trigger_now()
        if hasattr(changeset, "model_dump"):
            return changeset.model_dump(mode="json")
        return changeset'''
new_block = '''    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is not None and hasattr(svn_watcher, "trigger_now"):
        try:
            changeset = await svn_watcher.trigger_now()
        except SvnNotInstalledError:
            raise HTTPException(
                status_code=400,
                detail="SVN \u547d\u4ee4\u884c\u5de5\u5177\u672a\u5b89\u88c5\u3002\u8bf7\u91cd\u88c5 TortoiseSVN \u52fe\u9009 'command line client tools'\uff0c\u6216\u5b89\u88c5 SlikSVN \u540e\u91cd\u542f\u684c\u9762\u3002",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"svn sync \u5931\u8d25: {e}")
        if hasattr(changeset, "model_dump"):
            return changeset.model_dump(mode="json")
        return changeset'''
assert old_block in src
src = src.replace(old_block, new_block, 1)

# 3. Wrap fallback with SvnNotInstalledError handler
old_fb = '''    try:
        await svn_client.update()
        info = await svn_client.info()
        rev = int(info.get("revision", 0)) if isinstance(info, dict) else 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"svn update \u5931\u8d25: {e}")'''
new_fb = '''    try:
        await svn_client.update()
        info = await svn_client.info()
        rev = int(info.get("revision", 0)) if isinstance(info, dict) else 0
    except SvnNotInstalledError:
        raise HTTPException(
            status_code=400,
            detail="SVN \u547d\u4ee4\u884c\u5de5\u5177\u672a\u5b89\u88c5\u3002\u8bf7\u91cd\u88c5 TortoiseSVN \u52fe\u9009 'command line client tools'\uff0c\u6216\u5b89\u88c5 SlikSVN \u540e\u91cd\u542f\u684c\u9762\u3002",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"svn update \u5931\u8d25: {e}")'''
assert old_fb in src
src = src.replace(old_fb, new_fb, 1)

p.write_bytes(src.encode("utf-8"))
print("game_svn.py patched, size=", len(src))