# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"e:\LTClaw2.0\LTclaw2.0\console\src\pages\Game\SvnSync.tsx")
content = p.read_text(encoding="utf-8")

# Fix 1: Add gameApi import
old_import = 'import { gameChangeApi } from "../../api/modules/gameChange";'
new_import = '''import { gameApi } from "../../api/modules/game";
import { gameChangeApi } from "../../api/modules/gameChange";'''
if old_import in content and 'import { gameApi }' not in content:
    content = content.replace(old_import, new_import, 1)
    print("Added gameApi import")

# Fix 2: Replace handleManualSync 
old_sync = '''  const handleManualSync = async () => {
    try {
      message.info(t("svnSync.syncStarted"));
      // Placeholder - actual API call would be:
      // await fetch('/api/game-project/sync/trigger', { method: 'POST' });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      message.success(t("svnSync.syncSuccess"));
      fetchSyncStatus(); // Refresh status
    } catch (err) {
      message.error(t("svnSync.syncFailed"));
    }
  };'''

new_sync = '''  const handleManualSync = async () => {
    if (!selectedAgent) return;
    try {
      message.info(t("svnSync.syncStarted"));
      const result = await gameApi.triggerSync(selectedAgent);
      message.success(t("svnSync.syncSuccess"));
      fetchSyncStatus(); // Refresh status
      if (result && result.changes && result.changes.length > 0) {
        setChangeLog(prev => [...result.changes, ...prev]);
      }
    } catch (err: any) {
      const errMsg = err?.message || t("svnSync.syncFailed");
      message.error(errMsg);
    }
  };'''

if old_sync in content:
    content = content.replace(old_sync, new_sync, 1)
    print("Replaced handleManualSync with real API call")

p.write_bytes(content.encode("utf-8"))
print(f"Done. File size: {len(content)} chars")