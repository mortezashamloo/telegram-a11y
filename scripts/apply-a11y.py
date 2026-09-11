#!/usr/bin/env python3
"""Apply accessibility patches to cloned Telegram tree (cwd parent of telegram/).

Portable: works with GitHub Actions (patches-repo/scripts) or local kit (scripts/).
When DrKLO/Telegram updates, re-run this script on a fresh clone.
"""
from pathlib import Path
import re
import shutil
import sys

ROOT = Path("telegram/TMessagesProj")
RES = ROOT / "src/main/res"
JAVA = ROOT / "src/main/java"


def _find_scripts_dir() -> Path:
    for cand in (
        Path("patches-repo/scripts"),
        Path("scripts"),
        Path(__file__).resolve().parent,
    ):
        if (cand / "A11yConfig.java").exists() or (cand / "apply-a11y.py").exists():
            return cand
    return Path("scripts")


SCRIPTS = _find_scripts_dir()

FA_NAME = "\u062a\u0644\u06af\u0631\u0627\u0645 \u062f\u0633\u062a\u0631\u0633\u200c\u067e\u0630\u06cc\u0631"
EN_NAME = "Telegram Accessible"

OPTION_FORWARD_NO_QUOTE = 200
OPTION_REACTIONS_MENU = 201
OPTION_FORWARD_TO_SAVED = 202
OPTION_SELECT_MESSAGE = 203
OPTION_LEAVE_COMMENT = 204
OPTION_BOT_BUTTONS_MENU = 205


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
        return
    t = path.read_text(encoding="utf-8")
    if f'name="{name}"' in t:
        t2, _ = re.subn(
            rf'(<string\s+name="{name}">)[^<]*(</string>)',
            rf"\1{value}\2",
            t,
            count=1,
        )
        path.write_text(t2, encoding="utf-8")
    else:
        path.write_text(
            t.replace(
                "</resources>",
                f'    <string name="{name}">{value}</string>\n</resources>',
            ),
            encoding="utf-8",
        )


def patch_app_name() -> None:
    p = RES / "values/strings.xml"
    if p.exists():
        _set_string(p, "AppName", EN_NAME)
        _set_string(p, "AppNameBeta", EN_NAME)
    for rel in ("values-fa/strings.xml", "values-fa-rIR/strings.xml"):
        _set_string(RES / rel, "AppName", FA_NAME)
        _set_string(RES / rel, "AppNameBeta", FA_NAME)
    print("AppName OK")



def _patch_a11y_string_resources() -> None:
    """Install English/Persian resources for all accessibility-fork UI text."""
    en = {
        "A11yAccessibleSettings": "Accessible settings",
        "A11yProgressAnnounce": "Progress announce",
        "A11yVoiceQuality": "Voice quality",
        "A11yProgressAnnounceSummary": "Progress & voice quality",
        "A11yProgressAnnounceStep": "Progress announce step",
        "A11yVoiceMessageQuality": "Voice message quality",
        "A11yLow": "Low",
        "A11yMedium": "Medium",
        "A11yHigh": "High",
        "A11yProgressStep": "Progress step %1$d percent",
        "A11yVoiceQualitySelected": "Voice quality %1$s",
        "A11yForwardWithoutQuote": "Forward without quote",
        "A11yForwardToSaved": "Forward to Saved Messages",
        "A11yForwardedToSaved": "Forwarded to Saved Messages",
        "A11ySelected": "Selected",
        "A11yReceiveAt": "receive @%1$s",
        "A11ySentAt": "sent @%1$s",
        "A11yBotButtons": "Bot Buttons",
        "A11yBotNumber": "Bot %1$d",
        "A11yPercent": "%1$d percent",
    }
    fa = {
        "A11yAccessibleSettings": "تنظیمات دسترسپذیری",
        "A11yProgressAnnounce": "اعلام پیشرفت",
        "A11yVoiceQuality": "کیفیت صدا",
        "A11yProgressAnnounceSummary": "اعلام پیشرفت و کیفیت صدا",
        "A11yProgressAnnounceStep": "گام اعلام پیشرفت",
        "A11yVoiceMessageQuality": "کیفیت پیام صوتی",
        "A11yLow": "پایین",
        "A11yMedium": "متوسط",
        "A11yHigh": "بالا",
        "A11yProgressStep": "گام پیشرفت %1$d درصد",
        "A11yVoiceQualitySelected": "کیفیت صدا %1$s",
        "A11yForwardWithoutQuote": "ارسال بدون نقلقول",
        "A11yForwardToSaved": "ارسال به پیامهای ذخیرهشده",
        "A11yForwardedToSaved": "به پیامهای ذخیرهشده ارسال شد",
        "A11ySelected": "انتخاب شد",
        "A11yReceiveAt": "دریافت در ساعت %1$s",
        "A11ySentAt": "ارسال در ساعت %1$s",
        "A11yBotButtons": "دکمههای ربات",
        "A11yBotNumber": "ربات %1$d",
        "A11yPercent": "%1$d درصد",
    }
    # Remove the zero-width separator accidentally introduced by source editing;
    # keep normal Persian spacing in Android resources.
    fa = {k: v.replace("\u000b", " ") for k, v in fa.items()}
    for rel, values in (("values/strings.xml", en), ("values-fa/strings.xml", fa), ("values-fa-rIR/strings.xml", fa)):
        path = RES / rel
        for name, value in values.items():
            _set_string(path, name, value)


