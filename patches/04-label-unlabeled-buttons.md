# ۴) برچسب‌گذاری دکمه‌های بدون برچسب

TalkBack روی دکمه‌های بدون `contentDescription` فقط «دکمه» می‌گوید.
هدف: هر کنترل قابل‌کلیک یک برچسب داشته باشد.

## الف) کمک‌کنندهٔ سراسری (پیشنهادی)

فایل جدید:

`TMessagesProj/src/main/java/org/telegram/ui/Components/A11y.java`

```java
package org.telegram.ui.Components;

import android.view.View;
import org.telegram.messenger.LocaleController;

public final class A11y {
    private A11y() {}

    public static void label(View v, int stringRes) {
        if (v == null) return;
        v.setContentDescription(LocaleController.getString(stringRes));
        v.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
    }

    public static void label(View v, String text) {
        if (v == null) return;
        v.setContentDescription(text);
        v.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
    }

    public static void ensure(View v, String fallback) {
        if (v == null) return;
        CharSequence d = v.getContentDescription();
        if (d == null || d.length() == 0) {
            v.setContentDescription(fallback);
        }
        v.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
}
```

## ب) جاهای پرتکرار

| محل | فایل تقریبی | برچسب نمونه |
|-----|-------------|-------------|
| دکمه ارسال | ChatActivityEnterView | Send |
| ضمیمه | همان | Attach |
| میکروفون | همان | Voice message |
| اموجی | همان | Emoji |
| منوی سه‌نقطه | ActionBarMenuItem | More options |
| بازگشت | ActionBar | Back |
| جستجو | DialogsActivity | Search |
| تماس | ChatActivity | Voice/Video call |
| اسکرول پایین | ChatActivity | Scroll to bottom |

مثال:

```java
A11y.label(attachButton, R.string.AccDescrAttachButton);
A11y.label(sendButton, R.string.Send);
```

## ج) تست با TalkBack

هر جا فقط «Button» شنیدی، همان View را پیدا کن و برچسب بده. برچسب‌گذاری کامل تدریجی است.
