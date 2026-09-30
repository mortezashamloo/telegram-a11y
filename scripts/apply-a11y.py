#!/usr/bin/env python3
"""Apply accessibility patches to cloned Telegram tree (12.10.5 baseline) (cwd parent of telegram/).

This revision is based on v23, preserving working accessibility features, retiring overlapping friend PR 1992, and restoring the 3-state small-file Radio Button. It preserves v10 patches and only
adds the requested small-file 3-state setting, exact progress steps, fresh-install
auto-download OFF defaults, and private-chat support for Go to first message.

Portable: works with GitHub Actions (patches-repo/scripts) or local kit (scripts/).
When DrKLO/Telegram updates, re-run this script on a fresh clone.
"""
from pathlib import Path
import re
import html
import shutil
import sys
import wave
import struct
import math

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
OPTION_LINKS_MENU = 206


def _set_string(path: Path, name: str, value: str) -> None:
    # Android string resources are XML. Escape XML text characters before
    # writing/updating a <string> element. In particular, "&" in labels such
    # as "Progress & voice quality" must be written as "&amp;".
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



def _patch_a11y_string_resources() -> None:
    """Install every accessibility-fork string resource referenced by A11yConfig.java.

    The previous build failed because A11yConfig referenced the
    Label/Title/On/Off resource names while the installer created only
    shorter alias names. Keep both the exact names and compatibility aliases.
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
        "A11yBlockSmallFilesLabel": "Do not auto-download small files: %s",
        "A11yNoAutoDownloadLabel": "Do not auto-download files: %s",
        "A11yVoiceOnlyAutoDownloadLabel": "Do not auto-download files except voice messages: %s",
        "A11yOn": "On", "A11yOff": "Off", "A11yCancel": "Cancel",
        "A11ySolarDate": "%1$s",
        "A11yAt": "at",
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
        "A11ySelected": "Selected", "A11yReceiveAt": "received at %1$s",
        "A11ySentAt": "sent at %1$s", "A11yBotButtons": "Bot Buttons",
        "A11yGoToFirstMessage": "Go to first message",
        "A11yLinks": "Links", "A11yLinksLabel": "Links: %s", "A11yNoLinks": "No links",
        "A11yBotNumber": "Bot %1$d",
        "A11yPercent": "%1$d percent",
        "A11yDownloaded": "Downloaded",
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
        "A11yBlockSmallFilesLabel": "دانلود خودکار فایل‌های کم‌حجم را متوقف کن: %s",
        "A11yNoAutoDownloadLabel": "دانلود خودکار هیچ فایلی: %s",
        "A11yVoiceOnlyAutoDownloadLabel": "دانلود خودکار فایل‌ها به‌جز پیام‌های صوتی: %s",
        "A11yOn": "روشن", "A11yOff": "خاموش", "A11yCancel": "لغو",
        "A11ySolarDate": "%1$s",
        "A11yAt": "در",
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
        "A11yLinks": "لینک‌ها", "A11yLinksLabel": "لینک‌ها: %s", "A11yNoLinks": "لینکی وجود ندارد",
        "A11yBotNumber": "ربات %1$d", "A11yPercent": "%1$d درصد",
        "A11yDownloaded": "دانلود شد",
    }
    for rel, values in (("values/strings.xml", en), ("values-fa/strings.xml", fa), ("values-fa-rIR/strings.xml", fa)):
        path = RES / rel
        if not path.exists():
            print("WARN: resource file missing:", path)
            continue
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
            'items.add("Links");': 'items.add(LocaleController.getString(R.string.A11yLinks));',
            'botBtnBuilder.setTitle("Bot Buttons");': 'botBtnBuilder.setTitle(LocaleController.getString(R.string.A11yBotButtons));',
            '("Bot " + (labels.size() + 1))': 'LocaleController.formatString("A11yBotNumber", R.string.A11yBotNumber, labels.size() + 1)',
            '"Accessible settings", "Progress & voice quality"': 'LocaleController.getString(R.string.A11yAccessibleSettings), LocaleController.getString(R.string.A11yProgressAnnounceSummary)',
            'parent.announceForAccessibility(org.telegram.messenger.LocaleController.formatString("A11yPercent", org.telegram.messenger.R.string.A11yPercent, step));': 'parent.announceForAccessibility(org.telegram.messenger.LocaleController.formatString("A11yPercent", org.telegram.messenger.R.string.A11yPercent, step));',
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
    cfg = dst.read_text(encoding="utf-8")
    # a11y-fork: recording beep stays OFF by default (matches A11yConfig.java's own
    # default) -- the user turns it on themselves from Accessible Settings. Recording
    # vibration (patch_recording_beep) is unconditional and independent of this setting.
    cfg = cfg.replace("getBoolean(PREF_SOLAR_CALENDAR, false)", "getBoolean(PREF_SOLAR_CALENDAR, true)")
    cfg = cfg.replace("getBoolean(PREF_RECORDING_BEEP, false)", "getBoolean(PREF_RECORDING_BEEP, true)")
    if "PREF_LINKS_MENU" not in cfg:
        cfg = cfg.replace(
            'public static final String PREF_SOLAR_CALENDAR = "a11y_solar_calendar";',
            'public static final String PREF_SOLAR_CALENDAR = "a11y_solar_calendar";\n    public static final String PREF_LINKS_MENU = "a11y_links_menu";'
        )
    if "PREF_BLOCK_SMALL_AUTO_DOWNLOADS" not in cfg:
        cfg = cfg.replace(
            'public static final String PREF_LINKS_MENU = "a11y_links_menu";',
            'public static final String PREF_LINKS_MENU = "a11y_links_menu";\n    public static final String PREF_BLOCK_SMALL_AUTO_DOWNLOADS = "a11y_block_small_auto_downloads";'
        )
    if "getBlockSmallAutoDownloads()" not in cfg:
        anchor = "    public static boolean getSolarCalendar() {"
        methods = (
            "    // a11y-fork: optional protection against automatic downloads of very small files.\n"
            "    // Default OFF; voice messages are exempt in DownloadController.\n"
            "    public static boolean getBlockSmallAutoDownloads() {\n"
            "        try {\n"
            "            return MessagesController.getGlobalMainSettings().getBoolean(PREF_BLOCK_SMALL_AUTO_DOWNLOADS, false);\n"
            "        } catch (Throwable ignore) {\n"
            "            return false;\n"
            "        }\n"
            "    }\n\n"
            "    public static void setBlockSmallAutoDownloads(boolean value) {\n"
            "        try {\n"
            "            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_BLOCK_SMALL_AUTO_DOWNLOADS, value).apply();\n"
            "            try { org.telegram.messenger.DownloadController.getInstance(UserConfig.selectedAccount).checkAutodownloadSettings(); } catch (Throwable ignore) {}\n"
            "        } catch (Throwable ignore) {\n"
            "        }\n"
            "    }\n\n"
        )
        if anchor in cfg:
            cfg = cfg.replace(anchor, methods + anchor, 1)
    if "getLinksMenuEnabled()" not in cfg:
        anchor = "    public static boolean getSolarCalendar() {"
        methods = (
            "    public static boolean getLinksMenuEnabled() {\n"
            "        try {\n"
            "            return MessagesController.getGlobalMainSettings().getBoolean(PREF_LINKS_MENU, false);\n"
            "        } catch (Throwable ignore) {\n"
            "            return false;\n"
            "        }\n"
            "    }\n\n"
            "    public static void setLinksMenuEnabled(boolean value) {\n"
            "        try {\n"
            "            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_LINKS_MENU, value).apply();\n"
            "        } catch (Throwable ignore) {\n"
            "        }\n"
            "    }\n\n"
        )
        if anchor in cfg:
            cfg = cfg.replace(anchor, methods + anchor, 1)
    if "which == 9" not in cfg and "getBlockSmallAutoDownloads()" in cfg:
        links_item = '                    LocaleController.formatString(R.string.A11yLinksLabel, onOff(getLinksMenuEnabled()))'
        if links_item in cfg and "A11yBlockSmallFilesLabel" not in cfg:
            cfg = cfg.replace(
                links_item,
                links_item + ',\n                    LocaleController.formatString(R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads()))',
                1,
            )
        elif "A11yBlockSmallFilesLabel" not in cfg:
            solar_item = '                    LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar()))'
            if solar_item in cfg:
                cfg = cfg.replace(
                    solar_item,
                    solar_item + ',\n                    LocaleController.formatString(R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads()))',
                    1,
                )

        links_handler = (
            "                        } else if (which == 8) {\n"
            "                            setLinksMenuEnabled(!getLinksMenuEnabled());\n"
            "                            announce(activity, LocaleController.formatString(\n"
            "                                    R.string.A11yLinksLabel, onOff(getLinksMenuEnabled())));\n"
            "                        }\n"
        )
        if links_handler in cfg:
            cfg = cfg.replace(
                links_handler,
                links_handler.replace(
                    "                        }\n",
                    "                        } else if (which == 9) {\n"
                    "                            setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());\n"
                    "                            announce(activity, LocaleController.formatString(\n"
                    "                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));\n"
                    "                        }\n",
                    1,
                ),
                1,
            )
        else:
            solar_handler = (
                "                        } else if (which == 7) {\n"
                "                            setSolarCalendar(!getSolarCalendar());\n"
                "                            announce(activity, LocaleController.formatString(\n"
                "                                    R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar())));\n"
                "                        }\n"
            )
            if solar_handler in cfg:
                cfg = cfg.replace(
                    solar_handler,
                    solar_handler.replace(
                        "                        }\n",
                        "                        } else if (which == 9) {\n"
                        "                            setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());\n"
                        "                            announce(activity, LocaleController.formatString(\n"
                        "                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));\n"
                        "                        }\n",
                        1,
                    ),
                    1,
                )


    # a11y-fork: Solar date replacement supports both old int and current long signatures.
    # It is date-only: Telegram's surrounding formatter controls the time-of-day.
    solar_start = cfg.find("    public static String formatSolarDate(")
    if solar_start >= 0:
        solar_end = cfg.find("    private static String toPersianDigits", solar_start)
        if solar_end > solar_start:
            solar_method = (
                "    public static String formatSolarDate(long unixSeconds) {\n"
                "        try {\n"
                "            java.util.Calendar cal = java.util.Calendar.getInstance();\n"
                "            cal.setTimeInMillis(unixSeconds * 1000L);\n"
                "            int gy = cal.get(java.util.Calendar.YEAR);\n"
                "            int gm = cal.get(java.util.Calendar.MONTH) + 1;\n"
                "            int gd = cal.get(java.util.Calendar.DAY_OF_MONTH);\n"
                "            int jy;\n"
                "            if (gy > 1600) { jy = 979; gy -= 1600; } else { jy = 0; gy -= 621; }\n"
                "            int[] gdm = {0,31,59,90,120,151,181,212,243,273,304,334};\n"
                "            int gy2 = gm > 2 ? gy + 1 : gy;\n"
                "            int days = 365 * gy + (gy2 + 3) / 4 - (gy2 + 99) / 100 + (gy2 + 399) / 400 - 80 + gd + gdm[gm - 1];\n"
                "            jy += 33 * (days / 12053); days %= 12053;\n"
                "            jy += 4 * (days / 1461); days %= 1461;\n"
                "            if (days > 365) { jy += (days - 1) / 365; days = (days - 1) % 365; }\n"
                "            int jm = days < 186 ? 1 + days / 31 : 7 + (days - 186) / 30;\n"
                "            int jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);\n"
                "            String[] faMonths = {\"فروردین\",\"اردیبهشت\",\"خرداد\",\"تیر\",\"مرداد\",\"شهریور\",\"مهر\",\"آبان\",\"آذر\",\"دی\",\"بهمن\",\"اسفند\"};\n"
                "            String[] enMonths = {\"Farvardin\",\"Ordibehesht\",\"Khordad\",\"Tir\",\"Mordad\",\"Shahrivar\",\"Mehr\",\"Aban\",\"Azar\",\"Dey\",\"Bahman\",\"Esfand\"};\n"
                "            boolean isFa = \"fa\".equalsIgnoreCase(java.util.Locale.getDefault().getLanguage());\n"
                "            String month = (isFa ? faMonths : enMonths)[jm - 1];\n"
                "            java.util.Calendar now = java.util.Calendar.getInstance();\n"
                "            int nowGy = now.get(java.util.Calendar.YEAR);\n"
                "            int nowGm = now.get(java.util.Calendar.MONTH) + 1;\n"
                "            int nowGd = now.get(java.util.Calendar.DAY_OF_MONTH);\n"
                "            int nowJy;\n"
                "            if (nowGy > 1600) { nowJy = 979; nowGy -= 1600; } else { nowJy = 0; nowGy -= 621; }\n"
                "            int nowGy2 = nowGm > 2 ? nowGy + 1 : nowGy;\n"
                "            int nowDays = 365 * nowGy + (nowGy2 + 3) / 4 - (nowGy2 + 99) / 100 + (nowGy2 + 399) / 400 - 80 + nowGd + gdm[nowGm - 1];\n"
                "            nowJy += 33 * (nowDays / 12053); nowDays %= 12053;\n"
                "            nowJy += 4 * (nowDays / 1461); nowDays %= 1461;\n"
                "            if (nowDays > 365) { nowJy += (nowDays - 1) / 365; }\n"
                "            String value = jy == nowJy ? String.format(java.util.Locale.US, \"%d %s\", jd, month) : String.format(java.util.Locale.US, \"%d %s %d\", jd, month, jy);\n"
                "            return LocaleController.formatString(R.string.A11ySolarDate, isFa ? toPersianDigits(value) : value);\n"
                "        } catch (Throwable ignore) { return \"\"; }\n"
                "    }\n\n"
                "    public static String formatSolarDateAudio(long unixSeconds) {\n"
                "        try {\n"
                "            long dateMs = unixSeconds * 1000L;\n"
                "            java.util.Calendar now = java.util.Calendar.getInstance();\n"
                "            java.util.Calendar msg = java.util.Calendar.getInstance();\n"
                "            msg.setTimeInMillis(dateMs);\n"
                "            int nowDay = now.get(java.util.Calendar.DAY_OF_YEAR);\n"
                "            int nowYear = now.get(java.util.Calendar.YEAR);\n"
                "            int msgDay = msg.get(java.util.Calendar.DAY_OF_YEAR);\n"
                "            int msgYear = msg.get(java.util.Calendar.YEAR);\n"
                "            java.text.SimpleDateFormat timeFmt = new java.text.SimpleDateFormat(\"HH:mm\", java.util.Locale.getDefault());\n"
                "            String time = timeFmt.format(new java.util.Date(dateMs));\n"
                "            if (msgDay == nowDay && msgYear == nowYear) {\n"
                "                return LocaleController.formatString(R.string.TodayAtFormatted, time);\n"
                "            } else if (msgDay + 1 == nowDay && msgYear == nowYear) {\n"
                "                return LocaleController.formatString(R.string.YesterdayAtFormatted, time);\n"
                "            } else {\n"
                "                String solar = formatSolarDate(unixSeconds);\n"
                "                if (solar == null || solar.isEmpty()) return LocaleController.formatDateAudio(unixSeconds, true);\n"
                "                return solar + \" \" + LocaleController.getString(R.string.A11yAt) + \" \" + time;\n"
                "            }\n"
                "        } catch (Throwable ignore) {\n"
                "            return LocaleController.formatDateAudio(unixSeconds, true);\n"
                "        }\n"
                "    }\n\n"
            )
            cfg = cfg[:solar_start] + solar_method + cfg[solar_end:]
    dst.write_text(cfg, encoding="utf-8")
    print("A11yConfig.java installed + Solar date fixed/date-only + small-file setting added")


def _inject_progress_announce(java_path: Path) -> None:
    if not java_path.exists():
        print(f"WARN: {java_path.name} missing")
        return
    t = java_path.read_text(encoding="utf-8")
    # Cached Telegram trees can already contain an older accessibility patch.
    # Normalize that stale block instead of returning early, otherwise an old
    # unqualified LocaleController/R reference can survive into the build.
    stale_patterns = [
        'LocaleController.formatString("A11yPercent", R.string.A11yPercent, step)',
        'parent.announceForAccessibility(step + " percent");',
    ]
    fixed_call = 'org.telegram.messenger.LocaleController.formatString("A11yPercent", org.telegram.messenger.R.string.A11yPercent, step)'
    changed_stale = False
    for stale in stale_patterns:
        if stale in t:
            if stale.startswith('parent.announceForAccessibility'):
                t = t.replace(stale, 'parent.announceForAccessibility(' + fixed_call + ');')
            else:
                t = t.replace(stale, fixed_call)
            changed_stale = True
    if changed_stale:
        java_path.write_text(t, encoding="utf-8")
        print(f"{java_path.name} stale progress references normalized")
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
                        if (pct >= 100) {
                            if (a11yLastAnnouncedPercent != 100) {
                                a11yLastAnnouncedPercent = 100;
                                parent.announceForAccessibility(org.telegram.messenger.LocaleController.getString(
                                        org.telegram.messenger.R.string.A11yDownloaded));
                            }
                        } else if (step != a11yLastAnnouncedPercent) {
                            a11yLastAnnouncedPercent = step;
                            parent.announceForAccessibility(org.telegram.messenger.LocaleController.formatString(
                                    "A11yPercent", org.telegram.messenger.R.string.A11yPercent, step));
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
    shared = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n                IS_FORWARD_NO_QUOTE = true;\n                // fall through to the normal Forward UI\n            case OPTION_FORWARD: {"
    if "case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote" not in t:
        if normal not in t:
            raise RuntimeError("normal OPTION_FORWARD case not found")
        t = t.replace(normal, shared, 1)

    # Add/replace Saved Messages handler immediately before normal Forward.
    marker = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
    saved_start = t.find(marker)
    if saved_start < 0:
        raise RuntimeError("forward no-quote case insertion failed")
    # Insert Saved case before no-quote case if it is not already present.
    if "a11y-fork: forward to Saved Messages" not in t:
        saved = '''            case OPTION_FORWARD_TO_SAVED: { // a11y-fork: forward to Saved Messages\n                if (selectedObject != null) {\n                    try {\n                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {\n                            toSend.addAll(selectedObjectGroup.messages);\n                        } else {\n                            toSend.add(selectedObject);\n                        }\n                        IS_FORWARD_NO_QUOTE = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();\n                        long savedId = getUserConfig().getClientUserId();\n                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n                        try {\n                            if (getParentActivity() != null) {\n                                getParentActivity().getWindow().getDecorView().announceForAccessibility(\"Forwarded to Saved Messages\");\n                            }\n                        } catch (Throwable ignore) {}\n                    } catch (Throwable e) {\n                        FileLog.e(e);\n                    }\n                }\n                selectedObject = null;\n                selectedObjectToEditCaption = null;\n                selectedObjectGroup = null;\n                break;\n            }\n'''
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
                t=t.replace(old,new,1); smh.write_text(t,encoding="utf-8"); print("drop_author one-shot v2 OK")
    t=ca.read_text(encoding="utf-8")
    # IMPORTANT: the forward handler itself also contains the token
    # IS_FORWARD_NO_QUOTE, so checking `if "IS_FORWARD_NO_QUOTE" not in t`
    # is not sufficient to detect the field declaration.
    if "public static boolean IS_FORWARD_NO_QUOTE" not in t:
        anchor="protected TLRPC.Chat currentChat;"
        if anchor in t:
            t=t.replace(anchor,"public static boolean IS_FORWARD_NO_QUOTE = false;\n    "+anchor,1)
            print("IS_FORWARD_NO_QUOTE field OK")
        else:
            print("WARN: currentChat anchor not found (IS_FORWARD_NO_QUOTE field)")

    # The new switch cases use these accessibility option IDs.  They must be
    # declared inside ChatActivity; Python constants at the top of this
    # script do not exist in the generated Java source.
    option_decl = (
        "private static final int OPTION_FORWARD_NO_QUOTE = 200;\n"
        "    private static final int OPTION_FORWARD_TO_SAVED = 202;"
    )
    if "private static final int OPTION_FORWARD_NO_QUOTE = 200;" not in t:
        field_anchor = "public static boolean IS_FORWARD_NO_QUOTE = false;"
        if field_anchor in t:
            t=t.replace(field_anchor, field_anchor+"\n    "+option_decl, 1)
            print("Forward option constants OK")
        else:
            print("WARN: IS_FORWARD_NO_QUOTE field anchor not found (option constants)")
    if "a11y-fork: forward menu extras" not in t:
        old=("                if (canForward) {\n"
             "                    items.add(LocaleController.getString(R.string.Forward));\n"
             "                    options.add(OPTION_FORWARD);\n"
             "                    icons.add(R.drawable.msg_forward);\n"
             "                }")
        new=("                if (canForward) {\n"
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
             "                }")
        if old in t: t=t.replace(old,new,1); print("Forward menu extras OK")
        else: print("WARN: canForward menu block not found")
    t=patch_forward_handler(t)
    ca.write_text(t,encoding="utf-8")
    print("Forward option handlers v2 OK")


def patch_photo_longpress_message_options() -> None:
    """Force TalkBack long-press on photo-only/no-caption messages into Message Options."""
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (photo long-press)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: photo-no-caption longpress v1"
    if marker in t:
        return
    needle = """            if (view instanceof ChatMessageCell && (((ChatMessageCell) view).getMessageObject() != null && ((ChatMessageCell) view).getMessageObject().type != MessageObject.TYPE_JOINED_CHANNEL)) {
"""
    if needle not in t:
        print("WARN: ChatActivity message long-press anchor not found (photo case)")
        return
    insert = """            // a11y-fork: photo-no-caption longpress v1
            if (view instanceof ChatMessageCell && !actionBar.isActionModeShowed()) {
                try {
                    MessageObject a11yPhotoMessage = ((ChatMessageCell) view).getMessageObject();
                    boolean a11yPhotoOnly = a11yPhotoMessage != null
                            && MessageObject.isPhoto(a11yPhotoMessage.messageOwner)
                            && android.text.TextUtils.isEmpty(a11yPhotoMessage.messageOwner.message);
                    android.view.accessibility.AccessibilityManager a11yPhotoAm =
                            (android.view.accessibility.AccessibilityManager) getParentActivity()
                                    .getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);
                    if (a11yPhotoOnly && a11yPhotoAm != null && a11yPhotoAm.isEnabled()) {
                        result = createMenu(view, true, false, x, y, true);
                        return true;
                    }
                } catch (Throwable ignore) {
                }
            }

