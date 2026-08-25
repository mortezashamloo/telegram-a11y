#!/usr/bin/env python3
"""Restore full post-a11y-menu from gzip+b64 parts, then run it."""
from pathlib import Path
import base64, gzip, runpy, sys
here = Path(__file__).resolve().parent
parts = sorted(here.glob("post-a11y-menu.gz.b64.*"))
if not parts:
    print("ERROR: no post-a11y-menu.gz.b64.* parts", file=sys.stderr)
    sys.exit(1)
b64 = "".join(p.read_text(encoding="ascii").strip() for p in parts)
data = gzip.decompress(base64.b64decode(b64))
target = here / "_post_a11y_menu_body.py"
target.write_bytes(data)
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