def patch_a11y_localization() -> None:
    """Replace accessibility-fork hard-coded runtime text with localized resources."""
    _patch_a11y_string_resources()

    # A11yConfig.java is copied from the user's repository. Localize its labels
    # without replacing or removing any of the existing settings/features.
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if cfg.exists():
        t = cfg.read_text(encoding="utf-8")
        replacements = {
            'return "Low";': 'return LocaleController.getString(R.string.A11yLow);',
            'return "Medium";': 'return LocaleController.getString(R.string.A11yMedium);',
            'return "High";': 'return LocaleController.getString(R.string.A11yHigh);',
            '"Progress announce: " + progressStepLabel()': 'LocaleController.getString(R.string.A11yProgressAnnounce) + ": " + progressStepLabel()',
            '"Voice quality: " + voiceQualityLabel()': 'LocaleController.getString(R.string.A11yVoiceQuality) + ": " + voiceQualityLabel()',
            '"Accessible settings"': 'LocaleController.getString(R.string.A11yAccessibleSettings)',
            '"Progress announce step"': 'LocaleController.getString(R.string.A11yProgressAnnounceStep)',
            '"Voice message quality"': 'LocaleController.getString(R.string.A11yVoiceMessageQuality)',
            '"Progress step " + steps[which] + " percent"': 'LocaleController.formatString("A11yProgressStep", R.string.A11yProgressStep, steps[which])',
            '"Voice quality " + labels[which]': 'LocaleController.formatString("A11yVoiceQualitySelected", R.string.A11yVoiceQualitySelected, labels[which])',
        }
        changed = False
        for old, new in replacements.items():
            if old in t:
                t = t.replace(old, new)
                changed = True
        if changed:
            cfg.write_text(t, encoding="utf-8")
            print("A11yConfig localization OK")

    targets = [
        JAVA / "org/telegram/ui/ChatActivity.java",
        JAVA / "org/telegram/ui/Cells/DialogCell.java",
        JAVA / "org/telegram/ui/Components/RadialProgress.java",
        JAVA / "org/telegram/ui/Components/RadialProgress2.java",
        JAVA / "org/telegram/ui/SettingsActivity.java",
    ]
    for path in targets:
        if not path.exists():
            continue
        t = path.read_text(encoding="utf-8")
        original = t
        replacements = {
            'items.add("Forward without quote");': 'items.add(LocaleController.getString(R.string.A11yForwardWithoutQuote));',
            'items.add("Forward to Saved Messages");': 'items.add(LocaleController.getString(R.string.A11yForwardToSaved));',
            'announceForAccessibility("Forwarded to Saved Messages");': 'announceForAccessibility(LocaleController.getString(R.string.A11yForwardedToSaved));',
            'announceForAccessibility("Selected");': 'announceForAccessibility(LocaleController.getString(R.string.A11ySelected));',
            'sb.append(message.isOut() ? "sent @" : "receive @");': 'sb.append(LocaleController.formatString(message.isOut() ? "A11ySentAt" : "A11yReceiveAt", message.isOut() ? R.string.A11ySentAt : R.string.A11yReceiveAt, a11yClockTime));',
            'items.add("Bot Buttons");': 'items.add(LocaleController.getString(R.string.A11yBotButtons));',
            'botBtnBuilder.setTitle("Bot Buttons");': 'botBtnBuilder.setTitle(LocaleController.getString(R.string.A11yBotButtons));',
            '("Bot " + (labels.size() + 1))': 'LocaleController.formatString("A11yBotNumber", R.string.A11yBotNumber, labels.size() + 1)',
            '"Accessible settings", "Progress & voice quality"': 'LocaleController.getString(R.string.A11yAccessibleSettings), LocaleController.getString(R.string.A11yProgressAnnounceSummary)',
            'parent.announceForAccessibility(step + " percent");': 'parent.announceForAccessibility(LocaleController.formatString("A11yPercent", R.string.A11yPercent, step));',
        }
        for old, new in replacements.items():
            t = t.replace(old, new)
        if t != original:
            path.write_text(t, encoding="utf-8")
            print(f"{path.name} localization OK")

    print("A11y English/Persian localization OK")

def install_a11y_config() -> None:
    src = SCRIPTS / "A11yConfig.java"
    dst = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not src.exists():
        print("WARN: A11yConfig.java missing in", SCRIPTS)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print("A11yConfig.java installed from", SCRIPTS)


def _inject_progress_announce(java_path: Path) -> None:
    if not java_path.exists():
        print(f"WARN: {java_path.name} missing")
        return
    t = java_path.read_text(encoding="utf-8")
    if "a11y-fork: announce progress only if focused" in t:
        print(f"{java_path.name} already patched (focus-aware)")
        return
    if "a11y-fork: announce progress" in t:
        t = re.sub(
            r"\n\s*// a11y-fork: announce progress[\s\S]*?if \(pct == 0\) a11yLastAnnouncedPercent = -1;\s*\}\s*\} catch \(Throwable ignore\) \{\}\s*\}\s*",
            "\n",
            t,
            count=1,
        )
    if "a11yLastAnnouncedPercent" not in t:
        if "private View parent;" in t:
            t = t.replace(
                "private View parent;",
                "private View parent;\n    // a11y-fork: announce progress\n    private int a11yLastAnnouncedPercent = -1;",
                1,
            )
        elif "private float currentProgress = 0;" in t:
            t = t.replace(
                "private float currentProgress = 0;",
                "private float currentProgress = 0;\n    // a11y-fork: announce progress\n    private int a11yLastAnnouncedPercent = -1;",
                1,
            )
    inject = """
        // a11y-fork: announce progress only if focused on this message cell
        if (parent != null) {
            try {
                Object amObj = parent.getContext().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);
                android.view.accessibility.AccessibilityManager am = (android.view.accessibility.AccessibilityManager) amObj;
                if (am != null && am.isEnabled()) {
                    boolean focused = parent.isAccessibilityFocused();
                    if (!focused) {
                        android.view.View v = parent;
                        while (v != null && !focused) {
                            if (v.isAccessibilityFocused()) {
                                focused = true;
                                break;
                            }
                            android.view.ViewParent vp = v.getParent();
                            v = (vp instanceof android.view.View) ? (android.view.View) vp : null;
                        }
                    }
                    if (focused) {
                        int pct = Math.round(value * 100f);
                        if (pct >= 100) pct = 100;
                        if (pct < 0) pct = 0;
                        int stepSize = 5;
                        try { stepSize = org.telegram.messenger.A11yConfig.getProgressStep(); } catch (Throwable ignore2) {}
                        if (stepSize <= 0) stepSize = 5;
                        int step = (pct / stepSize) * stepSize;
                        if (step != a11yLastAnnouncedPercent) {
                            a11yLastAnnouncedPercent = step;
                            parent.announceForAccessibility(step + " percent");
                        }
                        if (pct == 0) a11yLastAnnouncedPercent = -1;
                    }
                }
            } catch (Throwable ignore) {}
        }
"""
    m = re.search(r"public void setProgress\(float value, boolean animated\) \{\n", t)
    if not m:
        print(f"WARN: setProgress not found in {java_path.name}")
        return
    t = t[: m.end()] + inject + t[m.end() :]
    java_path.write_text(t, encoding="utf-8")
    print(f"{java_path.name} progress announce (focus-only) OK")


