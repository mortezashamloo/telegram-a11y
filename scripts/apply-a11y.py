#!/usr/bin/env python3
"""Apply accessibility patches to cloned Telegram tree (cwd parent of telegram/).

Portable: works with GitHub Actions (patches-repo/scripts) or local kit (scripts/).
When DrKLO/Telegram updates, re-run this script on a fresh clone.
"""
from pathlib import Path
import re
import html
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
    """Write/update an Android <string> resource, escaping XML text."""
    value = html.escape(value, quote=False)
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

def install_a11y_config() -> None:
    src = SCRIPTS / "A11yConfig.java"
    dst = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not src.exists():
        print("WARN: A11yConfig.java missing in", SCRIPTS)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    cfg = dst.read_text(encoding="utf-8")
    cfg = cfg.replace("getBoolean(PREF_RECORDING_BEEP, false)", "getBoolean(PREF_RECORDING_BEEP, true)")
    cfg = cfg.replace("getBoolean(PREF_SOLAR_CALENDAR, false)", "getBoolean(PREF_SOLAR_CALENDAR, true)")
    dst.write_text(cfg, encoding="utf-8")
    print("A11yConfig.java installed + beep default ON")


def _patch_a11y_string_resources() -> None:
    """Install every accessibility-fork string resource referenced by A11yConfig.java.

    English values match official Telegram wording where possible.
    Persian values are natural, user-friendly Farsi for TalkBack users.
    """
    en = {
        "A11yAccessibleSettingsTitle": "Accessible settings",
        "A11yProgressAnnounceLabel": "Progress announce: %s",
        "A11yProgressStepLabel": "Progress step %1$d percent",
        "A11yProgressStepPickerTitle": "Progress announce step",
        "A11yVoiceQualityLabel": "Voice quality: %s",
        "A11yVoiceQualityPickerTitle": "Voice message quality",
        "A11yVoiceLow": "Low",
        "A11yVoiceMedium": "Medium",
        "A11yVoiceHigh": "High",
        "A11yHideSponsorLabel": "Hide sponsor channel: %s",
        "A11ySponsorHidden": "Sponsor channel hidden",
        "A11ySponsorShown": "Sponsor channel shown",
        "A11yGhostModeLabel": "Ghost mode: %s",
        "A11yGhostOn": "Ghost mode on",
        "A11yGhostOff": "Ghost mode off",
        "A11yStatusPreviewLabel": "Show status in preview: %s",
        "A11yStatusOn": "Status preview on",
        "A11yStatusOff": "Status preview off",
        "A11yForwardSavedNoQuoteLabel": "Forward to Saved Messages with no quote: %s",
        "A11yRecordingBeepLabel": "Recording start beep: %s",
        "A11ySolarCalendarLabel": "Solar calendar: %s",
        "A11yOn": "On", "A11yOff": "Off", "A11yCancel": "Cancel",
        "A11yAccessibleSettings": "Accessible settings",
        "A11yProgressAnnounce": "Progress announce",
        "A11yVoiceQuality": "Voice quality",
        "A11yProgressAnnounceSummary": "Progress & voice quality",
        "A11yProgressAnnounceStep": "Progress announce step",
        "A11yVoiceMessageQuality": "Voice message quality",
        "A11yLow": "Low", "A11yMedium": "Medium", "A11yHigh": "High",
        "A11yProgressStep": "Progress step %1$d percent",
        "A11yVoiceQualitySelected": "Voice quality %1$s",
        "A11yForwardWithoutQuote": "Forward without quote",
        "A11yForwardToSaved": "Forward to Saved Messages",
        "A11yForwardedToSaved": "Forwarded to Saved Messages",
        "A11ySelected": "Selected",
        "A11yBotButtons": "Bot Buttons",
        "A11yGoToFirstMessage": "Go to first message",
        "A11yBotNumber": "Bot %1$d",
        "A11yPercent": "%1$d percent",
    }
    fa = {
        "A11yAccessibleSettingsTitle": "تنظیمات دسترس‌پذیری",
        "A11yProgressAnnounceLabel": "اعلام پیشرفت: %s",
        "A11yProgressStepLabel": "گام پیشرفت %1$d درصد",
        "A11yProgressStepPickerTitle": "گام اعلام پیشرفت",
        "A11yVoiceQualityLabel": "کیفیت صدا: %s",
        "A11yVoiceQualityPickerTitle": "کیفیت پیام صوتی",
        "A11yVoiceLow": "پایین",
        "A11yVoiceMedium": "متوسط",
        "A11yVoiceHigh": "بالا",
        "A11yHideSponsorLabel": "مخفی کردن کانال حامی: %s",
        "A11ySponsorHidden": "کانال حامی مخفی شد",
        "A11ySponsorShown": "کانال حامی نمایش داده شد",
        "A11yGhostModeLabel": "حالت روح: %s",
        "A11yGhostOn": "حالت روح روشن شد",
        "A11yGhostOff": "حالت روح خاموش شد",
        "A11yStatusPreviewLabel": "نمایش وضعیت در پیش‌نمایش: %s",
        "A11yStatusOn": "نمایش وضعیت روشن شد",
        "A11yStatusOff": "نمایش وضعیت خاموش شد",
        "A11yForwardSavedNoQuoteLabel": "ارسال به پیام‌های ذخیره‌شده بدون نقل‌قول: %s",
        "A11yRecordingBeepLabel": "بوق شروع ضبط: %s",
        "A11ySolarCalendarLabel": "تقویم خورشیدی: %s",
        "A11yOn": "روشن",
        "A11yOff": "خاموش",
        "A11yCancel": "لغو",
        "A11yAccessibleSettings": "تنظیمات دسترس‌پذیری",
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
        "A11yForwardWithoutQuote": "ارسال بدون نقل‌قول",
        "A11yForwardToSaved": "ارسال به پیام‌های ذخیره‌شده",
        "A11yForwardedToSaved": "به پیام‌های ذخیره‌شده ارسال شد",
        "A11ySelected": "انتخاب شد",
        "A11yBotButtons": "دکمه‌های ربات",
        "A11yGoToFirstMessage": "رفتن به اولین پیام",
        "A11yBotNumber": "ربات %1$d",
        "A11yPercent": "%1$d درصد",
    }
    for rel, values in (("values/strings.xml", en), ("values-fa/strings.xml", fa), ("values-fa-rIR/strings.xml", fa)):
        path = RES / rel
        if not path.exists():
            print("WARN: resource file missing:", path)
            continue
        for name, value in values.items():
            _set_string(path, name, value)


