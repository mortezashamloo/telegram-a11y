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
    solar_start=cfg.find("    public static String formatSolarDate(int unixSeconds) {")
    if solar_start >= 0:
        solar_end=cfg.find("    private static String toPersianDigits",solar_start)
        if solar_end > solar_start:
            solar_method="""    public static String formatSolarDate(int unixSeconds) {
        try {
            java.util.Calendar cal=java.util.Calendar.getInstance();
            cal.setTimeInMillis(((long) unixSeconds)*1000L);
            int gy=cal.get(java.util.Calendar.YEAR);
            int gm=cal.get(java.util.Calendar.MONTH)+1;
            int gd=cal.get(java.util.Calendar.DAY_OF_MONTH);
            int jy;
            if (gy > 1600) { jy=979; gy-=1600; } else { jy=0; gy-=621; }
            int[] gdm={0,31,59,90,120,151,181,212,243,273,304,334};
            int gy2=gm > 2 ? gy+1 : gy;
            int days=365*gy+(gy2+3)/4-(gy2+99)/100+(gy2+399)/400-80+gd+gdm[gm-1];
            jy+=33*(days/12053); days%=12053;
            jy+=4*(days/1461); days%=1461;
            if (days > 365) { jy+=(days-1)/365; days=(days-1)%365; }
            int jm=days < 186 ? 1+days/31 : 7+(days-186)/30;
            int jd=1+(days < 186 ? days%31 : (days-186)%30);
            String[] fa={"فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"};
            String[] en={"Farvardin","Ordibehesht","Khordad","Tir","Mordad","Shahrivar","Mehr","Aban","Azar","Dey","Bahman","Esfand"};
            boolean isFa="fa".equalsIgnoreCase(java.util.Locale.getDefault().getLanguage());
            String month=(isFa ? fa : en)[jm-1];
            if (isFa) {
                String value=String.format(java.util.Locale.US, "%d %s %d", jd, month, jy);
                return LocaleController.formatString(R.string.A11ySolarDate, toPersianDigits(value));
            }
            String value=String.format(java.util.Locale.US, "%d %s %d", jd, month, jy);
            return LocaleController.formatString(R.string.A11ySolarDate, value);
        } catch (Throwable ignore) { return ""; }
    }

"""
            cfg=cfg[:solar_start]+solar_method+cfg[solar_end:]
    dst.write_text(cfg,encoding="utf-8")
    print("A11yConfig.java installed + beep/Jalali defaults ON + locale-independent solar date")


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


def patch_forward_handler(t: str) -> str:
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE" in t:
        start = t.find("            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: OPTION_FORWARD_NO_QUOTE")
        end = t.find("            case OPTION_FORWARD: {", start)
        if start >= 0 and end >= 0:
            t = t[:start] + t[end:]

    normal = "            case OPTION_FORWARD: {"
    shared = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n                IS_FORWARD_NO_QUOTE = true;\n                // fall through to the normal Forward UI\n            case OPTION_FORWARD: {"
    if "case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote" not in t:
        if normal not in t:
            raise RuntimeError("normal OPTION_FORWARD case not found")
        t = t.replace(normal, shared, 1)

    marker = "            case OPTION_FORWARD_NO_QUOTE: // a11y-fork: forward without quote\n"
    saved_start = t.find(marker)
    if saved_start < 0:
        raise RuntimeError("forward no-quote case insertion failed")
    if "a11y-fork: forward to Saved Messages" not in t:
        saved = '''            case OPTION_FORWARD_TO_SAVED: { // a11y-fork: forward to Saved Messages
                if (selectedObject != null) {
                    try {
                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();
                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {
                            toSend.addAll(selectedObjectGroup.messages);
                        } else {
                            toSend.add(selectedObject);
                        }
                        IS_FORWARD_NO_QUOTE = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();
                        long savedId = getUserConfig().getClientUserId();
                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);
                        try {
                            if (getParentActivity() != null) {
                                getParentActivity().getWindow().getDecorView().announceForAccessibility("Forwarded to Saved Messages");
                            }
                        } catch (Throwable ignore) {}
                    } catch (Throwable e) {
                        FileLog.e(e);
                    }
                }
                selectedObject = null;
                selectedObjectToEditCaption = null;
                selectedObjectGroup = null;
                break;
            }
'''
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
    if "public static boolean IS_FORWARD_NO_QUOTE" not in t:
        anchor="protected TLRPC.Chat currentChat;"
        if anchor in t:
            t=t.replace(anchor,"public static boolean IS_FORWARD_NO_QUOTE = false;\n    "+anchor,1)
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



