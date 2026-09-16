#!/usr/bin/env python3
import os

target_file = "TMessagesProj/src/main/java/org/telegram/ui/AccessibilitySettingsActivity.java"

if not os.path.exists(target_file):
    print(f"Error: {target_file} not found.")
    exit(1)

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Check if injection already present
if "a11y_forward_no_quote_saved" in content:
    print("A11y menu enhancements already applied.")
    exit(0)

injection_code = """
        // --- A11y Custom Settings Injection ---
        TextCheckCell cellForwardNoQuoteSaved = new TextCheckCell(getParentActivity());
        cellForwardNoQuoteSaved.setTextAndCheck(
            LocaleController.getString("A11yForwardNoQuoteSaved", R.string.A11yForwardNoQuoteSaved),
            A11yConfig.isForwardNoQuoteSavedEnabled(),
            true
        );
        cellForwardNoQuoteSaved.setOnClickListener(v -> {
            boolean newState = !A11yConfig.isForwardNoQuoteSavedEnabled();
            A11yConfig.setForwardNoQuoteSavedEnabled(newState);
            cellForwardNoQuoteSaved.setChecked(newState);
        });
        linearLayout.addView(cellForwardNoQuoteSaved);
        // --- End A11y Custom Settings Injection ---
"""

if "linearLayout.addView(cellProgressStep);" in content:
    content = content.replace(
        "linearLayout.addView(cellProgressStep);",
        "linearLayout.addView(cellProgressStep);\n" + injection_code
    )
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully injected A11y settings menu options.")
else:
    print("Warning: Anchor pattern not found in AccessibilitySettingsActivity.java")