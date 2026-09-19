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
    public static final String PREF_FORWARD_SAVED_NO_QUOTE = "a11y_forward_saved_no_quote";
    public static final String PREF_RECORDING_BEEP = "a11y_recording_beep";
    public static final String PREF_SOLAR_CALENDAR = "a11y_solar_calendar";

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

    // Accessibility-fork: Forward to Saved Messages without a quote.
    public static boolean getForwardSavedNoQuote() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_FORWARD_SAVED_NO_QUOTE, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setForwardSavedNoQuote(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_FORWARD_SAVED_NO_QUOTE, value).apply();
        } catch (Throwable ignore) {
        }
    }

    // Accessibility-fork: optional short beep when voice recording starts.
    // Disabled by default.
    public static boolean getRecordingBeep() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_RECORDING_BEEP, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setRecordingBeep(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_RECORDING_BEEP, value).apply();
        } catch (Throwable ignore) {
        }
    }

    // Accessibility-fork: optional Solar Hijri/Jalali date in chat-list
    // TalkBack descriptions. Disabled by default.
    public static boolean getSolarCalendar() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_SOLAR_CALENDAR, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setSolarCalendar(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_SOLAR_CALENDAR, value).apply();
        } catch (Throwable ignore) {
        }
    }

    /**
     * Convert a Unix timestamp (seconds) to a Solar Hijri/Jalali date.
     * The conversion is Gregorian -> Jalali and does not depend on any
     * third-party calendar library.
     */
    public static String formatSolarDate(int unixSeconds) {
        try {
            java.util.Calendar cal = java.util.Calendar.getInstance();
            cal.setTimeInMillis(((long) unixSeconds) * 1000L);
            int gy = cal.get(java.util.Calendar.YEAR);
            int gm = cal.get(java.util.Calendar.MONTH) + 1;
            int gd = cal.get(java.util.Calendar.DAY_OF_MONTH);

            int jy;
            if (gy > 1600) {
                jy = 979;
                gy -= 1600;
            } else {
                jy = 0;
                gy -= 621;
            }

            int[] gdm = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
            int gy2 = gm > 2 ? gy + 1 : gy;
            int days = 365 * gy
                    + (gy2 + 3) / 4
                    - (gy2 + 99) / 100
                    + (gy2 + 399) / 400
                    - 80 + gd + gdm[gm - 1];

            jy += 33 * (days / 12053);
            days %= 12053;
            jy += 4 * (days / 1461);
            days %= 1461;
            if (days > 365) {
                jy += (days - 1) / 365;
                days = (days - 1) % 365;
            }

            int jm = days < 186 ? 1 + days / 31 : 7 + (days - 186) / 30;
            int jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);

            String[] faMonths = {
                    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
            };
            String[] enMonths = {
                    "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
                    "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"
            };

            boolean fa = false;
            try {
                java.util.Locale locale = java.util.Locale.getDefault();
                fa = "fa".equalsIgnoreCase(locale.getLanguage());
            } catch (Throwable ignore) {
                fa = "fa".equalsIgnoreCase(java.util.Locale.getDefault().getLanguage());
            }

            String date = String.format(java.util.Locale.US, "%d %s %d",
                    jd, fa ? faMonths[jm - 1] : enMonths[jm - 1], jy);
            if (fa) {
                date = toPersianDigits(date);
            }
            return LocaleController.formatString(R.string.A11ySolarDate, date);
        } catch (Throwable ignore) {
            return "";
        }
    }

    private static String toPersianDigits(String value) {
        if (value == null) return "";
        return value
                .replace('0', '۰').replace('1', '۱').replace('2', '۲')
                .replace('3', '۳').replace('4', '۴').replace('5', '۵')
                .replace('6', '۶').replace('7', '۷').replace('8', '۸')
                .replace('9', '۹');
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
                    LocaleController.formatString(R.string.A11yStatusPreviewLabel, onOff(getShowStatusInPreview())),
                    LocaleController.formatString(R.string.A11yForwardSavedNoQuoteLabel, onOff(getForwardSavedNoQuote())),
                    LocaleController.formatString(R.string.A11yRecordingBeepLabel, onOff(getRecordingBeep())),
                    LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar()))
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
                        } else if (which == 5) {
                            setForwardSavedNoQuote(!getForwardSavedNoQuote());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.formatString(R.string.A11yForwardSavedNoQuoteLabel, onOff(getForwardSavedNoQuote())));
                            } catch (Throwable ignore) {
                            }
                        } else if (which == 6) {
                            setRecordingBeep(!getRecordingBeep());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.formatString(R.string.A11yRecordingBeepLabel, onOff(getRecordingBeep())));
                            } catch (Throwable ignore) {
                            }
                        } else if (which == 7) {
                            setSolarCalendar(!getSolarCalendar());
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar())));
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