"""
    t=t.replace(needle,insert+needle,1)
    ca.write_text(t,encoding="utf-8")
    print("Photo-only/no-caption TalkBack long-press -> Message Options OK")

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
    # The workflow already applies patches/04-comment-and-reactions.patch,
    # which implements the Reactions menu item using OPTION_TOGGLE_REACTIONS_ROW.
    # Do not add a second item with OPTION_REACTIONS_MENU.
    if "OPTION_TOGGLE_REACTIONS_ROW" in t and "Accessibility: put reactions behind" in t:
        print("ChatActivity Reactions menu already provided by 04-comment-and-reactions.patch")
        return
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
        "            // a11y-fork: under TalkBack, long-press must open the full\n"
        "            // single-message Message Options menu for every ChatMessageCell\n"
        "            // type (text, photo, video, document/file, voice, etc.).\n"
        "            boolean a11yOn2 = false;\n"
        "            try {\n"
        "                android.view.accessibility.AccessibilityManager am2 = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n"
        "                a11yOn2 = am2 != null && am2.isEnabled();\n"
        "            } catch (Throwable ignore) {}\n"
        "            if (a11yOn2) {\n"
        "                createMenu(cell, true, false, x, y, true);\n"
        "            } else {\n"
        "                createMenu(cell, false, false, x, y, false);\n"
        "                startMultiselect(chatListView.getChildAdapterPosition(cell));\n"
        "            }"
    )
    if "a11y-fork: under TalkBack, long-press must open the full" not in t:
        if old_dlp in t:
            t = t.replace(old_dlp, new_dlp, 1)
            print("didLongPress universal TalkBack Message Options OK")
        elif "a11y-fork: do not auto-start multi-select under TalkBack" in t:
            old_v1 = (
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
            if old_v1 in t:
                t = t.replace(old_v1, new_dlp, 1)
                print("didLongPress universal TalkBack Message Options upgraded OK")
            else:
                print("WARN: didLongPress v1 block not found")
        else:
            print("WARN: didLongPress block not found")

    # Telegram 12.10.5 uses a direct ChatMessageCellDelegate.didLongPress implementation
    # for accessibility-triggered long clicks. The older anchor above may not exist, so
    # patch the exact current delegate method as a safe fallback.
    if "a11y-fork: 12.10.5 TalkBack didLongPress" not in t:
        old_dlp_125 = '        public void didLongPress(ChatMessageCell cell, float x, float y) {\n            createMenu(cell, false, false, x, y, false);\n            startMultiselect(chatListView.getChildAdapterPosition(cell));\n        }'
        new_dlp_125 = '        public void didLongPress(ChatMessageCell cell, float x, float y) {\n            // a11y-fork: 12.10.5 TalkBack didLongPress\n            boolean a11yTalkBack = false;\n            try {\n                android.view.accessibility.AccessibilityManager am = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n                a11yTalkBack = am != null && am.isEnabled() && am.isTouchExplorationEnabled();\n            } catch (Throwable ignore) {}\n            if (a11yTalkBack) {\n                createMenu(cell, true, false, x, y, true);\n            } else {\n                createMenu(cell, false, false, x, y, false);\n                startMultiselect(chatListView.getChildAdapterPosition(cell));\n            }\n        }'
        if old_dlp_125 in t:
            t=t.replace(old_dlp_125,new_dlp_125,1)
            print("12.10.5 TalkBack didLongPress routing OK")
        else:
            print("WARN: 12.10.5 didLongPress exact anchor not found")

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



def patch_a11y_download_settings() -> None:
    """Add explicit all-download and voice-only download controls."""
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        print("WARN: A11yConfig.java missing (download settings)")
        return
    t = cfg.read_text(encoding="utf-8")
    if "PREF_NO_AUTO_DOWNLOAD" not in t:
        t=t.replace(
            'public static final String PREF_BLOCK_SMALL_AUTO_DOWNLOADS = "a11y_block_small_auto_downloads";',
            'public static final String PREF_BLOCK_SMALL_AUTO_DOWNLOADS = "a11y_block_small_auto_downloads";\n'
            '    public static final String PREF_NO_AUTO_DOWNLOAD = "a11y_no_auto_download";\n'
            '    public static final String PREF_VOICE_ONLY_AUTO_DOWNLOAD = "a11y_voice_only_auto_download";',1)
    if "getNoAutoDownload()" not in t:
        anchor='    public static boolean getSolarCalendar() {'
        methods='''    public static boolean getNoAutoDownload() {
        try { return MessagesController.getGlobalMainSettings().getBoolean(PREF_NO_AUTO_DOWNLOAD, false); }
        catch (Throwable ignore) { return false; }
    }

    public static void setNoAutoDownload(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit()
                    .putBoolean(PREF_NO_AUTO_DOWNLOAD, value)
                    .putBoolean(PREF_VOICE_ONLY_AUTO_DOWNLOAD, false)
                    .apply();
            try { org.telegram.messenger.DownloadController.getInstance(UserConfig.selectedAccount).checkAutodownloadSettings(); } catch (Throwable ignore) {}
        } catch (Throwable ignore) {}
    }

    public static boolean getVoiceOnlyAutoDownload() {
        try { return MessagesController.getGlobalMainSettings().getBoolean(PREF_VOICE_ONLY_AUTO_DOWNLOAD, true); }
        catch (Throwable ignore) { return true; }
    }

    public static void setVoiceOnlyAutoDownload(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit()
                    .putBoolean(PREF_VOICE_ONLY_AUTO_DOWNLOAD, value)
                    .putBoolean(PREF_NO_AUTO_DOWNLOAD, false)
                    .apply();
            try { org.telegram.messenger.DownloadController.getInstance(UserConfig.selectedAccount).checkAutodownloadSettings(); } catch (Throwable ignore) {}
        } catch (Throwable ignore) {}
    }

'''
        if anchor in t: t=t.replace(anchor,methods+anchor,1)
    small='LocaleController.formatString(R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads()))'
    if 'R.string.A11yNoAutoDownloadLabel' not in t and small in t:
        t=t.replace(small, small+',\n                    LocaleController.formatString(R.string.A11yNoAutoDownloadLabel, onOff(getNoAutoDownload())),\n                    LocaleController.formatString(R.string.A11yVoiceOnlyAutoDownloadLabel, onOff(getVoiceOnlyAutoDownload()))',1)
    if 'which == 10' not in t and 'which == 9' in t:
        h='''                        } else if (which == 9) {
                            setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));
                        }
'''
        r='''                        } else if (which == 9) {
                            setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));
                        } else if (which == 10) {
                            setNoAutoDownload(!getNoAutoDownload());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yNoAutoDownloadLabel, onOff(getNoAutoDownload())));
                        } else if (which == 11) {
                            setVoiceOnlyAutoDownload(!getVoiceOnlyAutoDownload());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yVoiceOnlyAutoDownloadLabel, onOff(getVoiceOnlyAutoDownload())));
                        }
'''
        if h in t: t=t.replace(h,r,1)
    cfg.write_text(t,encoding='utf-8')
    print('A11y download settings: all-download + voice-only controls OK')

def patch_auto_download_policy() -> None:
    """Default automatic downloads OFF for photo/video/document on all networks;
    voice messages remain enabled. User changes are not overridden after first run.
    """
    dc = JAVA / "org/telegram/messenger/DownloadController.java"
    if not dc.exists():
        print("WARN: DownloadController missing (auto-download policy)")
        return
    t = dc.read_text(encoding="utf-8")
    marker = "a11y-fork: default auto-download policy v1"
    if marker not in t:
        anchor = "    public DownloadController(int instance) {"
        helper = (
            "    // " + marker + "\n"
            "    private void applyA11yDefaultAutoDownloadPolicy() {\n"
            "        try {\n"
            "            android.content.SharedPreferences prefs = MessagesController.getMainSettings(currentAccount);\n"
            "            if (prefs.getBoolean(\"a11y_auto_download_defaults_applied_v1\", false)) return;\n"
            "            int voiceOnlyMask = 0;\n"
            "            for (int i = 0; i < 4; i++) {\n"
            "                mobilePreset.mask[i] = voiceOnlyMask; wifiPreset.mask[i] = voiceOnlyMask; roamingPreset.mask[i] = voiceOnlyMask;\n"
            "            }\n"
            "            mobilePreset.enabled = false; wifiPreset.enabled = false; roamingPreset.enabled = false;\n"
            "            mobilePreset.preloadVideo = false; wifiPreset.preloadVideo = false; roamingPreset.preloadVideo = false;\n"
            "            mobilePreset.preloadMusic = false; wifiPreset.preloadMusic = false; roamingPreset.preloadMusic = false;\n"
            "            currentMobilePreset = 3; currentWifiPreset = 3; currentRoamingPreset = 3;\n"
            "            prefs.edit().putString(\"mobilePreset\", mobilePreset.toString()).putString(\"wifiPreset\", wifiPreset.toString()).putString(\"roamingPreset\", roamingPreset.toString())\n"
            "                    .putInt(\"currentMobilePreset\", 3).putInt(\"currentWifiPreset\", 3).putInt(\"currentRoamingPreset\", 3)\n"
            "                    .putBoolean(\"a11y_auto_download_defaults_applied_v1\", true).commit();\n"
            "            checkAutodownloadSettings();\n"
            "        } catch (Throwable e) { FileLog.e(e); }\n"
            "    }\n\n"
        )
        if anchor in t:
            t=t.replace(anchor,helper+anchor,1)
        else:
            print("WARN: DownloadController constructor anchor not found")
            return
        anchor2 = """        if (getUserConfig().isClientActivated()) {
            checkAutodownloadSettings();
        }
