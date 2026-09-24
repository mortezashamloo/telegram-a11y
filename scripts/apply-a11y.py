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

# Java-side option ids. Keep in sync with the constants we declare in
# ChatActivity via _ensure_chat_activity_option_constants().
OPTION_FORWARD_NO_QUOTE = 200
OPTION_REACTIONS_MENU = 201
OPTION_FORWARD_TO_SAVED = 202
OPTION_SELECT_MESSAGE = 203
OPTION_LINKS_MENU = 204
OPTION_BOT_BUTTONS_MENU = 205
OPTION_LEAVE_COMMENT = 206  # reserved, not used yet


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
    """Install every accessibility-fork string resource referenced by A11yConfig.java."""
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
        "A11yLinksLabel": "Links menu: %s",
        "A11yOn": "On", "A11yOff": "Off", "A11yCancel": "Cancel",
        "A11ySolarDate": "%1$s",
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
        "A11yGoToFirstMessage": "Go to first message", "A11yBotNumber": "Bot %1$d",
        "A11yPercent": "%1$d percent",
        "A11yLinks": "Links",
    }
    fa = {
        "A11yAccessibleSettingsTitle": "طھظ†ط¸غŒظ…ط§طھ ط¯ط³طھط±ط³â€Œظ¾ط°غŒط±غŒ",
        "A11yProgressAnnounceLabel": "ط§ط¹ظ„ط§ظ… ظ¾غŒط´ط±ظپطھ: %s",
        "A11yProgressStepLabel": "ع¯ط§ظ… ظ¾غŒط´ط±ظپطھ %1$d ط¯ط±طµط¯",
        "A11yProgressStepPickerTitle": "ع¯ط§ظ… ط§ط¹ظ„ط§ظ… ظ¾غŒط´ط±ظپطھ",
        "A11yVoiceQualityLabel": "ع©غŒظپغŒطھ طµط¯ط§: %s",
        "A11yVoiceQualityPickerTitle": "ع©غŒظپغŒطھ ظ¾غŒط§ظ… طµظˆطھغŒ",
        "A11yVoiceLow": "ظ¾ط§غŒغŒظ†", "A11yVoiceMedium": "ظ…طھظˆط³ط·", "A11yVoiceHigh": "ط¨ط§ظ„ط§",
        "A11yHideSponsorLabel": "ظ…ط®ظپغŒ ع©ط±ط¯ظ† ع©ط§ظ†ط§ظ„ ط­ط§ظ…غŒ: %s",
        "A11ySponsorHidden": "ع©ط§ظ†ط§ظ„ ط­ط§ظ…غŒ ظ…ط®ظپغŒ ط´ط¯",
        "A11ySponsorShown": "ع©ط§ظ†ط§ظ„ ط­ط§ظ…غŒ ظ†ظ…ط§غŒط´ ط¯ط§ط¯ظ‡ ط´ط¯",
        "A11yGhostModeLabel": "ط­ط§ظ„طھ ط±ظˆط­: %s",
        "A11yGhostOn": "ط­ط§ظ„طھ ط±ظˆط­ ط±ظˆط´ظ† ط´ط¯", "A11yGhostOff": "ط­ط§ظ„طھ ط±ظˆط­ ط®ط§ظ…ظˆط´ ط´ط¯",
        "A11yStatusPreviewLabel": "ظ†ظ…ط§غŒط´ ظˆط¶ط¹غŒطھ ط¯ط± ظ¾غŒط´â€Œظ†ظ…ط§غŒط´: %s",
        "A11yStatusOn": "ظ†ظ…ط§غŒط´ ظˆط¶ط¹غŒطھ ط±ظˆط´ظ† ط´ط¯", "A11yStatusOff": "ظ†ظ…ط§غŒط´ ظˆط¶ط¹غŒطھ ط®ط§ظ…ظˆط´ ط´ط¯",
        "A11yForwardSavedNoQuoteLabel": "ظپظˆط±ظˆط§ط±ط¯ ط¨ظ‡ ظ¾غŒط§ظ…â€Œظ‡ط§غŒ ط°ط®غŒط±ظ‡â€Œط´ط¯ظ‡ ط¨ط¯ظˆظ† ظ†ظ‚ظ„â€Œظ‚ظˆظ„: %s",
        "A11yRecordingBeepLabel": "ط¨ظˆظ‚ ط´ط±ظˆط¹ ط¶ط¨ط·: %s",
        "A11ySolarCalendarLabel": "طھظ‚ظˆغŒظ… ط®ظˆط±ط´غŒط¯غŒ: %s",
        "A11yLinksLabel": "ظ…ظ†ظˆغŒ ظ¾غŒظˆظ†ط¯ظ‡ط§: %s",
        "A11yOn": "ط±ظˆط´ظ†", "A11yOff": "ط®ط§ظ…ظˆط´", "A11yCancel": "ظ„ط؛ظˆ",
        "A11ySolarDate": "%1$s",
        "A11yAccessibleSettings": "طھظ†ط¸غŒظ…ط§طھ ط¯ط³طھط±ط³â€Œظ¾ط°غŒط±غŒ",
        "A11yProgressAnnounce": "ط§ط¹ظ„ط§ظ… ظ¾غŒط´ط±ظپطھ", "A11yVoiceQuality": "ع©غŒظپغŒطھ طµط¯ط§",
        "A11yProgressAnnounceSummary": "ط§ط¹ظ„ط§ظ… ظ¾غŒط´ط±ظپطھ ظˆ ع©غŒظپغŒطھ طµط¯ط§",
        "A11yProgressAnnounceStep": "ع¯ط§ظ… ط§ط¹ظ„ط§ظ… ظ¾غŒط´ط±ظپطھ", "A11yVoiceMessageQuality": "ع©غŒظپغŒطھ ظ¾غŒط§ظ… طµظˆطھغŒ",
        "A11yLow": "ظ¾ط§غŒغŒظ†", "A11yMedium": "ظ…طھظˆط³ط·", "A11yHigh": "ط¨ط§ظ„ط§",
        "A11yProgressStep": "ع¯ط§ظ… ظ¾غŒط´ط±ظپطھ %1$d ط¯ط±طµط¯",
        "A11yVoiceQualitySelected": "ع©غŒظپغŒطھ طµط¯ط§ %1$s",
        "A11yForwardWithoutQuote": "ظپظˆط±ظˆط§ط±ط¯ ط¨ط¯ظˆظ† ظ†ظ‚ظ„â€Œظ‚ظˆظ„",
        "A11yForwardToSaved": "ط§ط±ط³ط§ظ„ ط¨ظ‡ ظ¾غŒط§ظ…â€Œظ‡ط§غŒ ط°ط®غŒط±ظ‡â€Œط´ط¯ظ‡",
        "A11yForwardedToSaved": "ط¨ظ‡ ظ¾غŒط§ظ…â€Œظ‡ط§غŒ ط°ط®غŒط±ظ‡â€Œط´ط¯ظ‡ ط§ط±ط³ط§ظ„ ط´ط¯", "A11ySelected": "ط§ظ†طھط®ط§ط¨ ط´ط¯",
        "A11yReceiveAt": "ط¯ط±غŒط§ظپطھ ط¯ط± ط³ط§ط¹طھ %1$s", "A11ySentAt": "ط§ط±ط³ط§ظ„ ط¯ط± ط³ط§ط¹طھ %1$s",
        "A11yBotButtons": "ط¯ع©ظ…ظ‡â€Œظ‡ط§غŒ ط±ط¨ط§طھ", "A11yGoToFirstMessage": "ط±ظپطھظ† ط¨ظ‡ ط§ظˆظ„غŒظ† ظ¾غŒط§ظ…",
        "A11yBotNumber": "ط±ط¨ط§طھ %1$d", "A11yPercent": "%1$d ط¯ط±طµط¯",
        "A11yLinks": "ظ¾غŒظˆظ†ط¯ظ‡ط§",
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


def patch_percent_localization() -> None:
    """Ensure the accessibility percentage announcement is localized in Persian."""
    for rel in ("values/strings.xml", "values-fa/strings.xml", "values-fa-rIR/strings.xml"):
        path = RES / rel
        if not path.exists():
            continue
        rt = path.read_text(encoding="utf-8")
        value = "%1$d percent" if rel == "values/strings.xml" else "%1$d ط¯ط±طµط¯"
        rt2, n = re.subn(r'(<string\s+name="A11yPercent">)[^<]*(</string>)', rf'\1{value}\2', rt, count=1)
        if n:
            path.write_text(rt2, encoding="utf-8")
    print("Percent localization OK")


def install_a11y_config() -> None:
    """Copy A11yConfig.java from scripts/ and flip a couple of defaults to ON.

    NOTE: we do NOT rewrite formatSolarDate here anymore. The canonical
    implementation lives in A11yConfig.java (long signature, Persian digits,
    locale detection) and is copied verbatim.
    """
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
    print("A11yConfig.java installed + beep/Jalali defaults ON")

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
                            parent.announceForAccessibility(LocaleController.formatString("A11yPercent", R.string.A11yPercent, step));
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
        saved = '''            case OPTION_FORWARD_TO_SAVED: { // a11y-fork: forward to Saved Messages\n                if (selectedObject != null) {\n                    try {\n                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {\n                            toSend.addAll(selectedObjectGroup.messages);\n                        } else {\n                            toSend.add(selectedObject);\n                        }\n                        IS_FORWARD_NO_QUOTE = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();\n                        long savedId = getUserConfig().getClientUserId();\n                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n                        try {\n                            if (getParentActivity() != null) {\n                                getParentActivity().getWindow().getDecorView().announceForAccessibility(LocaleController.getString(R.string.A11yForwardedToSaved));\n                            }\n                        } catch (Throwable ignore) {}\n                    } catch (Throwable e) {\n                        FileLog.e(e);\n                    }\n                }\n                selectedObject = null;\n                selectedObjectToEditCaption = null;\n                selectedObjectGroup = null;\n                break;\n            }\n'''
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
    # IMPORTANT: the forward handler itself also contains the token
    # IS_FORWARD_NO_QUOTE, so checking `if "IS_FORWARD_NO_QUOTE" not in t`
    # is not sufficient to detect the field declaration.
    if "public static boolean IS_FORWARD_NO_QUOTE" not in t:
        anchor = "protected TLRPC.Chat currentChat;"
        if anchor in t:
            t = t.replace(anchor, "public static boolean IS_FORWARD_NO_QUOTE = false;\n    " + anchor, 1)
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
            t = t.replace(field_anchor, field_anchor + "\n    " + option_decl, 1)
            print("Forward option constants OK")
        else:
            print("WARN: IS_FORWARD_NO_QUOTE field anchor not found (option constants)")
    if "a11y-fork: forward menu extras" not in t:
        old = ("                if (canForward) {\n"
               "                    items.add(LocaleController.getString(R.string.Forward));\n"
               "                    options.add(OPTION_FORWARD);\n"
               "                    icons.add(R.drawable.msg_forward);\n"
               "                }")
        new = ("                if (canForward) {\n"
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
        if old in t:
            t = t.replace(old, new, 1)
            print("Forward menu extras OK")
        else:
            print("WARN: canForward menu block not found")
    t = patch_forward_handler(t)
    ca.write_text(t, encoding="utf-8")
    print("Forward option handlers v2 OK")

def _ensure_chat_activity_option_constants(t: str) -> str:
    """Declare every accessibility option id we reference inside ChatActivity.

    The Python constants at the top of this file are NOT Java constants; any
    `options.add(204)`-style literal we generate must have a matching Java
    field. Call this once before writing ChatActivity back to disk.
    """
    needed = [
        ("OPTION_FORWARD_NO_QUOTE", OPTION_FORWARD_NO_QUOTE),
        ("OPTION_REACTIONS_MENU", OPTION_REACTIONS_MENU),
        ("OPTION_FORWARD_TO_SAVED", OPTION_FORWARD_TO_SAVED),
        ("OPTION_SELECT_MESSAGE", OPTION_SELECT_MESSAGE),
        ("OPTION_LINKS_MENU", OPTION_LINKS_MENU),
        ("OPTION_BOT_BUTTONS_MENU", OPTION_BOT_BUTTONS_MENU),
    ]
    class_anchor = "public class ChatActivity"
    class_idx = t.find(class_anchor)
    if class_idx == -1:
        return t
    brace_idx = t.find("{", class_idx)
    if brace_idx == -1:
        return t

    decls = []
    for name, value in needed:
        token = f"private static final int {name} ="
        if token not in t:
            decls.append(f"    {token} {value}; // a11y-fork: option id {value}")
    if not decls:
        return t
    block = "\n" + "\n".join(decls) + "\n"
    return t[: brace_idx + 1] + block + t[brace_idx + 1 :]


def patch_reactions_as_menu() -> None:
    """
    Accessibility-fork: put the emoji reactions row behind a "Reactions"
    menu item (hidden/collapsed by default, revealed on tap).

    The menu ITEM itself is inserted by patch_message_menu_order() so the
    final order is guaranteed to be Links -> Bot Buttons -> Reactions ->
    Select. This function only handles the reactions row visibility toggle
    and the field declaration used by the toggle index.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")

    # Field declaration for the toggle index, inserted right after the
    # ChatActivity class opening brace.
    if "accessibilityReactionsToggleIndex" not in t:
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

    # Hide the reactions row by default; the "Reactions" menu item reveals
    # it on tap.
    marker = "a11y-fork: reactions menu item -- hide the reactions row"
    if marker not in t:
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
            print("ChatActivity reactions-menu visibility toggle OK")

    t = _ensure_chat_activity_option_constants(t)
    ca.write_text(t, encoding="utf-8")
    print("ChatActivity reactions-menu field+toggle OK")


def patch_longpress_message_menu() -> None:
    """
    Accessibility-fork: long-press behaviour under TalkBack.

    This function is ONLY responsible for:
      1. Prefer the single-message menu under TalkBack (avoids multi-select).
      2. Do not auto-start multi-select on long-press under TalkBack.

    The actual menu ITEMS (Links, Bot Buttons, Reactions, Select) are
    inserted by patch_message_menu_order() so the final order is guaranteed.
    """
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

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity long-press behaviour OK")

def patch_message_menu_order() -> None:
    """
    Accessibility-fork: insert every accessibility menu item in ONE place,
    in the exact order the user requested:

        Links -> Bot Buttons -> Reactions -> Select (last)

    All four items are injected just before the sponsored-item block in
    fillMessageMenu(), using a single shared anchor. Because they are
    inserted together, the final on-screen order is deterministic and does
    not depend on which patch function runs first.

    Links is only shown when A11yConfig.getLinksMenu() is ON.
    Bot Buttons is only shown when the message has inline bot buttons.
    Reactions is only shown when the message supports reactions.
    Select is only shown when there is no action mode and the message is
    a normal (non-sponsored, contentType == 0) message.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (message menu order)")
        return
    t = ca.read_text(encoding="utf-8")

    marker = "// a11y-fork: message menu order v2"
    if marker in t:
        print("ChatActivity message menu order v2 already patched")
        t = _ensure_chat_activity_option_constants(t)
        ca.write_text(t, encoding="utf-8")
        return

    anchor = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if anchor not in t:
        print("WARN: sponsored anchor not found (message menu order)")
        return

    insert = (
        "        // a11y-fork: message menu order v2\n"
        "        // Order: Links, Bot Buttons, Reactions, Select (Select last)\n"
        "\n"
        "        // 1) Links\n"
        "        if (message != null && org.telegram.messenger.A11yConfig.getLinksMenu()\n"
        "                && hasAccessibleLinks(message)) {\n"
        "            items.add(LocaleController.getString(R.string.A11yLinks));\n"
        f"            options.add({OPTION_LINKS_MENU});\n"
        "            icons.add(R.drawable.msg_link);\n"
        "        }\n"
        "\n"
        "        // 2) Bot Buttons\n"
        "        if (message != null && message.hasInlineBotButtons()) {\n"
        "            items.add(LocaleController.getString(R.string.A11yBotButtons));\n"
        f"            options.add({OPTION_BOT_BUTTONS_MENU});\n"
        "            icons.add(R.drawable.msg_viewreplies);\n"
        "        }\n"
        "\n"
        "        // 3) Reactions\n"
        "        accessibilityReactionsToggleIndex = -1;\n"
        "        if (message != null && message.isReactionsAvailable()) {\n"
        "            items.add(LocaleController.getString(R.string.Reactions));\n"
        "            icons.add(R.drawable.msg_reactions2);\n"
        f"            options.add({OPTION_REACTIONS_MENU});\n"
        "            accessibilityReactionsToggleIndex = items.size() - 1;\n"
        "        }\n"
        "\n"
        "        // 4) Select (last)\n"
        "        if (!actionBar.isActionModeShowed() && message != null && message.contentType == 0 && !message.isSponsored()) {\n"
        "            items.add(LocaleController.getString(R.string.Select));\n"
        f"            options.add({OPTION_SELECT_MESSAGE});\n"
        "            icons.add(R.drawable.msg_forward);\n"
        "        }\n"
        "\n"
    )
    t = t.replace(anchor, insert + anchor, 1)

    # Install the helper that decides whether the Links item should appear.
    # It looks at the message text, caption and webpage -- but NOT inline
    # bot buttons, which are handled by the Bot Buttons item.
    if "// a11y-fork: hasAccessibleLinks helper" not in t:
        helper_anchor = "    public void firstLoadMessages() {"
        helper = (
            "    // a11y-fork: hasAccessibleLinks helper\n"
            "    private boolean hasAccessibleLinks(MessageObject message) {\n"
            "        if (message == null || message.messageOwner == null) {\n"
            "            return false;\n"
            "        }\n"
            "        try {\n"
            "            if (message.messageOwner.media instanceof TLRPC.TL_messageMediaWebPage\n"
            "                    && message.messageOwner.media.webpage != null\n"
            "                    && !TextUtils.isEmpty(message.messageOwner.media.webpage.url)) {\n"
            "                return true;\n"
            "            }\n"
            "            if (message.messageOwner.entities != null) {\n"
            "                for (int i = 0; i < message.messageOwner.entities.size(); i++) {\n"
            "                    TLRPC.MessageEntity e = message.messageOwner.entities.get(i);\n"
            "                    if (e instanceof TLRPC.TL_messageEntityUrl\n"
            "                            || e instanceof TLRPC.TL_messageEntityTextUrl\n"
            "                            || e instanceof TLRPC.TL_messageEntityMention\n"
            "                            || e instanceof TLRPC.TL_messageEntityBotCommand) {\n"
            "                        return true;\n"
            "                    }\n"
            "                }\n"
            "            }\n"
            "            // Caption entities live in messageOwner.media.caption entities only\n"
            "            // for newer Telegram builds; older builds put them in\n"
            "            // messageOwner.entities too. The loop above already covers the\n"
            "            // common case; this is a defensive fallback.\n"
            "            if (message.caption != null) {\n"
            "                java.util.regex.Matcher m = java.util.regex.Pattern\n"
            "                        .compile(\"(https?://|t\\\\.me/|@[A-Za-z0-9_]{4,})\")\n"
            "                        .matcher(message.caption.toString());\n"
            "                if (m.find()) {\n"
            "                    return true;\n"
            "                }\n"
            "            }\n"
            "        } catch (Throwable ignore) {\n"
            "        }\n"
            "        return false;\n"
            "    }\n"
            "\n"
        )
        if helper_anchor in t:
            t = t.replace(helper_anchor, helper + helper_anchor, 1)
            print("ChatActivity hasAccessibleLinks helper OK")
        else:
            print("WARN: firstLoadMessages anchor not found (hasAccessibleLinks helper)")

    t = _ensure_chat_activity_option_constants(t)
    ca.write_text(t, encoding="utf-8")
    print("ChatActivity message menu order v2 (Links, Bot, Reactions, Select) OK")


def patch_links_menu() -> None:
    """
    Accessibility-fork: the "Links" menu item opens a dialog that lists
    every link found in the message (text entities + caption + webpage).
    Inline bot buttons are intentionally NOT counted as links.

    Default: OFF (A11yConfig.getLinksMenu()); the user turns it on from
    Accessible settings. When OFF, the item is not added to the menu at all
    (see patch_message_menu_order), so this handler is never reached.
    """
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (links menu)")
        return
    t = ca.read_text(encoding="utf-8")

    if "a11y-fork: OPTION_LINKS_MENU handler" in t:
        print("ChatActivity links menu handler already patched")
        return

    old_case = "            case OPTION_RETRY: {\n"
    new_case = (
        "            case OPTION_LINKS_MENU: { // a11y-fork: OPTION_LINKS_MENU handler\n"
        "                try {\n"
        "                    MessageObject msg = selectedObject;\n"
        "                    final ArrayList<String> links = new ArrayList<>();\n"
        "                    final ArrayList<String> labels = new ArrayList<>();\n"
        "                    if (msg != null && msg.messageOwner != null) {\n"
        "                        // webpage link\n"
        "                        if (msg.messageOwner.media instanceof TLRPC.TL_messageMediaWebPage\n"
        "                                && msg.messageOwner.media.webpage != null\n"
        "                                && !TextUtils.isEmpty(msg.messageOwner.media.webpage.url)) {\n"
        "                            String url = msg.messageOwner.media.webpage.url;\n"
        "                            String title = msg.messageOwner.media.webpage.title;\n"
        "                            if (!links.contains(url)) {\n"
        "                                links.add(url);\n"
        "                                labels.add(!TextUtils.isEmpty(title) ? title + \" â€” \" + url : url);\n"
        "                            }\n"
        "                        }\n"
        "                        // entities on the message text\n"
        "                        if (msg.messageOwner.entities != null && msg.messageText != null) {\n"
        "                            for (int i = 0; i < msg.messageOwner.entities.size(); i++) {\n"
        "                                TLRPC.MessageEntity entity = msg.messageOwner.entities.get(i);\n"
        "                                String url = null;\n"
        "                                if (entity instanceof TLRPC.TL_messageEntityTextUrl) {\n"
        "                                    url = ((TLRPC.TL_messageEntityTextUrl) entity).url;\n"
        "                                } else if (entity instanceof TLRPC.TL_messageEntityUrl\n"
        "                                        || entity instanceof TLRPC.TL_messageEntityMention\n"
        "                                        || entity instanceof TLRPC.TL_messageEntityBotCommand) {\n"
        "                                    int start = entity.offset;\n"
        "                                    int end = entity.offset + entity.length;\n"
        "                                    if (start >= 0 && end <= msg.messageText.length()) {\n"
        "                                        url = msg.messageText.subSequence(start, end).toString();\n"
        "                                    }\n"
        "                                }\n"
        "                                if (!TextUtils.isEmpty(url) && !links.contains(url)) {\n"
        "                                    links.add(url);\n"
        "                                    labels.add(url);\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                        // caption entities (defensive: some builds keep them separate)\n"
        "                        if (msg.caption != null) {\n"
        "                            java.util.regex.Matcher m = java.util.regex.Pattern\n"
        "                                    .compile(\"https?://[^\\\\s]+\")\n"
        "                                    .matcher(msg.caption.toString());\n"
        "                            while (m.find()) {\n"
        "                                String url = m.group();\n"
        "                                if (!TextUtils.isEmpty(url) && !links.contains(url)) {\n"
        "                                    links.add(url);\n"
        "                                    labels.add(url);\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                    if (!links.isEmpty() && getParentActivity() != null) {\n"
        "                        AlertDialog.Builder b = new AlertDialog.Builder(getParentActivity());\n"
        "                        b.setTitle(LocaleController.getString(R.string.A11yLinks));\n"
        "                        b.setItems(labels.toArray(new CharSequence[0]), (dialog, which) -> {\n"
        "                            if (which >= 0 && which < links.size()) {\n"
        "                                try {\n"
        "                                    android.content.Intent intent = new android.content.Intent(\n"
        "                                            android.content.Intent.ACTION_VIEW,\n"
        "                                            android.net.Uri.parse(links.get(which)));\n"
        "                                    getParentActivity().startActivity(intent);\n"
        "                                } catch (Throwable e) {\n"
        "                                    FileLog.e(e);\n"
        "                                }\n"
        "                            }\n"
        "                        });\n"
        "                        b.setNegativeButton(LocaleController.getString(R.string.A11yCancel), null);\n"
        "                        showDialog(b.create());\n"
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
    if old_case in t:
        t = t.replace(old_case, new_case, 1)
        print("Links handler OK")
    else:
        print("WARN: OPTION_RETRY anchor not found (links menu)")

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity links menu handler OK")

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
    insert = needle + "\n        // a11y-fork: Accessible settings entry\n        items.add(SettingCell.Factory.of(100, IconBackgroundColors.GREEN.top, IconBackgroundColors.GREEN.bottom, R.drawable.settings_privacy, LocaleController.getString(R.string.A11yAccessibleSettings), LocaleController.getString(R.string.A11yProgressAnnounceSummary)));"
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


def patch_recording_beep() -> None:
    """Play a short recording-start beep through Android's accessibility audio stream."""
    mc = JAVA / "org/telegram/messenger/MediaController.java"
    if not mc.exists():
        print("WARN: MediaController missing (recording beep)")
        return
    t = mc.read_text(encoding="utf-8")
    marker = "a11y-fork: recording-start beep-v4"
    if marker in t:
        print("MediaController recording beep v4 already patched")
        return
    needle = "try { org.telegram.messenger.A11yConfig.applyVoiceBitrateToNative(); } catch (Throwable ignore) {}"
    if needle not in t:
        print("WARN: MediaController record-start anchor not found (recording beep)")
        return
    replacement = needle + """
                    // a11y-fork: recording-start beep-v4
                    try {
                        if (org.telegram.messenger.A11yConfig.getRecordingBeep()) {
                            final int sampleRate = 44100;
                            final int durationMs = 110;
                            final int sampleCount = sampleRate * durationMs / 1000;
                            final short[] pcm = new short[sampleCount];
                            final double frequency = 880.0;
                            final double amplitude = 0.55 * Short.MAX_VALUE;
                            for (int i = 0; i < sampleCount; i++) {
                                double fade = 1.0 - ((double) i / (double) sampleCount) * 0.45;
                                pcm[i] = (short) (Math.sin(2.0 * Math.PI * frequency * i / sampleRate) * amplitude * fade);
                            }
                            final int bufferBytes = pcm.length * 2;
                            final android.media.AudioTrack track = new android.media.AudioTrack(
                                    android.media.AudioManager.STREAM_ACCESSIBILITY,
                                    sampleRate,
                                    android.media.AudioFormat.CHANNEL_OUT_MONO,
                                    android.media.AudioFormat.ENCODING_PCM_16BIT,
                                    bufferBytes,
                                    android.media.AudioTrack.MODE_STATIC);
                            track.setVolume(1.0f);
                            track.write(pcm, 0, pcm.length);
                            track.play();
                            org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> {
                                try { track.stop(); } catch (Throwable ignore) {}
                                try { track.release(); } catch (Throwable ignore) {}
                            }, durationMs + 100);
                        }
                    } catch (Throwable e) {
                        org.telegram.messenger.FileLog.e(e);
                    }"""
    t = t.replace(needle, replacement, 1)
    mc.write_text(t, encoding="utf-8")
    print("MediaController recording-start accessibility-stream beep v4 OK")

def patch_dialogcell_preview_muted_status() -> None:
    """
    Accessibility-fork additions to DialogCell.java's TalkBack description:
      - remove the "Muted" announcement entirely
      - read the contact's online/last-seen status when enabled
      - bump the message-preview length read aloud to 300 characters

    The date/time part of the description is NOT touched here; it is handled
    by patch_message_time_and_solar() which uses A11yConfig.formatAccessibleDate.
    """
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (preview/muted/status)")
        return
    t = dc.read_text(encoding="utf-8")

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
        "        // a11y-fork: muted/status/preview-300 -- \"Muted\" removed.\n"
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
    if old_block in t:
        t = t.replace(old_block, new_block, 1)
    elif "a11y-fork: muted/status/preview-300" not in t:
        print("WARN: DialogCell muted/status block not found")

    old_len = (
        "            int len = messageLayout == null ? -1 : messageLayout.getText().length();\n"
        "            if (len > 0) {"
    )
    new_len = (
        "            int len = 300; // a11y-fork: read up to 300 characters\n"
        "            if (len > 0 && len < messageString.length()) {"
    )
    if old_len in t:
        t = t.replace(old_len, new_len, 1)

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted/status/preview-300 OK")


def patch_message_time_and_solar() -> None:
    """Keep Telegram's native sent/received date+time announcement.

    When Solar Calendar is enabled, A11yConfig.formatAccessibleDate() returns
    the Solar Hijri date with the same Telegram wording ("Today at ...",
    "Yesterday at ...", or "SOLAR_DATE at HH:MM"). When it is disabled, the
    function returns exactly what LocaleController.formatDateAudio returns,
    so the wording and format remain 100% Telegram-native.
    """
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (time/Jalali)")
        return
    t = dc.read_text(encoding="utf-8")
    marker = "a11y-fork-v6: official Telegram send/receive date LAST"
    if marker in t:
        print("DialogCell official Telegram time + solar-date already patched")
        return

    # Remove any old custom accessibility time tail if this script is being
    # applied to a tree that already contains an earlier v2/v3/v4 patch.
    old_custom_tail = (
        "        // a11y-fork: sent/received time read last\n"
        "        String a11yClockTime = LocaleController.formatDateAudio(lastDate, true);\n"
        "        sb.append(message.isOut() ? \"sent @\" : \"receive @\");\n"
        "        sb.append(a11yClockTime);\n"
        "        sb.append(\". \");\n"
    )
    if old_custom_tail in t:
        t = t.replace(old_custom_tail, "", 1)

    old_custom_tail_v3 = (
        "        // a11y-fork: explicit separator before time\n"
        "        sb.append(\". \");\n"
        "        sb.append(message.isOut() ? \"sent at \" : \"received at \");\n"
        "        sb.append(a11yClockTime);\n"
        "        sb.append(\". \");\n"
        "        // a11y-fork: Jalali date\n"
        "        try {\n"
        "            if (org.telegram.messenger.A11yConfig.getSolarCalendar()) {\n"
        "                String solarDate = org.telegram.messenger.A11yConfig.formatSolarDate(lastDate);\n"
        "                if (solarDate != null && solarDate.length() > 0) {\n"
        "                    sb.append(solarDate);\n"
        "                    sb.append(\". \");\n"
        "                }\n"
        "            }\n"
        "        } catch (Throwable ignore) {}"
    )
    if old_custom_tail_v3 in t:
        t = t.replace(old_custom_tail_v3, "", 1)

    # Find the LAST event.setContentDescription(sb) block (the one that runs
    # after `int lastDate = lastMessageDate;` is declared) and insert the
    # official Telegram date tail there.
    end_anchor = '\n        event.setContentDescription(sb);\n        setContentDescription(sb);\n    }'
    end_idx = t.rfind(end_anchor)
    if end_idx < 0:
        end_anchor = '\n        setContentDescription(sb);\n    }'
        end_idx = t.rfind(end_anchor)
    if end_idx >= 0 and t.rfind('int lastDate = lastMessageDate;', 0, end_idx) < 0:
        print("WARN: DialogCell lastDate not declared before end anchor; skipping date tail")
        end_idx = -1
    if end_idx >= 0:
        native_tail = (
            '        // a11y-fork-v6: official Telegram send/receive date LAST\n'
            '        String a11yDate = org.telegram.messenger.A11yConfig.formatAccessibleDate(lastDate, true);\n'
            '        if (message.isOut()) {\n'
            '            sb.append(LocaleController.formatString("AccDescrSentDate", R.string.AccDescrSentDate, a11yDate));\n'
            '        } else {\n'
            '            sb.append(LocaleController.formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, a11yDate));\n'
            '        }\n'
            '        sb.append(". ");\n'
        )
        t = t[:end_idx + 1] + native_tail + t[end_idx + 1:]
    else:
        print("WARN: DialogCell content-description end anchor not found")

    dc.write_text(t, encoding="utf-8")
    print("DialogCell official Telegram time format + optional Solar date OK")


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

    The menu ITEM itself is inserted by patch_message_menu_order(); this
    function only hides the inline row and installs the dialog handler.
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

    # 2) Install the "Bot Buttons" dialog handler in ChatActivity.
    t2 = ca.read_text(encoding="utf-8")
    if "a11y-fork: OPTION_BOT_BUTTONS_MENU handler" in t2:
        print("ChatActivity bot-buttons-menu handler already patched")
        return

    old_case = "            case OPTION_RETRY: {\n"
    new_case = (
        "            case OPTION_BOT_BUTTONS_MENU: { // a11y-fork: OPTION_BOT_BUTTONS_MENU handler\n"
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
        "                        botBtnBuilder.setTitle(LocaleController.getString(R.string.A11yBotButtons));\n"
        "                        botBtnBuilder.setItems(itemsArr, (dialog, which) -> {\n"
        "                            if (which >= 0 && which < btnsFinal.size() && chatActivityEnterView != null) {\n"
        "                                chatActivityEnterView.didPressedBotButton(btnsFinal.get(which), msgFinal, msgFinal);\n"
        "                            }\n"
        "                        });\n"
        "                        botBtnBuilder.setNegativeButton(LocaleController.getString(R.string.A11yCancel), null);\n"
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
    if old_case in t2:
        t2 = t2.replace(old_case, new_case, 1)
        ca.write_text(t2, encoding="utf-8")
        print("ChatActivity bot-buttons-menu handler OK")
    else:
        print("WARN: ChatActivity OPTION_RETRY case anchor not found (bot buttons menu handler)")


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
        branch = "                } else if (id == OPTION_GO_TO_FIRST_MESSAGE) { // a11y-fork: go-to-first-message handler\n                    accessibilityGoToFirstMessage();\n                } else if (id == view_as_topics) {"
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
    """TalkBack: announce document files once as localized 'file <filename>'."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (file description spacing)")
        return
    t = cmc.read_text(encoding="utf-8")

    # Remove the accessibility-fork block from v3/v4/v5 if present. It caused
    # the filename to be spoken a second time.
    custom = re.compile(
        r'\n\s*// a11y-fork: real document filename\n'
        r'\s*String a11yDocumentName = FileLoader\.getDocumentFileName\(documentAttach\);\n'
        r'\s*if \(!TextUtils\.isEmpty\(a11yDocumentName\)\) \{[\s\S]*?'
        r'\s*\}\n\s*\}', re.MULTILINE
    )
    t, n = custom.subn('', t, count=1)
    if n:
        print("ChatMessageCell old duplicate filename block removed")

    # Telegram's official block normally announces only the extension/type.
    # Replace that block with one announcement containing the real filename.
    old = (
        "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
        "                        String fileName = FileLoader.getAttachFileName(documentAttach);\n"
        "                        if (fileName.indexOf('.') != -1) {\n"
        "                            sb.append(formatString(R.string.AccDescrDocumentType, fileName.substring(fileName.lastIndexOf('.') + 1).toUpperCase(Locale.ROOT)));\n"
        "                        }\n"
        "                    }"
    )
    new = (
        "                    if (documentAttach != null && documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT) {\n"
        "                        String a11yDocumentName = FileLoader.getDocumentFileName(documentAttach);\n"
        "                        if (!TextUtils.isEmpty(a11yDocumentName)) {\n"
        "                            sb.append(formatString(R.string.AccDescrDocumentType, a11yDocumentName));\n"
        "                        }\n"
        "                    }"
    )
    if old in t:
        t = t.replace(old, new, 1)
        print("ChatMessageCell single real filename block OK")
    elif "String a11yDocumentName = FileLoader.getDocumentFileName(documentAttach);" not in t:
        print("WARN: ChatMessageCell document accessibility anchor not found")

    for rel in ("values/strings.xml", "values-fa/strings.xml", "values-fa-rIR/strings.xml"):
        path = RES / rel
        if not path.exists():
            continue
        rt = path.read_text(encoding="utf-8")
        value = "file %s. " if "fa" not in rel else "ظپط§غŒظ„ %s. "
        rt2, n = re.subn(
            r'(<string\s+name="AccDescrDocumentType">)[^<]*(</string>)',
            rf'\1{value}\2', rt, count=1
        )
        if n:
            path.write_text(rt2, encoding="utf-8")
            print(f"{rel} AccDescrDocumentType = {value.strip()}")
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell document filename will be announced once")


def patch_chat_message_solar_date() -> None:
    """Use the accessibility-fork date formatter for ChatMessageCell.

    When Solar Calendar is OFF, A11yConfig.formatAccessibleDate returns
    exactly what LocaleController.formatDateAudio returns, so the wording
    and time format are 100% Telegram-native. When ON, the date part is
    replaced with the Solar Hijri date using the same Telegram structure
    ("Today at ...", "Yesterday at ...", or "SOLAR_DATE at HH:MM").
    """
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (chat solar date)")
        return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-fork-v6: chat solar date"
    if marker in t:
        print("ChatMessageCell solar date already patched")
        return

    # Replace the two native accessibility date blocks. Only the date
    # argument is changed; AccDescrSentDate/ReceivedDate strings and the
    # surrounding wording remain native.
    old_sent = (
        '                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));'
    )
    new_sent = (
        '                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, org.telegram.messenger.A11yConfig.formatAccessibleDate(currentMessageObject.messageOwner.date, true)));'
    )
    old_recv = (
        '                        sb.append(formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));'
    )
    new_recv = (
        '                        sb.append(formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, org.telegram.messenger.A11yConfig.formatAccessibleDate(currentMessageObject.messageOwner.date, true)));'
    )
    changed = False
    if old_sent in t:
        t = t.replace(old_sent, new_sent, 1)
        changed = True
        print("ChatMessageCell sent-date OK")
    if old_recv in t:
        t = t.replace(old_recv, new_recv, 1)
        changed = True
        print("ChatMessageCell received-date OK")
    if changed:
        t = t.replace(
            '    private class MessageAccessibilityNodeProvider',
            '    // ' + marker + '\n    private class MessageAccessibilityNodeProvider',
            1,
        )
        cmc.write_text(t, encoding="utf-8")
        print("ChatMessageCell Solar Hijri accessibility date OK")
    else:
        print("WARN: ChatMessageCell sent/received accessibility date anchors not found")


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


def validate_generated_sources() -> None:
    """Fail early on common malformed Java generated by accessibility patches."""
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if ca.exists():
        text = ca.read_text(encoding="utf-8", errors="replace")
        if "a11y-fork: OPTION_SELECT_MESSAGE handler" in text:
            start = text.index("a11y-fork: OPTION_SELECT_MESSAGE handler")
            end = text.find("case OPTION_RETRY", start)
            if end < 0:
                end = min(len(text), start + 5000)
            block = text[start:end]
            if block.count("try {") > block.count("catch (") + block.count("finally {"):
                raise RuntimeError("Malformed Select handler: unmatched try/catch in ChatActivity.java")

    cm = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if cm.exists():
        text = cm.read_text(encoding="utf-8", errors="replace")
        # Prevent the known numeric-ID accessibility regression for documents.
        if "a11y-fork: file description" in text and "access_hash" in text:
            raise RuntimeError("Document accessibility description still contains internal numeric identifiers")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found (clone DrKLO/Telegram as ./telegram)", file=sys.stderr)
        return 1
    print("Using scripts dir:", SCRIPTS.resolve())
    patch_app_name()
    install_a11y_config()
    patch_a11y_localization()
    patch_percent_localization()
    patch_radial_progress()
    patch_dialogcell_name_then_type()
    patch_hide_share_and_comment()
    patch_forward_menu_extras()
    # Menu order is guaranteed by patch_message_menu_order alone:
    # Links -> Bot Buttons -> Reactions -> Select (Select last).
    patch_longpress_message_menu()
    patch_reactions_as_menu()
    patch_message_menu_order()
    patch_links_menu()
    patch_voice_bitrate()
    patch_settings_menu()
    patch_recording_beep()
    patch_dialogcell_preview_muted_status()
    patch_message_time_and_solar()
    patch_chat_message_cell_float_coordinates()
    patch_hide_sponsor_channel()
    patch_ghost_mode()
    patch_bot_buttons_menu()
    patch_go_to_first_message()
    patch_file_description_spacing()
    patch_chat_message_solar_date()
    patch_chat_message_cell_accessibility_long_click()
    patch_stuck_together_bubbles_long_press()
    validate_generated_sources()
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