def patch_a11y_localization() -> None:
    """Replace accessibility-fork hard-coded runtime text with localized resources.

    Includes ChatMessageCell.java so its hard-coded "Bot Buttons" strings
    also get localized. Also normalizes the "percent" hard-coded text used
    by the progress announcer in RadialProgress/RadialProgress2.
    """
    _patch_a11y_string_resources()

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
        JAVA / "org/telegram/ui/Cells/ChatMessageCell.java",
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
    # IMPORTANT: percent string is localized via A11yPercent resource, NOT
    # hard-coded "step + percent". This makes it read "۲۵ درصد" in Persian.
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
                            try {
                                parent.announceForAccessibility(
                                    org.telegram.messenger.LocaleController.formatString(
                                        "A11yPercent",
                                        org.telegram.messenger.R.string.A11yPercent,
                                        step));
                            } catch (Throwable ignore3) {
                                parent.announceForAccessibility(step + " percent");
                            }
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
    print(f"{java_path.name} progress announce (focus-only, localized) OK")


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


def patch_forward_handler(t: str) -> str:
    # If the broken old handler exists, remove it completely. It is the source
    # of the observed NO_QUOTE -> Saved Messages fall-through.
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE" in t:
        start = t.find("            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: OPTION_FORWARD_NO_QUOTE")
        end = t.find("            case OPTION_FORWARD: {", start)
        if start >= 0 and end >= 0:
            t = t[:start] + t[end:]

    # Ensure the no-quote case shares the normal Forward handler, not Saved.
    normal = "            case OPTION_FORWARD: {"
    shared = (
        "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
        "                IS_FORWARD_NO_QUOTE = true;\n"
        "                // fall through to the normal Forward UI\n"
        "            case OPTION_FORWARD: {"
    )
    if "case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote" not in t:
        if normal not in t:
            raise RuntimeError("normal OPTION_FORWARD case not found")
        t = t.replace(normal, shared, 1)

    # Add/replace Saved Messages handler immediately before normal Forward.
    marker = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
    saved_start = t.find(marker)
    if saved_start < 0:
        raise RuntimeError("forward no-quote case insertion failed")
    if "a11y-fork: forward to Saved Messages" not in t:
        saved = (
            "            case OPTION_FORWARD_TO_SAVED: { // a11y-fork: forward to Saved Messages\n"
            "                if (selectedObject != null) {\n"
            "                    try {\n"
            "                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n"
            "                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {\n"
            "                            toSend.addAll(selectedObjectGroup.messages);\n"
            "                        } else {\n"
            "                            toSend.add(selectedObject);\n"
            "                        }\n"
            "                        IS_FORWARD_NO_QUOTE = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();\n"
            "                        long savedId = getUserConfig().getClientUserId();\n"
            "                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n"
            "                        try {\n"
            "                            if (getParentActivity() != null) {\n"
            "                                getParentActivity().getWindow().getDecorView().announceForAccessibility(\"Forwarded to Saved Messages\");\n"
            "                            }\n"
            "                        } catch (Throwable ignore) {}\n"
            "                    } catch (Throwable e) {\n"
            "                        FileLog.e(e);\n"
            "                    }\n"
            "                }\n"
            "                selectedObject = null;\n"
            "                selectedObjectToEditCaption = null;\n"
            "                selectedObjectGroup = null;\n"
            "                break;\n"
            "            }\n"
        )
        t = t[:saved_start] + saved + t[saved_start:]
    return t


def patch_forward_menu_extras() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    smh = JAVA / "org/telegram/messenger/SendMessagesHelper.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (forward menu)")
        return
    if smh.exists():
        t = smh.read_text(encoding="utf-8")
        if "a11y-fork: drop-author one-shot v2" not in t:
            old = "req.drop_author = forwardFromMyName;"
            new = "req.drop_author = forwardFromMyName || org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE; org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE = false;"
            if old in t:
                t = t.replace(old, new, 1)
                smh.write_text(t, encoding="utf-8")
                print("drop_author one-shot v2 OK")
    t = ca.read_text(encoding="utf-8")
    if "public static boolean IS_FORWARD_NO_QUOTE" not in t:
        anchor = "protected TLRPC.Chat currentChat;"
        if anchor in t:
            t = t.replace(anchor, "public static boolean IS_FORWARD_NO_QUOTE = false;\n    " + anchor, 1)
            print("IS_FORWARD_NO_QUOTE field OK")
        else:
            print("WARN: currentChat anchor not found (IS_FORWARD_NO_QUOTE field)")

    option_decl = (
        "private static final int OPTION_FORWARD_NO_QUOTE = 200;\n"
        "    private static final int OPTION_FORWARD_TO_SAVED = 202;"
    )
    if "private static final int OPTION_FORWARD_NO_QUOTE = 200;" not in t:
        field_anchor = "public static boolean IS_FORWARD_NO_QUOTE = false;"
        if field_anchor in t:
            t = t.replace(field_anchor, field_anchor + "\n    " + option_decl, 1)
            print("Forward option constants OK")
        else:
            print("WARN: IS_FORWARD_NO_QUOTE field anchor not found (option constants)")
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
            "                    items.add(LocaleController.getString(R.string.A11yForwardWithoutQuote));\n"
            f"                    options.add({OPTION_FORWARD_NO_QUOTE});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                    items.add(LocaleController.getString(R.string.A11yForwardToSaved));\n"
            f"                    options.add({OPTION_FORWARD_TO_SAVED});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                }"
        )
        if old in t:
            t = t.replace(old, new, 1)
            print("Forward menu extras OK")
        else:
            print("WARN: canForward menu block not found")
    t = patch_forward_handler(t)
    ca.write_text(t, encoding="utf-8")
    print("Forward option handlers v2 OK")


