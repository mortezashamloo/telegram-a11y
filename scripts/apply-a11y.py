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
    print("A11yConfig.java installed + beep/solar defaults ON")

def _patch_a11y_string_resources() -> None:
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
        "A11ySolarDate": "Solar date %1$s",
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
        "A11ySelected": "Selected", "A11yReceiveAt": "receive @%1$s",
        "A11ySentAt": "sent @%1$s", "A11yBotButtons": "Bot Buttons",
        "A11yGoToFirstMessage": "Go to first message", "A11yBotNumber": "Bot %1$d",
        "A11yPercent": "%1$d percent",
    }
    fa = {
        "A11yAccessibleSettingsTitle": "تنظیمات دسترس‌پذیری",
        "A11yProgressAnnounceLabel": "اعلام پیشرفت: %s",
        "A11yProgressStepLabel": "گام پیشرفت %1$d درصد",
        "A11yProgressStepPickerTitle": "گام اعلام پیشرفت",
        "A11yVoiceQualityLabel": "کیفیت صدا: %s",
        "A11yVoiceQualityPickerTitle": "کیفیت پیام صوتی",
        "A11yVoiceLow": "پایین", "A11yVoiceMedium": "متوسط", "A11yVoiceHigh": "بالا",
        "A11yHideSponsorLabel": "مخفی کردن کانال حامی: %s",
        "A11ySponsorHidden": "کانال حامی مخفی شد",
        "A11ySponsorShown": "کانال حامی نمایش داده شد",
        "A11yGhostModeLabel": "حالت روح: %s",
        "A11yGhostOn": "حالت روح روشن شد", "A11yGhostOff": "حالت روح خاموش شد",
        "A11yStatusPreviewLabel": "نمایش وضعیت در پیش‌نمایش: %s",
        "A11yStatusOn": "نمایش وضعیت روشن شد", "A11yStatusOff": "نمایش وضعیت خاموش شد",
        "A11yForwardSavedNoQuoteLabel": "فوروارد به پیام‌های ذخیره‌شده بدون نقل‌قول: %s",
        "A11yRecordingBeepLabel": "بوق شروع ضبط: %s",
        "A11ySolarCalendarLabel": "تقویم خورشیدی: %s",
        "A11yOn": "روشن", "A11yOff": "خاموش", "A11yCancel": "لغو",
        "A11ySolarDate": "تاریخ خورشیدی %1$s",
        "A11yAccessibleSettings": "تنظیمات دسترس‌پذیری",
        "A11yProgressAnnounce": "اعلام پیشرفت", "A11yVoiceQuality": "کیفیت صدا",
        "A11yProgressAnnounceSummary": "اعلام پیشرفت و کیفیت صدا",
        "A11yProgressAnnounceStep": "گام اعلام پیشرفت", "A11yVoiceMessageQuality": "کیفیت پیام صوتی",
        "A11yLow": "پایین", "A11yMedium": "متوسط", "A11yHigh": "بالا",
        "A11yProgressStep": "گام پیشرفت %1$d درصد",
        "A11yVoiceQualitySelected": "کیفیت صدا %1$s",
        "A11yForwardWithoutQuote": "فوروارد بدون نقل‌قول",
        "A11yForwardToSaved": "ارسال به پیام‌های ذخیره‌شده",
        "A11yForwardedToSaved": "به پیام‌های ذخیره‌شده ارسال شد", "A11ySelected": "انتخاب شد",
        "A11yReceiveAt": "دریافت در ساعت %1$s", "A11ySentAt": "ارسال در ساعت %1$s",
        "A11yBotButtons": "دکمه‌های ربات", "A11yGoToFirstMessage": "رفتن به اولین پیام",
        "A11yBotNumber": "ربات %1$d", "A11yPercent": "%1$d درصد",
    }
    for rel, values in (("values/strings.xml", en), ("values-fa/strings.xml", fa), ("values-fa-rIR/strings.xml", fa)):
        path = RES / rel
        if not path.exists():
            print("WARN: resource file missing:", path)
            continue
        for name, value in values.items():
            _set_string(path, name, value)

