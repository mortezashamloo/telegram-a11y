# کیت قابل‌حمل Telegram Accessible (مثل espeak)

وقتی سورس رسمی [DrKLO/Telegram](https://github.com/DrKLO/Telegram) آپدیت شد، **نیازی نیست همه چیز را از صفر بنویسی**.  
همین ریپو (`mortezashamloo/telegram-a11y`) همان کیت است.

## چه چیزی را در Google Drive کپی کنی؟

کل ریپو یا حداقل این پوشه‌ها:

```
telegram-a11y/
  scripts/
    apply-a11y.py          ← موتور اصلی پچ‌ها
    A11yConfig.java        ← تنظیمات دسترس‌پذیری
    inject-api.py          ← API ID / HASH
    slim-arm64.py          ← فقط arm64
  .github/workflows/
    build-apk.yml          ← بیلد خودکار GitHub Actions
  KIT-FOR-GOOGLE-DRIVE.md  ← این فایل
  patches/                 ← مستندات (اختیاری)
```

**رمز API را در Drive نگذار.** فقط در GitHub Secrets بماند:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`

## روش ۱ — پیشنهادی (GitHub Actions، بدون لپ‌تاپ قوی)

1. سورس جدید لازم نیست دستی clone کنی؛ workflow خودش `DrKLO/Telegram` را می‌گیرد.
2. برو Actions → **Build APK** → **Run workflow**
3. APK را از Artifacts دانلود کن.

هر بار که `scripts/apply-a11y.py` را بهتر کنی، همان روی **آخرین** سورس رسمی اعمال می‌شود.

## روش ۲ — روی کامپیوتر خودت

```bash
git clone --recursive https://github.com/DrKLO/Telegram.git telegram
# این کیت را کنارش بگذار، مثلاً patches-repo/

export API_ID=... API_HASH=...
python3 patches-repo/scripts/inject-api.py
python3 patches-repo/scripts/apply-a11y.py
python3 patches-repo/scripts/slim-arm64.py   # اختیاری

cd telegram
./gradlew :TMessagesProj_App:assembleAfatDebug
```

اگر `apply-a11y.py` بگوید `WARN: ... not found`، یعنی تلگرام آن تکه کد را عوض کرده؛ همان تابع را در اسکریپت با کد جدید هماهنگ کن (مثل پچ espeak).

## پچ‌های فعلی که اسکریپت اعمال می‌کند

| پچ | توضیح |
|----|--------|
| AppName / AppNameBeta | Telegram Accessible / تلگرام دسترس‌پذیر |
| RadialProgress2 + RadialProgress | درصد فقط وقتی فوکوس TalkBack روی همان پیام است |
| DialogCell | اول اسم، بعد نوع (channel / group / bot) |
| ChatMessageCell | مخفی Share و Leave comment بین پیام‌ها |
| A11yConfig + Settings | منوی Accessible settings |
| audio.c + MediaController | کیفیت ویس Low/Med/High |
| drop_author flag | پایه فوروارد بدون نقل‌قول |

## هنوز در صف

- Reaction به‌صورت زیر‌منو
- فوروارد بدون نقل‌قول به‌عنوان آیتم جدا در منو
- Leave comment داخل گزینه‌های پیام
- contentDescription برای دکمه‌های بدون برچسب

## نکته درباره Blindgram

ایده و نیاز نابینایان همان است؛ این پروژه روی **آخرین سورس رسمی** با پچ‌های کم‌حجم و قابل‌باز‌اعمال جلو می‌رود تا بعد از هر آپدیت تلگرام، دوباره بتوان همان تنظیمات را برگرداند.
