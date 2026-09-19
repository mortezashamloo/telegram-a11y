#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply accessibility patches to cloned Telegram tree (cwd parent of telegram/)."""
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
                            try {
                                parent.announceForAccessibility(org.telegram.messenger.LocaleController.formatString(org.telegram.messenger.R.string.A11yPercentAnnounce, step));
                            } catch (Throwable ignore3) {
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
            "                    items.add(LocaleController.getString(R.string.A11yForwardNoQuote));\n"
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
    if "a11y-fork: OPTION_FORWARD_NO_QUOTE" not in t:
        old_case = "            case OPTION_FORWARD: {"
        new_case = (
            f"            case {OPTION_FORWARD_NO_QUOTE}: {{ // a11y-fork: OPTION_FORWARD_NO_QUOTE\n"
            "                if (getMessagesController().isFrozen()) {\n"
            "                    AccountFrozenAlert.show(currentAccount);\n"
            "                    selectedObject = null;\n"
            "                    selectedObjectToEditCaption = null;\n"
            "                    selectedObjectGroup = null;\n"
            "                    return;\n"
            "                }\n"
            "                IS_FORWARD_NO_QUOTE = true;\n"
            "                forwardingMessage = selectedObject;\n"
            "                forwardingMessageGroup = selectedObjectGroup;\n"
            "                Bundle a11yFnqArgs = new Bundle();\n"
            "                a11yFnqArgs.putBoolean(\"onlySelect\", true);\n"
            "                a11yFnqArgs.putInt(\"dialogsType\", DialogsActivity.DIALOGS_TYPE_FORWARD);\n"
            "                a11yFnqArgs.putInt(\"messagesCount\", 1);\n"
            "                a11yFnqArgs.putInt(\"hasPoll\", forwardingMessage.isTodo() ? 3 : forwardingMessage.isPoll() ? (forwardingMessage.isPublicPoll() ? 2 : 1) : 0);\n"
            "                if (ChatObject.isMonoForum(currentChat) && ChatObject.canManageMonoForum(currentAccount, currentChat) && currentChat.linked_monoforum_id != 0) {\n"
            "                    a11yFnqArgs.putLong(\"forward_into_channel\", -currentChat.linked_monoforum_id);\n"
            "                }\n"
            "                a11yFnqArgs.putBoolean(\"hasInvoice\", forwardingMessage.isInvoice());\n"
            "                a11yFnqArgs.putBoolean(\"canSelectTopics\", true);\n"
            "                DialogsActivity a11yFnqFragment = new DialogsActivity(a11yFnqArgs);\n"
            "                a11yFnqFragment.setDelegate(this);\n"
            "                presentFragment(a11yFnqFragment);\n"
            "                break;\n"
            "            }\n"
            f"            case {OPTION_FORWARD_TO_SAVED}: {{ // a11y-fork: forward to Saved Messages\n"
            "                if (selectedObject != null) {\n"
            "                    try {\n"
            "                        java.util.ArrayList<MessageObject> toSend = new java.util.ArrayList<>();\n"
            "                        if (selectedObjectGroup != null && selectedObjectGroup.messages != null) {\n"
            "                            toSend.addAll(selectedObjectGroup.messages);\n"
            "                        } else {\n"
            "                            toSend.add(selectedObject);\n"
            "                        }\n"
            "                        long savedId = getUserConfig().getClientUserId();\n"
            "                        boolean a11ySavedNoQuote = org.telegram.messenger.A11yConfig.getForwardSavedNoQuote();\n"
            "                        if (a11ySavedNoQuote) {\n"
            "                            IS_FORWARD_NO_QUOTE = true;\n"
            "                        }\n"
            "                        getSendMessagesHelper().sendMessage(toSend, savedId, false, false, true, 0, 0);\n"
            "                        if (a11ySavedNoQuote) {\n"
            "                            IS_FORWARD_NO_QUOTE = false;\n"
            "                        }\n"
            "                        try {\n"
            "                            if (getParentActivity() != null) {\n"
            "                                getParentActivity().getWindow().getDecorView().announceForAccessibility(LocaleController.getString(R.string.A11yForwardedToSaved));\n"
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
            "            case OPTION_FORWARD: {"
        )
        if old_case in t:
            t = t.replace(old_case, new_case, 1)
            print("Forward option handlers OK")
        else:
            print("WARN: OPTION_FORWARD case not found")
    ca.write_text(t, encoding="utf-8")


def patch_reactions_as_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (reactions menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: reactions menu item" in t:
        print("ChatActivity reactions-menu already patched")
        return

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: reactions menu item\n"
        "        accessibilityReactionsToggleIndex = -1;\n"
        "        try {\n"
        "            if (message != null && message.canSetReaction() && !items.contains(LocaleController.getString(R.string.Reactions))) {\n"
        "                items.add(LocaleController.getString(R.string.Reactions));\n"
        "                icons.add(R.drawable.msg_reactions2);\n"
        f"                options.add({OPTION_REACTIONS_MENU});\n"
        "                accessibilityReactionsToggleIndex = items.size() - 1;\n"
        "            }\n"
        "        } catch (Throwable a11yReactErr) {\n"
        "            FileLog.e(a11yReactErr);\n"
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
        "                    if (scrimPopupWindowItems != null) {\n"
        "                        final ReactionsContainerLayout reactionsLayoutForToggle = reactionsLayout;\n"
        "                        final String reactionsLabel = LocaleController.getString(R.string.Reactions);\n"
        "                        for (int a11yRi = 0; a11yRi < scrimPopupWindowItems.length; a11yRi++) {\n"
        "                            final ActionBarMenuSubItem a11yRItem = scrimPopupWindowItems[a11yRi];\n"
        "                            if (a11yRItem == null || a11yRItem.getTextView() == null) continue;\n"
        "                            CharSequence a11yRText = a11yRItem.getTextView().getText();\n"
        "                            if (a11yRText != null && reactionsLabel.contentEquals(a11yRText)) {\n"
        "                                a11yRItem.setOnClickListener(reactionsToggleView -> {\n"
        "                                    boolean show = reactionsLayoutForToggle.getVisibility() != View.VISIBLE;\n"
        "                                    reactionsLayoutForToggle.setVisibility(show ? View.VISIBLE : View.GONE);\n"
        "                                });\n"
        "                            }\n"
        "                        }\n"
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
            f"        try {{\n"
            f"            if (!actionBar.isActionModeShowed() && message != null && message.contentType == 0 && !message.isSponsored()) {{\n"
            f"                items.add(LocaleController.getString(R.string.Select));\n"
            f"                options.add({OPTION_SELECT_MESSAGE});\n"
            f"                icons.add(R.drawable.msg_forward);\n"
            f"            }}\n"
            f"        }} catch (Throwable a11ySelectErr) {{\n"
            f"            FileLog.e(a11ySelectErr);\n"
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
            f"                                getParentActivity().getWindow().getDecorView().announceForAccessibility(LocaleController.getString(R.string.A11ySelectedAnnounce));\n"
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
            r"try { org.telegram.messenger.A11yConfig.applyVoiceBitrateToNative(); } catch (Throwable ignore) {}\n                    "
            r"// a11y-fork: optional beep before record\n"
            r"try { if (org.telegram.messenger.A11yConfig.getBeepOnRecord()) { "
            r"android.media.ToneGenerator tg = new android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC, 80); "
            r"tg.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 120); "
            r"android.os.Handler h = new android.os.Handler(android.os.Looper.getMainLooper()); "
            r"h.postDelayed(() -> { try { tg.release(); } catch (Throwable ig) {} }, 250); "
            r"} } catch (Throwable ignore) {}\n                    "
            r"\1",
            t,
        )
        if n:
            t = t2
            print(f"MediaController apply voice + beep before record x{n}")
    mc.write_text(t, encoding="utf-8")


def patch_settings_menu() -> None:
    sa = JAVA / "org/telegram/ui/SettingsActivity.java"
    if not sa.exists():
        print("WARN: SettingsActivity missing")
        return
    t = sa.read_text(encoding="utf-8")
    needle = 'items.add(SettingCell.Factory.of(10, IconBackgroundColors.PURPLE.top, IconBackgroundColors.PURPLE.bottom, R.drawable.settings_language, getString(R.string.SettingsLanguage), LocaleController.getCurrentLanguageName()));'
    insert = needle + "\n        // a11y-fork: Accessible settings entry\n        items.add(SettingCell.Factory.of(100, IconBackgroundColors.GREEN.top, IconBackgroundColors.GREEN.bottom, R.drawable.settings_privacy, getString(R.string.A11yAccessibleSettingsTitle), getString(R.string.A11yAccessibleSettingsSubtitle)));"
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
        "        // a11y-fork: muted/status/preview-300\n"
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
            "        if (sb.length() > 0 && sb.charAt(sb.length() - 1) != ' ') {\n"
            "            sb.append(\". \");\n"
            "        }\n"
            "        String a11yClockTime = LocaleController.formatDateAudio(lastDate, true);\n"
            "        sb.append(message.isOut() ? LocaleController.getString(R.string.A11ySentPrefix) : LocaleController.getString(R.string.A11yReceivePrefix));\n"
            "        sb.append(a11yClockTime);\n"
            "        sb.append(\". \");\n"
            "        event.setContentDescription(sb);\n"
            "        setContentDescription(sb);\n"
            "    }\n"
            "\n"
            "    private MessageObject getCaptionMessage() {"
        )
        if old_tail not in t:
            print("WARN: DialogCell tail anchor not found")
        else:
            t = t.replace(old_tail, new_tail, 1)

    dc.write_text(t, encoding="utf-8")
    print("DialogCell muted removed / status announce / preview-300 / time-last OK")