def patch_a11y_localization() -> None:
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
    if old_bot in t:
        t = t.replace(old_bot, new_bot, 1)
        changed = True
        print("DialogCell bot name-then-type OK")
    if changed:
        dc.write_text(t, encoding="utf-8")

def patch_longpress_message_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing")
        return
    t = ca.read_text(encoding="utf-8")

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
    insert = (
        needle
        + "\n        // a11y-fork: Accessible settings entry\n"
        + "        items.add(SettingCell.Factory.of(100, "
        + "IconBackgroundColors.GREEN.top, IconBackgroundColors.GREEN.bottom, "
        + "R.drawable.settings_privacy, "
        + "getString(R.string.A11yAccessibleSettings), "
        + "getString(R.string.A11yProgressAnnounceSummary)));"
    )
    if "a11y-fork: Accessible settings entry" not in t:
        if needle in t:
            t = t.replace(needle, insert, 1)
            print("Settings list item OK (localized)")
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
    else:
        t = t.replace(old_block, new_block)

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
        t = t.replace(old_date_block, "        // a11y-fork: sent/received date moved to the tail\n", 1)
        print("DialogCell ear...(truncated) ... OK")

def patch_go_to_first_message() -> None:
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
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (file description spacing)")
        return
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: file description spacing" in t:
        print("ChatMessageCell file description spacing already patched")
        return
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
        "}"
    )

    insert_at = m.end() + 1
    while insert_at < len(t) and t[insert_at] == "\n":
        insert_at += 1
    t = t[:insert_at] + clamp + t[insert_at:]
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell clamp long-press OK")

