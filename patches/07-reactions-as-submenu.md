# 07 – Reactions as submenu in message long-press menu

**هدف:** با نگه‌داشتن روی پیام، منوی اصلی (Reply / Forward / Copy / …) خلوت بماند؛ **Reactions** به‌جای نوار جدا بالای منو، یک **آیتم داخل منو** باشد که زیرمنو باز کند.

برای TalkBack مفید است: آیتم‌های سطح اول کمتر و قابل پیمایش خطی‌تر.

## رفتار فعلی (رسمی)

در `ChatActivity.createMenu(...)`:

- نوار `ReactionsContainerLayout` معمولاً **بالای** لیست اکشن‌ها نشان داده می‌شود.
- لیست زیرین: Reply, Copy, Forward, Delete, …

## رفتار مطلوب (a11y-fork)

1. نوار واکنش بالای منو **نشان داده نشود** (یا فقط وقتی کاربر آیتم Reactions را زد).
2. در لیست منو یک آیتم واضح:
   - عنوان: `Reactions` / «واکنش‌ها»
   - آیکن: مثلاً `R.drawable.msg_reactions` یا مشابه
3. با انتخاب آن → **زیرمنو / swipe-back panel** همان picker واکنش‌ها (`ReactionsContainerLayout`) باز شود.
4. بقیهٔ آیتم‌ها (Reply, Forward, Copy, …) در سطح اول بمانند.

## محل تغییر

فایل اصلی: `TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java`

مناطق تقریبی (شماره خط upstream جابه‌جا می‌شود):

1. جایی که `isReactionsViewAvailable` و `ReactionsContainerLayout` به `scrimPopupContainerLayout` اضافه می‌شوند → برای fork: نوار را نساز / اضافه نکن.
2. ساخت آیتم‌های `items` / `options` / `icons` (یا `ItemOptions`) → یک گزینهٔ `OPTION_REACTIONS` (عدد ثابت جدید) اضافه کن.
3. در `processSelectedOption` / کلیک آیتم → باز کردن پنل واکنش‌ها، ترجیحاً با الگوی موجود:
   ```java
   ItemOptions subOptions = options.makeSwipeback();
   // back + embed ReactionsContainerLayout
   ```
   یا نمایش همان `reactionsLayout` داخل swipeback.

## دسترسی (TalkBack)

- آیتم منو باید `contentDescription` واضح داشته باشد: «Reactions» / «واکنش‌ها».
- بعد از باز شدن زیرمنو، فوکوس روی اولین واکنش یا دکمهٔ Back باشد.
- با Back سیستم / آیتم Back، به منوی اصلی برگردد.

## وضعیت

مستندات آماده است. پیاده‌سازی کامل UI داخل `createMenu` بزرگ و حساس است؛ همراه پچ 05/06 در **بیلد بعدی** اعمال می‌شود تا بیلد جاری قطع نشود.
