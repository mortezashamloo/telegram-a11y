# 02 – Hide Share button between messages

**File:** `TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java`

In `checkNeedDrawShareButton` (or equivalent), make it always return false so the share icon between bubbles is never drawn. This speeds up TalkBack navigation (fewer focus stops).

```java
// a11y-fork: hide share button for faster TalkBack navigation
private boolean checkNeedDrawShareButton(MessageObject messageObject) {
    return false;
}
```

If the method has more logic, the simplest safe change is to add `return false;` at the very top.