"""
        repl2 = """        // a11y-fork: default auto-download policy v1
        applyA11yDefaultAutoDownloadPolicy();
        if (getUserConfig().isClientActivated()) {
            checkAutodownloadSettings();
        }
"""
        if anchor2 in t: t=t.replace(anchor2,repl2,1)
        else: print("WARN: DownloadController post-constructor anchor not found")
    if "a11y-fork: block small automatic downloads" not in t:
        generic_anchor = """        long maxSize = preset.sizes[typeToIndex(type)];
        return (type == AUTODOWNLOAD_TYPE_PHOTO || size != 0 && size <= maxSize) && (type == AUTODOWNLOAD_TYPE_AUDIO || (mask & type) != 0);"""
        generic_repl = """        long maxSize = preset.sizes[typeToIndex(type)];
        // a11y-fork: block small automatic downloads (generic type/size path)
        if (org.telegram.messenger.A11yConfig.getNoAutoDownload()) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getVoiceOnlyAutoDownload()
                && type != AUTODOWNLOAD_TYPE_AUDIO) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getNoAutoDownload()) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getVoiceOnlyAutoDownload()
                && type != AUTODOWNLOAD_TYPE_AUDIO) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return false;
        }
        return (type == AUTODOWNLOAD_TYPE_PHOTO || size != 0 && size <= maxSize) && (type == AUTODOWNLOAD_TYPE_AUDIO || (mask & type) != 0);"""
        if generic_anchor in t:
            t=t.replace(generic_anchor,generic_repl,1)

        a="""        long size = MessageObject.getMessageSize(message);
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        b="""        long size = MessageObject.getMessageSize(message);
        // a11y-fork: block small automatic downloads
        if (org.telegram.messenger.A11yConfig.getNoAutoDownload()) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getVoiceOnlyAutoDownload()
                && type != AUTODOWNLOAD_TYPE_AUDIO) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return 0;
        }
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        if a in t: t=t.replace(a,b,1)
        else: print("WARN: DownloadController message-size anchor not found")
        a2="""        final long size = overrideSize;
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        b2="""        final long size = overrideSize;
        // a11y-fork: block small automatic downloads (override-size path)
        if (org.telegram.messenger.A11yConfig.getNoAutoDownload()) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getVoiceOnlyAutoDownload()
                && type != AUTODOWNLOAD_TYPE_AUDIO) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return 0;
        }
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        if a2 in t: t=t.replace(a2,b2,1)
        else: print("WARN: DownloadController override-size anchor not found")
        a3="""        long size = MessageObject.getMediaSize(media);
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        b3="""        long size = MessageObject.getMediaSize(media);
        // a11y-fork: block small automatic downloads (media path)
        if (org.telegram.messenger.A11yConfig.getNoAutoDownload()) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getVoiceOnlyAutoDownload()
                && type != AUTODOWNLOAD_TYPE_AUDIO) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return 0;
        }
        if (isVideo && preset.preloadVideo && size > maxSize && maxSize > 2 * 1024 * 1024) {"""
        if a3 in t: t=t.replace(a3,b3,1)
        else: print("WARN: DownloadController media-size anchor not found")
    dc.write_text(t,encoding="utf-8")
    print("DownloadController default auto-download OFF except voice + small-file guard OK")

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


def patch_recording_beep() -> None:
    """Install an audible cue directly at MediaController.startRecording()."""
    mc = JAVA / "org/telegram/messenger/MediaController.java"
    if not mc.exists():
        print("WARN: MediaController missing (recording beep)")
        return
    t = mc.read_text(encoding="utf-8")
    marker = "a11y-fork: recording-start beep-v2"
    if marker in t:
        print("MediaController recording-start beep v2 already patched")
        return

    # Remove the old fragile v1 implementation if a checkout was already patched.
    old = re.compile(r'\n\s*// a11y-fork: recording-start beep-wav-v1[\s\S]*?\n\s*\}\s*catch \(Throwable e\) \{\s*\n\s*FileLog\.e\(e\);\s*\n\s*\}\s*', re.MULTILINE)
    t, n = old.subn("\n", t, count=1)
    if n:
        print("Old recording beep v1 removed")

    # Anchor to Telegram's real recording entry point, not to our bitrate patch.
    sig = re.compile(r'(?m)^(?P<i>\s*)public void startRecording\(int currentAccount, long dialogId, MessageObject replyToMsg, MessageObject replyToTopMsg, TL_stories\.StoryItem replyStory, int guid, boolean manual, SendMessageChatArguments sendMessageChatArguments, long monoForumPeerId, MessageSuggestionParams suggestionParams\) \{\n')
    m = sig.search(t)
    if not m:
        print("WARN: MediaController.startRecording() declaration not found (recording beep)")
        return
    i = m.group("i") + "    "
    block = """        // a11y-fork: recording-start beep-v2 -- BEFORE Telegram starts recording
        try {
            try {
                android.content.Context a11yCtx = org.telegram.messenger.ApplicationLoader.applicationContext;
                if (a11yCtx != null) {
                    android.os.Vibrator a11yVibrator = (android.os.Vibrator) a11yCtx.getSystemService(android.content.Context.VIBRATOR_SERVICE);
                    if (a11yVibrator != null && a11yVibrator.hasVibrator()) {
                        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                            a11yVibrator.vibrate(android.os.VibrationEffect.createOneShot(50, android.os.VibrationEffect.DEFAULT_AMPLITUDE));
                        } else {
                            a11yVibrator.vibrate(50);
                        }
                    }
                }
            } catch (Throwable ignoreVibration) {}
            if (org.telegram.messenger.A11yConfig.getRecordingBeep()) {
                try {
                    android.media.ToneGenerator a11yTone = new android.media.ToneGenerator(android.media.AudioManager.STREAM_RING, 90);
                    a11yTone.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 120);
                    new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
                        try { a11yTone.release(); } catch (Throwable ignoreRelease) {}
                    }, 160);
                } catch (Throwable beepError) {
                    org.telegram.messenger.FileLog.e(beepError);
                }
            }
        } catch (Throwable ignoreBeep) {}
"""
    block = "\n".join(i + line if line else "" for line in block.splitlines()) + "\n"
    t = t[:m.end()] + block + t[m.end():]
    mc.write_text(t, encoding="utf-8")
    print("MediaController recording-start beep v3 (ringtone stream) OK")

def patch_solar_calendar_preview() -> None:
    """Intentionally disabled: Solar Hijri must NOT be injected into DialogCell Preview."""
    print("DialogCell Solar Hijri preview injection intentionally disabled")

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

    # Keep Telegram's native preview date/time block untouched.
    # Solar Hijri applies only to message-focus accessibility in ChatMessageCell.

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted removed / status announce / preview-300 / time-last OK")