def patch_reactions_as_menu() -> None:
    """
    Accessibility-fork: put the emoji reactions row behind a "Reactions"
    menu item. Inserted at the same anchor Bot Buttons/Select use.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "OPTION_TOGGLE_REACTIONS_ROW" in t and "Accessibility: put reactions behind" in t:
        print("ChatActivity Reactions menu already provided by 04-comment-and-reactions.patch")
        return
    if "a11y-fork: reactions menu item" in t:
        print("ChatActivity reactions-menu already patched")
        return

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


def patch_forward_handler(t: str) -> str:
    # If the broken old handler exists, remove it completely. It is the source
    # of the observed NO_QUOTE -> Saved Messages fall-through.
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE" in t:
        start = t.find("            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: OPTION_FORWARD_NO_QUOTE")
        end = t.find("            case OPTION_FORWARD: {", start)
        if start >= 0 and end >= 0:
            t = t[:start] + t[end:]

    # Ensure the no-quote case shares the normal Forward handler, not Saved.
    normal = "            case OPTION_FORWARD: {"
    shared = (
        "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
        "                IS_FORWARD_NO_QUOTE = true;\n"
        "                // fall through to the normal Forward UI\n"
        "            case OPTION_FORWARD: {"
    )
    if "case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote" not in t:
        if normal not in t:
            raise RuntimeError("normal OPTION_FORWARD case not found")
        t = t.replace(normal, shared, 1)

    # Add/replace Saved Messages handler immediately before normal Forward.
    marker = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
    saved_start = t.find(marker)
    if saved_start < 0:
        raise RuntimeError("forward no-quote case insertion failed")
    if "a11y-fork: forward to Saved Messages" not in t:
        saved = (
            "            case OPTION_FORWARD_TO_SAVED: { // a11y-fork: forward to Saved Messages\n"
            "                if (selectedObject != null) {\n"
            "                    try {\n"
            "                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n"
            "                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {\n"
            "                            toSend.addAll(selectedObjectGroup.messages);\n"
            "                        } else {\n"
            "                            toSend.add(selectedObject);\n"
            "                        }\n"
            "                        IS_FORWARD_NO_QUOTE = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();\n"
            "                        long savedId = getUserConfig().getClientUserId();\n"
            "                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n"
            "                        try {\n"
            "                            if (getParentActivity() != null) {\n"
            "                                getParentActivity().getWindow().getDecorView().announceForAccessibility(\"Forwarded to Saved Messages\");\n"
            "                            }\n"
            "                        } catch (Throwable ignore) {}\n"
            "                    } catch (Throwable e) {\n"
            "                        FileLog.e(e);\n"
            "                    }\n"
            "                }\n"
            "                selectedObject = null;\n"
            "                selectedObjectToEditCaption = null;\n"
            "                selectedObjectGroup = null;\n"
            "                break;\n"
            "            }\n"
        )
        t = t[:saved_start] + saved + t[saved_start:]
    return t


def patch_forward_menu_extras() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    smh = JAVA / "org/telegram/messenger/SendMessagesHelper.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (forward menu)")
        return
    if smh.exists():
        t = smh.read_text(encoding="utf-8")
        if "a11y-fork: drop-author one-shot v2" not in t:
            old = "req.drop_author = forwardFromMyName;"
            new = "req.drop_author = forwardFromMyName || org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE; org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE = false;"
            if old in t:
                t = t.replace(old, new, 1)
                smh.write_text(t, encoding="utf-8")
                print("drop_author one-shot v2 OK")
    t = ca.read_text(encoding="utf-8")
    if "public static boolean IS_FORWARD_NO_QUOTE" not in t:
        anchor = "protected TLRPC.Chat currentChat;"
        if anchor in t:
            t = t.replace(anchor, "public static boolean IS_FORWARD_NO_QUOTE = false;\n    " + anchor, 1)
            print("IS_FORWARD_NO_QUOTE field OK")
        else:
            print("WARN: currentChat anchor not found (IS_FORWARD_NO_QUOTE field)")

    option_decl = (
        "private static final int OPTION_FORWARD_NO_QUOTE = 200;\n"
        "    private static final int OPTION_FORWARD_TO_SAVED = 202;"
    )
    if "private static final int OPTION_FORWARD_NO_QUOTE = 200;" not in t:
        field_anchor = "public static boolean IS_FORWARD_NO_QUOTE = false;"
        if field_anchor in t:
            t = t.replace(field_anchor, field_anchor + "\n    " + option_decl, 1)
            print("Forward option constants OK")
        else:
            print("WARN: IS_FORWARD_NO_QUOTE field anchor not found (option constants)")
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
            "                    items.add(LocaleController.getString(R.string.A11yForwardWithoutQuote));\n"
            f"                    options.add({OPTION_FORWARD_NO_QUOTE});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                    items.add(LocaleController.getString(R.string.A11yForwardToSaved));\n"
            f"                    options.add({OPTION_FORWARD_TO_SAVED});\n"
            "                    icons.add(R.drawable.msg_forward);\n"
            "                }"
        )
        if old in t:
            t = t.replace(old, new, 1)
            print("Forward menu extras OK")
        else:
            print("WARN: canForward menu block not found")
    t = patch_forward_handler(t)
    ca.write_text(t, encoding="utf-8")
    print("Forward option handlers v2 OK")


def patch_reactions_as_menu() -> None:
    """
    Accessibility-fork: put the emoji reactions row behind a "Reactions"
    menu item. Inserted at the same anchor Bot Buttons/Select use.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "OPTION_TOGGLE_REACTIONS_ROW" in t and "Accessibility: put reactions behind" in t:
        print("ChatActivity Reactions menu already provided by 04-comment-and-reactions.patch")
        return
    if "a11y-fork: reactions menu item" in t:
        print("ChatActivity reactions-menu already patched")
        return

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