def patch_hide_sponsor_channel() -> None:
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
        print("WARN: DialogsActivity onResume anchor not found")
        return
    t = t.replace(old, new, 1)
    da.write_text(t, encoding="utf-8")
    print("DialogsActivity hide-sponsor-channel OK")


def patch_ghost_mode() -> None:
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
        print("WARN: ChatActivity markDialogAsRead call sites not found")
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
            "            // a11y-fork: bot buttons menu\n"
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
    if "a11y-fork: bot buttons menu" in t2:
        print("ChatActivity bot-buttons-menu already patched")
        return

    old_item = (
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    new_item = (
        "        // a11y-fork: bot buttons menu\n"
        "        try {\n"
        "            if (message != null && message.hasInlineBotButtons()) {\n"
        "                items.add(LocaleController.getString(R.string.A11yBotButtons));\n"
        f"                options.add({OPTION_BOT_BUTTONS_MENU});\n"
        "                icons.add(R.drawable.msg_viewreplies);\n"
        "            }\n"
        "        } catch (Throwable a11yBotBtnErr) {\n"
        "            FileLog.e(a11yBotBtnErr);\n"
        "        }\n"
        "\n"
        "        if (message.isSponsored() && !getUserConfig().isPremium() "
        "&& !getMessagesController().premiumFeaturesBlocked() && !message.sponsoredCanReport) {\n"
    )
    if old_item not in t2:
        print("WARN: ChatActivity sponsored-item anchor not found")
        return
    t2 = t2.replace(old_item, new_item, 1)

    old_case = "            case OPTION_RETRY: {\n"
    new_case = (
        f"            case {OPTION_BOT_BUTTONS_MENU}: {{ // a11y-fork: OPTION_BOT_BUTTONS_MENU\n"
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
        "                                CharSequence label = !TextUtils.isEmpty(btn.text) ? btn.text : (LocaleController.getString(R.string.A11yBotButtons) + \" \" + (labels.size() + 1));\n"
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
        print("WARN: ChatActivity OPTION_RETRY case anchor not found")
        return
    t2 = t2.replace(old_case, new_case, 1)

    ca.write_text(t2, encoding="utf-8")
    print("ChatActivity bot-buttons-menu item+handler OK")
    def patch_add_a11y_strings() -> None:
    strings = {
        "A11yBotButtons": ("Bot Buttons", "\u062f\u06a9\u0645\u0647\u200c\u0647\u0627\u06cc \u0631\u0628\u0627\u062a"),
        "A11yForwardNoQuote": ("Forward without quote", "\u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0628\u062f\u0648\u0646 \u0646\u0642\u0644\u200c\u0642\u0648\u0644"),
        "A11yForwardToSaved": ("Forward to Saved Messages", "\u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647"),
        "A11yForwardedToSaved": ("Forwarded to Saved Messages", "\u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647 \u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0634\u062f"),
        "A11ySelectedAnnounce": ("Selected", "\u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f"),
        "A11ySentPrefix": ("sent ", "\u0627\u0631\u0633\u0627\u0644 "),
        "A11yReceivePrefix": ("receive ", "\u062f\u0631\u06cc\u0627\u0641\u062a "),
        "A11yAccessibleSettingsTitle": ("Accessible settings", "\u062a\u0646\u0637\u06cc\u0645\u0627\u062a \u062f\u0633\u062a\u0631\u0633\u200c\u067e\u0630\u06cc\u0631\u06cc"),
        "A11yAccessibleSettingsSubtitle": ("Progress & voice quality", "\u067e\u06cc\u0634\u0631\u0641\u062a \u0648 \u06a9\u06cc\u0641\u06cc\u062a \u0635\u062f\u0627"),
        "A11yProgressAnnounceLabel": ("Progress announce: %1$s", "\u0627\u0639\u0644\u0627\u0645 \u067e\u06cc\u0634\u0631\u0641\u062a: %1$s"),
        "A11yProgressStepPickerTitle": ("Progress announce step", "\u0641\u0627\u0635\u0644\u0647\u0654 \u0627\u0639\u0644\u0627\u0645 \u067e\u06cc\u0634\u0631\u0641\u062a"),
        "A11yVoiceQualityLabel": ("Voice quality: %1$s", "\u06a9\u06cc\u0641\u06cc\u062a \u0635\u062f\u0627: %1$s"),
        "A11yVoiceQualityPickerTitle": ("Voice message quality", "\u06a9\u06cc\u0641\u06cc\u062a \u067e\u06cc\u0627\u0645 \u0635\u0648\u062a\u06cc"),
        "A11yHideSponsorLabel": ("Hide sponsor channel: %1$s", "\u0645\u062e\u0641\u06cc\u200c\u06a9\u0631\u062f\u0646 \u06a9\u0627\u0646\u0627\u0644 \u0627\u0633\u067e\u0627\u0646\u0633\u0631: %1$s"),
        "A11yGhostModeLabel": ("Ghost mode (hide read receipts): %1$s", "\u062d\u0627\u0644\u062a \u0631\u0648\u062d (\u0645\u062e\u0641\u06cc\u200c\u06a9\u0631\u062f\u0646 \u062f\u06cc\u062f\u0647\u200c\u0634\u062f\u0646 \u067e\u06cc\u0627\u0645): %1$s"),
        "A11yStatusPreviewLabel": ("Announce contact status in chat list: %1$s", "\u0627\u0639\u0644\u0627\u0645 \u0648\u0636\u0639\u06cc\u062a \u0645\u062e\u0627\u0637\u0628 \u062f\u0631 \u0641\u0647\u0631\u0633\u062a \u06af\u0641\u062a\u06af\u0648\u0647\u0627: %1$s"),
        "A11yOn": ("On", "\u0631\u0648\u0634\u0646"),
        "A11yOff": ("Off", "\u062e\u0627\u0645\u0648\u0634"),
        "A11ySponsorHidden": ("Sponsor channel hidden", "\u06a9\u0627\u0646\u0627\u0644 \u0627\u0633\u067e\u0627\u0646\u0633\u0631 \u0645\u062e\u0641\u06cc \u0634\u062f"),
        "A11ySponsorShown": ("Sponsor channel shown", "\u06a9\u0627\u0646\u0627\u0644 \u0627\u0633\u067e\u0627\u0646\u0633\u0631 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0634\u062f"),
        "A11yGhostOn": ("Ghost mode on", "\u062d\u0627\u0644\u062a \u0631\u0648\u062d \u0631\u0648\u0634\u0646 \u0634\u062f"),
        "A11yGhostOff": ("Ghost mode off", "\u062d\u0627\u0644\u062a \u0631\u0648\u062d \u062e\u0627\u0645\u0648\u0634 \u0634\u062f"),
        "A11yStatusOn": ("Contact status announcements on", "\u0627\u0639\u0644\u0627\u0645 \u0648\u0636\u0639\u06cc\u062a \u0645\u062e\u0627\u0637\u0628 \u0631\u0648\u0634\u0646 \u0634\u062f"),
        "A11yStatusOff": ("Contact status announcements off", "\u0627\u0639\u0644\u0627\u0645 \u0648\u0636\u0639\u06cc\u062a \u0645\u062e\u0627\u0637\u0628 \u062e\u0627\u0645\u0648\u0634 \u0634\u062f"),
        "A11yVoiceLow": ("Low", "\u06a9\u0645"),
        "A11yVoiceMedium": ("Medium", "\u0645\u062a\u0648\u0633\u0637"),
        "A11yVoiceHigh": ("High", "\u0632\u06cc\u0627\u062f"),
        "A11yProgressStepLabel": ("%1$d%%", "%1$d\u066a"),
        "A11yCancel": ("Cancel", "\u0644\u063a\u0648"),
        "A11yGoToFirstMessage": ("Go to first message", "\u0631\u0641\u062a\u0646 \u0628\u0647 \u0627\u0648\u0644\u06cc\u0646 \u067e\u06cc\u0627\u0645"),
        "A11yFwdSavedNoQuoteLabel": ("Forward to Saved Messages with no quote: %1$s", "\u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647 \u0628\u062f\u0648\u0646 \u0646\u0642\u0644\u200c\u0642\u0648\u0644: %1$s"),
        "A11yFwdSavedNoQuoteOn": ("Forward to Saved Messages with no quote on", "\u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0628\u062f\u0648\u0646 \u0646\u0642\u0644\u200c\u0642\u0648\u0644 \u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647 \u0631\u0648\u0634\u0646 \u0634\u062f"),
        "A11yFwdSavedNoQuoteOff": ("Forward to Saved Messages with no quote off", "\u0641\u0648\u0631\u0648\u0627\u0631\u062f \u0628\u062f\u0648\u0646 \u0646\u0642\u0644\u200c\u0642\u0648\u0644 \u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647 \u062e\u0627\u0645\u0648\u0634 \u0634\u062f"),
        "A11yBeepOnRecordLabel": ("Beep on voice record: %1$s", "\u0628\u0648\u0642 \u0647\u0646\u06af\u0627\u0645 \u0636\u0628\u0637 \u0648\u06cc\u0633: %1$s"),
        "A11yBeepOnRecordOn": ("Beep on voice record on", "\u0628\u0648\u0642 \u0647\u0646\u06af\u0627\u0645 \u0636\u0628\u0637 \u0648\u06cc\u0633 \u0631\u0648\u0634\u0646 \u0634\u062f"),
        "A11yBeepOnRecordOff": ("Beep on voice record off", "\u0628\u0648\u0642 \u0647\u0646\u06af\u0627\u0645 \u0636\u0628\u0637 \u0648\u06cc\u0633 \u062e\u0627\u0645\u0648\u0634 \u0634\u062f"),
        "A11yPercentAnnounce": ("%1$d percent", "%1$d \u062f\u0631\u0635\u062f"),
    }

    def ensure_in_file(path: Path, lang_index: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            t = path.read_text(encoding="utf-8")
        else:
            t = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'
        added = 0
        for name, values in strings.items():
            marker = f'name="{name}"'
            if marker in t:
                continue
            value = values[lang_index].replace("&", "&amp;").replace("'", "\\'").replace('"', "&quot;")
            if values[lang_index] != values[lang_index].strip():
                value = f'"{value}"'
            entry = f'    <string name="{name}">{value}</string>\n'
            t = t.replace("</resources>", entry + "</resources>", 1)
            added += 1
        path.write_text(t, encoding="utf-8")
        print(f"{path}: {added} string(s) added")

    en_path = ROOT / "src/main/res/values/strings.xml"
    fa_path = ROOT / "src/main/res/values-fa/strings.xml"
    if not en_path.exists():
        print("WARN: values/strings.xml missing")
        return
    ensure_in_file(en_path, 0)
    ensure_in_file(fa_path, 1)


def patch_go_to_first_message() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (go to first message)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: go to first message" in t:
        print("ChatActivity go-to-first-message already patched")
        return

    old_const = "    private final static int translate = 62;\n"
    new_const = (
        "    private final static int translate = 62;\n"
        "    private final static int a11y_go_to_first_message = 210; // a11y-fork: go to first message\n"
    )
    if old_const not in t:
        print("WARN: ChatActivity translate-const anchor not found (go to first message)")
        return
    t = t.replace(old_const, new_const, 1)

    old_add = (
        "            headerItem.setContentDescription(LocaleController.getString(R.string.AccDescrMoreOptions));\n"
    )
    new_add = (
        "            headerItem.setContentDescription(LocaleController.getString(R.string.AccDescrMoreOptions));\n"
        "\n"
        "            // a11y-fork: go to first message\n"
        "            headerItem.lazilyAddSubItem(a11y_go_to_first_message, R.drawable.msg_go_up, LocaleController.getString(R.string.A11yGoToFirstMessage));\n"
    )
    if old_add not in t:
        print("WARN: ChatActivity headerItem-setup anchor not found (go to first message)")
        return
    t = t.replace(old_add, new_add)

    old_click = (
        "                } else if (id == search) {\n"
        "                    openSearchWithText(isSupportedTags() ? \"\" : null);\n"
    )
    new_click = (
        "                } else if (id == search) {\n"
        "                    openSearchWithText(isSupportedTags() ? \"\" : null);\n"
        "                } else if (id == a11y_go_to_first_message) {\n"
        "                    // a11y-fork: go to first message\n"
        "                    try {\n"
        "                        scrollToMessageId(1, 0, false, 0, true, 0);\n"
        "                    } catch (Throwable e) {\n"
        "                        FileLog.e(e);\n"
        "                    }\n"
    )
    if old_click not in t:
        print("WARN: ChatActivity search-click anchor not found (go to first message)")
        return
    t = t.replace(old_click, new_click, 1)

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity go-to-first-message OK")


def patch_leave_comment_menu() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (leave comment menu)")
        return
    t = ca.read_text(encoding="utf-8")
    if "a11y-fork: leave comment menu" in t:
        print("ChatActivity leave-comment-menu already patched")
        return

    old_const = "    private final static int a11y_go_to_first_message = 210; // a11y-fork: go to first message\n"
    new_const = (
        "    private final static int a11y_go_to_first_message = 210; // a11y-fork: go to first message\n"
        f"    private final static int OPTION_LEAVE_COMMENT = {OPTION_LEAVE_COMMENT}; // a11y-fork: leave comment menu\n"
    )
    if old_const not in t:
        print("WARN: ChatActivity const anchor not found (leave comment menu)")
        return
    t = t.replace(old_const, new_const, 1)

    old_item = (
        "        // a11y-fork: reactions menu item\n"
        "        accessibilityReactionsToggleIndex = -1;\n"
    )
    new_item = (
        "        // a11y-fork: leave comment menu\n"
        "        try {\n"
        "            if (message != null && message.messageOwner != null && message.messageOwner.replies != null) {\n"
        "                int a11yRepliesCount = message.getRepliesCount();\n"
        "                items.add(a11yRepliesCount > 0 ? LocaleController.formatPluralString(\"ViewReplies\", a11yRepliesCount) : LocaleController.getString(R.string.LeaveAComment));\n"
        "                icons.add(R.drawable.msg_viewreplies);\n"
        f"                options.add({OPTION_LEAVE_COMMENT});\n"
        "            }\n"
        "        } catch (Throwable a11yLcErr) {\n"
        "            FileLog.e(a11yLcErr);\n"
        "        }\n"
        "\n"
        "        // a11y-fork: reactions menu item\n"
        "        accessibilityReactionsToggleIndex = -1;\n"
    )
    if old_item not in t:
        print("WARN: ChatActivity reactions-item anchor not found (leave comment menu)")
        return
    t = t.replace(old_item, new_item, 1)

    old_case = f"            case {OPTION_BOT_BUTTONS_MENU}: {{ // a11y-fork: OPTION_BOT_BUTTONS_MENU\n"
    new_case = (
        "            case OPTION_LEAVE_COMMENT: { // a11y-fork: leave comment menu\n"
        "                try {\n"
        "                    MessageObject a11yLcMsg = selectedObject;\n"
        "                    if (a11yLcMsg != null) {\n"
        "                        int a11yLcMaxReadId;\n"
        "                        long a11yLcLinkedChatId;\n"
        "                        if (a11yLcMsg.messageOwner.replies != null) {\n"
        "                            a11yLcMaxReadId = a11yLcMsg.messageOwner.replies.read_max_id;\n"
        "                            a11yLcLinkedChatId = a11yLcMsg.messageOwner.replies.channel_id;\n"
        "                        } else {\n"
        "                            a11yLcMaxReadId = -1;\n"
        "                            a11yLcLinkedChatId = 0;\n"
        "                        }\n"
        "                        openDiscussionMessageChat(currentChat.id, a11yLcMsg, a11yLcMsg.getId(), a11yLcLinkedChatId, a11yLcMaxReadId, 0, null);\n"
        "                    }\n"
        "                } catch (Throwable e) {\n"
        "                    FileLog.e(e);\n"
        "                }\n"
        "                selectedObject = null;\n"
        "                selectedObjectGroup = null;\n"
        "                break;\n"
        "            }\n"
        f"            case {OPTION_BOT_BUTTONS_MENU}: {{ // a11y-fork: OPTION_BOT_BUTTONS_MENU\n"
    )
    if old_case not in t:
        print("WARN: ChatActivity bot-buttons-case anchor not found (leave comment menu)")
        return
    t = t.replace(old_case, new_case, 1)

    ca.write_text(t, encoding="utf-8")
    print("ChatActivity leave-comment-menu OK")


def patch_talkback_action_long_click() -> None:
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        print("WARN: ChatMessageCell missing (talkback action long click)")
        return
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: talkback action long click" in t:
        print("ChatMessageCell talkback-action-long-click already patched")
        return

    old = (
        "        public boolean performAction(int virtualViewId, int action, Bundle arguments) {\n"
        "            if (virtualViewId == HOST_VIEW_ID) {\n"
        "                performAccessibilityAction(action, arguments);\n"
        "            } else {\n"
    )
    new = (
        "        public boolean performAction(int virtualViewId, int action, Bundle arguments) {\n"
        "            if (virtualViewId == HOST_VIEW_ID) {\n"
        "                // a11y-fork: talkback action long click\n"
        "                if (action == AccessibilityNodeInfo.ACTION_LONG_CLICK) {\n"
        "                    if (delegate != null) {\n"
        "                        delegate.didLongPress(ChatMessageCell.this, lastTouchX, lastTouchY);\n"
        "                    }\n"
        "                    return true;\n"
        "                }\n"
        "                performAccessibilityAction(action, arguments);\n"
        "            } else {\n"
    )
    if old not in t:
        print("WARN: ChatMessageCell performAction anchor not found")
        return
    t = t.replace(old, new, 1)

    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell talkback-action-long-click OK")


def patch_longpress_single_finger() -> None:
    ca = JAVA / "org/telegram/ui/ChatActivity.java"
    if not ca.exists():
        print("WARN: ChatActivity missing (single-finger long-press)")
        return
    t = ca.read_text(encoding="utf-8")

    if "a11y-fork: onItemLongClick under TalkBack" not in t:
        candidates = [
            "    @Override\n    public boolean onItemLongClick(android.widget.AdapterView<?> adapterView, View view, int i, long l) {\n",
            "    public boolean onItemLongClick(android.widget.AdapterView<?> adapterView, View view, int i, long l) {\n",
        ]
        inserted = False
        for needle in candidates:
            if needle in t:
                replacement = needle + (
                    "        // a11y-fork: onItemLongClick under TalkBack\n"
                    "        try {\n"
                    "            android.view.accessibility.AccessibilityManager amItem = (android.view.accessibility.AccessibilityManager) getParentActivity().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);\n"
                    "            if (amItem != null && amItem.isEnabled() && view instanceof ChatMessageCell) {\n"
                    "                didLongPress((ChatMessageCell) view, view.getWidth() / 2f, view.getHeight() / 2f);\n"
                    "                return true;\n"
                    "            }\n"
                    "        } catch (Throwable ignore) {}\n"
                )
                t = t.replace(needle, replacement, 1)
                inserted = True
                print("onItemLongClick a11y guard OK")
                break
        if not inserted:
            print("WARN: onItemLongClick signature not found")

    ca.write_text(t, encoding="utf-8")


def patch_talkback_action_long_click_enhanced() -> None:
    cmc = JAVA / "org/telegram/ui/Cells/ChatMessageCell.java"
    if not cmc.exists():
        return
    t = cmc.read_text(encoding="utf-8")
    if "a11y-fork: talkback action long click enhanced" in t:
        print("ChatMessageCell enhanced talkback long-click already patched")
        return
    old = (
        "                if (action == AccessibilityNodeInfo.ACTION_LONG_CLICK) {\n"
        "                    if (delegate != null) {\n"
        "                        delegate.didLongPress(ChatMessageCell.this, lastTouchX, lastTouchY);\n"
        "                    }\n"
        "                    return true;\n"
        "                }\n"
    )
    new = (
        "                // a11y-fork: talkback action long click enhanced\n"
        "                if (action == AccessibilityNodeInfo.ACTION_LONG_CLICK) {\n"
        "                    if (delegate != null) {\n"
        "                        int a11yX = lastTouchX > 0 ? lastTouchX : getWidth() / 2;\n"
        "                        int a11yY = lastTouchY > 0 ? lastTouchY : getHeight() / 2;\n"
        "                        delegate.didLongPress(ChatMessageCell.this, a11yX, a11yY);\n"
        "                    }\n"
        "                    return true;\n"
        "                }\n"
    )
    if old not in t:
        print("WARN: enhanced talkback long-click anchor not found")
        return
    t = t.replace(old, new, 1)
    cmc.write_text(t, encoding="utf-8")
    print("ChatMessageCell enhanced talkback long-click OK")


def main() -> int:
    if not Path("telegram").is_dir():
        print("ERROR: telegram/ not found (clone DrKLO/Telegram as ./telegram)", file=sys.stderr)
        return 1
    print("Using scripts dir:", SCRIPTS.resolve())
    patch_app_name()
    patch_add_a11y_strings()
    install_a11y_config()
    patch_radial_progress()
    patch_dialogcell_name_then_type()
    patch_hide_share_and_comment()
    patch_forward_menu_extras()
    patch_voice_bitrate()
    patch_settings_menu()
    patch_dialogcell_preview_muted_status()
    patch_hide_sponsor_channel()
    patch_ghost_mode()
    patch_bot_buttons_menu()
    patch_reactions_as_menu()
    patch_longpress_message_menu()
    patch_go_to_first_message()
    patch_leave_comment_menu()
    patch_talkback_action_long_click()
    patch_longpress_single_finger()
    patch_talkback_action_long_click_enhanced()
    print("A11y REAL patches done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
