package org.telegram.messenger;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;

/**
 * Accessibility-fork user preferences + simple settings dialog.
 * All user-facing strings are Android string resources (values/strings.xml,
 * values-fa/strings.xml) so they follow the device/app language automatically.
 */
public class A11yConfig {

    public static final String PREF_PROGRESS_STEP = "a11y_progress_step";
    public static final String PREF_VOICE_QUALITY = "a11y_voice_quality";
    public static final String PREF_HIDE_SPONSOR = "a11y_hide_sponsor_channel";
    public static final String PREF_GHOST_MODE = "a11y_ghost_mode";
    public static final String PREF_SHOW_STATUS_IN_PREVIEW = "a11y_show_status_preview";

    public static int getProgressStep() {
        try {
            int step = MessagesController.getGlobalMainSettings().getInt(PREF_PROGRESS_STEP, 5);
            if (step != 1 && step != 5 && step != 10 && step != 20) {
                step = 5;
            }
            return step;
        } catch (Throwable ignore) {
            return 5;
        }
    }

    public static void setProgressStep(int step) {
        try {
            if (step != 1 && step != 5 && step != 10 && step != 20) {
                step = 5;
            }
            MessagesController.getGlobalMainSettings().edit().putInt(PREF_PROGRESS_STEP, step).apply();
        } catch (Throwable ignore) {
        }
    }

    public static int getVoiceQuality() {
        try {
            return MessagesController.getGlobalMainSettings().getInt(PREF_VOICE_QUALITY, 1);
        } catch (Throwable ignore) {
            return 1;
        }
    }

    public static void setVoiceQuality(int q) {
        try {
            if (q < 0) q = 0;
            if (q > 2) q = 2;
            MessagesController.getGlobalMainSettings().edit().putInt(PREF_VOICE_QUALITY, q).apply();
            applyVoiceBitrateToNative();
        } catch (Throwable ignore) {
        }
    }

    public static int voiceBitrateForQuality(int q) {
        if (q <= 0) return 16000;
        if (q == 1) return 32000;
        return 64000;
    }

    public static void applyVoiceBitrateToNative() {
        try {
            int br = voiceBitrateForQuality(getVoiceQuality());
            MediaController.getInstance().setRecordBitrate(br);
        } catch (Throwable ignore) {
        }
    }

    public static String progressStepLabel() {
        return LocaleController.formatString(R.string.A11yProgressStepLabel, getProgressStep());
    }

    // Accessibility-fork: hide the proxy sponsor/promo channel from the chat list
    public static boolean getHideSponsorChannel() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_HIDE_SPONSOR, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setHideSponsorChannel(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_HIDE_SPONSOR, value).apply();
        } catch (Throwable ignore) {
        }
    }

    // Accessibility-fork: Ghost Mode -- suppress outgoing read receipts
    // ("seen") so the sender can't tell you've read their message. Local
    // unread badges for you may not clear while this is on -- see
    // ChatActivity's markDialogAsRead call sites.
    public static boolean getGhostMode() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_GHOST_MODE, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setGhostMode(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_GHOST_MODE, value).apply();
        } catch (Throwable ignore) {
        }
    }

    // Accessibility-fork: announce contact online/last-seen status at the
    // end of the chat-list preview (e.g. "Leila: online")
    public static boolean getShowStatusInPreview() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_SHOW_STATUS_IN_PREVIEW, true);
        } catch (Throwable ignore) {
            return true;
        }
    }

    public static void setShowStatusInPreview(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_SHOW_STATUS_IN_PREVIEW, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static String voiceQualityLabel() {
        int q = getVoiceQuality();
        if (q <= 0) return LocaleController.getString(R.string.A11yVoiceLow);
        if (q == 1) return LocaleController.getString(R.string.A11yVoiceMedium);
        return LocaleController.getString(R.string.A11yVoiceHigh);
    }

    private static String onOff(boolean value) {
        return LocaleController.getString(value ? R.string.A11yOn : R.string.A11yOff);
    }

    public static void showSettingsDialog(Activity activity) {
        if (activity == null) {
            return;
        }
        try {
            final String[] items = new String[]{
                    LocaleController.formatString(R.string.A11yProgressAnnounceLabel, progressStepLabel()),
                    LocaleController.formatString(R.string.A11yVoiceQualityLabel, voiceQualityLabel()),
                    LocaleController.formatString(R.string.A11yHideSponsorLabel, onOff(getHideSponsorChannel())),
                    LocaleController.formatString(R.string.A11yGhostModeLabel, onOff(getGhostMode())),
                    LocaleController.formatString(R.string.A11yStatusPreviewLabel, onOff(getShowStatusInPreview()))
            };
            new AlertDialog.Builder(activity)
                    .setTitle(LocaleController.getString(R.string.A11yAccessibleSettingsTitle))
                    .setItems(items, (dialog, which) -> {
                        if (which == 0) {
                            showProgressStepPicker(activity);
                        } else if (which == 1) {
                            showVoiceQualityPicker(activity);
                        } else if (which == 2) {
                            setHideSponsorChannel(!getHideSponsorChannel());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.getString(getHideSponsorChannel() ? R.string.A11ySponsorHidden : R.string.A11ySponsorShown));
                            } catch (Throwable ignore) {
                            }
                        } else if (which == 3) {
                            setGhostMode(!getGhostMode());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.getString(getGhostMode() ? R.string.A11yGhostOn : R.string.A11yGhostOff));
                            } catch (Throwable ignore) {
                            }
                        } else if (which == 4) {
                            setShowStatusInPreview(!getShowStatusInPreview());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.getString(getShowStatusInPreview() ? R.string.A11yStatusOn : R.string.A11yStatusOff));
                            } catch (Throwable ignore) {
                            }
                        }
                    })
                    .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                    .show();
        } catch (Throwable ignore) {
        }
    }

    private static void showProgressStepPicker(Activity activity) {
        final int[] steps = new int[]{1, 5, 10, 20};
        final String[] labels = new String[steps.length];
        for (int i = 0; i < steps.length; i++) {
            labels[i] = LocaleController.formatString(R.string.A11yProgressStepLabel, steps[i]);
        }
        int cur = getProgressStep();
        int checked = 1;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] == cur) checked = i;
        }
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11yProgressStepPickerTitle))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setProgressStep(steps[which]);
                    d.dismiss();
                    try {
                        activity.getWindow().getDecorView().announceForAccessibility(labels[which]);
                    } catch (Throwable ignore) {
                    }
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }

    private static void showVoiceQualityPicker(Activity activity) {
        final String[] labels = new String[]{
                LocaleController.getString(R.string.A11yVoiceLow),
                LocaleController.getString(R.string.A11yVoiceMedium),
                LocaleController.getString(R.string.A11yVoiceHigh)
        };
        int checked = getVoiceQuality();
        if (checked < 0 || checked > 2) checked = 1;
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11yVoiceQualityPickerTitle))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setVoiceQuality(which);
                    d.dismiss();
                    try {
                        activity.getWindow().getDecorView().announceForAccessibility(labels[which]);
                    } catch (Throwable ignore) {
                    }
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }
}