def patch_dialogcell_time_last() -> None:
    """Move Telegram's native sent/received sentence to the absolute end of Preview.

    Do not build a separate accessibility field: Telegram's own StringBuilder is
    the content description used by both the AccessibilityEvent and the View.
    Removing the native block and inserting the exact same block immediately
    before those final calls guarantees TalkBack receives it as the last item.
    Preview deliberately stays Gregorian/native; Solar Hijri is for chat-message
    date separators only.
    """
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (time-last)")
        return
    t = dc.read_text(encoding="utf-8")
    marker = "a11y-fork: preview sent-received-last v5"
    if marker in t:
        print("DialogCell sent/received LAST v5 already patched")
        return

    # Remove any field-based v4 implementation from v16, if present.
    t = re.sub(
        r'(?m)^\s*// a11y-fork: preview sent-received field(?: v[0-9]+)?\n\s*private String a11yPreviewSentReceivedDate;\n',
        '', t, count=1
    )
    t = re.sub(
        r'(?m)^\s*// a11y-fork: preview sent-received-last[^\n]*\n'
        r'\s*if \(a11yPreviewSentReceivedDate != null && a11yPreviewSentReceivedDate\.length\(\) > 0\) \{\n'
        r'\s*sb\.append\(a11yPreviewSentReceivedDate\);\n'
        r'\s*sb\.append\("\. "\);\n\s*\}\n',
        '', t, count=1
    )

    # Remove the native early sent/received block, wherever it occurs.
    native = re.compile(
        r'(?m)^\s*String date = LocaleController\.formatDateAudio\(lastDate, true\);\n'
        r'\s*if \(message\.isOut\(\)\) \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrSentDate", R\.string\.AccDescrSentDate, date\)\);\n'
        r'\s*\} else \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrReceivedDate", R\.string\.AccDescrReceivedDate, date\)\);\n'
        r'\s*\}\n\s*sb\.append\("\. "\);\n'
    )
    m = native.search(t)
    if not m:
        print("WARN: DialogCell native sent/received date block not found (time-last)")
        return
    t = t[:m.start()] + t[m.end():]

    # Insert it immediately before the final accessibility-description calls.
    tail = (
        '        // ' + marker + '\n'
        '        String a11yPreviewDate = LocaleController.formatDateAudio(lastDate, true);\n'
        '        if (message.isOut()) {\n'
        '            sb.append(LocaleController.formatString("AccDescrSentDate", R.string.AccDescrSentDate, a11yPreviewDate));\n'
        '        } else {\n'
        '            sb.append(LocaleController.formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, a11yPreviewDate));\n'
        '        }\n'
        '        sb.append(". ");\n'
    )
    final = re.search(r'(?m)^        event\.setContentDescription\(sb\);\n        setContentDescription\(sb\);', t)
    if not final:
        print("WARN: DialogCell final event/setContentDescription pair not found (time-last)")
        return
    t = t[:final.start()] + tail + t[final.start():]
    dc.write_text(t, encoding="utf-8")
    print("DialogCell sent/received LAST v5 OK")




def patch_locale_controller_solar_date_chat() -> None:
    """Patch Telegram's shared chat-date formatter for the Solar Calendar.

    The date separator can reach ChatActionCell through MessageObject.messageText,
    so changing only ChatActionCell.setCustomDate() does not reliably affect what
    TalkBack reads. Telegram 12.10.5 centralizes the separator formatting in
    LocaleController.formatDateChat(long, boolean).

    We preserve Telegram's original checkYear/one-year decision by passing the
    same flag to A11yConfig.formatSolarDateChat(). The notification/chat-list
    preview path is intentionally not modified because this patch touches only
    formatDateChat(), not DialogCell's preview description.
    """
    lc = JAVA / "org/telegram/messenger/LocaleController.java"
    if not lc.exists():
        print("WARN: LocaleController missing (solar chat-date formatter)")
        return
    t = lc.read_text(encoding="utf-8")
    marker = "a11y-fork: solar formatDateChat v1"
    if marker in t:
        return

    old = "    public static String formatDateChat(long date, boolean checkYear) {\n"
    new = (
        old
        + "        // " + marker + "\n"
        + "        try {\n"
        + "            if (A11yConfig.getSolarCalendar()) {\n"
        + "                String a11ySolar = A11yConfig.formatSolarDateChat(date, checkYear);\n"
        + "                if (a11ySolar != null && !a11ySolar.isEmpty()) {\n"
        + "                    return a11ySolar;\n"
        + "                }\n"
        + "            }\n"
        + "        } catch (Throwable ignore) {\n"
        + "        }\n"
    )
    if t.count(old) != 1:
        print("WARN: LocaleController.formatDateChat anchor not found exactly once")
        return
    lc.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("LocaleController Solar formatDateChat root fix OK")


