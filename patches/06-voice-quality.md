# 06 – Voice message quality: Low / Medium / High

**هدف:** هنگام ارسال ویس، کیفیت قابل انتخاب باشد تا حجم/کیفیت کنترل شود (مفید برای اینترنت ضعیف و TalkBack).

## سطوح پیشنهادی (Opus, mono, speech)

| Level | Bitrate | کاربرد |
|-------|---------|--------|
| Low | 16000 | حجم کم، اینترنت ضعیف |
| Medium | 32000 | تعادل (پیش‌فرض پیشنهادی) |
| High | 64000 | کیفیت بهتر |

## فایل‌های درگیر

1. `TMessagesProj/jni/audio.c` — بیت‌ریت Opus الان ثابت است:
   ```c
   const opus_int32 bitrate = OPUS_BITRATE_MAX;
   ```
   باید از یک متغیر سراسری / پارامتر JNI خوانده شود، مثلاً:
   ```c
   static opus_int32 g_record_bitrate = 32000;
   // در initRecorder:
   opus_encoder_ctl(_encoder, OPUS_SET_BITRATE(g_record_bitrate));
   ```
   و JNI جدید یا گسترش `startRecord` برای ست کردن بیت‌ریت قبل از encode.

2. `MediaController.java` — قبل از `startRecord` کیفیت ذخیره‌شده را به native پاس بده.

3. تنظیمات UI (یکی از این دو):
   - **ساده:** در Settings → Data and Storage یک لیست `Voice message quality` با سه گزینه
   - **سریع برای ارسال:** long-press روی دکمهٔ میکروفون → منوی Low / Medium / High

4. ذخیره با `MessagesController.getMainSettings(currentAccount)` یا `SharedPreferences`:
   ```java
   // key: "a11y_voice_quality" values: 0=low, 1=medium, 2=high
   ```

## نکتهٔ CI / native

چون `audio.c` native است، بعد از پچ باید NDK دوباره کامپایل شود (همین workflow فعلی همین کار را می‌کند). پچ‌های فقط-Java برای این فیچر کافی نیستند.

## وضعیت

مستندات آماده است. پیاده‌سازی کامل (JNI + Settings UI) در بیلد بعدی اعمال می‌شود تا بیلد جاری `telegram-a11y` قطع نشود.