def patch_reactions_as_menu() -> None:
    """Put the emoji reactions row behind a "Reactions" menu item."""
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
    marker = "a11y-fork: recording-start beep-v5"
    if marker in t:
        print("MediaController recording beep v5 already patched")
        return
    needle = "try { org.telegram.messenger.A11yConfig.applyVoiceBitrateToNative(); } catch (Throwable ignore) {}"
    if needle not in t:
        print("WARN: MediaController record-start anchor not found (recording beep)")
        return
    replacement = needle + """
                    // a11y-fork: recording-start beep-v5
                    try {
                        if (org.telegram.messenger.A11yConfig.getRecordingBeep()) {
                            final android.media.ToneGenerator a11yBeepGen =
                                    new android.media.ToneGenerator(android.media.AudioManager.STREAM_ACCESSIBILITY, 90);
                            a11yBeepGen.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 140);
                            org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> {
                                try { a11yBeepGen.stopTone(); } catch (Throwable ignore) {}
                                try { a11yBeepGen.release(); } catch (Throwable ignore) {}
                            }, 220);
                        }
                    } catch (Throwable e) {
                        try {
                            final android.media.ToneGenerator a11yBeepGen2 =
                                    new android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC, 90);
                            a11yBeepGen2.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 140);
                            org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> {
                                try { a11yBeepGen2.stopTone(); } catch (Throwable ignore) {}
                                try { a11yBeepGen2.release(); } catch (Throwable ignore) {}
                            }, 220);
                        } catch (Throwable e2) {
                            org.telegram.messenger.FileLog.e(e2);
                        }
                    }"""
    t = t.replace(needle, replacement, 1)
    mc.write_text(t, encoding="utf-8")
    print("MediaController recording-start beep v5 (ToneGenerator) OK")



def patch_dialogcell_preview_muted_status() -> None:
    """Remove Muted, read status, bump preview to 300 chars, and preserve Telegram native time."""
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (preview/muted/status)")
        return
    t = dc.read_text(encoding="utf-8")

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

    native_block = re.compile(
        r'\n\s*String date = LocaleController\.formatDateAudio\(lastDate, true\);\n'
        r'\s*if \(message\.isOut\(\)\) \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrSentDate", R\.string\.AccDescrSentDate, date\)\);\n'
        r'\s*\} else \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrReceivedDate", R\.string\.AccDescrReceivedDate, date\)\);\n'
        r'\s*\}\n'
        r'\s*sb\.append\("\. "\);',
        re.MULTILINE
    )
    match = native_block.search(t)
    if match:
        t = t[:match.start()] + "\n" + t[match.end():]
    marker_re = re.compile(
        r'\n\s*// a11y-fork: official-time-solar-date-v4\n'
        r'\s*String date = LocaleController\.formatDateAudio\(lastDate, true\);[\s\S]*?'
        r'\s*sb\.append\("\. "\);', re.MULTILINE
    )
    t = marker_re.sub("", t, count=1)
    end_anchor = '        event.setContentDescription(sb);'
    if end_anchor not in t:
        end_anchor = '        setContentDescription(sb);'
    if end_anchor in t:
        native_tail = (
            '        // a11y-fork-v6: official Telegram send/receive date LAST\n'
            '        String a11yDate = LocaleController.formatDateAudio(lastDate, true);\n'
            '        try {\n'
            '            if (org.telegram.messenger.A11yConfig.getSolarCalendar()) {\n'
            '                String solarDate = org.telegram.messenger.A11yConfig.formatSolarDate(lastDate);\n'
            '                if (solarDate != null && solarDate.length() > 0) {\n'
            '                    a11yDate = solarDate;\n'
            '                }\n'
            '            }\n'
            '        } catch (Throwable ignore) {\n'
            '        }\n'
            '        if (message.isOut()) {\n'
            '            sb.append(LocaleController.formatString("AccDescrSentDate", R.string.AccDescrSentDate, a11yDate));\n'
            '        } else {\n'
            '            sb.append(LocaleController.formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, a11yDate));\n'
            '        }\n'
            '        sb.append(". ");\n'
        )
        t=t.replace(end_anchor, native_tail+end_anchor, 1)
    else:
        print("WARN: DialogCell content-description end anchor not found")

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted/status/preview-300 OK; official Telegram time format preserved")


