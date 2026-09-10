# -*- coding: utf-8 -*-
import re
import os

def remove_hidden_char(text):
    return text.replace('\x01', '').replace('\u0001', '')

def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = remove_hidden_char(content)
    if cleaned != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        return True
    return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_fix = [
        os.path.join(base_dir, "scripts/apply-a11y.py"),
        os.path.join(base_dir, "scripts/post-a11y-menu.py"),
        os.path.join(base_dir, "scripts/patch-proxy-muted.py"),
        os.path.join(base_dir, "TMessagesProj/src/main/res/values/strings.xml"),
        os.path.join(base_dir, "TMessagesProj/src/main/res/values-fa/strings.xml"),
    ]
    for file_path in files_to_fix:
        if process_text_file(file_path):
            print(f"✅ اصلاح شد: {file_path}")
        else:
            print(f"✓ بدون تغییر: {file_path}")

if __name__ == "__main__":
    main()