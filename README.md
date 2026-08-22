# telegram-a11y

TalkBack-friendly patches for official [Telegram Android](https://github.com/DrKLO/Telegram) + GitHub Actions workflow to build an APK without a powerful PC.

## Features

1. Chat list: **name first, then type** (e.g. "Grok, channel")
2. **Hide Share button** between messages (faster navigation)
3. Announce **upload/download progress percent**
4. **Label unlabeled buttons**
5. **Forward without quote** as a **separate** menu/action option (does not replace normal Forward)

## Quick start

1. Add repository secrets:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   (from https://my.telegram.org)
2. Actions → **Build APK** → Run workflow
3. Download the artifact when finished

See [SETUP-GITHUB.md](SETUP-GITHUB.md) and [patches/README.md](patches/README.md).

## License

Patches are minimal modifications intended for use with Telegram Android (GPL-2.0). Respect Telegram API Terms and GPL when distributing builds.
