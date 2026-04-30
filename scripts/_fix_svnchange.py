from pathlib import Path
import uuid

p = Path(r"e:\LTClaw2.0\LTclaw2.0\console\src\pages\Game\SvnSync.tsx")
content = p.read_text(encoding="utf-8")

# Fix the ChangeSet to SvnChange conversion
old_conversion = '''        const newChanges = [
          ...result.added.map(path => ({ revision: result.to_rev, action: "A", path, author: "manual", timestamp: new Date().toISOString() })),
          ...result.modified.map(path => ({ revision: result.to_rev, action: "M", path, author: "manual", timestamp: new Date().toISOString() })),
          ...result.deleted.map(path => ({ revision: result.to_rev, action: "D", path, author: "manual", timestamp: new Date().toISOString() }))
        ];'''

new_conversion = '''        const newChanges: SvnChange[] = [
          ...result.added.map(path => ({ 
            id: `${result.to_rev}-A-${path}`, 
            revision: result.to_rev, 
            action: "A" as const, 
            paths: [path], 
            author: "manual", 
            timestamp: new Date().toISOString(),
            message: "Manual sync - file added"
          })),
          ...result.modified.map(path => ({ 
            id: `${result.to_rev}-M-${path}`, 
            revision: result.to_rev, 
            action: "M" as const, 
            paths: [path], 
            author: "manual", 
            timestamp: new Date().toISOString(),
            message: "Manual sync - file modified"
          })),
          ...result.deleted.map(path => ({ 
            id: `${result.to_rev}-D-${path}`, 
            revision: result.to_rev, 
            action: "D" as const, 
            paths: [path], 
            author: "manual", 
            timestamp: new Date().toISOString(),
            message: "Manual sync - file deleted"
          }))
        ];'''

if old_conversion in content:
    content = content.replace(old_conversion, new_conversion, 1)
    print("Fixed SvnChange type conversion")

p.write_bytes(content.encode("utf-8"))
print("Done")