def patch_message_time_and_solar() -> None:
    """Keep Telegram's native sent/received date+time announcement."""
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (time/Jalali)")
        return
    t = dc.read_text(encoding="utf-8")
    marker = "a11y-fork: official-time-solar-date-v4"
    if marker in t:
        print("DialogCell official Telegram time + solar-date already patched")
        return

    old_custom = ("        // a11y-fork: explicit separator before time\n"
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
                  "        } catch (Throwable ignore) {}")
    if old_custom in t:
        t=t.replace(old_custom, "        // a11y-fork: official-time-solar-date-v4\n", 1)

    native = ("        String date = LocaleController.formatDateAudio(lastDate, true);\n"
              "        if (message.isOut()) {\n"
              "            sb.append(LocaleController.formatString(\"AccDescrSentDate\", R.string.AccDescrSentDate, date));\n"
              "        } else {\n"
              "            sb.append(LocaleController.formatString(\"AccDescrReceivedDate\", R.string.AccDescrReceivedDate, date));\n"
              "        }\n"
              "        sb.append(\". \");")
    native_repl = ("        // a11y-fork: official-time-solar-date-v4\n"
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
                   "        sb.append(\". \");")
    if native in t:
        t=t.replace(native,native_repl,1)
    else:
        print("WARN: Telegram native sent/received date block not found")
        return
    dc.write_text(t,encoding="utf-8")
    print("DialogCell official Telegram time format + optional Solar date OK")


def patch_chat_message_cell_float_coordinates() -> None:
    """Fix float vs int coordinates for TalkBack long-press."""
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
    """Hide proxy sponsor/promo channel from chat list when enabled."""
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
    """Ghost Mode -- skip markDialogAsRead when enabled."""
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



def patch_dialogcell_preview_muted_status() -> None:
    """Remove Muted, read status, bump preview to 300 chars, and preserve Telegram native time."""
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (preview/muted/status)")
        return
    t = dc.read_text(encoding="utf-8")

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

    native_block = re.compile(
        r'\n\s*String date = LocaleController\.formatDateAudio\(lastDate, true\);\n'
        r'\s*if \(message\.isOut\(\)\) \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrSentDate", R\.string\.AccDescrSentDate, date\)\);\n'
        r'\s*\} else \{\n'
        r'\s*sb\.append\(LocaleController\.formatString\("AccDescrReceivedDate", R\.string\.AccDescrReceivedDate, date\)\);\n'
        r'\s*\}\n'
        r'\s*sb\.append\("\. "\);',
        re.MULTILINE
    )
    match = native_block.search(t)
    if match:
        t = t[:match.start()] + "\n" + t[match.end():]
    marker_re = re.compile(
        r'\n\s*// a11y-fork: official-time-solar-date-v4\n'
        r'\s*String date = LocaleController\.formatDateAudio\(lastDate, true\);[\s\S]*?'
        r'\s*sb\.append\("\. "\);', re.MULTILINE
    )
    t = marker_re.sub("", t, count=1)
    end_anchor = '        event.setContentDescription(sb);'
    if end_anchor not in t:
        end_anchor = '        setContentDescription(sb);'
    if end_anchor in t:
        native_tail = (
            '        // a11y-fork-v6: official Telegram send/receive date LAST\n'
            '        String a11yDate = LocaleController.formatDateAudio(lastDate, true);\n'
            '        try {\n'
            '            if (org.telegram.messenger.A11yConfig.getSolarCalendar()) {\n'
            '                String solarDate = org.telegram.messenger.A11yConfig.formatSolarDate(lastDate);\n'
            '                if (solarDate != null && solarDate.length() > 0) {\n'
            '                    a11yDate = solarDate;\n'
            '                }\n'
            '            }\n'
            '        } catch (Throwable ignore) {\n'
            '        }\n'
            '        if (message.isOut()) {\n'
            '            sb.append(LocaleController.formatString("AccDescrSentDate", R.string.AccDescrSentDate, a11yDate));\n'
            '        } else {\n'
            '            sb.append(LocaleController.formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, a11yDate));\n'
            '        }\n'
            '        sb.append(". ");\n'
        )
        t=t.replace(end_anchor, native_tail+end_anchor, 1)
    else:
        print("WARN: DialogCell content-description end anchor not found")

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted/status/preview-300 OK; official Telegram time format preserved")


