# 03 – Announce upload/download percent (TalkBack)

## Why previous APK had no changes

Most “patches” were **documentation only** (`.md`). CI only auto-applies `*.patch` + a few sed lines. The APK you installed was built from an early workflow with almost **no real code edits**.

## NekoGram pattern

Nekogram exposes `AccConfig.announceFileProgress` (default `true`) and settings string `AccAnnounceFileProgress` (“Announce file progress”). The actual announce logic is meant to fire while file radial progress updates — throttle so TalkBack is not flooded.

Our CI injects equivalent behavior into Telegram’s `RadialProgress` (message media load/upload ring):

- On progress change, if accessibility is enabled
- Announce every **10%** step: `"Uploading 40 percent"` / `"Downloading 40 percent"` (or generic `"40 percent"`)
- Skip tiny deltas

## Implementation location

- `org.telegram.ui.Components.RadialProgress` — `setProgress(float, boolean)`
- Optionally `ChatMessageCell` when it updates `radialProgress`

## Manual test

1. TalkBack on
2. Send a large file / download a large media
3. Hear percent steps ~0, 10, 20, … 100
