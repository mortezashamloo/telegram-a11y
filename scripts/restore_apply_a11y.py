#!/usr/bin/env python3
"""Restore scripts/apply-a11y.py from base64 part files (committed next to this script)."""
from pathlib import Path
import base64
import sys
here = Path(__file__).resolve().parent
parts = sorted(here.glob("apply-a11y.b64.*"))
if not parts:
    print("No apply-a11y.b64.* parts found", file=sys.stderr)
    sys.exit(1)
data = "".join(p.read_text(encoding="ascii").strip() for p in parts)
out = here / "apply-a11y.py"
out.write_bytes(base64.b64decode(data))
print(f"Restored {out} ({out.stat().st_size} bytes) from {len(parts)} parts")
