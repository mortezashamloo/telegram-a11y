# -*- coding: utf-8 -*-
"""
Strips stray \x01/\u0001 control characters that can end up embedded in a
few generated/patched files (the root cause of the "illegal character"
DialogCell.java compile errors seen earlier).
"""
import os

def remove_hidden_char(text):
    return text.replace('\x01', '').replace('\u0001', '')

def process_text_file(file_path):
    if not os.path.isfile(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = remove_hidden_char(content)
    if cleaned != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        return True
    return False

def main():
    # a11y-fork: base_dir already IS patches-repo/scripts -- don't prepend
    # "scripts/" again (that was the "scripts/scripts" bug).
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # repo_root is two levels up from patches-repo/scripts; the cloned
    # Telegram source lives at repo_root/telegram, a sibling of
    # patches-repo, not inside it.
    repo_root = os.path.dirname(os.path.dirname(base_dir))
    telegram_dir = os.path.join(repo_root, "telegram")

    files_to_fix = [
        os.path.join(base_dir, "apply-a11y.py"),
        os.path.join(base_dir, "post-a11y-menu.py"),
        os.path.join(base_dir, "patch-proxy-muted.py"),
        os.path.join(telegram_dir, "TMessagesProj", "src", "main", "res", "values", "strings.xml"),
        os.path.join(telegram_dir, "TMessagesProj", "src", "main", "res", "values-fa", "strings.xml"),
    ]
    for file_path in files_to_fix:
        result = process_text_file(file_path)
        if result is True:
            print(f"fixed: {file_path}")
        elif result is False:
            print(f"unchanged: {file_path}")
        else:
            print(f"skip (not found): {file_path}")

if __name__ == "__main__":
    main()
