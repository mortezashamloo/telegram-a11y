# راه‌اندازی بیلد روی GitHub Actions (کامپیوتر ضعیف)

## ۱) ریپو

ریپوی `mortezashamloo/telegram-a11y` ساخته شده و پچ‌ها + workflow داخلش است.

## ۲) Secrets

Settings → Secrets and variables → Actions → New repository secret:

| Name | Value |
|------|--------|
| `TELEGRAM_API_ID` | عدد از my.telegram.org |
| `TELEGRAM_API_HASH` | رشته از my.telegram.org |

## ۳) اجرا

1. Actions → **Build APK** → **Run workflow**
2. صبر کن (معمولاً ۴۵ تا ۹۰ دقیقه؛ بار اول طولانی‌تر)
3. از Artifacts فایل `telegram-a11y-debug` را دانلود کن

## ۴) نصب روی گوشی

- Unknown sources را برای مرورگر/فایل‌منیجر اجازه بده
- APK را نصب کن

## ویژگی فوروارد بدون نقل‌قول

پچ ۰۵ این گزینه را **جدا** از فوروارد معمولی اضافه می‌کند (نه اینکه همه فورواردها را بی‌نقل‌قول کند).

برای اعمال کامل منو باید طبق `patches/05-forward-without-quote.md` در ChatActivity.java آیتم منو/اکشن‌مود اضافه شود. CI فعلاً فلگ و منطق SendMessagesHelper را تزریق می‌کند.

## محدودیت‌ها

- بیلد کامل تلگرام سنگین است؛ گاهی GHA از RAM/disk خطا می‌دهد → دوباره Run کن
- NDK/native ممکن است اولین بار fail شود؛ لاگ را بفرست تا workflow را تنظیم کنیم
- برای انتشار عمومی: applicationId جدا، نام اپ جدا، رعایت GPL
