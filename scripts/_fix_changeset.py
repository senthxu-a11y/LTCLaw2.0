from pathlib import Path

p = Path(r"e:\LTClaw2.0\LTclaw2.0\console\src\pages\Game\SvnSync.tsx")
content = p.read_text(encoding="utf-8")

# Fix the API result handling 
old_handle = '''      if (result && result.changes && result.changes.length > 0) {
        setChangeLog(prev => [...result.changes, ...prev]);
      }'''

new_handle = '''      if (result && (result.added.length > 0 || result.modified.length > 0 || result.deleted.length > 0)) {
        // Convert ChangeSet to SvnChange format and update recent changes
        const newChanges = [
          ...result.added.map(path => ({ revision: result.to_rev, action: "A", path, author: "manual", timestamp: new Date().toISOString() })),
          ...result.modified.map(path => ({ revision: result.to_rev, action: "M", path, author: "manual", timestamp: new Date().toISOString() })),
          ...result.deleted.map(path => ({ revision: result.to_rev, action: "D", path, author: "manual", timestamp: new Date().toISOString() }))
        ];
        setRecentChanges(prev => [...newChanges, ...prev]);
      }'''

if old_handle in content:
    content = content.replace(old_handle, new_handle, 1)
    print("Fixed ChangeSet handling")

p.write_bytes(content.encode("utf-8"))
print("Done")