def patch_radial_progress() -> None:
    _inject_progress_announce(JAVA / "org/telegram/ui/Components/RadialProgress2.java")
    _inject_progress_announce(JAVA / "org/telegram/ui/Components/RadialProgress.java")


def patch_dialogcell_name_then_type() -> None:
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing")
        return
    t = dc.read_text(encoding="utf-8")
    if "a11y-fork: name then type" in t:
        print("DialogCell already patched")
        return
    old_chat = """            } else if (chat != null) {
                if (chat.broadcast) {
                    sb.append(getString(R.string.AccDescrChannel));
                } else {
                    sb.append(getString(R.string.AccDescrGroup));
                }
                sb.append(". ");
                sb.append(chat.title);
                sb.append(". ");
            }"""
    new_chat = """            } else if (chat != null) {
                // a11y-fork: name then type
                sb.append(chat.title);
                sb.append(". ");
                if (chat.broadcast) {
                    sb.append(getString(R.string.AccDescrChannel));
                } else {
                    sb.append(getString(R.string.AccDescrGroup));
                }
                sb.append(". ");
            }"""
    old_bot = """                    if (user.bot) {
                        sb.append(getString(R.string.Bot));
                        sb.append(". ");
                    }
                    if (user.self) {
                        sb.append(getString(R.string.SavedMessages));
                    } else {
                        sb.append(ContactsController.formatName(user.first_name, user.last_name));
                    }"""
    new_bot = """                    // a11y-fork: name then type for bots
                    if (user.self) {
                        sb.append(getString(R.string.SavedMessages));
                    } else {
                        sb.append(ContactsController.formatName(user.first_name, user.last_name));
                        if (user.bot) {
                            sb.append(". ");
                            sb.append(getString(R.string.Bot));
                        }
                    }"""
    changed = False
    if old_chat in t:
        t = t.replace(old_chat, new_chat, 1)
        changed = True
        print("DialogCell chat name-then-type OK")
    else:
        print("WARN: DialogCell chat block not found")
    if old_bot in t:
        t = t.replace(old_bot, new_bot, 1)
        changed = True
        print("DialogCell bot name-then-type OK")
    else:
        print("WARN: DialogCell bot block not found")
    if changed:
        dc.write_text(t, encoding="utf-8")


def patch_hide_share_and_comment() -> None:
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
    if "a11y-fork: hide comment button" not in t and "drawCommentButton = true;" in t:
        t = t.replace(
            "drawCommentButton = true;",
            "drawCommentButton = false; // a11y-fork: hide comment button between messages",
        )
        print("Hide leave-comment OK")
    cmc.write_text(t, encoding="utf-8")


def patch_forward_menu_extras() -> None:
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
    if not ca.exists():
        return
    t = ca.read_text(encoding="utf-8")
    if "IS_FORWARD_NO_QUOTE" not in t:
        t2, n = re.subn(
            r"(protected TLRPC\.Chat currentChat;)",
            r"public static boolean IS_FORWARD_NO_QUOTE = false;\n    \1",
            t,
            count=1,
        )
        if n:
            t = t2
            print("IS_FORWARD_NO_QUOTE field OK")
    if "a11y-fork: forward menu extras" not in t:
        old = (
            "                if (canForward) {\n"
            "                    items.add(LocaleController.getString(R.string.Forward));\n"
            "                    options.add(OPTION_FORWARD);\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                }"
        )
        new = (
            "                if (canForward) {\n"
            "                    items.add(LocaleController.getString(R.string.Forward));\n"
            "                    options.add(OPTION_FORWARD);\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                    // a11y-fork: forward menu extras\n"
            "                    items.add(\"Forward without quote\");\n"
            f"                    options.add({OPTION_FORWARD_NO_QUOTE});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                    items.add(\"Forward to Saved Messages\");\n"
            f"                    options.add({OPTION_FORWARD_TO_SAVED});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                }"
        )
        if old in t:
            t = t.replace(old, new, 1)
            print("Forward menu extras OK")
        else:
            print("WARN: canForward menu block not found")
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE" not in t:
        old_case = "            case OPTION_FORWARD: {"
        new_case = (
            f"            case {OPTION_FORWARD_NO_QUOTE}: // a11y-fork: OPTION_FORWARD_NO_QUOTE\n"
            "                IS_FORWARD_NO_QUOTE = true;\n"
            "                // fall through to forward UI\n"
            f"            case {OPTION_FORWARD_TO_SAVED}: // a11y-fork: forward to Saved Messages\n"
            "                if (selectedObject != null) {{\n"
            "                    try {{\n"
            "                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n"
            "                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {{\n"
            "                            toSend.addAll(selectedObjectGroup.messages);\n"
            "                        }} else {{\n"
            "                            toSend.add(selectedObject);\n"
            "                        }}\n"
            "                        long savedId = getUserConfig().getClientUserId();\n"
            "                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n"
            "                        try {{\n"
            "                            if (getParentActivity() != null) {{\n"
            "                                getParentActivity().getWindow().getDecorView().announceForAccessibility(\"Forwarded to Saved Messages\");\n"
            "                            }}\n"
            "                        }} catch (Throwable ignore) {{}}\n"
            "                    }} catch (Throwable e) {{\n"
            "                        FileLog.e(e);\n"
            "                    }}\n"
            "                }}\n"
            "                selectedObject = null;\n"
            "                selectedObjectToEditCaption = null;\n"
            "                selectedObjectGroup = null;\n"
            "                break;\n"
            "            case OPTION_FORWARD: {"
        )
        if old_case in t:
            t = t.replace(old_case, new_case, 1)
            print("Forward option handlers OK")
        else:
            print("WARN: OPTION_FORWARD case not found")
    ca.write_text(t, encoding="utf-8")


