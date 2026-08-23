# Accessibility patches for Telegram Android (TalkBack)

| # | Feature | Status in CI |
|---|---------|--------------|
| 01 | Chat list: name first, then type | docs |
| 02 | Hide Share button between messages | **auto sed** |
| 03 | Announce upload/download percent | docs |
| 04 | Label unlabeled buttons | docs |
| 05 | Forward without quote (separate option) | **partial auto** (flag + drop_author); full menu item needs more UI work |
| 06 | Voice quality Low / Medium / High | docs (native Opus) |
| 07 | Reactions as submenu | docs |
| 08 | App name: Telegram Accessible / تلگرام دسترس‌پذیر | **auto** in workflow |

## CI notes

Workflow applies:
- `*.patch` files
- AppName string replace (EN + FA)
- Forward-without-quote `IS_FORWARD_NO_QUOTE` + `drop_author`
- Hide share button (`checkNeedDrawShareButton` → return false)

Icon/logo: custom image later (user-provided).

## 05 note

«فوروارد بدون نقل‌قول» باید گزینهٔ **جدا** باشد. فعلاً پرچم و منطق ارسال در CI ست می‌شود؛ تکمیل آیتم منو در ChatActionMode در نسخه‌های بعدی.
