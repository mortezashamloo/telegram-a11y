#!/usr/bin/env python3
"""Restore full post-a11y-menu body from b64 parts if needed, then exec."""
from pathlib import Path
import base64
import runpy
import sys

here = Path(__file__).resolve().parent
parts = sorted(here.glob("post-a11y-menu.b64.*"))
if parts:
    data = base64.b64decode("".join(p.read_text(encoding="ascii").strip() for p in parts))
    target = here / "_post_a11y_menu_body.py"
    target.write_bytes(data)
    # Execute body as main
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
else:
    print("ERROR: no post-a11y-menu.b64.* parts", file=sys.stderr)
    sys.exit(1)