def patch_chat_action_solar_date_accessibility() -> None:
    """Override ChatActionCell's FINAL accessibility text with Jalali after Telegram sets it."""
    ca = JAVA / "org/telegram/ui/Cells/ChatActionCell.java"
    if not ca.exists():
        print("WARN: ChatActionCell missing (solar accessibility)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: solar date accessibility v2"
    if marker in t:
        return

    # v18 inserted the override immediately after the method signature. Telegram's
    # original method then continued and overwrote it with accessibilityText, so
    # TalkBack still received the Gregorian date. In v19 we inject at the VERY END
    # of the existing method, after info.setEnabled(true), so the Jalali value wins.
    old = "        info.setEnabled(true);\n    }"
    new = """        info.setEnabled(true);
        // a11y-fork: solar date accessibility v2
        // IMPORTANT: this must be after Telegram's native info.setText()/setContentDescription()
        // so the Gregorian separator text cannot overwrite the Jalali accessibility text.
        try {
            if (org.telegram.messenger.A11yConfig.getSolarCalendar()
                    && customDate != 0
                    && !TextUtils.isEmpty(customText)) {
                String a11ySolarDate = org.telegram.messenger.A11yConfig.formatSolarDate(customDate);
                if (a11ySolarDate != null && !a11ySolarDate.isEmpty()) {
                    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                        info.setContentDescription(a11ySolarDate);
                    } else {
                        info.setText(a11ySolarDate);
                    }
                }
            }
        } catch (Throwable ignore) {
        }
    }"""
    if old not in t:
        print("WARN: ChatActionCell info.setEnabled anchor not found (solar accessibility)")
        return
    t = t.replace(old, new, 1)
    ca.write_text(t, encoding="utf-8")
    print("ChatActionCell FINAL Solar date accessibility override v2 OK")

def patch_chat_action_solar_date_header() -> None:
    """Replace Telegram's Gregorian chat date-separator heading with Jalali while preserving native year logic."""
    ca=JAVA / "org/telegram/ui/Cells/ChatActionCell.java"
    if not ca.exists():
        print("WARN: ChatActionCell missing (solar date header)")
        return
    t=ca.read_text(encoding="utf-8")
    marker="a11y-fork: solar date separator header v2"
    if marker in t: return
    old='            newText = LocaleController.formatDateChat(date);'
    new='''            // a11y-fork: solar date separator header v2
            if (org.telegram.messenger.A11yConfig.getSolarCalendar()) {
                String a11ySolarHeader = org.telegram.messenger.A11yConfig.formatSolarDate(date);
                newText = a11ySolarHeader != null && !a11ySolarHeader.isEmpty()
                        ? a11ySolarHeader
                        : LocaleController.formatDateChat(date);
            } else {
                newText = LocaleController.formatDateChat(date);
            }'''
    if old not in t:
        print("WARN: ChatActionCell date-separator anchor not found")
        return
    t=t.replace(old,new,1)
    t=t.replace('    public void setCustomDate(int date, boolean scheduled, boolean inLayout) {','    // '+marker+'\n    public void setCustomDate(int date, boolean scheduled, boolean inLayout) {',1)
    ca.write_text(t,encoding="utf-8")
    print("ChatActionCell Solar date separator header OK")


def patch_chat_message_solar_date() -> None:
    """ChatMessageCell does not own the date separator; ChatActionCell does."""
    print("ChatMessageCell Solar date skipped; ChatActionCell owns date-separator behavior")

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



def patch_links_as_menu() -> None:
    # Optional Links item at the end of the accessibility message-menu tail.
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (links menu)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: links menu v1"
    if marker in t:
        return
    if "a11y-fork: OPTION_LINKS_MENU declaration" not in t:
        idx=t.find("public class ChatActivity")
        if idx>=0:
            brace=t.find("{",idx)
            if brace>=0:
                t=t[:brace+1]+"\n    private static final int OPTION_LINKS_MENU = 206; // a11y-fork: OPTION_LINKS_MENU declaration\n"+t[brace+1:]
    bot_anchor='        // a11y-fork: bot buttons menu\n        if (message != null && message.hasInlineBotButtons()) {'
    links_item='''        // a11y-fork: links menu v1
        if (org.telegram.messenger.A11yConfig.getLinksMenuEnabled() && message != null && a11yMessageHasLinks(message)) {
            items.add(LocaleController.getString(R.string.A11yLinks));
            options.add(OPTION_LINKS_MENU);
            icons.add(R.drawable.msg_forward);
        }

'''
    if bot_anchor not in t:
        print("WARN: Bot Buttons anchor not found; Links item not inserted")
        ca.write_text(t,encoding="utf-8")
        return
    t=t.replace(bot_anchor,links_item+bot_anchor,1)
    helper_anchor='    private void fillMessageMenu(ArrayList<CharSequence> items, ArrayList<Integer> options, ArrayList<Integer> icons, MessageObject message) {'
    helper='''    // a11y-fork: links menu helper
    private boolean a11yMessageHasLinks(MessageObject message) {
        if (message == null || message.messageOwner == null) return false;
        try {
            if (message.messageOwner.entities != null) {
                for (TLRPC.MessageEntity e : message.messageOwner.entities) {
                    if (e instanceof TLRPC.TL_messageEntityUrl || e instanceof TLRPC.TL_messageEntityTextUrl || e instanceof TLRPC.TL_messageEntityEmail || e instanceof TLRPC.TL_messageEntityMention || e instanceof TLRPC.TL_messageEntityMentionName) return true;
                }
            }
            String raw = message.messageOwner.message;
            return raw != null && raw.matches("(?s).*https?://[^\\\\s]+.*");
        } catch (Throwable ignore) { return false; }
    }

    private void a11yShowMessageLinks(MessageObject message) {
        try {
            java.util.ArrayList<String> links = new java.util.ArrayList<>();
            String raw = message != null && message.messageOwner != null ? message.messageOwner.message : null;
            if (raw == null) raw = "";
            if (message != null && message.messageOwner != null && message.messageOwner.entities != null) {
                for (TLRPC.MessageEntity e : message.messageOwner.entities) {
                    String url = null;
                    if (e instanceof TLRPC.TL_messageEntityTextUrl) {
                        url = ((TLRPC.TL_messageEntityTextUrl)e).url;
                    } else if (e instanceof TLRPC.TL_messageEntityUrl || e instanceof TLRPC.TL_messageEntityEmail) {
                        int s=Math.max(0,Math.min(raw.length(),e.offset));
                        int end=Math.max(s,Math.min(raw.length(),s+e.length));
                        url=raw.substring(s,end);
                        if (e instanceof TLRPC.TL_messageEntityEmail) url="mailto:"+url;
                    } else if (e instanceof TLRPC.TL_messageEntityMention) {
                        // a11y-fork: @username mention -> t.me deep link
                        int s=Math.max(0,Math.min(raw.length(),e.offset));
                        int end=Math.max(s,Math.min(raw.length(),s+e.length));
                        String uname=raw.substring(s,end);
                        if (uname.startsWith("@")) uname=uname.substring(1);
                        if (uname.length()>0) url="https://t.me/"+uname;
                    } else if (e instanceof TLRPC.TL_messageEntityMentionName) {
                        // a11y-fork: tap-to-profile mention (no @ in raw text) -> t.me deep link by user id
                        long uid = ((TLRPC.TL_messageEntityMentionName)e).user_id;
                        if (uid != 0) url="tg://user?id="+uid;
                    }
                    if (url != null && url.length()>0 && !links.contains(url)) links.add(url);
                }
            }
            java.util.regex.Matcher m=java.util.regex.Pattern.compile("https?://[^\\\\s<>\\"]+").matcher(raw);
            while(m.find()) {
                String url=m.group();
                while(url.endsWith(".")||url.endsWith(",")||url.endsWith(")")||url.endsWith("]")) url=url.substring(0,url.length()-1);
                if(url.length()>0&&!links.contains(url)) links.add(url);
            }
            if(links.isEmpty()) {
                if(getParentActivity()!=null) getParentActivity().getWindow().getDecorView().announceForAccessibility(LocaleController.getString(R.string.A11yNoLinks));
                return;
            }
            final String[] values=links.toArray(new String[0]);
            new AlertDialog.Builder(getParentActivity()).setTitle(LocaleController.getString(R.string.A11yLinks)).setItems(values,(dialog,which)->{
                if(which>=0&&which<values.length) {
                    try { getParentActivity().startActivity(new android.content.Intent(android.content.Intent.ACTION_VIEW,android.net.Uri.parse(values[which]))); }
                    catch(Throwable e){ FileLog.e(e); }
                }
            }).setNegativeButton(LocaleController.getString(R.string.A11yCancel),null).show();
        } catch(Throwable e) { FileLog.e(e); }
    }

'''
    fmm_idx = t.find("public void fillMessageMenu(")
    if fmm_idx == -1:
        fmm_idx = t.find(helper_anchor)
    if fmm_idx >= 0:
        t = t[:fmm_idx] + helper + t[fmm_idx:]
    else:
        print("WARN: fillMessageMenu anchor not found")
    case_anchor='            case OPTION_BOT_BUTTONS_MENU: {'
    case='''            case OPTION_LINKS_MENU: { // a11y-fork: links menu handler
                a11yShowMessageLinks(selectedObject);
                selectedObject=null;
                selectedObjectToEditCaption=null;
                selectedObjectGroup=null;
                break;
            }
'''
    if case_anchor in t: t=t.replace(case_anchor,case+case_anchor,1)
    else: print("WARN: Bot Buttons handler anchor not found")
    ca.write_text(t,encoding="utf-8")
    print("ChatActivity optional Links menu OK")


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
            t = t.replace(anchor, anchor + "\n    private final static int OPTION_GO_TO_FIRST_MESSAGE = 75; // a11y-fork: OPTION_GO_TO_FIRST_MESSAGE declaration", 1)

    if "a11y-fork: go-to-first-message state" not in t:
        anchor = "    private boolean loadingForward;"
        if anchor in t:
            t = t.replace(anchor, anchor + "\n    private boolean a11yGoToFirstMessageRequested; // a11y-fork: go-to-first-message state", 1)

    if "a11y-fork: go-to-first-message helper" not in t:
        anchor = "    public void firstLoadMessages() {"
        helper = """    // a11y-fork: go-to-first-message helper
    private void accessibilityGoToFirstMessage() {
        if (dialog_id == 0 || isTopic) {
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
        if anchor in t: t=t.replace(anchor, helper+anchor,1)

    if "a11y-fork: go-to-first-message menu" not in t:
        anchor = """            if (currentChat != null && !isTopic) {
                viewAsTopics = headerItem.lazilyAddSubItem(view_as_topics, R.drawable.msg_topics, LocaleController.getString(R.string.TopicViewAsTopics));
            }"""
        insert = anchor + """
            if (dialog_id != 0 && !isTopic) {
                // a11y-fork: go-to-first-message menu
                headerItem.lazilyAddSubItem(OPTION_GO_TO_FIRST_MESSAGE, R.drawable.msg_search, LocaleController.getString(R.string.A11yGoToFirstMessage));
            }"""
        if anchor in t: t=t.replace(anchor,insert,1)

    if "a11y-fork: go-to-first-message handler" not in t:
        anchor = "                } else if (id == view_as_topics) {"
        branch = "                } else if (id == OPTION_GO_TO_FIRST_MESSAGE) { // a11y-fork: go-to-first-message handler\n                    accessibilityGoToFirstMessage();\n                } else if (id == view_as_topics) {"
        # branch currently contains literal backslash-n; convert after assignment
        branch=branch.replace('\\n','\n')
        if anchor in t: t=t.replace(anchor,branch,1)

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
        if anchor in t: t=t.replace(anchor,replacement,1)

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity go-to-first-message OK")


def patch_file_description_spacing() -> None:
    """TalkBack: announce the real document filename as a single clean "file <name>" (with a real
    space, never concatenated), not Telegram's internal numeric storage filename and not a
    separate/duplicated extension-type announcement (which read out of order and could confuse
    TalkBack's long-press gesture)."""
    cmc=JAVA/"org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (file description spacing)"); return
    t=cmc.read_text(encoding="utf-8")
    marker="a11y-fork: real document filename"
    # Clean up: if an older revision of this patch (with the redundant extension-type
    # announcement) already applied, replace it with the simplified single-announcement version.
    old_verbose = (
        "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
        "                        // a11y-fork: real document filename\n"
        "                        String a11yDocumentName = FileLoader.getDocumentFileName(documentAttach);\n"
        "                        if (!TextUtils.isEmpty(a11yDocumentName)) {\n"
        "                            sb.append(a11yDocumentName);\n"
        "                            sb.append(\". \");\n"
        "                            String a11yExtension = a11yDocumentName;\n"
        "                            int a11yDot = a11yExtension.lastIndexOf('.');\n"
        "                            if (a11yDot >= 0 && a11yDot + 1 < a11yExtension.length()) {\n"
        "                                a11yExtension = a11yExtension.substring(a11yDot + 1).toUpperCase(Locale.ROOT);\n"
        "                                sb.append(formatString(R.string.AccDescrDocumentType, a11yExtension));\n"
        "                                sb.append(\" \");\n"
        "                            }\n"
        "                        }\n"
        "                    }")
    if old_verbose in t:
        t = t.replace(old_verbose, "", 1)  # drop; the block below (re)inserts the clean version

    if marker not in t:
        old=(
            "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
            "                        String fileName = FileLoader.getAttachFileName(documentAttach);\n"
            "                        if (fileName.indexOf('.') != -1) {\n"
            "                            sb.append(formatString(R.string.AccDescrDocumentType, fileName.substring(fileName.lastIndexOf('.') + 1).toUpperCase(Locale.ROOT)));\n"
            "                        }\n"
            "                    }")
        new=(
            "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
            "                        // a11y-fork: real document filename -- single \"File: <name>\" announcement,\n"
            "                        // built as one literal Java string so \"File\" can never end up glued to\n"
            "                        // the filename (that broke TalkBack reading and its long-press gesture).\n"
            "                        // Telegram sets messageText to the filename itself when a document has\n"
            "                        // no separate caption, and the untouched native code just below (which\n"
            "                        // appends messageText) would then read that same filename a second time --\n"
            "                        // so when that's about to happen, say only \"File:\" here and let that\n"
            "                        // native code supply the name once (still followed by its file size).\n"
            "                        String a11yDocumentName = FileLoader.getDocumentFileName(documentAttach);\n"
            "                        if (!TextUtils.isEmpty(a11yDocumentName)) {\n"
            "                            boolean a11yNameWillRepeat = !TextUtils.isEmpty(currentMessageObject.messageText)\n"
            "                                    && currentMessageObject.messageText.toString().trim().equals(a11yDocumentName.trim());\n"
            "                            sb.append(\"File: \");\n"
            "                            if (!a11yNameWillRepeat) {\n"
            "                                sb.append(a11yDocumentName);\n"
            "                                sb.append(\". \");\n"
            "                            }\n"
            "                        }\n"
            "                    }")
        if old in t:
            t=t.replace(old,new,1); cmc.write_text(t,encoding="utf-8"); print("ChatMessageCell single clean \"file <name>\" announcement OK")
        else: print("WARN: ChatMessageCell document accessibility anchor not found")
    else:
        cmc.write_text(t,encoding="utf-8")
        print("ChatMessageCell real document filename already patched")
    # AccDescrDocumentType is no longer referenced by the patched block above
    # (the clean "file <name>" text is built directly in Java), so it's left untouched.

def patch_chat_message_cell_granularity_navigation() -> None:
    """Implement real character/word TalkBack text-navigation for the message
    accessibility node. The base View class's performAccessibilityAction has no
    text-cursor concept for a non-TextView custom View, so ACTION_NEXT/PREVIOUS_
    AT_MOVEMENT_GRANULARITY were never handled -- TalkBack would fall through to
    unrelated "move to next accessibility element" behavior (observed as jumping
    to the toolbar's Search button) instead of stepping character-by-character
    or word-by-word through the message text. This adds the missing declaration
    (setMovementGranularities/addAction) plus the actual traversal logic.
    """
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (granularity navigation)")
        return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-fork: granularity-navigation-v1"
    if marker in t:
        print("ChatMessageCell granularity navigation already patched")
        return

    field_anchor = "    CharSequence accessibilityText;"
    if field_anchor not in t:
        print("WARN: accessibilityText field anchor not found (granularity navigation)")
        return
    t = t.replace(field_anchor, field_anchor + "\n    private int a11yGranularityCursor = -1; // " + marker, 1)

    reset_anchor = "        accessibilityText = null;"
    if reset_anchor not in t:
        print("WARN: accessibilityText reset anchor not found (granularity navigation)")
        return
    t = t.replace(reset_anchor, reset_anchor + "\n        a11yGranularityCursor = -1;", 1)

    decl_anchor = (
        "                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {\n"
        "                    info.setContentDescription(accessibilityText.toString());\n"
        "                } else {\n"
        "                    info.setText(accessibilityText);\n"
        "                }\n"
    )
    if decl_anchor not in t:
        print("WARN: host info.setText anchor not found (granularity navigation)")
        return
    decl_new = (
        "                // " + marker + "\n"
        "                info.setMovementGranularities(AccessibilityNodeInfo.MOVEMENT_GRANULARITY_CHARACTER\n"
        "                        | AccessibilityNodeInfo.MOVEMENT_GRANULARITY_WORD);\n"
        "                info.addAction(AccessibilityNodeInfo.ACTION_NEXT_AT_MOVEMENT_GRANULARITY);\n"
        "                info.addAction(AccessibilityNodeInfo.ACTION_PREVIOUS_AT_MOVEMENT_GRANULARITY);\n"
        + decl_anchor
    )
    t = t.replace(decl_anchor, decl_new, 1)

    trav_anchor = "        return super.performAccessibilityAction(action, arguments);\n    }"
    if trav_anchor not in t:
        print("WARN: performAccessibilityAction fallthrough anchor not found (granularity navigation)")
        return
    trav_new = '        // a11y-fork: granularity-navigation-v1\n        if ((action == AccessibilityNodeInfo.ACTION_NEXT_AT_MOVEMENT_GRANULARITY\n                || action == AccessibilityNodeInfo.ACTION_PREVIOUS_AT_MOVEMENT_GRANULARITY)\n                && arguments != null && accessibilityText != null) {\n            try {\n                int a11yGranularity = arguments.getInt(AccessibilityNodeInfo.ACTION_ARGUMENT_MOVEMENT_GRANULARITY_INT);\n                boolean a11yForward = action == AccessibilityNodeInfo.ACTION_NEXT_AT_MOVEMENT_GRANULARITY;\n                String a11yFullText = accessibilityText.toString();\n                int a11yLen = a11yFullText.length();\n                int a11yCur = a11yGranularityCursor;\n                if (a11yCur < 0 || a11yCur > a11yLen) {\n                    a11yCur = a11yForward ? 0 : a11yLen;\n                }\n                int[] a11ySeg = null;\n                if (a11yGranularity == AccessibilityNodeInfo.MOVEMENT_GRANULARITY_CHARACTER) {\n                    if (a11yForward) {\n                        if (a11yCur < a11yLen) {\n                            int a11yNext = a11yCur + Character.charCount(a11yFullText.codePointAt(a11yCur));\n                            a11ySeg = new int[]{a11yCur, Math.min(a11yLen, a11yNext)};\n                        }\n                    } else {\n                        if (a11yCur > 0) {\n                            int a11yPrev = a11yCur - Character.charCount(a11yFullText.codePointBefore(a11yCur));\n                            a11ySeg = new int[]{Math.max(0, a11yPrev), a11yCur};\n                        }\n                    }\n                } else if (a11yGranularity == AccessibilityNodeInfo.MOVEMENT_GRANULARITY_WORD) {\n                    android.icu.text.BreakIterator a11yWordIt = android.icu.text.BreakIterator.getWordInstance();\n                    a11yWordIt.setText(a11yFullText);\n                    if (a11yForward) {\n                        int a11yStart = a11yWordIt.following(Math.max(0, Math.min(a11yLen - 1, a11yCur - 1)));\n                        while (a11yStart != android.icu.text.BreakIterator.DONE && a11yStart < a11yLen) {\n                            int a11yEnd = a11yWordIt.next();\n                            if (a11yEnd == android.icu.text.BreakIterator.DONE) break;\n                            if (Character.isLetterOrDigit(a11yFullText.codePointAt(a11yStart))) {\n                                a11ySeg = new int[]{a11yStart, a11yEnd};\n                                break;\n                            }\n                            a11yStart = a11yEnd;\n                        }\n                    } else {\n                        int a11yEnd = a11yWordIt.preceding(Math.max(0, Math.min(a11yLen, a11yCur)));\n                        while (a11yEnd != android.icu.text.BreakIterator.DONE && a11yEnd > 0) {\n                            int a11yStart = a11yWordIt.previous();\n                            if (a11yStart == android.icu.text.BreakIterator.DONE) break;\n                            if (a11yStart < a11yEnd && Character.isLetterOrDigit(a11yFullText.codePointAt(a11yStart))) {\n                                a11ySeg = new int[]{a11yStart, a11yEnd};\n                                break;\n                            }\n                            a11yEnd = a11yStart;\n                        }\n                    }\n                }\n                if (a11ySeg != null) {\n                    a11yGranularityCursor = a11yForward ? a11ySeg[1] : a11ySeg[0];\n                    AccessibilityEvent a11yTravEvent = AccessibilityEvent.obtain(AccessibilityEvent.TYPE_VIEW_TEXT_TRAVERSED_AT_MOVEMENT_GRANULARITY);\n                    a11yTravEvent.setPackageName(getContext().getPackageName());\n                    a11yTravEvent.setSource(ChatMessageCell.this, AccessibilityNodeProvider.HOST_VIEW_ID);\n                    a11yTravEvent.setFromIndex(a11ySeg[0]);\n                    a11yTravEvent.setToIndex(a11ySeg[1]);\n                    a11yTravEvent.setAction(action);\n                    a11yTravEvent.setMovementGranularity(a11yGranularity);\n                    a11yTravEvent.getText().add(a11yFullText);\n                    if (getParent() != null) {\n                        getParent().requestSendAccessibilityEvent(ChatMessageCell.this, a11yTravEvent);\n                    }\n                    return true;\n                }\n                return false;\n            } catch (Throwable a11yGranErr) {\n                FileLog.e(a11yGranErr);\n            }\n        }\n        return super.performAccessibilityAction(action, arguments);\n    }'
    t = t.replace(trav_anchor, trav_new, 1)

    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell granularity navigation v1 OK")


def patch_chat_message_solar_date() -> None:
    """Keep ChatMessageCell unchanged; Solar date is handled by the shared chat-date formatter."""
    print("ChatMessageCell Solar date skipped; DialogCell owns native date behavior")

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
        "                return performAccessibilityAction(action, arguments);\n"
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

def patch_reorder_a11y_menu_items() -> None:
    """Move Select / Reactions / Bot Buttons / Links out of their original
    early insertion point (right before the sponsored-ad block, i.e. near
    the TOP of the menu) and place them, in this exact order, at the very
    END of fillMessageMenu -- after every native item (Copy, Delete, Reply,
    Report, Save to Downloads/Gallery, etc.), right before the method's
    closing brace. Must run after patch_longpress_message_menu,
    patch_reactions_as_menu, patch_bot_buttons_menu and patch_links_as_menu,
    since it relocates the exact blocks those functions insert.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (menu reorder)")
        return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-fork: menu items reordered to end-v1"
    if marker in t:
        print("ChatActivity a11y menu items already reordered")
        return

    blocks = {
        "links": (
            "        // a11y-fork: links menu v1\n"
            "        if (org.telegram.messenger.A11yConfig.getLinksMenuEnabled() && message != null && a11yMessageHasLinks(message)) {\n"
            "            items.add(LocaleController.getString(R.string.A11yLinks));\n"
            "            options.add(OPTION_LINKS_MENU);\n"
            "            icons.add(R.drawable.msg_forward);\n"
            "        }\n\n"
        ),
        "bot_buttons": (
            "        // a11y-fork: bot buttons menu\n"
            "        if (message != null && message.hasInlineBotButtons()) {\n"
            "            items.add(\"Bot Buttons\");\n"
            "            options.add(OPTION_BOT_BUTTONS_MENU);\n"
            "            icons.add(R.drawable.msg_viewreplies);\n"
            "        }\n\n"
        ),
        "reactions": (
            "        // a11y-fork: reactions menu item\n"
            "        accessibilityReactionsToggleIndex = -1;\n"
            "        if (isReactionsAvailableFinal) {\n"
            "            items.add(LocaleController.getString(R.string.Reactions));\n"
            "            icons.add(R.drawable.msg_reactions2);\n"
            f"            options.add({OPTION_REACTIONS_MENU});\n"
            "            accessibilityReactionsToggleIndex = items.size() - 1;\n"
            "        }\n\n"
        ),
        "select": (
            "        // a11y-fork: OPTION_SELECT_MESSAGE menu\n"
            "        if (!actionBar.isActionModeShowed() && message != null && message.contentType == 0 && !message.isSponsored()) {\n"
            "            items.add(LocaleController.getString(R.string.Select));\n"
            f"            options.add({OPTION_SELECT_MESSAGE});\n"
            "            icons.add(R.drawable.msg_forward);\n"
            "        }\n\n"
        ),
    }

    missing = [name for name, block in blocks.items() if block not in t]
    if missing:
        print(f"WARN: a11y menu-item block(s) not found for reorder: {', '.join(missing)} (left in original position)")
        return

    for block in blocks.values():
        t = t.replace(block, "", 1)

    fmm_idx = t.find("public void fillMessageMenu(")
    if fmm_idx < 0:
        print("WARN: fillMessageMenu not found (menu reorder)")
        return
    open_paren_close = t.find(") {", fmm_idx)
    brace_idx = t.find("{", open_paren_close if open_paren_close >= 0 else fmm_idx)
    if brace_idx < 0:
        print("WARN: fillMessageMenu opening brace not found (menu reorder)")
        return
    depth = 0
    i = brace_idx
    end_idx = -1
    while i < len(t):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break
        i += 1
    if end_idx < 0:
        print("WARN: fillMessageMenu closing brace not found (menu reorder)")
        return

    ordered = (
        f"        // {marker} -- order: Links, Bot Buttons, Reactions, Select\n"
        + blocks["links"] + blocks["bot_buttons"] + blocks["reactions"] + blocks["select"]
    )
    t = t[:end_idx] + ordered + t[end_idx:]
    ca.write_text(t, encoding="utf-8")
    print("ChatActivity a11y menu items reordered to end (Links, Bot Buttons, Reactions, Select) OK")




def patch_small_file_localization() -> None:
    """Add localized labels required by the 3-state small-file setting."""
    en = {
        "A11ySmallFilesModeLabel": "Small files auto-download: %s",
        "A11ySmallFilesAuto": "Auto-download small files",
        "A11ySmallFilesVoiceOnly": "Do not download small files except voice messages",
        "A11ySmallFilesOff": "Do not download small files",
        "A11ySmallFilesPickerTitle": "Small files auto-download",
    }
    fa = {
        "A11ySmallFilesModeLabel": "دانلود خودکار فایل‌های کم‌حجم: %s",
        "A11ySmallFilesAuto": "دانلود خودکار فایل‌های کم‌حجم",
        "A11ySmallFilesVoiceOnly": "دانلود نکردن فایل‌های کم‌حجم به‌جز پیام‌های صوتی",
        "A11ySmallFilesOff": "دانلود نکردن فایل‌های کم‌حجم",
        "A11ySmallFilesPickerTitle": "دانلود خودکار فایل‌های کم‌حجم",
    }
    for rel, values in (("values/strings.xml", en), ("values-fa/strings.xml", fa), ("values-fa-rIR/strings.xml", fa)):
        path = RES / rel
        if not path.exists():
            continue
        for name, value in values.items():
            _set_string(path, name, value)
    print("Small-file 3-state localization OK")

def patch_small_file_radio_settings() -> None:
    """Present the three small-file modes as one mutually-exclusive radio-button setting."""
    cfg=JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        print("WARN: A11yConfig.java missing (small-file radio settings)")
        return
    t=cfg.read_text(encoding="utf-8")
    marker="a11y-fork: small-file radio settings v1"
    if marker in t: return
    t=t.replace('MessagesController.getGlobalMainSettings().getInt("a11y_small_files_mode", SMALL_FILES_AUTO)','MessagesController.getGlobalMainSettings().getInt("a11y_small_files_mode", SMALL_FILES_VOICE_ONLY)',1)
    # Remove all legacy small-file entries from the Accessible Settings list.
    # patch_small_file_three_state() may have already converted the old
    # A11yBlockSmallFilesLabel entry into getSmallFilesAutoDownloadModeAnnouncement();
    # that became the extra option immediately after the Radio Button in v18.
    t=t.replace('                    LocaleController.formatString(R.string.A11yNoAutoDownloadLabel, onOff(getNoAutoDownload())),\n','')
    t=t.replace('                    LocaleController.formatString(R.string.A11yVoiceOnlyAutoDownloadLabel, onOff(getVoiceOnlyAutoDownload())),\n','')
    t=t.replace('                    LocaleController.formatString(R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())),\n','')
    t=t.replace('                    getSmallFilesAutoDownloadModeAnnouncement(),\n','')
    if 'getSmallFilesAutoDownloadModeAnnouncement()' not in t:
        anchor='                    LocaleController.formatString(R.string.A11yLinksLabel, onOff(getLinksMenuEnabled()))'
        if anchor in t:
            t=t.replace(anchor,anchor+',\n                    getSmallFilesAutoDownloadModeAnnouncement()',1)
    old='''                        } else if (which == 9) {
                            setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));
                        } else if (which == 10) {
                            setNoAutoDownload(!getNoAutoDownload());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yNoAutoDownloadLabel, onOff(getNoAutoDownload())));
                        } else if (which == 11) {
                            setVoiceOnlyAutoDownload(!getVoiceOnlyAutoDownload());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yVoiceOnlyAutoDownloadLabel, onOff(getVoiceOnlyAutoDownload())));
                        }'''
    if old in t:
        t=t.replace(old,'''                        } else if (which == 9) {
                            showSmallFilesModePicker(activity);
                        }''',1)
    cycle_handler = """                        } else if (which == 9) {
                            int a11ySmallFilesMode = cycleSmallFilesAutoDownloadMode();
                            announce(activity, getSmallFilesAutoDownloadModeAnnouncement());
                        }"""
    if cycle_handler in t:
        t=t.replace(cycle_handler, """                        } else if (which == 9) {
                            showSmallFilesModePicker(activity);
                        }""", 1)
    if 'private static void showSmallFilesModePicker(Activity activity)' not in t:
        anchor='    private static void announce(Activity activity, String text) {'
        method='''    // a11y-fork: small-file radio settings v1
    private static void showSmallFilesModePicker(Activity activity) {
        final String[] labels = new String[]{
                LocaleController.getString(R.string.A11ySmallFilesAuto),
                LocaleController.getString(R.string.A11ySmallFilesVoiceOnly),
                LocaleController.getString(R.string.A11ySmallFilesOff)
        };
        int checked = getSmallFilesAutoDownloadMode();
        if (checked < SMALL_FILES_AUTO || checked > SMALL_FILES_OFF) checked = SMALL_FILES_VOICE_ONLY;
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11ySmallFilesPickerTitle))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setSmallFilesAutoDownloadMode(which);
                    d.dismiss();
                    announce(activity, getSmallFilesAutoDownloadModeAnnouncement());
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }

'''
        if anchor in t: t=t.replace(anchor,method+anchor,1)
    t=t.replace('    // a11y-fork: small-file radio settings v1\n', '    // '+marker+'\n',1) if '    // a11y-fork: small-file radio settings v1\n' in t else t
    cfg.write_text(t,encoding="utf-8")
    print("Small-file setting converted to single-choice radio buttons OK")


def patch_remove_obsolete_small_file_switch() -> None:
    """Remove the legacy independent small-file switch now that radio modes are authoritative."""
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        print("WARN: A11yConfig.java missing (remove obsolete small-file switch)")
        return
    t = cfg.read_text(encoding="utf-8")
    marker = "a11y-fork: obsolete small-file switch removed v1"
    if marker in t:
        return
    # Remove any list entry for the old boolean switch, regardless of its position.
    t = re.sub(
        r'(?m)^\s*LocaleController\.formatString\(R\.string\.A11yBlockSmallFilesLabel, onOff\(getBlockSmallAutoDownloads\(\)\)\),\n',
        '', t
    )
    # Remove the old click handler if it survived an earlier patch.
    t = re.sub(
        r'(?m)^\s*\}\s*else if \(which == 9\) \{\n\s*setBlockSmallAutoDownloads\(!getBlockSmallAutoDownloads\(\)\);\n\s*announce\(activity, LocaleController\.formatString\(\n\s*R\.string\.A11yBlockSmallFilesLabel, onOff\(getBlockSmallAutoDownloads\(\)\)\)\);\n\s*\}\n',
        '', t
    )
    # If a previous radio patch already owns index 9, leave its handler intact.
    t = re.sub(
        r'(?m)^\s*LocaleController\.formatString\(R\.string\.A11yBlockSmallFilesLabel, onOff\(getBlockSmallAutoDownloads\(\)\)\),?\s*$',
        '', t
    )
    cfg.write_text(t, encoding="utf-8")
    print("Obsolete small-file switch removed; radio modes are authoritative OK")


def patch_small_file_radio_ui_cleanup_v3() -> None:
    """Make the 3-state Radio Button the only small-file settings row."""
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        print("WARN: A11yConfig.java missing (small-file radio cleanup v3)")
        return
    t = cfg.read_text(encoding="utf-8")
    marker = "a11y-fork: small-file radio cleanup v3"
    # Remove legacy independent rows and the legacy announcement row from the
    # settings array. Keep the resource strings themselves for compatibility.
    patterns = [
        r'(?m)^\s*LocaleController\.formatString\(R\.string\.A11yBlockSmallFilesLabel, onOff\(getBlockSmallAutoDownloads\(\)\)\),?\s*\n',
        r'(?m)^\s*LocaleController\.formatString\(R\.string\.A11yNoAutoDownloadLabel, onOff\(getNoAutoDownload\(\)\)\),?\s*\n',
        r'(?m)^\s*LocaleController\.formatString\(R\.string\.A11yVoiceOnlyAutoDownloadLabel, onOff\(getVoiceOnlyAutoDownload\(\)\)\),?\s*\n',
        r'(?m)^\s*getSmallFilesAutoDownloadModeAnnouncement\(\),?\s*\n',
    ]
    for pat in patterns:
        t = re.sub(pat, '', t)

    # Remove legacy small-file click handlers if they still exist. Do not touch
    # the authoritative radio-picker handler.
    t = re.sub(
        r'(?ms)^\s*\}\s*else if \(which == 9\) \{\s*'
        r'setBlockSmallAutoDownloads\(!getBlockSmallAutoDownloads\(\)\);\s*'
        r'announce\(activity, LocaleController\.formatString\(\s*'
        r'R\.string\.A11yBlockSmallFilesLabel, onOff\(getBlockSmallAutoDownloads\(\)\)\)\);\s*'
        r'\}\s*',
        '\n',
        t,
    )
    if marker not in t:
        t += "\n    // " + marker + "\n"
    cfg.write_text(t, encoding="utf-8")
    print("Small-file Radio Button cleanup v3 OK")



def patch_small_file_radio_restore_v24() -> None:
    """Restore the single 3-state small-file Radio Button after cleanup."""
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        print("WARN: A11yConfig.java missing (small-file radio restore v24)")
        return
    t = cfg.read_text(encoding="utf-8")
    marker = "a11y-fork: restore small-file radio button v24"
    if marker in t:
        return
    row = '                    getSmallFilesAutoDownloadModeAnnouncement(),'
    if 'getSmallFilesAutoDownloadModeAnnouncement(),' not in t:
        links = '                    LocaleController.formatString(R.string.A11yLinksLabel, onOff(getLinksMenuEnabled()))'
        if links in t:
            t = t.replace(links, links + ',\n' + row, 1)
        else:
            solar = '                    LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar()))'
            if solar in t:
                t = t.replace(solar, solar + ',\n' + row, 1)
            else:
                print("WARN: settings-list anchor for small-file Radio Button not found")
    if 'showSmallFilesModePicker(activity);' not in t:
        links_handler = """                        } else if (which == 8) {
                            setLinksMenuEnabled(!getLinksMenuEnabled());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yLinksLabel, onOff(getLinksMenuEnabled())));
                        }"""
        if links_handler in t:
            replacement = links_handler + " else if (which == 9) {\n                            showSmallFilesModePicker(activity);\n                        }"
            t = t.replace(links_handler, replacement, 1)
        else:
            print("WARN: Links handler anchor for small-file Radio Button not found")
    if 'private static void showSmallFilesModePicker(Activity activity)' not in t:
        anchor2='    private static void announce(Activity activity, String text) {'
        method="""    // a11y-fork: restore small-file radio button v24
    private static void showSmallFilesModePicker(Activity activity) {
        final String[] labels = new String[]{
                LocaleController.getString(R.string.A11ySmallFilesAuto),
                LocaleController.getString(R.string.A11ySmallFilesVoiceOnly),
                LocaleController.getString(R.string.A11ySmallFilesOff)
        };
        int checked = getSmallFilesAutoDownloadMode();
        if (checked < SMALL_FILES_AUTO || checked > SMALL_FILES_OFF) {
            checked = SMALL_FILES_VOICE_ONLY;
        }
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11ySmallFilesPickerTitle))
                .setSingleChoiceItems(labels, checked, (dialog, which) -> {
                    setSmallFilesAutoDownloadMode(which);
                    dialog.dismiss();
                    announce(activity, getSmallFilesAutoDownloadModeAnnouncement());
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }

"""
        if anchor2 in t:
            t=t.replace(anchor2,method+anchor2,1)
        else:
            print("WARN: announce() anchor missing for small-file picker")
    t += '\n    // ' + marker + '\n'
    cfg.write_text(t,encoding="utf-8")
    print("Small-file 3-state Radio Button restored v24 OK")


def patch_small_file_three_state() -> None:
    """Upgrade the v10 small-file boolean to a localized 3-state mode without removing
    the old getters/setters. Modes: 0 allow small files, 1 block small files except voice,
    2 block all small files. Existing larger-file auto-download policy remains unchanged.
    """
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    dc = JAVA / "org/telegram/messenger/DownloadController.java"
    if not cfg.exists() or not dc.exists():
        print("WARN: A11yConfig/DownloadController missing (small-file 3-state)")
        return
    c = cfg.read_text(encoding="utf-8")
    marker = "a11y-fork: small-file three-state mode v1"
    if marker not in c:
        anchor = "    public static boolean getBlockSmallAutoDownloads() {"
        if anchor in c:
            methods = r"""    // a11y-fork: small-file three-state mode v1
    // 0 = auto-download small files, 1 = do not download small files except voice,
    // 2 = do not download small files at all.
    public static final int SMALL_FILES_AUTO = 0;
    public static final int SMALL_FILES_VOICE_ONLY = 1;
    public static final int SMALL_FILES_OFF = 2;

    public static int getSmallFilesAutoDownloadMode() {
        try {
            int mode = MessagesController.getGlobalMainSettings().getInt("a11y_small_files_mode", SMALL_FILES_AUTO);
            return mode < SMALL_FILES_AUTO || mode > SMALL_FILES_OFF ? SMALL_FILES_AUTO : mode;
        } catch (Throwable ignore) {
            return SMALL_FILES_AUTO;
        }
    }

    public static void setSmallFilesAutoDownloadMode(int mode) {
        if (mode < SMALL_FILES_AUTO || mode > SMALL_FILES_OFF) mode = SMALL_FILES_AUTO;
        try {
            MessagesController.getGlobalMainSettings().edit().putInt("a11y_small_files_mode", mode).apply();
            try { org.telegram.messenger.DownloadController.getInstance(UserConfig.selectedAccount).checkAutodownloadSettings(); } catch (Throwable ignore) {}
        } catch (Throwable ignore) {
        }
    }

    public static int cycleSmallFilesAutoDownloadMode() {
        int mode = (getSmallFilesAutoDownloadMode() + 1) % 3;
        setSmallFilesAutoDownloadMode(mode);
        return mode;
    }

    public static String getSmallFilesAutoDownloadModeLabel() {
        switch (getSmallFilesAutoDownloadMode()) {
            case SMALL_FILES_VOICE_ONLY:
                return LocaleController.getString(R.string.A11ySmallFilesVoiceOnly);
            case SMALL_FILES_OFF:
                return LocaleController.getString(R.string.A11ySmallFilesOff);
            default:
                return LocaleController.getString(R.string.A11ySmallFilesAuto);
        }
    }

    public static String getSmallFilesAutoDownloadModeAnnouncement() {
        return LocaleController.formatString(R.string.A11ySmallFilesModeLabel,
                getSmallFilesAutoDownloadModeLabel());
    }

"""
            c = c.replace(anchor, methods + anchor, 1)
    c = c.replace('LocaleController.formatString(R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads()))',
                  'getSmallFilesAutoDownloadModeAnnouncement()')
    old_handler = """setBlockSmallAutoDownloads(!getBlockSmallAutoDownloads());
                            announce(activity, LocaleController.formatString(
                                    R.string.A11yBlockSmallFilesLabel, onOff(getBlockSmallAutoDownloads())));"""
    new_handler = """int a11ySmallFilesMode = cycleSmallFilesAutoDownloadMode();
                            announce(activity, getSmallFilesAutoDownloadModeAnnouncement());"""
    c = c.replace(old_handler, new_handler)
    cfg.write_text(c, encoding="utf-8")

    d = dc.read_text(encoding="utf-8")
    if marker not in d:
        old = """if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return false;
        }"""
        new = """if (org.telegram.messenger.A11yConfig.getSmallFilesAutoDownloadMode()
                == org.telegram.messenger.A11yConfig.SMALL_FILES_VOICE_ONLY
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return false;
        }
        if (org.telegram.messenger.A11yConfig.getSmallFilesAutoDownloadMode()
                == org.telegram.messenger.A11yConfig.SMALL_FILES_OFF
                && size > 0 && size <= 512 * 1024) {
            return false;
        }"""
        d = d.replace(old, new)
        old0 = """if (org.telegram.messenger.A11yConfig.getBlockSmallAutoDownloads()
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return 0;
        }"""
        new0 = """if (org.telegram.messenger.A11yConfig.getSmallFilesAutoDownloadMode()
                == org.telegram.messenger.A11yConfig.SMALL_FILES_VOICE_ONLY
                && type != AUTODOWNLOAD_TYPE_AUDIO && size > 0 && size <= 512 * 1024) {
            return 0;
        }
        if (org.telegram.messenger.A11yConfig.getSmallFilesAutoDownloadMode()
                == org.telegram.messenger.A11yConfig.SMALL_FILES_OFF
                && size > 0 && size <= 512 * 1024) {
            return 0;
        }"""
        d = d.replace(old0, new0)
        d = '// ' + marker + '\n' + d
    dc.write_text(d, encoding="utf-8")
    print("Small-file 3-state mode OK")


def patch_exact_progress_steps() -> None:
    """Force the accessible progress picker/logic to the requested 1, 5, 10, 20 percent steps."""
    cfg = JAVA / "org/telegram/messenger/A11yConfig.java"
    if not cfg.exists():
        return
    t = cfg.read_text(encoding="utf-8")
    t2 = re.sub(r'int\[\]\s+steps\s*=\s*new\s+int\[\]\s*\{[^}]*\};',
                'int[] steps = new int[]{1, 5, 10, 20}; // a11y-fork: exact progress steps', t, count=1)
    t2 = re.sub(r'int\[\]\s+steps\s*=\s*\{[^}]*\};',
                'int[] steps = {1, 5, 10, 20}; // a11y-fork: exact progress steps', t2, count=1)
    if 'a11y-fork: exact progress steps' not in t2:
        t2 = t2.replace('new int[]{5, 10, 20, 50}', 'new int[]{1, 5, 10, 20} // a11y-fork: exact progress steps')
        t2 = t2.replace('new int[] {5, 10, 20, 50}', 'new int[] {1, 5, 10, 20} // a11y-fork: exact progress steps')
    cfg.write_text(t2, encoding="utf-8")
    print("Progress steps 1/5/10/20 OK")
def patch_friend_chat_jump_focus() -> None:
    """PR 2003: move TalkBack focus to the message Telegram just jumped to."""
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists(): return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-friend: focus highlighted message"
    if marker in t: return
    anchor = "    private int getHeightForMessage(MessageObject object, boolean withGroupCaption) {"
    idx = t.find(anchor)
    if idx < 0:
        print("WARN: ChatActivity highlight-focus anchor missing")
        return
    block = """    // a11y-friend: focus highlighted message
    private int accessibilityFocusedHighlightId = Integer.MAX_VALUE;
    private Runnable focusHighlightedMessageRunnable;

    private void focusHighlightedMessageForAccessibility() {
        if (highlightMessageId == Integer.MAX_VALUE || !AndroidUtilities.isAccessibilityScreenReaderEnabled()
                || accessibilityFocusedHighlightId == highlightMessageId || chatListView == null) return;
        accessibilityFocusedHighlightId = highlightMessageId;
        final int id = highlightMessageId;
        if (focusHighlightedMessageRunnable != null) AndroidUtilities.cancelRunOnUIThread(focusHighlightedMessageRunnable);
        focusHighlightedMessageRunnable = () -> {
            focusHighlightedMessageRunnable = null;
            if (highlightMessageId != id || chatListView == null) return;
            for (int i = 0; i < chatListView.getChildCount(); i++) {
                View child = chatListView.getChildAt(i);
                if (child instanceof ChatMessageCell) {
                    MessageObject mo = ((ChatMessageCell) child).getMessageObject();
                    if (mo != null && mo.getId() == id && child.isShown()) {
                        child.performAccessibilityAction(AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS, null);
                        return;
                    }
                }
            }
        };
        AndroidUtilities.runOnUIThread(focusHighlightedMessageRunnable, searching ? 900 : 250);
    }

