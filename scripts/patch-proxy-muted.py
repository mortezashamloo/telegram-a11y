#!/usr/bin/env python3
"""
Safe replacement for patch-proxy-muted.py.

This version deliberately avoids regex replacement backreferences.
That prevents Python from turning replacement text such as \\1 into
the control character U+0001, which previously produced:

    illegal character: '\\u0001'

in DialogCell.java.

It preserves the intended accessibility changes:
- remove the "Muted" announcement
- announce online/last-seen status when enabled
- extend DialogCell preview limits from 150 to 300
- announce sent/received time at the end
"""

from pathlib import Path

ROOT = Path("telegram/TMessagesProj")
JAVA = ROOT / "src/main/java"
DC = JAVA / "org/telegram/ui/Cells/DialogCell.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        print(f"WARN: {label}: anchor not found")
        return text
    if count > 1:
        print(f"WARN: {label}: found {count} matches; changing only the first")
    text = text.replace(old, new, 1)
    print(f"OK: {label}")
    return text


def main() -> None:
    if not DC.exists():
        print("WARN: DialogCell.java not found:", DC)
        return

    text = DC.read_text(encoding="utf-8")

    # ------------------------------------------------------------
    # 1. Remove "Muted" and announce the user's actual status.
    # ------------------------------------------------------------
    old_status = (
        "        if (dialogMuted) {\n"
        "            sb.append(getString(R.string.AccDescrNotificationsMuted));\n"
        "            sb.append(\". \");\n"
        "        }\n"
        "        if (isOnline()) {\n"
        "            sb.append(getString(R.string.AccDescrUserOnline));\n"
        "            sb.append(\". \");\n"
        "        }\n"
    )

    new_status = (
        "        // a11y-fork: remove Muted and announce user status.\n"
        "        if (user != null && org.telegram.messenger.A11yConfig.getShowStatusInPreview()) {\n"
        "            try {\n"
        "                String statusText = LocaleController.formatUserStatus(org.telegram.messenger.UserConfig.selectedAccount, user);\n"
        "                if (statusText != null && statusText.length() > 0) {\n"
        "                    sb.append(statusText);\n"
        "                    sb.append(\". \");\n"
        "                }\n"
        "            } catch (Throwable ignore) {\n"
        "            }\n"
        "        }\n"
    )

    text = replace_once(
        text, old_status, new_status,
        "remove Muted / add user status"
    )

    # ------------------------------------------------------------
    # 2. Extend the six known DialogCell preview limits to 300.
    #    Literal replacement is intentional: no regex \\1/\\2.
    # ------------------------------------------------------------
    preview_replacements = [
        (
            "if (mess.length() > 150) {\n"
            "                        mess = mess.substring(0, 150);",
            "if (mess.length() > 300) {\n"
            "                        mess = mess.substring(0, 300);",
            "custom dialog preview 150 -> 300",
        ),
        (
            "mess = MessageObject.formatRichMessage(draftMessage.rich_message, false, false, 150);",
            "mess = MessageObject.formatRichMessage(draftMessage.rich_message, false, false, 300);",
            "draft rich-message preview 150 -> 300",
        ),
        (
            "if (mess.length() > 150) {\n"
            "                                mess = mess.subSequence(0, 150);",
            "if (mess.length() > 300) {\n"
            "                                mess = mess.subSequence(0, 300);",
            "draft text preview 150 -> 300",
        ),
        (
            "if (messageString.length() > 150) {\n"
            "                                            messageString = messageString.subSequence(0, 150);",
            "if (messageString.length() > 300) {\n"
            "                                            messageString = messageString.subSequence(0, 300);",
            "message-string preview 150 -> 300",
        ),
        (
            "if (mess.length() > 150) {\n"
            "                mess = mess.subSequence(0, 150);",
            "if (mess.length() > 300) {\n"
            "                mess = mess.subSequence(0, 300);",
            "middle preview 150 -> 300",
        ),
        (
            "if (mess.length() > 150) {\n"
            "                    mess = mess.subSequence(0, 150);",
            "if (mess.length() > 300) {\n"
            "                    mess = mess.subSequence(0, 300);",
            "message preview 150 -> 300",
        ),
        (
            "if (mess.length() > 150) {\n"
            "                mess = mess.subSequence(0, 150);",
            "if (mess.length() > 300) {\n"
            "                mess = mess.subSequence(0, 300);",
            "final preview 150 -> 300",
        ),
    ]

    for old, new, label in preview_replacements:
        text = replace_once(text, old, new, label)

    # ------------------------------------------------------------
    # 3. Move sent/received time to the end of the TalkBack text.
    # ------------------------------------------------------------
    old_date = (
        "        String date = LocaleController.formatDateAudio(lastDate, true);\n"
        "        if (message.isOut()) {\n"
        "            sb.append(LocaleController.formatString(\"AccDescrSentDate\", R.string.AccDescrSentDate, date));\n"
        "        } else {\n"
        "            sb.append(LocaleController.formatString(\"AccDescrReceivedDate\", R.string.AccDescrReceivedDate, date));\n"
        "        }\n"
        "        sb.append(\". \");\n"
    )

    text = replace_once(
        text, old_date, "",
        "remove early sent/received time"
    )

    old_tail = (
        "        event.setContentDescription(sb);\n"
        "        setContentDescription(sb);\n"
        "    }\n"
        "\n"
        "    private MessageObject getCaptionMessage() {"
    )

    new_tail = (
        "        // a11y-fork: sent/received time is announced last.\n"
        "        String a11yClockTime = LocaleController.formatDateAudio(lastDate, true);\n"
        "        sb.append(message.isOut() ? \"sent \" : \"receive \");\n"
        "        sb.append(a11yClockTime);\n"
        "        sb.append(\". \");\n"
        "        event.setContentDescription(sb);\n"
        "        setContentDescription(sb);\n"
        "    }\n"
        "\n"
        "    private MessageObject getCaptionMessage() {"
    )

    text = replace_once(
        text, old_tail, new_tail,
        "append sent/received time at end"
    )

    # Safety check: never write a Java source file containing U+0001.
    if "\x01" in text:
        raise RuntimeError("Refusing to write DialogCell.java: U+0001 remains")

    DC.write_text(text, encoding="utf-8")
    print("DialogCell accessibility patch completed safely.")


if __name__ == "__main__":
    main()