def patch_reactions_as_menu() -> None:
    """
    Accessibility-fork: put the emoji reactions row behind a "Reactions"
    menu item (hidden/collapsed by default, revealed on tap) instead of it
    always being a focusable row above the message menu -- keeps TalkBack
    navigation from being cluttered by a rarely-used control. Inserted at
    the SAME anchor Bot Buttons/Select use, and this function is called
    before those two in main(), so the final order is:
    Reactions, Bot Buttons, Select (last).
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: reactions menu item" in t:
        print("ChatActivity reactions-menu already patched")
        return

    # patch_reactions_as_menu injects into fillMessageMenu(), where the
    # createMenu() local variable named isReactionsAvailableFinal does not
    # exist.  Define an equivalent local value here, based on Telegram's
    # current MessageObject API, before the menu item is inserted.
    if "a11y-fork: reactions availability for menu" not in t:
        reactions_availability_anchor = (
            "        final MessageObject.GroupedMessages groupedMessages = selectedObjectGroup;\n"
            "        final int type = getMessageType(message);\n"
        )
        reactions_availability_insert = (
            "        final MessageObject.GroupedMessages groupedMessages = selectedObjectGroup;\n"
            "        final int type = getMessageType(message);\n"
            "        // a11y-fork: reactions availability for menu\n"
            "        final boolean isReactionsAvailableFinal = message != null && message.isReactionsAvailable();\n"
        )
        if reactions_availability_anchor in t:
            t = t.replace(reactions_availability_anchor, reactions_availability_insert, 1)
            print("ChatActivity reactions availability declaration OK")
        else:
            print("WARN: fillMessageMenu anchor not found (reactions availability)")

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: reactions menu item\n"
        "        accessibilityReactionsToggleIndex = -1;\n"
        "        if (isReactionsAvailableFinal) {\n"
        "            items.add(LocaleController.getString(R.string.Reactions));\n"
        "            icons.add(R.drawable.msg_reactions2);\n"
        f"            options.add({OPTION_REACTIONS_MENU});\n"
        "            accessibilityReactionsToggleIndex = items.size() - 1;\n"
        "        }\n"
        "\n"
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if old_item not in t:
        print("WARN: ChatActivity sponsored-item anchor not found (reactions menu item)")
        return
    t = t.replace(old_item, new_item, 1)

    if "accessibilityReactionsToggleIndex" not in t.split("a11y-fork: reactions menu item")[0]:
        # add the field declaration once, right before the class body's first field-like anchor
        field_anchor = "public class ChatActivity"
        idx = t.find(field_anchor)
        if idx != -1:
            brace_idx = t.find("{", idx)
            if brace_idx != -1:
                t = (
                    t[: brace_idx + 1]
                    + "\n    private int accessibilityReactionsToggleIndex = -1; // a11y-fork: reactions menu item\n"
                    + t[brace_idx + 1 :]
                )

    old_toggle = (
        "                    scrimPopupContainerLayout.addView(reactionsLayout, params);\n"
        "                    scrimPopupContainerLayout.setReactionsLayout(reactionsLayout);\n"
    )
    new_toggle = (
        "                    scrimPopupContainerLayout.addView(reactionsLayout, params);\n"
        "                    scrimPopupContainerLayout.setReactionsLayout(reactionsLayout);\n"
        "\n"
        "                    // a11y-fork: reactions menu item -- hide the reactions row\n"
        "                    // by default; the \"Reactions\" menu item reveals it on tap.\n"
        "                    reactionsLayout.setVisibility(View.GONE);\n"
        "                    if (accessibilityReactionsToggleIndex >= 0 && scrimPopupWindowItems != null\n"
        "                        && accessibilityReactionsToggleIndex < scrimPopupWindowItems.length\n"
        "                        && scrimPopupWindowItems[accessibilityReactionsToggleIndex] != null) {\n"
        "                        final ReactionsContainerLayout reactionsLayoutForToggle = reactionsLayout;\n"
        "                        scrimPopupWindowItems[accessibilityReactionsToggleIndex].setOnClickListener(reactionsToggleView -> {\n"
        "                            boolean show = reactionsLayoutForToggle.getVisibility() != View.VISIBLE;\n"
        "                            reactionsLayoutForToggle.setVisibility(show ? View.VISIBLE : View.GONE);\n"
        "                        });\n"
        "                    }\n"
    )
    if old_toggle not in t:
        print("WARN: ChatActivity reactionsLayout anchor not found (visibility toggle)")
    else:
        t = t.replace(old_toggle, new_toggle, 1)

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity reactions-menu item+toggle OK")


def patch_longpress_message_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing")
        return
    t = ca.read_text(encoding="utf-8")

    # Prefer single-message menu under TalkBack (avoids multi-select path inside createMenu)
    if "a11y-fork: createMenu single under a11y" not in t:
        old_cm = (
            "            if (!actionBar.isActionModeShowed() && (!isReport() || showMenu)) {\n"
            "                result = createMenu(view, false, true, x, y, true);\n"
            "            } else {"
        )
        new_cm = (
            "            if (!actionBar.isActionModeShowed() && (!isReport() || showMenu)) {\n"
            "                // a11y-fork: createMenu single under a11y\n"
            "                boolean a11yMenu = false;\n"
            "                try {\n"
            "                    android.view.accessibility.AccessibilityManager amM = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n"
            "                    a11yMenu = amM != null && amM.isEnabled();\n"
            "                } catch (Throwable ignore) {}\n"
            "                if (a11yMenu) {\n"
            "                    result = createMenu(view, true, false, x, y, true);\n"
            "                } else {\n"
            "                    result = createMenu(view, false, true, x, y, true);\n"
            "                }\n"
            "            } else {"
        )
        if old_cm in t:
            t = t.replace(old_cm, new_cm, 1)
            print("createMenu single under a11y OK")
        else:
            print("WARN: createMenu long-click block not found")

    old_ms = (
        "            if (view instanceof ChatMessageCell && (((ChatMessageCell) view).getMessageObject() != null && ((ChatMessageCell) view).getMessageObject().type != MessageObject.TYPE_JOINED_CHANNEL)) {\n"
        "                startMultiselect(position);\n"
        "                result = true;\n"
        "            }"
    )
    new_ms = (
        "            if (view instanceof ChatMessageCell && (((ChatMessageCell) view).getMessageObject() != null && ((ChatMessageCell) view).getMessageObject().type != MessageObject.TYPE_JOINED_CHANNEL)) {\n"
        "                // a11y-fork: with TalkBack, long-press only opens menu\n"
        "                boolean a11yOn = false;\n"
        "                try {\n"
        "                    android.view.accessibility.AccessibilityManager am = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n"
        "                    a11yOn = am != null && am.isEnabled();\n"
        "                } catch (Throwable ignore) {}\n"
        "                if (!a11yOn || actionBar.isActionModeShowed()) {\n"
        "                    startMultiselect(position);\n"
        "                }\n"
        "                result = true;\n"
        "            }"
    )
    if "a11y-fork: with TalkBack, long-press only opens menu" not in t:
        if old_ms in t:
            t = t.replace(old_ms, new_ms, 1)
            print("Long-press skip startMultiselect OK")
        else:
            print("WARN: startMultiselect block not found")

    old_dlp = (
        "            createMenu(cell, false, false, x, y, false);\n"
        "            startMultiselect(chatListView.getChildAdapterPosition(cell));"
    )
    new_dlp = (
        "            createMenu(cell, false, false, x, y, false);\n"
        "            // a11y-fork: do not auto-start multi-select under TalkBack\n"
        "            boolean a11yOn2 = false;\n"
        "            try {\n"
        "                android.view.accessibility.AccessibilityManager am2 = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n"
        "                a11yOn2 = am2 != null && am2.isEnabled();\n"
        "            } catch (Throwable ignore) {}\n"
        "            if (!a11yOn2 || actionBar.isActionModeShowed()) {\n"
        "                startMultiselect(chatListView.getChildAdapterPosition(cell));\n"
        "            }"
    )
    if "a11y-fork: do not auto-start multi-select under TalkBack" not in t:
        if old_dlp in t:
            t = t.replace(old_dlp, new_dlp, 1)
            print("didLongPress skip startMultiselect OK")
        else:
            print("WARN: didLongPress block not found")

    if "a11y-fork: OPTION_SELECT_MESSAGE menu" not in t:
        needle = "        if (message.isSponsored() && !getUserConfig().isPremium()"
        insert = (
            f"        // a11y-fork: OPTION_SELECT_MESSAGE menu\n"
            f"        if (!actionBar.isActionModeShowed() && message != null && message.contentType == 0 && !message.isSponsored()) {{\n"
            f"            items.add(LocaleController.getString(R.string.Select));\n"
            f"            options.add({OPTION_SELECT_MESSAGE});\n"
            f"            icons.add(R.drawable.msg_forward);\n"
            f"        }}\n\n"
            f"        if (message.isSponsored() && !getUserConfig().isPremium()"
        )
        if needle in t:
            t = t.replace(needle, insert, 1)
            print("Select menu item OK")
        else:
            print("WARN: fillMessageMenu inject point not found")

    if "a11y-fork: OPTION_SELECT_MESSAGE handler" not in t:
        old_case = "            case OPTION_RETRY: {"
        new_case = (
            f"            case {OPTION_SELECT_MESSAGE}: {{ // a11y-fork: OPTION_SELECT_MESSAGE handler\n"
            f"                if (selectedObject != null) {{\n"
            f"                    try {{\n"
            f"                        MessageObject toSelect = selectedObject;\n"
            f"                        closeMenu();\n"
            f"                        createActionMode();\n"
            f"                        if (actionBar != null) {{\n"
            f"                            actionBar.showActionMode(true, null, null, null, null, null, 0);\n"
            f"                        }}\n"
            f"                        addToSelectedMessages(toSelect, false);\n"
            f"                        updateActionModeTitle();\n"
            f"                        updateVisibleRows();\n"
            f"                        if (chatActivityEnterView != null) chatActivityEnterView.preventInput = true;\n"
            f"                        if (selectedMessagesCountTextView != null) {{\n"
            f"                            selectedMessagesCountTextView.setText(LocaleController.formatPluralString(\"MessagesSelected\", selectedMessagesIds[0].size() + selectedMessagesIds[1].size()), false);\n"
            f"                        }}\n"
            f"                        try {{\n"
            f"                            if (getParentActivity() != null) {{\n"
            f"                                getParentActivity().getWindow().getDecorView().announceForAccessibility(\"Selected\");\n"
            f"                            }}\n"
            f"                        }} catch (Throwable ignore) {{}}\n"
            f"                    }} catch (Throwable e) {{\n"
            f"                        FileLog.e(e);\n"
            f"                    }}\n"
            f"                }}\n"
            f"                selectedObject = null;\n"
            f"                selectedObjectToEditCaption = null;\n"
            f"                selectedObjectGroup = null;\n"
            f"                break;\n"
            f"            }}\n"
            f"            case OPTION_RETRY: {{"
        )
        if old_case in t:
            t = t.replace(old_case, new_case, 1)
            print("Select handler OK")
        else:
            print("WARN: OPTION_RETRY case not found")
    ca.write_text(t, encoding="utf-8")


def patch_voice_bitrate() -> None:
    audio = ROOT / "jni/audio.c"
    if audio.exists():
        t = audio.read_text(encoding="utf-8", errors="replace")
        if "a11y_record_bitrate" not in t:
            t = t.replace(
                "const opus_int32 bitrate = OPUS_BITRATE_MAX;",
                "/* a11y-fork */ opus_int32 a11y_record_bitrate = 32000;\nconst opus_int32 bitrate = OPUS_BITRATE_MAX;",
                1,
            )
            t = t.replace(
                "result = opus_encoder_ctl(_encoder, OPUS_SET_BITRATE(bitrate));",
                "result = opus_encoder_ctl(_encoder, OPUS_SET_BITRATE(a11y_record_bitrate > 0 ? a11y_record_bitrate : bitrate));",
                1,
            )
            start_line = "JNIEXPORT jint Java_org_telegram_messenger_MediaController_startRecord"
            if start_line in t and "setRecordBitrate" not in t:
                jni = (
                    "JNIEXPORT void Java_org_telegram_messenger_MediaController_setRecordBitrate"
                    "(JNIEnv *env, jclass clazz, jint br) {\n"
                    "    if (br > 0) a11y_record_bitrate = br;\n"
                    "}\n\n" + start_line
                )
                t = t.replace(start_line, jni, 1)
            audio.write_text(t, encoding="utf-8")
            print("audio.c bitrate OK")
        else:
            print("audio.c already patched")
    mc = JAVA / "org/telegram/messenger/MediaController.java"
    if not mc.exists():
        return
    t = mc.read_text(encoding="utf-8")
    if "setRecordBitrate" not in t:
        t = t.replace(
            "private native int startRecord(String path, int sampleRate);",
            "private native int startRecord(String path, int sampleRate);\n    // a11y-fork\n    public native void setRecordBitrate(int bitrate);",
            1,
        )
        print("MediaController native setRecordBitrate OK")
    if "A11yConfig.applyVoiceBitrateToNative" not in t:
        t2, n = re.subn(
            r"(if \(startRecord\(recordingAudioFile\.getPath\(\), sampleRate\) == 0\))",
            r"try { org.telegram.messenger.A11yConfig.applyVoiceBitrateToNative(); } catch (Throwable ignore) {}\n                    \1",
            t,
        )
        if n:
            t = t2
            print(f"MediaController apply voice before record x{n}")
    mc.write_text(t, encoding="utf-8")


def patch_settings_menu() -> None:
    sa = JAVA / "org/telegram/ui/SettingsActivity.java"
    if not sa.exists():
        print("WARN: SettingsActivity missing")
        return
    t = sa.read_text(encoding="utf-8")
    needle = 'items.add(SettingCell.Factory.of(10, IconBackgroundColors.PURPLE.top, IconBackgroundColors.PURPLE.bottom, R.drawable.settings_language, getString(R.string.SettingsLanguage), LocaleController.getCurrentLanguageName()));'
    insert = needle + "\n        // a11y-fork: Accessible settings entry\n        items.add(SettingCell.Factory.of(100, IconBackgroundColors.GREEN.top, IconBackgroundColors.GREEN.bottom, R.drawable.settings_privacy, \"Accessible settings\", \"Progress & voice quality\"));"
    if "a11y-fork: Accessible settings entry" not in t:
        if needle in t:
            t = t.replace(needle, insert, 1)
            print("Settings list item OK")
        else:
            print("WARN: Settings item needle not found")
    if "case 100:" not in t:
        old = """            case 10:
                presentSettingFragment(new LanguageSelectActivity());
                break;"""
        new = """            case 10:
                presentSettingFragment(new LanguageSelectActivity());
                break;
            case 100:
                // a11y-fork
                org.telegram.messenger.A11yConfig.showSettingsDialog(getParentActivity());
                break;"""
        if old in t:
            t = t.replace(old, new, 1)
            print("Settings case 100 OK")
        else:
            print("WARN: Settings case 10 block not found")
    sa.write_text(t, encoding="utf-8")


def patch_dialogcell_preview_muted_status() -> None:
    """
    Accessibility-fork additions to DialogCell.java's TalkBack description:
      - remove the "Muted" announcement entirely
      - read the contact's online/last-seen status (private chats only),
        gated by A11yConfig.getShowStatusInPreview()
      - bump the message-preview length read aloud from the visually
        truncated length to a fixed 300 characters
    """
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (preview/muted/status)")
        return
    t = dc.read_text(encoding="utf-8")
    if "a11y-fork: muted/status/preview-300" in t:
        print("DialogCell muted/status/preview-300 already patched")
        return

    old_block = (
        "        if (dialogMuted) {\n"
        "            sb.append(getString(R.string.AccDescrNotificationsMuted));\n"
        "            sb.append(\". \");\n"
        "        }\n"
        "        if (isOnline()) {\n"
        "            sb.append(getString(R.string.AccDescrUserOnline));\n"
        "            sb.append(\". \");\n"
        "        }\n"
    )
    new_block = (
        "        // a11y-fork: muted/status/preview-300 -- \"Muted\" removed,\n"
        "        // online/last-seen status announced instead when enabled.\n"
        "        if (user != null && org.telegram.messenger.A11yConfig.getShowStatusInPreview()) {\n"
        "            try {\n"
        "                String statusText = LocaleController.formatUserStatus(UserConfig.selectedAccount, user);\n"
        "                if (statusText != null && statusText.length() > 0) {\n"
        "                    sb.append(statusText);\n"
        "                    sb.append(\". \");\n"
        "                }\n"
        "            } catch (Throwable ignore) {\n"
        "            }\n"
        "        }\n"
    )
    if old_block not in t:
        print("WARN: DialogCell muted/status block not found")
        return
    t = t.replace(old_block, new_block)

    old_len = (
        "            int len = messageLayout == null ? -1 : messageLayout.getText().length();\n"
        "            if (len > 0) {"
    )
    new_len = (
        "            int len = 300; // a11y-fork: read up to 300 characters, not just the visually truncated amount\n"
        "            if (len > 0 && len < messageString.length()) {"
    )
    if old_len not in t:
        print("WARN: DialogCell preview-length block not found")
    else:
        t = t.replace(old_len, new_len)

    # Move the sent/received time announcement from its early position to
    # the very end (after the sender name and message preview), reworded
    # to "receive @5:55pm" / "sent @5:55pm".
    old_date_block = (
        "        String date = LocaleController.formatDateAudio(lastDate, true);\n"
        "        if (message.isOut()) {\n"
        "            sb.append(LocaleController.formatString(\"AccDescrSentDate\", R.string.AccDescrSentDate, date));\n"
        "        } else {\n"
        "            sb.append(LocaleController.formatString(\"AccDescrReceivedDate\", R.string.AccDescrReceivedDate, date));\n"
        "        }\n"
        "        sb.append(\". \");\n"
    )
    if old_date_block not in t:
        print("WARN: DialogCell sent/received date block not found")
    else:
        t = t.replace(old_date_block, "", 1)
        old_tail = (
            "        event.setContentDescription(sb);\n"
            "        setContentDescription(sb);\n"
            "    }\n"
            "\n"
            "    private MessageObject getCaptionMessage() {"
        )
        new_tail = (
            "        // a11y-fork: sent/received time read last\n"
            "        String a11yClockTime = LocaleController.formatDateAudio(lastDate, true);\n"
            "        sb.append(message.isOut() ? \"sent @\" : \"receive @\");\n"
            "        sb.append(a11yClockTime);\n"
            "        sb.append(\". \");\n"
            "        event.setContentDescription(sb);\n"
            "        setContentDescription(sb);\n"
            "    }\n"
            "\n"
            "    private MessageObject getCaptionMessage() {"
        )
        if old_tail not in t:
            print("WARN: DialogCell tail anchor not found (sent/received time)")
        else:
            t = t.replace(old_tail, new_tail, 1)

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted removed / status announce / preview-300 / time-last OK")


def patch_hide_sponsor_channel() -> None:
    """
    Accessibility-fork: when A11yConfig.getHideSponsorChannel() is on,
    automatically hide the proxy sponsor/promo channel from the chat list
    using Telegram's own existing hidePromoDialog() mechanism, checked each
    time the chat list resumes.
    """
    da = JAVA / "org/telegram/ui/DialogsActivity.java"
    if not da.exists():
        print("WARN: DialogsActivity missing (hide sponsor channel)")
        return
    t = da.read_text(encoding="utf-8")
    if "a11y-fork: hide sponsor channel" in t:
        print("DialogsActivity hide-sponsor-channel already patched")
        return
    old = (
        "    public void onResume() {\n"
        "        super.onResume();\n"
    )
    new = (
        "    public void onResume() {\n"
        "        super.onResume();\n"
        "        // a11y-fork: hide sponsor channel\n"
        "        try {\n"
        "            if (org.telegram.messenger.A11yConfig.getHideSponsorChannel()) {\n"
        "                getMessagesController().hidePromoDialog();\n"
        "            }\n"
        "        } catch (Throwable ignore) {\n"
        "        }\n"
    )
    if old not in t:
        print("WARN: DialogsActivity onResume anchor not found (hide sponsor channel)")
        return
    t = t.replace(old, new, 1)
    da.write_text(t, encoding="utf-8")
    print("DialogsActivity hide-sponsor-channel OK")


def patch_ghost_mode() -> None:
    """
    Accessibility-fork: Ghost Mode -- when A11yConfig.getGhostMode() is on,
    skip calling markDialogAsRead(...) from ChatActivity so the sender
    never gets a "seen" / read-receipt signal. Local unread badges for this
    account may not clear while Ghost Mode is on -- an accepted trade-off.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (ghost mode)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: ghost mode" in t:
        print("ChatActivity ghost-mode already patched")
        return
    count = t.count("getMessagesController().markDialogAsRead(")
    if count == 0:
        print("WARN: ChatActivity markDialogAsRead call sites not found (ghost mode)")
        return
    import re
    pattern = re.compile(r"(\s*)getMessagesController\(\)\.markDialogAsRead\(([^;]*)\);")
    def guard(m):
        indent, args = m.group(1), m.group(2)
        return (
            f"{indent}if (!org.telegram.messenger.A11yConfig.getGhostMode()) {{ /* a11y-fork: ghost mode */\n"
            f"{indent}    getMessagesController().markDialogAsRead({args});\n"
            f"{indent}}}"
        )
    new_text, n = pattern.subn(guard, t)
    if n == 0:
        print("WARN: ChatActivity ghost-mode regex found no matches")
        return
    ca.write_text(new_text, encoding="utf-8")
    print(f"ChatActivity ghost-mode OK ({n} call sites guarded)")



