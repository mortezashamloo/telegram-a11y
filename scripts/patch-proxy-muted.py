#!/usr/bin/env python3
"""Extra a11y patches: skip muted in TalkBack (default), hide proxy sponsor channel."""
from pathlib import Path
import re
import sys

ROOT = Path("telegram/TMessagesProj")
JAVA = ROOT / "src/main/java"


def patch_dialogcell_muted() -> None:
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing")
        return
    t = dc.read_text(encoding="utf-8")
    if "a11y-fork: optional muted" in t:
        print("DialogCell muted already patched")
        return
    old = (
        "        if (dialogMuted) {\n"
        "            sb.append(getString(R.string.AccDescrNotificationsMuted));\n"
        '            sb.append(". ");\n'
        "        }"
    )
    new = (
        "        // a11y-fork: optional muted announcement (default off)\n"
        "        if (dialogMuted && org.telegram.messenger.A11yConfig.isAnnounceMuted()) {\n"
        "            sb.append(getString(R.string.AccDescrNotificationsMuted));\n"
        '            sb.append(". ");\n'
        "        }"
    )
    if old in t:
        dc.write_text(t.replace(old, new, 1), encoding="utf-8")
        print("DialogCell skip muted (default) OK")
    else:
        print("WARN: DialogCell muted block not found")


def patch_proxy_sponsor_hide() -> None:
    mc = JAVA / "org/telegram/messenger/MessagesController.java"
    if not mc.exists():
        print("WARN: MessagesController missing")
        return
    t = mc.read_text(encoding="utf-8")
    if "a11y-fork: hide proxy sponsor" in t:
        print("MessagesController proxy sponsor already patched")
        return
    needle = "                        promoDialog = dialogs_dict.get(did);"
    insert = (
        "                        promoDialog = dialogs_dict.get(did);\n"
        "                        // a11y-fork: hide proxy sponsor\n"
        "                        try {\n"
        "                            if (promoDialogType == PROMO_TYPE_PROXY\n"
        "                                    && org.telegram.messenger.A11yConfig.isHideProxySponsor()) {\n"
        "                                AndroidUtilities.runOnUIThread(() -> hidePromoDialog());\n"
        "                                return;\n"
        "                            }\n"
        "                        } catch (Throwable ignore) {\n"
        "                        }"
    )
    if needle in t:
        mc.write_text(t.replace(needle, insert, 1), encoding="utf-8")
        print("MessagesController hide proxy sponsor OK")
    else:
        m = re.search(r"promoDialog\s*=\s*dialogs_dict\.get\(did\);", t)
        if m:
            t = t[: m.start()] + insert + t[m.end() :]
            mc.write_text(t, encoding="utf-8")
            print("MessagesController hide proxy sponsor OK (loose)")
        else:
            print("WARN: promoDialog = dialogs_dict needle not found")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found", file=sys.stderr)
        return 1
    patch_dialogcell_muted()
    patch_proxy_sponsor_hide()
    print("patch-proxy-muted done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