def patch_message_time_and_solar() -> None:
    """Keep Telegram's native sent/received date+time announcement."""
    dc = JAVA / "org/telegram/ui/Cells/DialogCell.java"
    if not dc.exists():
        print("WARN: DialogCell missing (time/Jalali)")
        return
    t = dc.read_text(encoding="utf-8")
    marker = "a11y-fork: official-time-solar-date-v4"
    if marker in t:
        print("DialogCell official Telegram time + solar-date already patched")
        return

    old_custom = ("        // a11y-fork: explicit separator before time\n"
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
                  "        } catch (Throwable ignore) {}")
    if old_custom in t:
        t=t.replace(old_custom, "        // a11y-fork: official-time-solar-date-v4\n", 1)

    native = ("        String date = LocaleController.formatDateAudio(lastDate, true);\n"
              "        if (message.isOut()) {\n"
              "            sb.append(LocaleController.formatString(\"AccDescrSentDate\", R.string.AccDescrSentDate, date));\n"
              "        } else {\n"
              "            sb.append(LocaleController.formatString(\"AccDescrReceivedDate\", R.string.AccDescrReceivedDate, date));\n"
              "        }\n"
              "        sb.append(\". \");")
    native_repl = ("        // a11y-fork: official-time-solar-date-v4\n"
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
                   "        sb.append(\". \");")
    if native in t:
        t=t.replace(native,native_repl,1)
    else:
        print("WARN: Telegram native sent/received date block not found")
        return
    dc.write_text(t,encoding="utf-8")
    print("DialogCell official Telegram time format + optional Solar date OK")


