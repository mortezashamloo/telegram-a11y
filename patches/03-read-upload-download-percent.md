# ۳) خواندن درصد آپلود و دانلود

TalkBack به‌طور پیش‌فرض درصد را مدام اعلام نمی‌کند. باید هنگام تغییر پیشرفت، رویداد دسترس‌پذیری بفرستی.

## الف) هنگام ساخت متن درصد (قبلاً در سلول هست)

در `ChatMessageCell` حدود متد ساخت `loadingProgressLayout` (جستجو: `loadingProgressLayout = new StaticLayout`)  
متن درصد مثل `"42%"` ساخته می‌شود. همانجا بعد از به‌روز شدن درصد، announce کن.

### الگوی پیشنهادی (داخل `ChatMessageCell`):

```java
private int lastAnnouncedProgress = -1;

private void maybeAnnounceProgress(int percent, boolean uploading) {
    if (percent < 0 || percent > 100) return;
    // فقط هر ۵٪ یک‌بار تا شلوغ نشود
    if (percent != 100 && percent / 5 == lastAnnouncedProgress / 5 && percent != 0) {
        return;
    }
    if (percent == lastAnnouncedProgress) return;
    lastAnnouncedProgress = percent;

    AccessibilityManager am = (AccessibilityManager)
            getContext().getSystemService(Context.ACCESSIBILITY_SERVICE);
    if (am == null || !am.isEnabled()) return;

    String msg = uploading
            ? LocaleController.formatString("A11yUploadingPercent", R.string.A11yUploadingPercent, percent)
            : LocaleController.formatString("A11yDownloadingPercent", R.string.A11yDownloadingPercent, percent);

    announceForAccessibility(msg);
}
```

### کجا صدا بزنی؟

هر جا `radialProgress.setProgress(loadingProgress, ...)` یا `loadingProgressLayout` با درصد جدید ساخته می‌شود:

```java
float loadingProgress = DownloadController.getProgress(progress); // 0..1
int percent = Math.round(loadingProgress * 100f);
maybeAnnounceProgress(percent, /* uploading= */ buttonState == /* upload state */);
```

## ب) رشته‌های فارسی / انگلیسی

در `TMessagesProj/src/main/res/values/strings.xml`:

```xml
<string name="A11yUploadingPercent">Uploading %1$d percent</string>
<string name="A11yDownloadingPercent">Downloading %1$d percent</string>
```

در `values-fa/strings.xml` (اگر هست):

```xml
<string name="A11yUploadingPercent">در حال ارسال، %1$d درصد</string>
<string name="A11yDownloadingPercent">در حال دریافت، %1$d درصد</string>
```

## ج) ریست هنگام پیام جدید

در جایی که `setMessageObject` / تعویض پیام سلول انجام می‌شود:

```java
lastAnnouncedProgress = -1;
```
