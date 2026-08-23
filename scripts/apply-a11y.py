#!/usr/bin/env python3
"""Apply accessibility patches to cloned Telegram tree (cwd parent of telegram/)."""
from pathlib import Path
import re
import sys

ROOT = Path("telegram/TMessagesProj")
RES = ROOT / "src/main/res"
JAVA = ROOT / "src/main/java"

FA_NAME = "\u062a\u0644\u06af\u0631\u0627\u0645 \u062f\u0633\u062a\u0631\u0633\u200c\u067e\u0630\u06cc\u0631"
EN_NAME = "Telegram Accessible"


def _set_string(path: Path, name: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<resources>\n"
            f'    <string name="{name}">{value}</string>\n'
            "</resources>\n",
            encoding="utf-8",
        )
        print(f"created {path} {name}")
        return
    t = path.read_text(encoding="utf-8")
    if f'name="{name}"' in t:
        t2, n = re.subn(
            rf'(<string\s+name="{name}">)[^<]*(</string>)',
            rf"\1{value}\2",
            t,
            count=1,
        )
        path.write_text(t2, encoding="utf-8")
        print(f"patched {path.name} {name} n={n}")
    else:
        path.write_text(
            t.replace(
                "</resources>",
                f'    <string name="{name}">{value}</string>\n</resources>',
            ),
            encoding="utf-8",
        )
        print(f"inserted {path.name} {name}")


def patch_app_name() -> None:
    # Debug builds use AndroidManifest_SDK23 -> @string/AppNameBeta
    # Release uses @string/AppName. Patch BOTH.
    for rel in ("values/strings.xml",):
        p = RES / rel
        if p.exists():
            _set_string(p, "AppName", EN_NAME)
            _set_string(p, "AppNameBeta", EN_NAME)
    for rel in ("values-fa/strings.xml", "values-fa-rIR/strings.xml"):
        p = RES / rel
        _set_string(p, "AppName", FA_NAME)
        _set_string(p, "AppNameBeta", FA_NAME)
    print("AppName + AppNameBeta OK")


def patch_radial_progress() -> None:
    rp = JAVA / "org/telegram/ui/Components/RadialProgress.java"
    if not rp.exists():
        print("WARN: RadialProgress.java missing")
        return
    t = rp.read_text(encoding="utf-8")
    if "a11y-fork: announce progress" in t:
        print("RadialProgress already patched")
        return
    t = t.replace(
        "private float currentProgress = 0;",
        "private float currentProgress = 0;\n"
        "    // a11y-fork: announce progress\n"
        "    private int a11yLastAnnouncedPercent = -1;",
        1,
    )
    inject = """
        // a11y-fork: announce progress every 5%
        if (parent != null) {
            try {
                Object amObj = parent.getContext().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);
                android.view.accessibility.AccessibilityManager am = (android.view.accessibility.AccessibilityManager) amObj;
                if (am != null && am.isEnabled()) {
                    int pct = Math.round(value * 100f);
                    if (pct >= 100) pct = 100;
                    if (pct < 0) pct = 0;
                    int step = (pct / 5) * 5;
                    if (step != a11yLastAnnouncedPercent) {
                        a11yLastAnnouncedPercent = step;
                        parent.announceForAccessibility(step + " percent");
                    }
                    if (pct == 0) a11yLastAnnouncedPercent = -1;
                }
            } catch (Throwable ignore) {}
        }
"""
    m = re.search(r"public void setProgress\(float value, boolean animated\) \{\n", t)
    if not m:
        print("WARN: setProgress not found")
        return
    t = t[: m.end()] + inject + t[m.end() :]
    rp.write_text(t, encoding="utf-8")
    print("RadialProgress announce every 5% OK")


def patch_hide_share() -> None:
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing")
        return
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: hide share" not in t:
        t2, n = re.subn(
            r"(boolean\s+checkNeedDrawShareButton\s*\([^)]*\)\s*\{)",
            r"\1\n        // a11y-fork: hide share button between messages\n        if (true) return false;",
            t,
            count=1,
        )
        if n:
            t = t2
            print("Hide share OK")
        else:
            print("WARN: checkNeedDrawShareButton not found")
    else:
        print("Hide share already present")

    # Channel "Leave a comment" bar under posts — hide from between messages
    if "a11y-fork: hide comment button" not in t:
        if "drawCommentButton = true;" in t:
            t = t.replace(
                "drawCommentButton = true;",
                "drawCommentButton = false; // a11y-fork: hide comment button between messages",
            )
            print("Hide leave-comment between messages OK")
        else:
            print("WARN: drawCommentButton = true not found")
    else:
        print("Hide comment already present")

    cmc.write_text(t, encoding="utf-8")


def patch_forward_no_quote() -> None:
    smh = JAVA / "org/telegram/messenger/SendMessagesHelper.java"
    if smh.exists():
        t = smh.read_text(encoding="utf-8")
        if "IS_FORWARD_NO_QUOTE" not in t:
            t2 = t.replace(
                "req.drop_author = forwardFromMyName;",
                "req.drop_author = forwardFromMyName || org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE; org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE = false;",
                1,
            )
            smh.write_text(t2, encoding="utf-8")
            print("drop_author OK")
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if ca.exists():
        t = ca.read_text(encoding="utf-8")
        if "IS_FORWARD_NO_QUOTE" not in t:
            t2, n = re.subn(
                r"(protected TLRPC\.Chat currentChat;)",
                r"public static boolean IS_FORWARD_NO_QUOTE = false;\n    \1",
                t,
                count=1,
            )
            if n:
                ca.write_text(t2, encoding="utf-8")
                print("IS_FORWARD_NO_QUOTE OK")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found", file=sys.stderr)
        return 1
    patch_app_name()
    patch_radial_progress()
    patch_hide_share()
    patch_forward_no_quote()
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