def patch_dialogcell_preview_muted_status() -> None:
    """
    Accessibility-fork additions to DialogCell.java's TalkBack description:
      - remove the "Muted" announcement entirely
      - read the contact's online/last-seen status (private chats only),
        gated by A11yConfig.getShowStatusInPreview()
      - bump the message-preview length read aloud from the visually
        truncated length to a fixed 300 characters
      - move the sent/received date block to the very end of the description,
        reusing Telegram's own `lastDate` variable (which Telegram already
        defines earlier in this method) -- we do NOT introduce a new local
        variable, we only REMOVE Telegram's early `String date = ...` block
        and re-emit an equivalent block at the tail.
      - if A11yConfig.getSolarCalendar() is ON, REPLACE the Gregorian date
        with the Solar Hijri date (still using Telegram's own `lastDate`
        and Telegram's own AccDescrSentDate/AccDescrReceivedDate format).
    """
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (preview/muted/status)")
        return
    t = dc.read_text(encoding="utf-8")
    if "a11y-fork: muted/status/preview-300" in t:
        print("DialogCell muted/status/preview-300 already patched")
        return

    # --- 1) Remove "Muted" block, add status announce ---
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
    else:
        t = t.replace(old_block, new_block)

    # --- 2) Preview length 300 ---
    old_len = (
        "            int len = messageLayout == null ? -1 : messageLayout.getText().length();\n"
        "            if (len > 0) {"
    )
    new_len = (
        "            int len = 300; // a11y-fork: read up to 300 characters\n"
        "            if (len > 0 && len < messageString.length()) {"
    )
    if old_len not in t:
        print("WARN: DialogCell preview-length block not found")
    else:
        t = t.replace(old_len, new_len)

    # --- 3) Remove Telegram's OWN early date block, then re-emit an
    # equivalent block at the TAIL, so the date is read last. If Solar
    # Hijri is enabled in A11yConfig, the Gregorian date is REPLACED with
    # the Solar Hijri one (same position, same wording, only the date
    # string changes). ---
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
        # Remove the early date block entirely; we will re-emit an
        # equivalent block at the tail below.
        t = t.replace(old_date_block, "        // a11y-fork: sent/received date moved to the tail\n", 1)
        print("DialogCell early date block removed OK")

        old_tail = (
            "        event.setContentDescription(sb);\n"
            "        setContentDescription(sb);\n"
            "    }\n"
            "\n"
            "    private MessageObject getCaptionMessage() {"
        )
        new_tail = (
            "        // a11y-fork: keep Telegram's native sent/received date format\n"
            "        // at the very end. When Solar Hijri is enabled in A11yConfig,\n"
            "        // REPLACE the Gregorian date with the Solar Hijri date.\n"
            "        String date = LocaleController.formatDateAudio(lastDate, true);\n"
            "        try {\n"
            "            if (org.telegram.messenger.A11yConfig.getSolarCalendar()) {\n"
            "                String solarDate = org.telegram.messenger.A11yConfig.formatSolarDate(lastDate);\n"
            "                if (solarDate != null && solarDate.length() > 0) {\n"
            "                    date = solarDate;\n"
            "                }\n"
            "            }\n"
            "        } catch (Throwable ignore) {\n"
            "        }\n"
            "        if (message.isOut()) {\n"
            "            sb.append(LocaleController.formatString(\"AccDescrSentDate\", R.string.AccDescrSentDate, date));\n"
            "        } else {\n"
            "            sb.append(LocaleController.formatString(\"AccDescrReceivedDate\", R.string.AccDescrReceivedDate, date));\n"
            "        }\n"
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
    print("DialogCell muted removed / status announce / preview-300 / time-last+solar OK")


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
    if "a11y-fork: OPTION_BOT_BUTTONS_MENU declaration" not in t2:
        class_anchor = "public class ChatActivity"
        class_idx = t2.find(class_anchor)
        if class_idx != -1:
            brace_idx = t2.find("{", class_idx)
            if brace_idx != -1:
                t2 = (
                    t2[: brace_idx + 1]
                    + "\n    private static final int OPTION_BOT_BUTTONS_MENU = 205; // a11y-fork: OPTION_BOT_BUTTONS_MENU declaration\n"
                    + t2[brace_idx + 1 :]
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

def patch_go_to_first_message() -> None:
    """Add a localized Go to first message action to group/channel More Options."""
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (go to first message)")
        return
    t = ca.read_text(encoding="utf-8")

    if "a11y-fork: OPTION_GO_TO_FIRST_MESSAGE declaration" not in t:
        anchor = "    private final static int id_chat_compose_panel = 1000;"
        if anchor in t:
            t = t.replace(
                anchor,
                anchor + "\n    private final static int OPTION_GO_TO_FIRST_MESSAGE = 75; // a11y-fork: OPTION_GO_TO_FIRST_MESSAGE declaration",
                1,
            )

    if "a11y-fork: go-to-first-message state" not in t:
        anchor = "    private boolean loadingForward;"
        if anchor in t:
            t = t.replace(
                anchor,
                anchor + "\n    private boolean a11yGoToFirstMessageRequested; // a11y-fork: go-to-first-message state",
                1,
            )

    if "a11y-fork: go-to-first-message helper" not in t:
        anchor = "    public void firstLoadMessages() {"
        helper = """    // a11y-fork: go-to-first-message helper
    private void accessibilityGoToFirstMessage() {
        if (currentChat == null || (!ChatObject.isChannel(currentChat) && !currentChat.megagroup)) {
            return;
        }
        wasManualScroll = true;
        a11yGoToFirstMessageRequested = true;
        if (forwardEndReached[0]) {
            a11yScrollToOldestLoadedMessage();
            return;
        }
        if (loadingForward) {
            return;
        }
        loadingForward = true;
        waitingForLoad.add(lastLoadIndex);
        getMessagesController().loadMessages(dialog_id, mergeDialogId, false, 50, minMessageId[0], 0, true, maxDate[0], classGuid, 1, 0, chatMode, threadMessageId, replyMaxReadId, lastLoadIndex++, isTopic);
    }

    private void a11yScrollToOldestLoadedMessage() {
        if (!a11yGoToFirstMessageRequested || chatAdapter == null || chatLayoutManager == null || messages.isEmpty()) {
            return;
        }
        MessageObject oldest = null;
        for (int i = 0; i < messages.size(); i++) {
            MessageObject object = messages.get(i);
            if (object == null || object.getId() <= 0 || object.isDateObject || object.isSponsored()) {
                continue;
            }
            if (oldest == null || object.getId() < oldest.getId()) {
                oldest = object;
            }
        }
        if (oldest != null) {
            int position = messages.indexOf(oldest);
            if (position >= 0) {
                chatAdapter.updateRowsSafe();
                chatLayoutManager.scrollToPositionWithOffset(chatAdapter.messagesStartRow + position, AndroidUtilities.dp(8), false);
            }
        }
        a11yGoToFirstMessageRequested = false;
    }

"""
        if anchor in t:
            t = t.replace(anchor, helper + anchor, 1)

    if "a11y-fork: go-to-first-message menu" not in t:
        anchor = """            if (currentChat != null && !isTopic) {
                viewAsTopics = headerItem.lazilyAddSubItem(view_as_topics, R.drawable.msg_topics, LocaleController.getString(R.string.TopicViewAsTopics));
            }"""
        insert = anchor + """
            if (currentChat != null && (ChatObject.isChannel(currentChat) || currentChat.megagroup) && !isTopic) {
                // a11y-fork: go-to-first-message menu
                headerItem.lazilyAddSubItem(OPTION_GO_TO_FIRST_MESSAGE, R.drawable.msg_search, LocaleController.getString(R.string.A11yGoToFirstMessage));
            }"""
        if anchor in t:
            t = t.replace(anchor, insert, 1)

    if "a11y-fork: go-to-first-message handler" not in t:
        anchor = "                } else if (id == view_as_topics) {"
        branch = (
            "                } else if (id == OPTION_GO_TO_FIRST_MESSAGE) { // a11y-fork: go-to-first-message handler\n"
            "                    accessibilityGoToFirstMessage();\n"
            "                } else if (id == view_as_topics) {"
        )
        if anchor in t:
            t = t.replace(anchor, branch, 1)

    if "a11y-fork: continue go-to-first-message" not in t:
        anchor = "            loadingForward = false;\n        } else {"
        replacement = """            loadingForward = false;
            // a11y-fork: continue go-to-first-message
            if (a11yGoToFirstMessageRequested) {
                if (forwardEndReached[loadIndex]) {
                    a11yScrollToOldestLoadedMessage();
                } else {
                    loadingForward = true;
                    waitingForLoad.add(lastLoadIndex);
                    getMessagesController().loadMessages(dialog_id, mergeDialogId, false, 50, minMessageId[loadIndex], 0, true, maxDate[loadIndex], classGuid, 1, 0, chatMode, threadMessageId, replyMaxReadId, lastLoadIndex++, isTopic);
                }
            }
        } else {"""
        if anchor in t:
            t = t.replace(anchor, replacement, 1)

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity go-to-first-message OK")


def patch_file_description_spacing() -> None:
    """Accessibility-fork: read file names the SAME way as official Telegram.

    Target TalkBack output (matching DrKLO/Telegram's default order):
        "<file name> <type> file"
    e.g. "telegram.apk apk file"

    We ALSO strip any long numeric ID that Telegram (or some forks) may
    prepend to the file description, because TalkBack would otherwise read
    a long meaningless number BEFORE the file name.

    NOTE: this function also prints a DEBUG dump of the lines around
    AccDescrDocumentType in ChatMessageCell.java, so we can see the exact
    pattern that Telegram uses for the numeric id (if any).
    """
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (file description spacing)")
        return

    # ---- DEBUG: dump the exact block Telegram uses ----
    try:
        src_text = cmc.read_text(encoding="utf-8")
        lines = src_text.splitlines()
        for idx, line in enumerate(lines):
            if "AccDescrDocumentType" in line:
                start = max(0, idx - 25)
                end = min(len(lines), idx + 8)
                print("=== DEBUG: AccDescrDocumentType block (ChatMessageCell.java) ===")
                for i in range(start, end):
                    print(f"{i+1:6d}: {lines[i]}")
                print("=== END DEBUG ===")
                break
    except Exception as e:
        print("DEBUG dump failed:", e)

    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: file description spacing" in t:
        print("ChatMessageCell file description spacing already patched")
        return

    # --- 1) Strip any numeric-only append tied to the document.
    removed_id = 0
    numeric_patterns = [
        re.compile(
            r"[ \t]*sb\.append\(\s*documentAttach\.(?:id|access_hash|dc_id|date|size)\s*\);\n"
        ),
        re.compile(
            r"[ \t]*sb\.append\(\s*String\.valueOf\(\s*documentAttach\.(?:id|size|dc_id)\s*\)\s*\);\n"
        ),
        re.compile(
            r"[ \t]*sb\.append\(\s*formatString\(\s*R\.string\.(?:AccDescrFileNumber|AccDescrFileId|AccDescrDocumentId)[^\)]*\)\s*\);\n"
        ),
    ]
    for pat in numeric_patterns:
        t, n = pat.subn("", t)
        removed_id += n
    if removed_id:
        print(f"ChatMessageCell removed {removed_id} numeric-id append(s) from file description")
    else:
        print("ChatMessageCell no numeric-id append found (OK, nothing to remove)")

    # --- 2) Use EXACTLY the same order as official Telegram:
    # fileName + " " + (ext + " file").
    old_block = (
        "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
        "                        String fileName = FileLoader.getAttachFileName(documentAttach);\n"
        "                        if (fileName.indexOf('.') != -1) {\n"
        "                            sb.append(formatString(R.string.AccDescrDocumentType, fileName.substring(fileName.lastIndexOf('.') + 1).toUpperCase(Locale.ROOT)));\n"
        "                        }\n"
        "                    }"
    )
    new_block = (
        "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
        "                        // a11y-fork: file description spacing\n"
        "                        // Format: \"telegram.apk apk file\" (same as official Telegram)\n"
        "                        String fileName = FileLoader.getAttachFileName(documentAttach);\n"
        "                        if (fileName.indexOf('.') != -1) {\n"
        "                            String ext = fileName.substring(fileName.lastIndexOf('.') + 1).toUpperCase(Locale.ROOT);\n"
        "                            sb.append(fileName);\n"
        "                            sb.append(\" \");\n"
        "                            sb.append(formatString(R.string.AccDescrDocumentType, ext));\n"
        "                            sb.append(\" \");\n"
        "                        } else {\n"
        "                            sb.append(fileName);\n"
        "                            sb.append(\" \");\n"
        "                        }\n"
        "                    }"
    )
    if old_block not in t:
        print("WARN: ChatMessageCell file spacing anchor not found")
    else:
        t = t.replace(old_block, new_block, 1)
        cmc.write_text(t, encoding="utf-8")
        print("ChatMessageCell file description spacing OK")

    # --- 3) Normalize AccDescrDocumentType in string resources to "%s file"
    # (same wording as official Telegram, e.g. "apk file").
    for rel in ("values/strings.xml", "values-fa/strings.xml", "values-fa-rIR/strings.xml"):
        path = RES / rel
        if not path.exists():
            continue
        rt = path.read_text(encoding="utf-8")
        rt2, n = re.subn(
            r'(<string\s+name="AccDescrDocumentType">)[^<]*(</string>)',
            r"\1%s file\2",
            rt,
            count=1,
        )
        if n:
            path.write_text(rt2, encoding="utf-8")
            print(f"{rel} AccDescrDocumentType normalized to '%s file'")


def patch_chat_message_cell_accessibility_long_click() -> None:
    """Route TalkBack long-clicks from ChatMessageCell host and virtual nodes."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-fork: accessibility-long-click-v2"
    if marker in t:
        return
    host = "        if (action == AccessibilityNodeInfo.ACTION_CLICK) {\n"
    host_new = (
        "        // " + marker + "\n"
        "        if (action == AccessibilityNodeInfo.ACTION_LONG_CLICK) {\n"
        "            try {\n"
        "                if (delegate != null && currentMessageObject != null) {\n"
        "                    float a11yX = lastTouchX > 0 ? lastTouchX : getWidth() / 2f;\n"
        "                    float a11yY = lastTouchY > 0 ? lastTouchY : getHeight() / 2f;\n"
        "                    delegate.didLongPress(ChatMessageCell.this, a11yX, a11yY);\n"
        "                    return true;\n"
        "                }\n"
        "            } catch (Throwable e) { FileLog.e(e); }\n"
        "            return true;\n"
        "        } else if (action == AccessibilityNodeInfo.ACTION_CLICK) {\n"
    )
    if host not in t:
        print("WARN: host long-click anchor missing")
        return
    t = t.replace(host, host_new, 1)
    prov = "            if (virtualViewId == HOST_VIEW_ID) {\n                performAccessibilityAction(action, arguments);\n            } else {\n"
    prov_new = (
        "            if (virtualViewId == HOST_VIEW_ID) {\n"
        "                performAccessibilityAction(action, arguments);\n"
        "            } else {\n"
        "                // " + marker + " virtual node\n"
        "                if (action == AccessibilityNodeInfo.ACTION_LONG_CLICK) {\n"
        "                    try {\n"
        "                        if (delegate != null && currentMessageObject != null) {\n"
        "                            float a11yX = lastTouchX > 0 ? lastTouchX : getWidth() / 2f;\n"
        "                            float a11yY = lastTouchY > 0 ? lastTouchY : getHeight() / 2f;\n"
        "                            delegate.didLongPress(ChatMessageCell.this, a11yX, a11yY);\n"
        "                            sendAccessibilityEventForVirtualView(virtualViewId, AccessibilityEvent.TYPE_VIEW_LONG_CLICKED);\n"
        "                            return true;\n"
        "                        }\n"
        "                    } catch (Throwable e) { FileLog.e(e); }\n"
        "                    return true;\n"
        "                }\n"
    )
    if prov not in t:
        print("WARN: provider long-click anchor missing")
        return
    t = t.replace(prov, prov_new, 1)
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell accessibility long-click v2 OK")


def patch_stuck_together_bubbles_long_press() -> None:
    """Accessibility-fork: fix long-press on grouped/bubble-clustered messages."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (stuck bubbles long press)")
        return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-fork: clamp long-press coordinates"
    if marker in t:
        print("ChatMessageCell clamp long-press already patched")
        return

    m = re.search(
        r"(?m)^([ \t]*)public void didLongPress\(ChatMessageCell cell, float x, float y\) \{",
        t,
    )
    if not m:
        print("WARN: didLongPress(cell,x,y) not found (stuck bubbles long press)")
        return

    indent = m.group(1)
    inner = indent + "    "
    clamp = (
        f"{inner}// {marker}\n"
        f"{inner}if (cell != null) {{\n"
        f"{inner}    int w = cell.getWidth();\n"
        f"{inner}    int h = cell.getHeight();\n"
        f"{inner}    if (w > 0 && (x < 0f || x >= (float) w)) {{\n"
        f"{inner}        x = Math.max(1f, Math.min((float) w - 2f, x));\n"
        f"{inner}    }}\n"
        f"{inner}    if (h > 0 && (y < 0f || y >= (float) h)) {{\n"
        f"{inner}        y = Math.max(1f, Math.min((float) h - 2f, y));\n"
        f"{inner}    }}\n"
        f"{inner}}}\n"
    )

    insert_at = m.end() + 1
    while insert_at < len(t) and t[insert_at] == "\n":
        insert_at += 1
    t = t[:insert_at] + clamp + t[insert_at:]
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell clamp long-press OK")


def patch_chat_message_cell_float_coordinates() -> None:
    """
    Fix the TalkBack long-press accessibility injection on current Telegram:
    lastTouchX/lastTouchY are floats, while the accessibility menu helper
    expects integer coordinates.
    """
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (float coordinate fix)")
        return
    t = cmc.read_text(encoding="utf-8")
    original = t
    t = t.replace(
        "int a11yX = lastTouchX > 0 ? lastTouchX : getWidth() / 2;",
        "int a11yX = lastTouchX > 0 ? (int) lastTouchX : getWidth() / 2;",
    )
    t = t.replace(
        "int a11yY = lastTouchY > 0 ? lastTouchY : getHeight() / 2;",
        "int a11yY = lastTouchY > 0 ? (int) lastTouchY : getHeight() / 2;",
    )
    if t != original:
        cmc.write_text(t, encoding="utf-8")
        print("ChatMessageCell float coordinate compile fix OK")
    else:
        print("ChatMessageCell float coordinate fix already OK/not needed")


def _create_beep_resource() -> None:
    """
    Create a simple sine-wave beep WAV (150ms, 1000Hz) inside
    TMessagesProj/src/main/res/raw/a11y_beep.wav so the Android
    MediaPlayer can play it reliably on every device/ROM.

    The file is generated ONLY if it does not already exist, so you can
    replace it with your own custom beep any time.

    Parameters tuned for TalkBack-friendly, clearly-audible beep:
      - 150 ms duration (not too short, so it's actually audible)
      - 1000 Hz frequency (well within the human hearing range)
      - 0.7 amplitude (louder than the previous 0.6)
    """
    import struct
    import math

    raw_dir = ROOT / "src/main/res/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    wav_path = raw_dir / "a11y_beep.wav"
    if wav_path.exists():
        print("a11y_beep.wav already exists (kept as is)")
        return

    sample_rate = 44100
    duration_ms = 150
    frequency = 1000.0
    amplitude = 0.7

    n_samples = int(sample_rate * duration_ms / 1000)
    data = bytearray()
    for i in range(n_samples):
        # Simple linear fade-out to avoid click at the end
        fade = 1.0 - (i / n_samples)
        value = int(amplitude * fade * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        data += struct.pack("<h", value)

    # WAV header
    byte_rate = sample_rate * 2
    block_align = 2
    header = b"RIFF"
    header += struct.pack("<I", 36 + len(data))
    header += b"WAVE"
    header += b"fmt "
    header += struct.pack("<I", 16)
    header += struct.pack("<H", 1)  # PCM
    header += struct.pack("<H", 1)  # mono
    header += struct.pack("<I", sample_rate)
    header += struct.pack("<I", byte_rate)
    header += struct.pack("<H", block_align)
    header += struct.pack("<H", 16)  # bits per sample
    header += b"data"
    header += struct.pack("<I", len(data))

    wav_path.write_bytes(header + bytes(data))
    print(f"a11y_beep.wav created ({len(header) + len(data)} bytes)")


def patch_recording_beep() -> None:
    """
    Add an optional recording-start beep, played via MediaPlayer on the
    UI thread from a bundled WAV resource (res/raw/a11y_beep.wav).

    Using runOnUIThread is important because MediaPlayer.create() can
    misbehave on background threads (no Looper). This is far more reliable
    than ToneGenerator, which is often silent on modern Android because of
    audio focus rules.

    The beep is gated by A11yConfig.getRecordingBeep().
    """
    _create_beep_resource()

    mc = JAVA / "org/telegram/messenger/MediaController.java"
    if not mc.exists():
        print("WARN: MediaController missing (recording beep)")
        return
    t = mc.read_text(encoding="utf-8")
    marker = "a11y-fork: recording-start beep (mediaplayer-ui-thread)"
    if marker in t:
        print("MediaController recording beep already patched")
        return

    needle = "try { org.telegram.messenger.A11yConfig.applyVoiceBitrateToNative(); } catch (Throwable ignore) {}"
    if needle not in t:
        print("WARN: MediaController record-start anchor not found (recording beep)")
        return

    replacement = needle + """
                    // a11y-fork: recording-start beep (mediaplayer-ui-thread)
                    try {
                        if (org.telegram.messenger.A11yConfig.getRecordingBeep()) {
                            org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> {
                                try {
                                    final android.media.MediaPlayer a11yBeep =
                                            android.media.MediaPlayer.create(
                                                    org.telegram.messenger.ApplicationLoader.applicationContext,
                                                    org.telegram.messenger.R.raw.a11y_beep);
                                    if (a11yBeep != null) {
                                        a11yBeep.setOnCompletionListener(mp -> {
                                            try { mp.release(); } catch (Throwable ignore) {}
                                        });
                                        a11yBeep.start();
                                    }
                                } catch (Throwable ignore) {
                                }
                            });
                        }
                    } catch (Throwable ignore) {
                    }"""
    t = t.replace(needle, replacement, 1)
    mc.write_text(t, encoding="utf-8")
    print("MediaController recording-start beep (MediaPlayer, UI thread) OK")

def patch_reorder_menu_items() -> None:
    """
    Accessibility-fork: move the three a11y extras to the VERY END of the
    message options menu, right BEFORE Telegram's own "Delete" item, so
    TalkBack users always see them in a stable and predictable order:

        ...all default Telegram items...
        Bot Buttons   (if present)
        Reactions     (if present)
        Select        (always present for single normal messages)
        Delete        (Telegram's own last item -- untouched)

    This runs AFTER every menu-item patch has already inserted its block.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reorder menu items)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: reorder-menu-items"
    if marker in t:
        print("ChatActivity menu reorder already patched")
        return

    # ---- 1) Cut the three a11y blocks if they exist somewhere upstream ----
    blocks = {}

    # Bot Buttons
    m = re.search(
        r"[ \t]*// a11y-fork: bot buttons menu\n"
        r"[ \t]*if \(message != null && message\.hasInlineBotButtons\(\)\) \{\n"
        r"(?:.*?\n)*?"
        r"[ \t]*\}\n",
        t,
    )
    if m:
        blocks["bot"] = m.group(0)
        t = t[: m.start()] + t[m.end():]

    # Reactions
    m = re.search(
        r"[ \t]*// a11y-fork: reactions menu item\n"
        r"[ \t]*accessibilityReactionsToggleIndex = -1;\n"
        r"[ \t]*if \(isReactionsAvailableFinal\) \{\n"
        r"(?:.*?\n)*?"
        r"[ \t]*\}\n",
        t,
    )
    if m:
        blocks["reactions"] = m.group(0)
        t = t[: m.start()] + t[m.end():]

    # Select
    m = re.search(
        r"[ \t]*// a11y-fork: OPTION_SELECT_MESSAGE menu\n"
        r"[ \t]*if \(!actionBar\.isActionModeShowed\(\) && message != null && message\.contentType == 0 && !message\.isSponsored\(\)\) \{\n"
        r"(?:.*?\n)*?"
        r"[ \t]*\}\n",
        t,
    )
    if m:
        blocks["select"] = m.group(0)
        t = t[: m.start()] + t[m.end():]

    if not blocks:
        print("WARN: reorder-menu-items: no a11y blocks found to reorder")
        return

    # ---- 2) Rebuild them in the exact order: bot -> reactions -> select ----
    ordered_parts = []
    for key in ("bot", "reactions", "select"):
        if key in blocks:
            ordered_parts.append(blocks[key])
    if not ordered_parts:
        print("WARN: reorder-menu-items: ordered_parts empty")
        return

    combined = (
        "        // a11y-fork: reorder-menu-items -- Bot Buttons -> Reactions -> Select (at the very end, before Delete)\n"
        + "".join(ordered_parts)
        + "\n"
    )

    # ---- 3) Reinsert right BEFORE the "Delete" item so our a11y items
    # appear at the very bottom of the menu, just above Delete. ----
    # Try a few common Telegram shapes for the Delete item, in priority order.
    candidate_anchors = [
        # Modern Telegram (options + icons lists):
        (
            "        if (canDelete) {\n"
            "            items.add(LocaleController.getString(R.string.Delete));\n"
            "            options.add(OPTION_DELETE);\n"
            "            icons.add(R.drawable.msg_delete);\n"
        ),
        # Slightly older shape:
        (
            "        if (canDelete) {\n"
            "            items.add(LocaleController.getString(R.string.Delete));\n"
            "            options.add(OPTION_DELETE);\n"
        ),
        # Fallback minimal shape:
        (
            "        if (canDelete) {\n"
            "            items.add(LocaleController.getString(R.string.Delete));\n"
        ),
    ]

    inserted = False
    for anchor in candidate_anchors:
        if anchor in t:
            t = t.replace(anchor, combined + anchor, 1)
            inserted = True
            print("reorder-menu-items: inserted before Delete (anchor matched)")
            break

    if not inserted:
        # Last-resort fallback: insert before the sponsored-item block
        # (previous behaviour). Emit a warning so we know to update the anchor.
        fallback = (
            "        if (message.isSponsored() && !getUserConfig().isPremium() "
            "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
        )
        if fallback in t:
            t = t.replace(fallback, combined + fallback, 1)
            print("WARN: reorder-menu-items: Delete anchor NOT found; "
                  "fell back to sponsored anchor (items may not be at the very end)")
        else:
            print("WARN: reorder-menu-items: no anchor found at all; aborting")
            return

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity menu reorder OK (Bot Buttons -> Reactions -> Select, before Delete)")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found (clone DrKLO/Telegram as ./telegram)", file=sys.stderr)
        return 1
    print("Using scripts dir:", SCRIPTS.resolve())

    # --- Resources / localization ---
    patch_app_name()
    install_a11y_config()
    patch_a11y_localization()

    # --- Progress announcements (localized "X percent" / "X درصد") ---
    patch_radial_progress()

    # --- DialogCell base ordering (name before type) ---
    patch_dialogcell_name_then_type()

    # --- Hide a11y-noisy elements ---
    patch_hide_share_and_comment()

    # --- Forward extras ---
    patch_forward_menu_extras()

    # --- Message options: Select, Reactions, Bot Buttons ---
    patch_longpress_message_menu()
    patch_reactions_as_menu()
    patch_bot_buttons_menu()

    # --- Voice / audio ---
    patch_voice_bitrate()

    # --- Settings entry (localized) ---
    patch_settings_menu()

    # --- Recording beep (MediaPlayer on UI thread + bundled WAV) ---
    patch_recording_beep()

    # --- DialogCell preview: muted/status/preview-300/no-date ---
    patch_dialogcell_preview_muted_status()

    # --- ChatMessageCell tweaks ---
    patch_chat_message_cell_float_coordinates()
    patch_file_description_spacing()
    patch_chat_message_cell_accessibility_long_click()
    patch_stuck_together_bubbles_long_press()

    # --- Hide sponsor / Ghost mode ---
    patch_hide_sponsor_channel()
    patch_ghost_mode()

    # --- Go to first message (channels/groups) ---
    patch_go_to_first_message()

    # --- FINAL STEP: reorder a11y menu items to the very end, before Delete.
    #     Must run last, after every menu-item patch has inserted its block. ---
    patch_reorder_menu_items()

    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())