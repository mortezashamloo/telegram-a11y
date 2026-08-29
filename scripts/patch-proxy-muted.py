#!/usr/bin/env python3
"""Extra a11y patches: muted, proxy sponsor, longer preview, proxy near chats, ghost mode."""
from pathlib import Path
import re
import sys

ROOT = Path("telegram/TMessagesProj")
JAVA = ROOT / "src/main/java"

PREVIEW_CHARS = 300


def patch_dialogcell_muted_and_preview() -> None:
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing")
        return
    t = dc.read_text(encoding="utf-8")
    changed = False

    if "a11y-fork: optional muted" not in t:
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
            t = t.replace(old, new, 1)
            changed = True
            print("DialogCell skip muted (default) OK")
        else:
            print("WARN: DialogCell muted block not found")

    if "a11y-fork: longer preview" not in t:
        n = 0
        t2, c = re.subn(
            r"if \(builder\.length\(\) > 150\)",
            f"if (builder.length() > {PREVIEW_CHARS}) /* a11y-fork: longer preview */",
            t,
        )
        t, n = t2, n + c
        t2, c = re.subn(
            r"if \(mess\.length\(\) > 150\) \{\s*mess = mess\.(substring|subSequence)\(0, 150\);",
            f"if (mess.length() > {PREVIEW_CHARS}) {{\n                mess = mess.\1(0, {PREVIEW_CHARS});",
            t,
            flags=re.S,
        )
        t, n = t2, n + c
        t2, c = re.subn(
            r"if \(messageString\.length\(\) > 150\) \{\s*messageString = messageString\.subSequence\(0, 150\);",
            f"if (messageString.length() > {PREVIEW_CHARS}) {{\n                                            messageString = messageString.subSequence(0, {PREVIEW_CHARS});",
            t,
            flags=re.S,
        )
        t, n = t2, n + c
        t2, c = re.subn(
            r"(formatRichMessage\([^\)]*?),\s*150\)",
            rf"\1, {PREVIEW_CHARS}) /* a11y-fork: longer preview */",
            t,
        )
        t, n = t2, n + c
        if n:
            changed = True
            print(f"DialogCell preview length 150->{PREVIEW_CHARS} OK ({n})")
        else:
            print("WARN: DialogCell preview length needles not found")

    if changed:
        dc.write_text(t, encoding="utf-8")


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


def patch_ghost_mode() -> None:
    """Skip server read receipts + typing when ghost mode is on."""
    mc = JAVA / "org/telegram/messenger/MessagesController.java"
    if not mc.exists():
        return
    t = mc.read_text(encoding="utf-8")
    changed = False

    if "a11y-fork: ghost completeReadTask" not in t:
        m = re.search(r"(private void completeReadTask\s*\(\s*ReadTask\s+\w+\s*\)\s*\{)", t)
        if m:
            insert = (
                m.group(1)
                + "\n        // a11y-fork: ghost completeReadTask"
                + "\n        try {"
                + "\n            if (org.telegram.messenger.A11yConfig.isGhostMode()) {"
                + "\n                return;"
                + "\n            }"
                + "\n        } catch (Throwable ignore) {"
                + "\n        }"
            )
            t = t[: m.start()] + insert + t[m.end() :]
            changed = True
            print("MessagesController ghost completeReadTask OK")
        else:
            print("WARN: completeReadTask not found")

    if "a11y-fork: ghost sendTyping" not in t:
        m = re.search(
            r"(public boolean sendTyping\s*\(\s*long dialogId,\s*long threadMsgId,\s*int action,\s*String emojicon,\s*int classGuid\s*\)\s*\{)",
            t,
        )
        if m:
            insert = (
                m.group(1)
                + "\n        // a11y-fork: ghost sendTyping"
                + "\n        try {"
                + "\n            if (org.telegram.messenger.A11yConfig.isGhostMode()) {"
                + "\n                return false;"
                + "\n            }"
                + "\n        } catch (Throwable ignore) {"
                + "\n        }"
            )
            t = t[: m.start()] + insert + t[m.end() :]
            changed = True
            print("MessagesController ghost sendTyping OK")
        else:
            print("WARN: sendTyping not found")

    if changed:
        mc.write_text(t, encoding="utf-8")


def patch_proxy_near_chats() -> None:
    """Always show Proxy in dialogs overflow when A11yConfig says so."""
    da = JAVA / "org/telegram/ui/DialogsActivity.java"
    if not da.exists():
        print("WARN: DialogsActivity missing")
        return
    t = da.read_text(encoding="utf-8")
    if "a11y-fork: show proxy near chats" in t:
        print("DialogsActivity proxy near chats already patched")
        return

    old = (
        "            final boolean proxyVisible = proxyEnabled && !TextUtils.isEmpty(proxyAddress)\n"
        "                    || getMessagesController().blockedCountry && !SharedConfig.proxyList.isEmpty();"
    )
    new = (
        "            // a11y-fork: show proxy near chats\n"
        "            boolean a11yProxy = false;\n"
        "            try { a11yProxy = org.telegram.messenger.A11yConfig.isShowProxyNearChats(); } catch (Throwable ignore) {}\n"
        "            final boolean proxyVisible = a11yProxy\n"
        "                    || proxyEnabled && !TextUtils.isEmpty(proxyAddress)\n"
        "                    || getMessagesController().blockedCountry && !SharedConfig.proxyList.isEmpty();"
    )
    if old in t:
        da.write_text(t.replace(old, new, 1), encoding="utf-8")
        print("DialogsActivity proxy near chats OK")
        return

    m = re.search(
        r"final boolean proxyVisible\s*=\s*proxyEnabled\s*&&\s*!TextUtils\.isEmpty\(proxyAddress\)\s*"
        r"\|\|\s*getMessagesController\(\)\.blockedCountry\s*&&\s*!SharedConfig\.proxyList\.isEmpty\(\);",
        t,
    )
    if m:
        replacement = (
            "boolean a11yProxy = false;\n"
            "            try { a11yProxy = org.telegram.messenger.A11yConfig.isShowProxyNearChats(); } catch (Throwable ignore) {}\n"
            "            final boolean proxyVisible = a11yProxy\n"
            "                    || proxyEnabled && !TextUtils.isEmpty(proxyAddress)\n"
            "                    || getMessagesController().blockedCountry && !SharedConfig.proxyList.isEmpty();"
            " // a11y-fork: show proxy near chats"
        )
        t = t[: m.start()] + replacement + t[m.end() :]
        da.write_text(t, encoding="utf-8")
        print("DialogsActivity proxy near chats OK (loose)")
    else:
        print("WARN: proxyVisible needle not found")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found", file=sys.stderr)
        return 1
    patch_dialogcell_muted_and_preview()
    patch_proxy_sponsor_hide()
    patch_ghost_mode()
    patch_proxy_near_chats()
    print("patch-proxy-muted done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
