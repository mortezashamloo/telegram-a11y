# Accessibility patches for Telegram Android (TalkBack)

| # | Feature | File(s) |
|---|---------|--------|
| 01 | Chat list: name first, then type | DialogCell.java |
| 02 | Hide Share button between messages | ChatMessageCell.java |
| 03 | Announce upload/download percent | ChatMessageCell.java + strings |
| 04 | Label unlabeled buttons | A11y helper + various views |
| 05 | **Forward without quote as separate option** | ChatActivity.java + SendMessagesHelper.java |

## 05 note (important)

«فوروارد بدون نقل‌قول» یک **گزینهٔ جدا** است، نه جایگزین فوروارد عادی:

- منوی long-press / ActionMode دو آیتم دارد:
  - Forward (عادی)
  - Forward without quote
- فقط دومی `drop_author = true` می‌فرستد.

جزئیات کامل در `05-forward-without-quote.md`.

## Applying

- Markdown files = human instructions.
- `*.patch` files are applied by the GitHub Actions workflow when present.
- Because Telegram’s ChatActivity is huge and line numbers drift, for 05 the CI also does a best-effort sed inject of the static flag + SendMessagesHelper change. Full menu items still need the documented edits (or a fresh unified diff against the exact commit you build).