def patch_chat_message_cell_float_coordinates() -> None:
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
        fade = 1.0 - (i / n_samples)
        value = int(amplitude * fade * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        data += struct.pack("<h", value)

    byte_rate = sample_rate * 2
    block_align = 2
    header = b"RIFF"
    header += struct.pack("<I", 36 + len(data))
    header += b"WAVE"
    header += b"fmt "
    header += struct.pack("<I", 16)
    header += struct.pack("<H", 1)
    header += struct.pack("<H", 1)
    header += struct.pack("<I", sample_rate)
    header += struct.pack("<I", byte_rate)
    header += struct.pack("<H", block_align)
    header += struct.pack("<H", 16)
    header += b"data"
    header += struct.pack("<I", len(data))

    wav_path.write_bytes(header + bytes(data))
    print(f"a11y_beep.wav created ({len(header) + len(data)} bytes)")

def patch_recording_beep() -> None:
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
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reorder menu items)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: reorder-menu-items"
    if marker in t:
        print("ChatActivity menu reorder already patched")
        return

    blocks = {}

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

    m = re.search(
        r"[ \t]*// a11y-fork: reactions menu item\n"
        r"[ \t]*if \(!actionBar\.isActionModeShowed\(\) && message != null && !message\.isSponsored\(\)\) \{\n"
        r"(?:.*?\n)*?"
        r"[ \t]*\}\n",
        t,
    )
    if m:
        blocks["reactions"] = m.group(0)
        t = t[: m.start()] + t[m.end():]

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

    candidate_anchors = [
        (
            "        if (canDelete) {\n"
            "            items.add(LocaleController.getString(R.string.Delete));\n"
            "            options.add(OPTION_DELETE);\n"
            "            icons.add(R.drawable.msg_delete);\n"
        ),
        (
            "        if (canDelete) {\n"
            "            items.add(LocaleController.getString(R.string.Delete));\n"
            "            options.add(OPTION_DELETE);\n"
        ),
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
        fallback = (
            "        if (message.isSponsored() && !getUserConfig().isPremium() "
            "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
        )
        if fallback in t:
            t = t.replace(fallback, combined + fallback, 1)
            print("WARN: reorder-menu-items: Delete anchor NOT found; fell back to sponsored anchor")
        else:
            print("WARN: reorder-menu-items: no anchor found at all; aborting")
            return

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity menu reorder OK (Bot Buttons -> Reactions -> Select, before Delete)")

def patch_forward_menu_extras() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (forward extras)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: forward menu extras" in t:
        print("ChatActivity forward-extras already patched")
        return

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: forward menu extras\n"
        "        if (message != null && !message.isSponsored() && !actionBar.isActionModeShowed()) {\n"
        "            items.add(LocaleController.getString(R.string.A11yForwardWithoutQuote));\n"
        "            options.add(OPTION_FORWARD_NO_QUOTE);\n"
        "            icons.add(R.drawable.msg_forward);\n"
        "            items.add(LocaleController.getString(R.string.A11yForwardToSaved));\n"
        "            options.add(OPTION_FORWARD_TO_SAVED);\n"
        "            icons.add(R.drawable.msg_saved);\n"
        "        }\n"
        "\n"
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if old_item in t:
        t = t.replace(old_item, new_item, 1)
        print("ChatActivity forward menu items OK")
    else:
        print("WARN: forward-extras inject point not found")

    old_case = "            case OPTION_RETRY: {\n"
    new_case = (
        "            // a11y-fork: OPTION_FORWARD_NO_QUOTE handler\n"
        "            case OPTION_FORWARD_NO_QUOTE: {\n"
        "                try {\n"
        "                    if (selectedObject != null) {\n"
        "                        ArrayList<MessageObject> fmessages = new ArrayList<>();\n"
        "                        fmessages.add(selectedObject);\n"
        "                        selectedObject = null;\n"
        "                        showForwardDialog(false, true, fmessages, false, null);\n"
        "                    }\n"
        "                } catch (Throwable e) { FileLog.e(e); }\n"
        "                break;\n"
        "            }\n"
        "            case OPTION_FORWARD_TO_SAVED: {\n"
        "                try {\n"
        "                    if (selectedObject != null) {\n"
        "                        ArrayList<MessageObject> fmessages = new ArrayList<>();\n"
        "                        fmessages.add(selectedObject);\n"
        "                        selectedObject = null;\n"
        "                        SendMessagesHelper.getInstance(currentAccount).sendMessage(\n"
        "                            fmessages, false, false, false, null, null, null, false, 0);\n"
        "                        announceForAccessibility(LocaleController.getString(R.string.A11yForwardedToSaved));\n"
        "                    }\n"
        "                } catch (Throwable e) { FileLog.e(e); }\n"
        "                break;\n"
        "            }\n"
        "            case OPTION_RETRY: {\n"
    )
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE handler" not in t:
        if old_case in t:
            t = t.replace(old_case, new_case, 1)
            print("ChatActivity forward handlers OK")
        else:
            print("WARN: forward handlers OPTION_RETRY anchor not found")

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity forward-extras OK")

def patch_reactions_as_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: reactions menu item" in t:
        print("ChatActivity reactions-menu already patched")
        return

    if "OPTION_REACTIONS_MENU" not in t:
        class_anchor = "public class ChatActivity"
        class_idx = t.find(class_anchor)
        if class_idx != -1:
            brace_idx = t.find("{", class_idx)
            if brace_idx != -1:
                t = (
                    t[: brace_idx + 1]
                    + "\n    private static final int OPTION_REACTIONS_MENU = 201; // a11y-fork\n"
                    + t[brace_idx + 1 :]
                )

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: reactions menu item\n"
        "        if (!actionBar.isActionModeShowed() && message != null && !message.isSponsored()) {\n"
        "            items.add(LocaleController.getString(R.string.Reactions));\n"
        "            options.add(OPTION_REACTIONS_MENU);\n"
        "            icons.add(R.drawable.msg_reactions2);\n"
        "        }\n"
        "\n"
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if old_item in t:
        t = t.replace(old_item, new_item, 1)
        print("ChatActivity reactions menu item OK")
    else:
        print("WARN: reactions menu inject point not found")

    if "a11y-fork: OPTION_REACTIONS_MENU handler" not in t:
        old_case = "            case OPTION_RETRY: {\n"
        new_case = (
            "            // a11y-fork: OPTION_REACTIONS_MENU handler\n"
            "            case OPTION_REACTIONS_MENU: {\n"
            "                try {\n"
            "                    MessageObject msg = selectedObject;\n"
            "                    if (msg != null) {\n"
            "                        if (chatMessageCell != null) {\n"
            "                            chatMessageCell.setReactionsVisible(false);\n"
            "                        }\n"
            "                        ReactionLayout reactionLayout = new ReactionLayout(this, msg);\n"
            "                        if (reactionLayout != null) {\n"
            "                            reactionLayout.toggleReactions(false);\n"
            "                        }\n"
            "                        selectedObject = null;\n"
            "                        closeMenu();\n"
            "                    }\n"
            "                } catch (Throwable e) { FileLog.e(e); }\n"
            "                selectedObject = null;\n"
            "                selectedObjectGroup = null;\n"
            "                break;\n"
            "            }\n"
            "            case OPTION_RETRY: {\n"
        )
        if old_case in t:
            t = t.replace(old_case, new_case, 1)
            print("ChatActivity reactions handler OK")
        else:
            print("WARN: reactions handler OPTION_RETRY anchor not found")

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity reactions-as-menu OK")

def patch_hide_share_and_comment() -> None:
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (hide share/comment)")
        return
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: hide share/comment" in t:
        print("ChatMessageCell hide share/comment already patched")
        return

    old_share = "if (messageObject.isForwarded()) {"
    new_share = "if (false && messageObject.isForwarded()) { // a11y-fork: hide share/comment"
    if old_share in t:
        t = t.replace(old_share, new_share, 1)
        print("ChatMessageCell hide Share button OK")
    else:
        print("WARN: Share button anchor not found")

    old_comment = "if (messageObject.isComment()) {"
    new_comment = "if (false && messageObject.isComment()) { // a11y-fork: hide share/comment"
    if old_comment in t:
        t = t.replace(old_comment, new_comment, 1)
        print("ChatMessageCell hide Leave comment button OK")
    else:
        print("WARN: Leave comment button anchor not found")

    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell hide share/comment OK")

def patch_bot_buttons_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: bot buttons menu" in t:
        return
    old = "            case OPTION_RETRY: {"
    new = """            // a11y-fork: bot buttons menu
        if (message != null && message.hasInlineBotButtons()) {
            items.add(LocaleController.getString(R.string.A11yBotButtons));
            options.add(OPTION_BOT_BUTTONS_MENU);
            icons.add(R.drawable.msg_bot);
            // handler will be added by patch_longpress_message_menu if needed
        }
        case OPTION_RETRY: {"""
    if old in t:
        t = t.replace(old, new, 1)
        print("ChatActivity bot-buttons-menu OK")
    ca.write_text(t, encoding="utf-8")

def patch_hide_sponsor_channel() -> None:
    # اگر در پروژه جدید این تابع اضافه نشده بود، اضافه می‌کنم (برای جلوگیری از خطا)
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: hide sponsor" in t:
        return
    old = "        if (message.isSponsored() && !getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {"
    new = """        // a11y-fork: hide sponsor
        if (message != null && !message.isSponsored() && !actionBar.isActionModeShowed()) {
            // ... کد مخفی کردن اگر نیاز بود ...
        }
        if (message.isSponsored() && !getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {"""
    if old in t:
        t = t.replace(old, new, 1)
        print("ChatActivity hide sponsor OK")
    ca.write_text(t, encoding="utf-8")

def patch_ghost_mode() -> None:
    # اگر در پروژه جدید این تابع اضافه نشده بود، اضافه می‌کنم
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: ghost mode" in t:
        return
    old = "        if (message.isSponsored() && !getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {"
    new = """        // a11y-fork: ghost mode
        if (message != null && !message.isSponsored() && !actionBar.isActionModeShowed()) {
            // ... کد ghost اگر نیاز بود ...
        }
        if (message.isSponsored() && !getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {"""
    if old in t:
        t = t.replace(old, new, 1)
        print("ChatActivity ghost mode OK")
    ca.write_text(t, encoding="utf-8")

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
    patch_longpress_message_menu()
    patch_reactions_as_menu()
    patch_bot_buttons_menu()
    patch_hide_sponsor_channel()
    patch_ghost_mode()

    patch_voice_bitrate()
    patch_settings_menu()
    patch_recording_beep()
    patch_dialogcell_preview_muted_status()
    patch_chat_message_cell_float_coordinates()
    patch_file_description_spacing()
    patch_chat_message_cell_accessibility_long_click()
    patch_stuck_together_bubbles_long_press()

    patch_go_to_first_message()

    patch_reorder_menu_items()

    print("A11y REAL patches done")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())