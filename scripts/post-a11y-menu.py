#!/usr/bin/env python3
"""Post-process ChatActivity + SettingsActivity for TalkBack:
- Reactions (121) then Select (203) at end of message menu
- Bot inline buttons as menu items (options 300+)
- Label Settings camera / avatar (unlabeled button)
"""
from pathlib import Path
import re
import sys

ROOT = Path("telegram/TMessagesProj/src/main/java")
CA = ROOT / "org/telegram/ui/ChatActivity.java"
SA = ROOT / "org/telegram/ui/SettingsActivity.java"

OPTION_REACTIONS = 121
OPTION_SELECT = 203
OPTION_BOT_BASE = 300  # 300..339


def patch_menu_order(t: str) -> str:
    needle = "                scrimPopupWindowItems = new ActionBarMenuSubItem[items.size()];"
    if needle not in t:
        print("WARN: scrimPopupWindowItems needle missing")
        return t
    if "a11y-fork: Reactions+Select at end of menu" in t:
        print("Menu order already applied")
        return t
    # Strip older Select-only reorder if present
    t = re.sub(
        r"[ \t]*// a11y-fork: Select to end of menu\n"
        r"[ \t]*try \{\n"
        r"(?:.*\n)*?"
        r"[ \t]*\} catch \(Throwable ignore\) \{\}\n"
        r"(?=[ \t]*scrimPopupWindowItems = new ActionBarMenuSubItem)",
        "",
        t,
        count=1,
    )
    block = f"""                // a11y-fork: Reactions+Select at end of menu
                try {{
                    java.util.ArrayList<Integer> moveOpts = new java.util.ArrayList<>();
                    moveOpts.add({OPTION_REACTIONS});
                    moveOpts.add({OPTION_SELECT});
                    for (Integer optId : moveOpts) {{
                        int idx = options.indexOf(optId);
                        if (idx >= 0 && idx < items.size()) {{
                            CharSequence it = items.remove(idx);
                            Integer op = options.remove(idx);
                            Integer ic = icons.remove(idx);
                            items.add(it);
                            options.add(op);
                            icons.add(ic);
                        }}
                    }}
                }} catch (Throwable ignore) {{}}
                scrimPopupWindowItems = new ActionBarMenuSubItem[items.size()];"""
    t = t.replace(needle, block, 1)
    print("Menu order: Reactions then Select at end OK")
    return t


