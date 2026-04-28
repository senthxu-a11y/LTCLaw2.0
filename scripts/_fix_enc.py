from pathlib import Path
d = Path("tests/unit/game")
for p in d.glob("*.py"):
    raw = p.read_bytes()
    txt = None
    for enc in ("utf-16","utf-16-le","utf-8-sig","utf-8"):
        try:
            txt = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    if txt is None:
        print("FAIL", p); continue
    txt = txt.replace("\x00","").lstrip("\ufeff")
    p.write_bytes(txt.encode("utf-8"))
    print("OK", p.name, len(raw), "->", p.stat().st_size)