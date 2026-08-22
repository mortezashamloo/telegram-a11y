# 05 – Forward without quote as a **separate** option

**هدف:** گزینهٔ «فوروارد بدون نقل‌قول» جدا و مستقل از «فوروارد» معمولی باشد.

- **Forward** معمولی → رفتار رسمی
- **Forward without quote** → همیشه `drop_author = true`

## فایل‌ها

1. `ChatActivity.java`
2. `SendMessagesHelper.java`

## ChatActivity.java

```java
private final static int forward_no_quote = 111;   // a11y-fork
public static boolean IS_FORWARD_NO_QUOTE = false; // a11y-fork
```

Handler:

```java
} else if (id == forward || id == forward_no_quote) {
    IS_FORWARD_NO_QUOTE = (id == forward_no_quote);
    openForward();
}
```

ActionMode (بعد از Forward عادی):

```java
actionModeViews.add(actionMode.addItemWithWidth(
    forward_no_quote,
    R.drawable.msg_forward,
    AndroidUtilities.dp(54),
    "Forward without quote"
));
```

منوی long-press:

```java
items.add("Forward without quote");
options.add(202);
icons.add(R.drawable.msg_forward);
```

```java
case 202: {
    IS_FORWARD_NO_QUOTE = true;
    // same openForward / DialogsActivity path
    break;
}
```

## SendMessagesHelper.java

```java
req.drop_author = forwardFromMyName || org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE;
org.telegram.ui.ChatActivity.IS_FORWARD_NO_QUOTE = false;
```

## نتیجه برای TalkBack

دو گزینهٔ جدا:
- Forward
- Forward without quote