def patch_chat_message_cell_float_coordinates() -> None:
    """Fix float vs int coordinates for TalkBack long-press."""
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
    """Hide proxy sponsor/promo channel from chat list when enabled."""
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
    """Ghost Mode -- skip markDialogAsRead when enabled."""
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
    """Fold scattered inline bot buttons into a single "Bot Buttons" menu item."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not cmc.exists() or not ca.exists():
        print("WARN: ChatMessageCell/ChatActivity missing (bot buttons menu)")
        return

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

    t2 = ca.read_text(encoding="utf-8")
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
        if anchor in t: t=t.replace(anchor, helper+anchor,1)

    if "a11y-fork: go-to-first-message menu" not in t:
        anchor = """            if (currentChat != null && !isTopic) {
                viewAsTopics = headerItem.lazilyAddSubItem(view_as_topics, R.drawable.msg_topics, LocaleController.getString(R.string.TopicViewAsTopics));
            }"""
        insert = anchor + """
            if (currentChat != null && (ChatObject.isChannel(currentChat) || currentChat.megagroup) && !isTopic) {
                // a11y-fork: go-to-first-message menu
                headerItem.lazilyAddSubItem(OPTION_GO_TO_FIRST_MESSAGE, R.drawable.msg_search, LocaleController.getString(R.string.A11yGoToFirstMessage));
            }"""
        if anchor in t: t=t.replace(anchor,insert,1)

    if "a11y-fork: go-to-first-message handler" not in t:
        anchor = "                } else if (id == view_as_topics) {"
        branch = "                } else if (id == OPTION_GO_TO_FIRST_MESSAGE) { // a11y-fork: go-to-first-message handler\n                    accessibilityGoToFirstMessage();\n                } else if (id == view_as_topics) {"
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
    """TalkBack: announce document files once as localized 'file <filename>'."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (file description spacing)")
        return
    t = cmc.read_text(encoding="utf-8")

    custom = re.compile(
        r'\n\s*// a11y-fork: real document filename\n'
        r'\s*String a11yDocumentName = FileLoader\.getDocumentFileName\(documentAttach\);\n'
        r'\s*if \(!TextUtils\.isEmpty\(a11yDocumentName\)\) \{[\s\S]*?'
        r'\s*\}\n\s*\}', re.MULTILINE
    )
    t, n = custom.subn('', t, count=1)
    if n:
        print("ChatMessageCell old duplicate filename block removed")

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
        value = "file %s. "
        rt2, n = re.subn(
            r'(<string\s+name="AccDescrDocumentType">)[^<]*(</string>)',
            rf'\1{value}\2', rt, count=1
        )
        if n:
            path.write_text(rt2, encoding="utf-8")
            print(f"{rel} AccDescrDocumentType = file %s")
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell document filename will be announced once")


def patch_chat_message_solar_date() -> None:
    """Use Solar Hijri for the ChatMessageCell accessibility date."""
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (chat solar date)")
        return
    t = cmc.read_text(encoding="utf-8")
    marker = "a11y-fork-v6: chat solar date"
    if marker in t:
        print("ChatMessageCell solar date already patched")
        return

    old_sent = (
        '                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));'
    )
    new_sent = (
        '                                sb.append(formatString("AccDescrSentDate", R.string.AccDescrSentDate, getString("TodayAt", R.string.TodayAt) + " " + (org.telegram.messenger.A11yConfig.getSolarCalendar() ? org.telegram.messenger.A11yConfig.formatSolarDate(currentMessageObject.messageOwner.date) + " " + LocaleController.formatDateAudio(currentMessageObject.messageOwner.date, true).replaceFirst("^.*?([0-9۰-۹]{1,2}:[0-9۰-۹]{2}).*$", "$1") : currentTimeString)));'
    )
    old_recv = (
        '                        sb.append(formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, getString("TodayAt", R.string.TodayAt) + " " + currentTimeString));'
    )
    new_recv = (
        '                        sb.append(formatString("AccDescrReceivedDate", R.string.AccDescrReceivedDate, getString("TodayAt", R.string.TodayAt) + " " + (org.telegram.messenger.A11yConfig.getSolarCalendar() ? org.telegram.messenger.A11yConfig.formatSolarDate(currentMessageObject.messageOwner.date) + " " + LocaleController.formatDateAudio(currentMessageObject.messageOwner.date, true).replaceFirst("^.*?([0-9۰-۹]{1,2}:[0-9۰-۹]{2}).*$", "$1") : currentTimeString)));'
    )
    changed = False
    if old_sent in t:
        t=t.replace(old_sent,new_sent,1); changed=True
    if old_recv in t:
        t=t.replace(old_recv,new_recv,1); changed=True
    if changed:
        t=t.replace('    private class MessageAccessibilityNodeProvider', '    // '+marker+'\n    private class MessageAccessibilityNodeProvider', 1)
        cmc.write_text(t,encoding="utf-8")
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
    """Fix long-press on grouped/bubble-clustered messages."""
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
    patch_longpress_message_menu()
    patch_reactions_as_menu()
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
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())