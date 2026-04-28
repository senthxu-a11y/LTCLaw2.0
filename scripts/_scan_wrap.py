from pathlib import Path
import sys

ROOT = Path(r"e:\LTClaw2.0\LTclaw2.0")
EXCLUDE = {".venv","node_modules","__pycache__","dist","build",".git"}
TARGETS = (".py",".ts",".tsx",".less",".json",".md")
HEADER = b"%TSD-Header-###%"

count = 0
wrapped = []
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    if any(part in EXCLUDE or part.endswith(".egg-info") for part in p.parts):
        continue
    if p.suffix not in TARGETS:
        continue
    try:
        with open(p, "rb") as f:
            head = f.read(16)
    except Exception:
        continue
    if head == HEADER:
        wrapped.append(str(p.relative_to(ROOT)))
        count += 1

print(f"WRAPPED COUNT: {count}")
for w in wrapped:
    print(w)