def patch_bot_buttons_menu(t: str) -> str:
    if "a11y-fork: bot buttons in message menu" in t:
        print("Bot buttons menu already applied")
        return t
    needle = "        if (message.isSponsored() && !getUserConfig().isPremium()"
    if needle not in t:
        print("WARN: fillMessageMenu inject for bot buttons not found")
        return t
    insert = f"""        // a11y-fork: bot buttons in message menu
        try {{
            if (message != null && message.hasInlineBotButtons() && message.messageOwner != null
                    && message.messageOwner.reply_markup instanceof TLRPC.TL_replyInlineMarkup) {{
                TLRPC.TL_replyInlineMarkup markup = (TLRPC.TL_replyInlineMarkup) message.messageOwner.reply_markup;
                int botIdx = 0;
                if (markup.rows != null) {{
                    for (int ri = 0; ri < markup.rows.size(); ri++) {{
                        org.telegram.tgnet.tl.TL_keyboard.KeyboardInlineButtonRow row = markup.rows.get(ri);
                        if (row == null || row.buttons == null) continue;
                        for (int bi = 0; bi < row.buttons.size(); bi++) {{
                            org.telegram.tgnet.tl.TL_keyboard.KeyboardInlineButton rawBtn = row.buttons.get(bi);
                            String btnText = rawBtn != null ? rawBtn.getText() : null;
                            if (btnText == null || btnText.length() == 0) {{
                                btnText = "Bot button " + (botIdx + 1);
                            }}
                            items.add(btnText);
                            options.add({OPTION_BOT_BASE} + botIdx);
                            icons.add(R.drawable.msg_bot);
                            botIdx++;
                            if (botIdx >= 40) break;
                        }}
                        if (botIdx >= 40) break;
                    }}
                }}
            }}
        }} catch (Throwable ignore) {{}}

        if (message.isSponsored() && !getUserConfig().isPremium()"""
    t = t.replace(needle, insert, 1)
    print("Bot buttons menu items OK")

    if "a11y-fork: bot button handler" not in t:
        old_case = "            case OPTION_RETRY: {"
        if old_case not in t:
            print("WARN: OPTION_RETRY for bot handler not found")
            return t
        cases = " ".join([f"case {OPTION_BOT_BASE + i}:" for i in range(40)])
        handler = f"""            // a11y-fork: bot button handler
            {cases} {{
                try {{
                    int botIdx = option - {OPTION_BOT_BASE};
                    MessageObject msg = selectedObject;
                    if (msg != null && msg.messageOwner != null
                            && msg.messageOwner.reply_markup instanceof TLRPC.TL_replyInlineMarkup) {{
                        TLRPC.TL_replyInlineMarkup markup = (TLRPC.TL_replyInlineMarkup) msg.messageOwner.reply_markup;
                        int n = 0;
                        org.telegram.tgnet.tl.TL_keyboard.KeyboardButtonProto found = null;
                        if (markup.rows != null) {{
                            outer:
                            for (int ri = 0; ri < markup.rows.size(); ri++) {{
                                org.telegram.tgnet.tl.TL_keyboard.KeyboardInlineButtonRow row = markup.rows.get(ri);
                                if (row == null || row.buttons == null) continue;
                                for (int bi = 0; bi < row.buttons.size(); bi++) {{
                                    if (n == botIdx) {{
                                        found = row.buttons.get(bi);
                                        break outer;
                                    }}
                                    n++;
                                }}
                            }}
                        }}
                        if (found != null && chatActivityEnterView != null) {{
                            closeMenu();
                            chatActivityEnterView.didPressedBotButton(found, msg, msg);
                        }}
                    }}
                }} catch (Throwable e) {{
                    FileLog.e(e);
                }}
                selectedObject = null;
                selectedObjectToEditCaption = null;
                selectedObjectGroup = null;
                break;
            }}
            case OPTION_RETRY: {{"""
        t = t.replace(old_case, handler, 1)
        print("Bot button handlers OK")
    return t


def patch_settings_labels(t: str) -> str:
    if "a11y-fork: settings camera label" in t:
        print("Settings labels already applied")
        return t
    old_cam = "        cameraButton = new FrameLayout(context);"
    if old_cam in t:
        t = t.replace(
            old_cam,
            "        cameraButton = new FrameLayout(context);\n"
            "        // a11y-fork: settings camera label\n"
            "        try {\n"
            "            cameraButton.setContentDescription(getString(R.string.AccDescrChangeProfilePicture));\n"
            "            cameraButton.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);\n"
            "        } catch (Throwable ignore) {}\n",
            1,
        )
        print("Settings cameraButton label OK")
    else:
        print("WARN: cameraButton not found")
    old_av = "        ScaleStateListAnimator.apply(avatarContainer);"
    if old_av in t and "a11y-fork: settings avatar label" not in t:
        t = t.replace(
            old_av,
            "        // a11y-fork: settings avatar label\n"
            "        try {\n"
            "            avatarContainer.setContentDescription(getString(R.string.AccDescrChangeProfilePicture));\n"
            "            avatarContainer.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);\n"
            "        } catch (Throwable ignore) {}\n"
            "        ScaleStateListAnimator.apply(avatarContainer);",
            1,
        )
        print("Settings avatarContainer label OK")
    if "a11y-fork: settings search label" not in t and "searchItem.setSearchFieldHint" in t:
        t = t.replace(
            "searchItem.setSearchFieldHint(getString(R.string.Search));",
            "searchItem.setSearchFieldHint(getString(R.string.Search));\n"
            "        // a11y-fork: settings search label\n"
            "        searchItem.setContentDescription(getString(R.string.Search));",
            1,
        )
        print("Settings searchItem label OK")
    return t


def main() -> int:
    if not CA.exists():
        print("ERROR: ChatActivity missing", file=sys.stderr)
        return 1
    t = CA.read_text(encoding="utf-8")
    t = patch_bot_buttons_menu(t)
    t = patch_menu_order(t)
    CA.write_text(t, encoding="utf-8")
    if SA.exists():
        st = SA.read_text(encoding="utf-8")
        st = patch_settings_labels(st)
        SA.write_text(st, encoding="utf-8")
    else:
        print("WARN: SettingsActivity missing")
    print("post-a11y-menu done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