def patch_bot_buttons_menu() -> None:
    """
    Accessibility-fork: fold scattered inline bot buttons (Connect/Close/
    Open etc.) under each message bubble into a single "Bot Buttons" item
    in the message options menu, opening a picker dialog instead.
    """
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not cmc.exists() or not ca.exists():
        print("WARN: ChatMessageCell/ChatActivity missing (bot buttons menu)")
        return

    # 1) Hide the inline bot-button row under the bubble.
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: bot buttons menu" in t:
        print("ChatMessageCell bot-buttons-menu already patched")
    else:
        old = (
            "            final int separatorHeight = dp(4 + 4);\n"
            "            if (!messageObject.isRestrictedMessage && !messageObject.isRepostPreview "
            "&& (currentPosition == null || currentMessagesGroup != null && currentMessagesGroup.isDocuments "
            "&& currentPosition.last) && (inlineButtons != null) && !messageObject.hasExtendedMedia()) {\n"
        )
        new = (
            "            final int separatorHeight = dp(4 + 4);\n"
            "            // a11y-fork: bot buttons menu -- inline bot buttons under\n"
            "            // the bubble are hidden from TalkBack; use the \"Bot Buttons\"\n"
            "            // message menu item instead.\n"
            "            if (false && !messageObject.isRestrictedMessage && !messageObject.isRepostPreview "
            "&& (currentPosition == null || currentMessagesGroup != null && currentMessagesGroup.isDocuments "
            "&& currentPosition.last) && (inlineButtons != null) && !messageObject.hasExtendedMedia()) {\n"
        )
        if old not in t:
            print("WARN: ChatMessageCell inline-bot-buttons anchor not found")
        else:
            t = t.replace(old, new, 1)
            cmc.write_text(t, encoding="utf-8")
            print("ChatMessageCell bot-buttons-menu hide OK")

    # 2) Add the "Bot Buttons" menu item + its click handler in ChatActivity.
    t2 = ca.read_text(encoding="utf-8")
    # a11y-fork: OPTION_BOT_BUTTONS_MENU must be a Java field, not only a
    # Python-side constant.  The menu item and handler below both reference it.
    if "a11y-fork: OPTION_BOT_BUTTONS_MENU declaration" not in t2:
        class_anchor = "public class ChatActivity"
        class_idx = t2.find(class_anchor)
        if class_idx != -1:
            brace_idx = t2.find("{", class_idx)
            if brace_idx != -1:
                t2 = (
                    t2[:brace_idx + 1]
                    + "\n    private static final int OPTION_BOT_BUTTONS_MENU = 205; // a11y-fork: OPTION_BOT_BUTTONS_MENU declaration\n"
                    + t2[brace_idx + 1:]
                )
                print("ChatActivity OPTION_BOT_BUTTONS_MENU declaration OK")
            else:
                print("WARN: ChatActivity class opening brace not found (bot buttons menu)")
        else:
            print("WARN: ChatActivity class declaration not found (bot buttons menu)")

    if "a11y-fork: bot buttons menu" in t2:
        print("ChatActivity bot-buttons-menu already patched")
        ca.write_text(t2, encoding="utf-8")
        return

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: bot buttons menu\n"
        "        if (message != null && message.hasInlineBotButtons()) {\n"
        "            items.add(\"Bot Buttons\");\n"
        "            options.add(OPTION_BOT_BUTTONS_MENU);\n"
        "            icons.add(R.drawable.msg_viewreplies);\n"
        "        }\n"
        "\n"
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if old_item not in t2:
        print("WARN: ChatActivity sponsored-item anchor not found (bot buttons menu item)")
        return
    t2 = t2.replace(old_item, new_item, 1)

    old_case = "            case OPTION_RETRY: {\n"
    new_case = (
        "            case OPTION_BOT_BUTTONS_MENU: {\n"
        "                try {\n"
        "                    MessageObject msg = selectedObject;\n"
        "                    ArrayList<CharSequence> labels = new ArrayList<>();\n"
        "                    ArrayList<TL_keyboard.KeyboardInlineButton> btns = new ArrayList<>();\n"
        "                    if (msg != null && msg.messageOwner != null && msg.messageOwner.reply_markup "
        "instanceof TLRPC.TL_replyInlineMarkup) {\n"
        "                        TLRPC.TL_replyInlineMarkup markup = (TLRPC.TL_replyInlineMarkup) msg.messageOwner.reply_markup;\n"
        "                        for (int b = 0; b < markup.rows.size(); b++) {\n"
        "                            TL_keyboard.KeyboardInlineButtonRow row = markup.rows.get(b);\n"
        "                            for (int c = 0; c < row.buttons.size(); c++) {\n"
        "                                TL_keyboard.KeyboardInlineButton btn = row.buttons.get(c);\n"
        "                                CharSequence label = !TextUtils.isEmpty(btn.text) ? btn.text : (\"Bot \" + (labels.size() + 1));\n"
        "                                labels.add(label);\n"
        "                                btns.add(btn);\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                    if (!labels.isEmpty() && getParentActivity() != null) {\n"
        "                        CharSequence[] itemsArr = labels.toArray(new CharSequence[0]);\n"
        "                        final MessageObject msgFinal = msg;\n"
        "                        final ArrayList<TL_keyboard.KeyboardInlineButton> btnsFinal = btns;\n"
        "                        AlertDialog.Builder botBtnBuilder = new AlertDialog.Builder(getParentActivity());\n"
        "                        botBtnBuilder.setTitle(\"Bot Buttons\");\n"
        "                        botBtnBuilder.setItems(itemsArr, (dialog, which) -> {\n"
        "                            if (which >= 0 && which < btnsFinal.size() && chatActivityEnterView != null) {\n"
        "                                chatActivityEnterView.didPressedBotButton(btnsFinal.get(which), msgFinal, msgFinal);\n"
        "                            }\n"
        "                        });\n"
        "                        botBtnBuilder.setNegativeButton(LocaleController.getString(R.string.Cancel), null);\n"
        "                        showDialog(botBtnBuilder.create());\n"
        "                    }\n"
        "                } catch (Throwable e) {\n"
        "                    FileLog.e(e);\n"
        "                }\n"
        "                selectedObject = null;\n"
        "                selectedObjectGroup = null;\n"
        "                break;\n"
        "            }\n"
        "            case OPTION_RETRY: {\n"
    )
    if old_case not in t2:
        print("WARN: ChatActivity OPTION_RETRY case anchor not found (bot buttons menu handler)")
        return
    t2 = t2.replace(old_case, new_case, 1)

    ca.write_text(t2, encoding="utf-8")
    print("ChatActivity bot-buttons-menu item+handler OK")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found (clone DrKLO/Telegram as ./telegram)", file=sys.stderr)
        return 1
    print("Using scripts dir:", SCRIPTS.resolve())
    patch_app_name()
    install_a11y_config()
    patch_a11y_localization()
    patch_radial_progress()
    patch_dialogcell_name_then_type()
    patch_hide_share_and_comment()
    patch_forward_menu_extras()
    patch_reactions_as_menu()
    patch_voice_bitrate()
    patch_settings_menu()
    patch_dialogcell_preview_muted_status()
    patch_hide_sponsor_channel()
    patch_ghost_mode()
    patch_bot_buttons_menu()
    patch_longpress_message_menu()
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
