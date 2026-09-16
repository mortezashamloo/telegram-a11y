#!/usr/bin/env python3
import os
import sys

def main():
    target_file = "telegram/TMessagesProj/src/main/java/org/telegram/ui/AccessibilitySettingsActivity.java"
    
    if not os.path.exists(target_file):
        found = False
        for root, dirs, files in os.walk("telegram"):
            if "AccessibilitySettingsActivity.java" in files:
                target_file = os.path.join(root, "AccessibilitySettingsActivity.java")
                found = True
                break
        if not found:
            print(f"[WARN] Target file {target_file} not found. Skipping post-a11y-menu patch.")
            return

    print(f"[INFO] Patching Accessible Settings menu in: {target_file}")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "PREF_FORWARD_NO_QUOTE_SAVED" in content or "isForwardNoQuoteSavedEnabled" in content:
        print("[INFO] Forward without quote option already exists in Accessible Settings.")
        return

    menu_item_code = '''
        // Option: Forward without quote to Saved Messages
        TextCheckCell forwardNoQuoteCell = new TextCheckCell(context);
        forwardNoQuoteCell.setTextAndCheck("Forward to Saved Messages with no quote", org.telegram.messenger.A11yConfig.isForwardNoQuoteSavedEnabled(), true);
        forwardNoQuoteCell.setOnClickListener(v -> {
            boolean newState = !org.telegram.messenger.A11yConfig.isForwardNoQuoteSavedEnabled();
            org.telegram.messenger.A11yConfig.setForwardNoQuoteSavedEnabled(newState);
            forwardNoQuoteCell.setChecked(newState);
        });
        linearLayout.addView(forwardNoQuoteCell);
    '''

    if "linearLayout.addView(" in content:
        injection_point = content.rfind("linearLayout.addView(")
        end_of_line = content.find(";", injection_point) + 1
        updated_content = content[:end_of_line] + "\n" + menu_item_code + content[end_of_line:]
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("[SUCCESS] Successfully added Forward without quote option to Accessible Settings.")
    else:
        print("[WARN] Could not find suitable injection point in AccessibilitySettingsActivity.java.")

if __name__ == "__main__":
    main()