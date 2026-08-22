# ۱) اول اسم، بعد نوع چت

**فایل:** `TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java`  
**متد:** `onPopulateAccessibilityEvent`

الان برای کانال/گروه این‌طور است (اول نوع، بعد اسم):

```java
} else if (chat != null) {
    if (chat.broadcast) {
        sb.append(getString(R.string.AccDescrChannel));
    } else {
        sb.append(getString(R.string.AccDescrGroup));
    }
    sb.append(". ");
    sb.append(chat.title);
    sb.append(". ");
}
```

### جایگزین کن با:

```java
} else if (chat != null) {
    // A11Y: name first, then type  →  "Grok, channel"
    sb.append(chat.title);
    sb.append(". ");
    if (chat.broadcast) {
        sb.append(getString(R.string.AccDescrChannel));
    } else {
        sb.append(getString(R.string.AccDescrGroup));
    }
    sb.append(". ");
}
```

برای بات هم اگر خواستی اول اسم باشد، بلوک `user.bot` را مشابه جابه‌جا کن:

```java
if (user.bot) {
    sb.append(ContactsController.formatName(user.first_name, user.last_name));
    sb.append(". ");
    sb.append(getString(R.string.Bot));
    sb.append(". ");
} else if (user.self) {
    ...
}
```

(در کد فعلی گاهی اول «Bot» و بعد اسم است.)
