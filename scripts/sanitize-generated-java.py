#!/usr/bin/env python3
from pathlib import Path

p = Path("telegram/TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java")
if not p.exists():
    raise SystemExit("ERROR: DialogCell.java not found")
s = p.read_text(encoding="utf-8")
# Older patch generator accidentally emitted ASCII control-A where substring was intended.
# Repair only that exact malformed Java expression; do not alter unrelated source.
bad = "mess.\x01(0, 300)"
if bad in s:
    count = s.count(bad)
    s = s.replace(bad, "mess.substring(0, 300)")
    p.write_text(s, encoding="utf-8")
    print(f"DialogCell preview sanitizer: fixed {count} malformed expression(s)")
elif "mess.substring(0, 300)" in s:
    print("DialogCell preview sanitizer: already fixed")
else:
    print("DialogCell preview sanitizer: malformed expression not present")
# Fail early if any ASCII control chars remain in Java source.
for path in [p]:
    data = path.read_bytes()
    controls = [b for b in data if b < 32 and b not in (9,10,13)]
    if controls:
        raise SystemExit(f"ERROR: control characters remain in {path}")
