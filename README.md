# telegram-a11y / تلگرام دسترس‌پذیر

**English** | **[فارسی](#فارسی)**

TalkBack-friendly patches for official [Telegram Android](https://github.com/DrKLO/Telegram), plus a GitHub Actions workflow to build an APK **without a powerful PC**.

> This is an **accessibility fork kit** (patches + CI), not the official Telegram app.  
> Package id: `org.telegram.messenger.accessible` (installs **next to** official Telegram).

---

## Features (TalkBack)

| Feature | Description |
|--------|-------------|
| Chat list order | **Name first, then type** (e.g. “Grok, channel”) |
| Less clutter between messages | Hide **Share** and on-bubble **Leave comment**; comment stays in the message menu |
| Progress | Announce **upload/download percent** |
| Long-press | Opens the **single-message menu** (not multi-select by default under TalkBack) |
| Select | **Select** is a menu item and starts action mode properly |
| Reactions | **Reactions** menu item shows/hides the reaction strip |
| Bot buttons | One **Bot buttons** item → dialog with the real bot actions (not scattered; not between messages) |
| Labels | Settings camera/avatar/search, Storage usage, and related controls |
| Language | Labels via `LocaleController` — **Persian when UI is Persian**, English otherwise |
| Forward without quote | Separate menu option (does not replace normal Forward) |
| APK size | **arm64-v8a only** (smaller; fine for modern phones) |

---

## For screen reader users (quick)

1. Open the repo on GitHub (or your fork).
2. **Actions** → **Build APK** → **Run workflow**.
3. Wait (often ~45–90 minutes the first times).
4. Download artifact **`telegram-accessible-arm64`** (and once: **`a11y-release-keystore`**).
5. Install the APK (Unknown sources / install from files as on your device).
6. Optional: save the keystore as GitHub **Secrets** so the **next** build can update the same install (same signature).

If Play Protect warns on older public debug builds, this kit uses a **unique package** and a **private keystore** so warnings are usually milder. Sideloaded apps may still show a soft warning; that is normal outside Play Store.

---

## One-time GitHub setup

### Required secrets

| Secret | Where from |
|--------|------------|
| `TELEGRAM_API_ID` | [my.telegram.org](https://my.telegram.org) |
| `TELEGRAM_API_HASH` | same |

### Recommended secrets (stable updates / Play Protect kit)

| Secret | Typical value |
|--------|----------------|
| `A11Y_KEYSTORE_BASE64` | Base64 of `a11y-release.keystore` (from the workflow artifact) |
| `A11Y_STORE_PASSWORD` | `telegram-a11y-local` (if you used defaults) |
| `A11Y_KEY_PASSWORD` | same as store password |
| `A11Y_KEY_ALIAS` | `a11ykey` |
| `A11Y_APP_PACKAGE` | optional; default `org.telegram.messenger.accessible` |

**Windows (PowerShell) — copy keystore to clipboard as Base64:**

```powershell
Set-Clipboard -Value ([Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Users\YOU\Downloads\a11y-release.keystore")))
```

Then: repo **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Order of secrets does **not** matter. A trailing blank line in Base64 is usually OK (CI trims it).

---

## Build your own fork (another blind developer / friend)

1. Fork this repo **or** create an empty repo and copy `scripts/`, `.github/workflows/`, `patches/`.
2. Add secrets above on **your** fork.
3. Run **Build APK**.
4. Keep **your** keystore private; do not commit it to git.
5. Respect [Telegram API Terms](https://core.telegram.org/api/terms) and **GPL-2.0** when you share APKs.

You do **not** need the official Telegram Play signing key. This kit generates **`a11y-release.keystore`**. That key is only for *your* builds — Google does **not** “whitelist” it as safe; it only keeps package id + signature stable.

---

## Releases on GitHub

After a good build:

1. Download the APK artifact from Actions.
2. Repo → **Releases** → **Create a new release**.
3. Tag e.g. `v1.0.0-a11y`, title e.g. `Telegram Accessible (arm64)`.
4. Upload the APK (+ short notes: TalkBack features, arm64-only, package id).
5. Paste a short English + Persian changelog.

Maintainers: prefer attaching the CI APK rather than rebuilding on a laptop.

See also [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

---

## Project layout

```
.github/workflows/build-apk.yml   # CI build
scripts/apply-a11y.py             # core TalkBack patches
scripts/post-a11y-menu.py         # menu order, bot submenu, labels
scripts/prepare-release-signing.py# unique package + keystore + google-services
scripts/slim-arm64.py             # arm64-only APK
patches/                          # docs + some .patch files
```

---

## License

Minimal patches for use with Telegram Android (**GPL-2.0**).  
Not affiliated with Telegram FZ-LLC. Use at your own risk.

---

# فارسی

پچ‌های دوستدار **TalkBack** برای [تلگرام اندروید رسمی](https://github.com/DrKLO/Telegram) + بیلد با **GitHub Actions** بدون نیاز به سیستم قوی.

> این یک **کیت دسترس‌پذیری** است (پچ + CI)، نه اپ رسمی تلگرام.  
> شناسه پکیج: `org.telegram.messenger.accessible` (کنار تلگرام رسمی نصب می‌شود).

## قابلیت‌ها (TalkBack)

- لیست چت: **اول نام، بعد نوع** (مثلاً «گراک، کانال»)
- بین پیام‌ها: مخفی **Share** و دکمهٔ روی حباب **Leave comment** (کامنت در منوی پیام)
- اعلام **درصد** آپلود/دانلود
- long-press: منوی **تک‌پیام** (نه multi-select پیش‌فرض زیر TalkBack)
- **Select** از منو → حالت انتخاب
- **Reactions** از منو (نمایش نوار واکنش)
- **دکمه‌های ربات**: یک آیتم «Bot buttons / دکمه‌های ربات» → دیالوگ؛ بین پیام‌ها پخش نیست
- برچسب Settings و Storage و کنترل‌های مرتبط
- برچسب‌ها با `LocaleController`: **فارسی وقتی زبان برنامه فارسی است**
- Forward without quote به‌صورت گزینهٔ جدا
- حجم کمتر: فقط **arm64**

## راهنمای سریع کاربران صفحه‌خوان

1. ریپو (یا فورک خودت) را در گیت‌هاب باز کن.
2. **Actions** → **Build APK** → **Run workflow**.
3. صبر کن (اغلب حدود ۴۵ تا ۹۰ دقیقه).
4. Artifactهای **`telegram-accessible-arm64`** و یک‌بار **`a11y-release-keystore`** را دانلود کن.
5. APK را نصب کن.
6. برای آپدیت بعدی روی همان نصب: keystore را در **Secrets** بگذار (جدول بالا).

## راه‌اندازی Secrets

الزامی: `TELEGRAM_API_ID` و `TELEGRAM_API_HASH` از [my.telegram.org](https://my.telegram.org).

پیشنهادی برای امضای ثابت:

- `A11Y_KEYSTORE_BASE64` — خروجی Base64 فایل `a11y-release.keystore`
- `A11Y_STORE_PASSWORD` — پیش‌فرض: `telegram-a11y-local`
- `A11Y_KEY_PASSWORD` — معمولاً همان
- `A11Y_KEY_ALIAS` — پیش‌فرض: `a11ykey`

**ویندوز — کپی Base64 به کلیپ‌بورد:**

```powershell
Set-Clipboard -Value ([Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Users\YOU\Downloads\a11y-release.keystore")))
```

ترتیب secretها مهم نیست.

## فورک برای خودت

1. این ریپو را Fork کن (یا فایل‌های `scripts/` و workflow را کپی کن).
2. Secrets را روی **فورک خودت** بگذار.
3. بیلد بگیر.
4. keystore را عمومی نکن و داخل git commit نکن.
5. شرایط API تلگرام و GPL را رعایت کن.

کلید امضای فروشگاه تلگرام لازم نیست؛ کیت **`a11y-release.keystore`** می‌سازد. گوگل این کلید را «تأیید امن» نمی‌کند؛ فقط پکیج و امضای تو را پایدار نگه می‌دارد.

## انتشار (Releases)

1. APK را از Actions بگیر.
2. **Releases** → **Create a new release**.
3. تگ مثلاً `v1.0.0-a11y`.
4. APK را ضمیمه کن و خلاصهٔ فارسی/انگلیسی بنویس (TalkBack، arm64، نام پکیج).

نیز ببینید: [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

## مجوز

پچ‌های حداقلی برای تلگرام اندروید (**GPL-2.0**).  
وابسته به Telegram FZ-LLC نیست. با مسئولیت خودتان استفاده کنید.