"""
    t = t[:idx] + block + t[idx:]
    t = t.replace("            highlightMessageId = Integer.MAX_VALUE;", "            highlightMessageId = Integer.MAX_VALUE;\n            accessibilityFocusedHighlightId = Integer.MAX_VALUE;", 1)
    anchor2 = "                if (highlightMessageId != Integer.MAX_VALUE) {\n                    startMessageUnselect();"
    if anchor2 in t:
        t = t.replace(anchor2, "                if (highlightMessageId != Integer.MAX_VALUE) {\n                    startMessageUnselect();\n                    if (cell.isHighlighted()) focusHighlightedMessageForAccessibility();", 1)
    ca.write_text(t, encoding="utf-8")
    print("Friend PR 2003 message-jump accessibility focus OK")


def patch_friend_search_result_announcement() -> None:
    """PR 2004: expose and announce the in-chat search result count."""
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists(): return
    t = ca.read_text(encoding="utf-8")
    marker = "a11y-friend: search result count"
    if marker in t: return
    old = """    private void updateSearchCountText() {
        if (searchCountText != null) {
            boolean animated = !LocaleController.isRTL;"""
    if old not in t:
        print("WARN: search count anchor missing")
        return
    t = t.replace(old, """    // a11y-friend: search result count
    private int accessibilityAnnouncedSearchIndex = -1;

    private void updateSearchCountText() {
        if (searchCountText != null) {
            boolean animated = !LocaleController.isRTL;""", 1)
    needle = """            } else {
                searchCountText.setText(LocaleController.formatString(R.string.Of, searchLastIndex + 1, searchLastCount), animated);
            }
"""
    repl = needle + """            CharSequence a11yCount = searchCountText.getText();
            searchCountText.setContentDescription(a11yCount);
            searchCountText.setImportantForAccessibility(TextUtils.isEmpty(a11yCount) ? View.IMPORTANT_FOR_ACCESSIBILITY_NO : View.IMPORTANT_FOR_ACCESSIBILITY_YES);
            searchCountText.setFocusable(!TextUtils.isEmpty(a11yCount));
            if (searchLastCount > 0 && searchLastIndex != accessibilityAnnouncedSearchIndex && AndroidUtilities.isAccessibilityScreenReaderEnabled()) {
                if (accessibilityAnnouncedSearchIndex != -1) searchCountText.announceForAccessibility(a11yCount);
                accessibilityAnnouncedSearchIndex = searchLastIndex;
            } else if (searchLastCount <= 0) accessibilityAnnouncedSearchIndex = -1;
"""
    if needle not in t:
        print("WARN: search count body anchor missing")
        return
    t = t.replace(needle, repl, 1)
    ca.write_text(t, encoding="utf-8")
    print("Friend PR 2004 search result announcement OK")


def patch_friend_anonymous_sender_name() -> None:
    """PR 2037: announce anonymous/channel senders."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists(): return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-friend: anonymous sender name"
    if marker in t: return
    anchor = "    private String getAuthorName() {"
    idx = t.find(anchor)
    if idx < 0:
        print("WARN: getAuthorName anchor missing")
        return
    helper = """    // a11y-friend: anonymous sender name
    private boolean isNeedAccessibilityAuthorName() {
        if (!isChat || currentMessageObject == null || currentMessageObject.isOut()) return false;
        if (currentUser != null) return true;
        return currentChat != null && (isMegagroup || currentChat.signature_profiles);
    }

"""
    t = t[:idx] + helper + t[idx:]
    old = """                    if (isChat && currentUser != null && !currentMessageObject.isOut()) {
                        sb.append(UserObject.getUserName(currentUser));
                        sb.setSpan(new ProfileSpan(currentUser), 0, sb.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);"""
    new = """                    if (isNeedAccessibilityAuthorName()) {
                        sb.append(getAuthorName());
                        if (currentUser != null) {
                            sb.setSpan(new ProfileSpan(currentUser), 0, sb.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                        }"""
    if old not in t:
        print("WARN: sender accessibility text anchor missing")
        return
    t = t.replace(old, new, 1)
    cmc.write_text(t, encoding="utf-8")
    print("Friend PR 2037 anonymous/channel sender announcement OK")


def patch_friend_reply_navigation() -> None:
    """PR 2044: make reply/forward strip activation follow the visual tap."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists(): return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-friend: reply navigation"
    if marker in t: return
    old = """                    } else if (virtualViewId == REPLY) {
                        if (delegate != null && (!isThreadChat || isMonoForum || currentMessageObject.getReplyTopMsgId() != 0) && (currentMessageObject.hasValidReplyMessageObject() || hasReplyQuote || currentMessageObject.messageOwner != null && currentMessageObject.messageOwner.reply_to != null && currentMessageObject.messageOwner.reply_to.reply_from != null)) {
                            delegate.didPressReplyMessage(ChatMessageCell.this, currentMessageObject.getReplyMsgId(), 0, 0, false);
                        }"""
    new = """                    } else if (virtualViewId == REPLY) {
                        // a11y-friend: reply navigation
                        if (replyPanelIsForward) {
                            if (delegate != null) {
                                if (currentForwardChannel != null) delegate.didPressChannelAvatar(ChatMessageCell.this, currentForwardChannel, currentMessageObject.messageOwner.fwd_from.channel_post, lastTouchX, lastTouchY, false);
                                else if (currentForwardUser != null) delegate.didPressUserAvatar(ChatMessageCell.this, currentForwardUser, lastTouchX, lastTouchY, false);
                                else if (currentForwardName != null) delegate.didPressHiddenForward(ChatMessageCell.this);
                            }
                        } else if (delegate != null && (currentMessageObject.hasValidReplyMessageObject() || currentMessageObject.isReplyToStory() || hasReplyQuote || currentMessageObject.messageOwner != null && currentMessageObject.messageOwner.reply_to != null && currentMessageObject.messageOwner.reply_to.reply_from != null)) {
                            delegate.didPressReplyMessage(ChatMessageCell.this, currentMessageObject.getReplyMsgId(), 0, 0, false);
                        }"""
    if old not in t:
        print("WARN: reply accessibility action anchor missing")
        return
    t = t.replace(old, new, 1)
    cmc.write_text(t, encoding="utf-8")
    print("Friend PR 2044 reply navigation OK")


def patch_friend_sender_avatar_menu() -> None:
    """PR 2045: expose the sender-avatar long-press menu as a TalkBack action."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    ids = RES / "values/ids.xml"
    strings = RES / "values/strings.xml"
    if not cmc.exists() or not ca.exists(): return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-friend: sender avatar menu"
    if marker in t: return
    anchor = "    private int getIconForCurrentState() {"
    idx = t.find(anchor)
    if idx < 0:
        print("WARN: sender avatar menu anchor missing")
        return
    helper = """    // a11y-friend: sender avatar menu
    private boolean hasSenderAvatarMenu() {
        return isAvatarVisible && currentMessageObject != null && delegate != null
                && (currentUser != null && currentUser.id != 0 || currentChat != null);
    }

    private boolean performSenderAvatarMenu() {
        if (!hasSenderAvatarMenu()) return false;
        if (currentUser != null && currentUser.id != 0) {
            return delegate.didLongPressUserAvatar(ChatMessageCell.this, currentUser, lastTouchX, lastTouchY);
        }
        if (currentChat != null) {
            int id = 0;
            if (currentMessageObject.messageOwner != null && currentMessageObject.messageOwner.fwd_from != null) {
                id = (currentMessageObject.messageOwner.fwd_from.flags & 16) != 0
                        ? currentMessageObject.messageOwner.fwd_from.saved_from_msg_id
                        : currentMessageObject.messageOwner.fwd_from.channel_post;
            }
            return delegate.didLongPressChannelAvatar(ChatMessageCell.this, currentChat, id, lastTouchX, lastTouchY);
        }
        return false;
    }

"""
    t = t[:idx] + helper + t[idx:]
    old = """        } else if (action == R.id.acc_action_small_button) {
            didPressMiniButton(true);"""
    if old in t:
        t = t.replace(old, old + "\n        } else if (action == R.id.acc_action_sender_avatar_menu) {\n            return performSenderAvatarMenu();", 1)
    needle = """                info.addAction(new AccessibilityNodeInfo.AccessibilityAction(R.id.acc_action_msg_options, getString(\"AccActionMessageOptions\", R.string.AccActionMessageOptions)));"""
    if needle in t:
        t = t.replace(needle, needle + "\n                if (hasSenderAvatarMenu()) info.addAction(new AccessibilityNodeInfo.AccessibilityAction(R.id.acc_action_sender_avatar_menu, getString(R.string.AccActionSenderOptions)));", 1)
    cmc.write_text(t, encoding="utf-8")
    cat = ca.read_text(encoding="utf-8")
    # Telegram 12.10.5 ChatMessageCellDelegate has no canLongPressAvatar() method.
    # Do not add a fake interface override; the accessibility action itself is
    # guarded by the actual avatar/user/chat state above.
    cat = cat.replace("""        @Override
        public boolean canLongPressAvatar(ChatMessageCell cell) {
            return isAvatarPreviewerEnabled();
        }

""", "", 1)
    ca.write_text(cat, encoding="utf-8")
    it = ids.read_text(encoding="utf-8")
    if "acc_action_sender_avatar_menu" not in it:
        ids.write_text(it.replace('    <item name="acc_action_msg_options" type="id"/>', '    <item name="acc_action_msg_options" type="id"/>\n    <item name="acc_action_sender_avatar_menu" type="id"/>', 1), encoding="utf-8")
    st = strings.read_text(encoding="utf-8")
    if 'name="AccActionSenderOptions"' not in st:
        strings.write_text(st.replace('    <string name="AccActionMessageOptions">Message options</string>', '    <string name="AccActionMessageOptions">Message options</string>\n    <string name="AccActionSenderOptions">Sender options</string>', 1), encoding="utf-8")
    print("Friend PR 2045 sender-avatar menu OK")

def patch_friend_playback_position() -> None:
    """PR 1993: announce elapsed/total playback position."""
    mc = JAVA / "org/telegram/messenger/MediaController.java"
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not mc.exists() or not cmc.exists(): return
    marker = "a11y-friend: playback position"
    t = mc.read_text(encoding="utf-8")
    if marker not in t:
        anchor = "    public boolean isPlayingMessage(MessageObject messageObject) {"
        if anchor in t:
            block = """    // a11y-friend: playback position
    public static CharSequence getPlaybackPositionDescription(MessageObject messageObject) {
        if (messageObject == null || !getInstance().isPlayingMessage(messageObject)) return null;
        int duration = (int) messageObject.getDuration();
        int position = messageObject.audioProgressSec;
        if (duration > 0 && messageObject.audioProgress > 0) position = Math.round(messageObject.audioProgress * duration);
        position = Math.max(0, Math.min(duration, position));
        return LocaleController.formatString(R.string.AccDescrPlayerDuration, LocaleController.formatDuration(position), LocaleController.formatDuration(duration));
    }

"""
            mc.write_text(t.replace(anchor, block + anchor, 1), encoding="utf-8")
    t = cmc.read_text(encoding="utf-8")
    if marker not in t:
        anchor = "    @Override\n    public boolean performAccessibilityAction(int action, Bundle arguments) {"
        idx = t.find(anchor)
        if idx >= 0:
            block = """    // a11y-friend: playback position
    private void announceA11yPlaybackPosition() {
        CharSequence p = MediaController.getPlaybackPositionDescription(currentMessageObject);
        if (p != null) announceForAccessibility(p);
    }

"""
            t = t[:idx] + block + t[idx:]
            seek = """            if (seekBarAccessibilityDelegate.performAccessibilityActionInternal(action, arguments)) {
                return true;
            }"""
            if seek in t:
                t = t.replace(seek, """            if (seekBarAccessibilityDelegate.performAccessibilityActionInternal(action, arguments)) {
                announceA11yPlaybackPosition();
                return true;
            }""", 1)
            old = """                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                    info.setContentDescription(accessibilityText.toString());
                } else {
                    info.setText(accessibilityText);
                }"""
            new = """                CharSequence a11ySpokenText = accessibilityText;
                CharSequence a11yPlayback = MediaController.getPlaybackPositionDescription(currentMessageObject);
                if (a11yPlayback != null) a11ySpokenText = TextUtils.concat(a11yPlayback, ", ", accessibilityText);
                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                    info.setContentDescription(a11ySpokenText.toString());
                } else {
                    info.setText(a11ySpokenText);
                }"""
            if old in t: t = t.replace(old, new, 1)
            cmc.write_text(t, encoding="utf-8")
    print("Friend PR 1993 playback-position accessibility OK")


def patch_friend_transfer_percentage() -> None:
    """Retired: PR 1992 overlaps with Telegram Accessible progress."""
    print("Friend PR 1992 SKIPPED; native a11y progress retained")


def _apply_friend_pr_patch(pr_number: int, label: str) -> None:
    """Apply an isolated upstream accessibility PR on a fresh Telegram checkout."""
    import subprocess
    from urllib.request import Request, urlopen
    repo_root = ROOT.parent.parent
    patch_root = ROOT.parent  # telegram/; PR paths start with TMessagesProj/
    stamp = repo_root / f".a11y_friend_pr_{pr_number}"
    if stamp.exists():
        print(f"Friend PR {pr_number} already applied: {label}")
        return
    url = f"https://github.com/DrKLO/Telegram/pull/{pr_number}.patch"
    try:
        req = Request(url, headers={"User-Agent": "Telegram-A11y-build"})
        patch = urlopen(req, timeout=30).read()
        proc = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], input=patch, cwd=str(patch_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode == 0:
            stamp.write_text(f"friend-pr-{pr_number}\n", encoding="utf-8")
            print(f"Friend PR {pr_number} applied: {label}")
        else:
            print(f"WARN: Friend PR {pr_number} ({label}) did not apply cleanly; skipped")
            print(proc.stdout.decode("utf-8", "replace")[-4000:])
    except Exception as exc:
        print(f"WARN: Friend PR {pr_number} ({label}) unavailable: {exc}")


def patch_friend_isolated_features() -> None:
    # These are intentionally applied before our own custom patches because they touch
    # otherwise-independent accessibility surfaces.
    _apply_friend_pr_patch(2007, "RecyclerView screen-reader row scrolling")
    _apply_friend_pr_patch(2042, "Profile action buttons discoverable by touch")
    _apply_friend_pr_patch(2039, "Chat avatar story/community action")
    _apply_friend_pr_patch(1986, "Story viewer TalkBack controls")
    _apply_friend_pr_patch(2025, "Story sticker sheet accessibility")
    _apply_friend_pr_patch(2026, "Story editor button names")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found (clone DrKLO/Telegram as ./telegram)", file=sys.stderr)
        return 1
    print("Using scripts dir:", SCRIPTS.resolve())
    patch_app_name()
    patch_friend_isolated_features()
    patch_friend_playback_position()
    # PR 1992 intentionally retired; our native accessibility progress is authoritative.
    patch_friend_chat_jump_focus()
    patch_friend_search_result_announcement()
    patch_friend_anonymous_sender_name()
    patch_friend_reply_navigation()
    patch_friend_sender_avatar_menu()
    install_a11y_config()
    patch_a11y_download_settings()
    patch_a11y_localization()
    patch_radial_progress()
    patch_dialogcell_name_then_type()
    patch_hide_share_and_comment()
    patch_forward_menu_extras()
    # Shared end-anchor order: Bot Buttons -> Reactions -> Select (Select last).
    patch_longpress_message_menu()
    patch_photo_longpress_message_options()
    patch_reactions_as_menu()
    patch_voice_bitrate()
    patch_settings_menu()
    patch_auto_download_policy()
    patch_small_file_localization()
    patch_small_file_three_state()
    patch_small_file_radio_settings()
    patch_small_file_radio_ui_cleanup_v3()
    patch_remove_obsolete_small_file_switch()
    patch_small_file_radio_restore_v24()
    patch_exact_progress_steps()
    patch_recording_beep()
    patch_dialogcell_preview_muted_status()
    patch_dialogcell_time_last()
    patch_chat_message_cell_float_coordinates()
    patch_hide_sponsor_channel()
    patch_ghost_mode()
    patch_bot_buttons_menu()
    patch_links_as_menu()
    patch_reorder_a11y_menu_items()
    patch_go_to_first_message()
    patch_file_description_spacing()
    patch_chat_message_solar_date()
    patch_chat_action_solar_date_header()
    patch_chat_action_solar_date_accessibility()
    patch_locale_controller_solar_date_chat()
    patch_chat_message_cell_accessibility_long_click()
    patch_chat_message_cell_granularity_navigation()
    patch_stuck_together_bubbles_long_press()
    print("Friend PR integration path fixed: git apply runs inside telegram/ for TMessagesProj paths")
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
