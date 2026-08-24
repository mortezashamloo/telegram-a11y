package org.telegram.messenger;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;

/**
 * Accessibility-fork user preferences + simple settings dialog.
 */
public class A11yConfig {

    public static final String PREF_PROGRESS_STEP = "a11y_progress_step";
    public static final String PREF_VOICE_QUALITY = "a11y_voice_quality";

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
        return getProgressStep() + "%";
    }

    public static String voiceQualityLabel() {
        int q = getVoiceQuality();
        if (q <= 0) return "Low";
        if (q == 1) return "Medium";
        return "High";
    }

    public static void showSettingsDialog(Activity activity) {
        if (activity == null) {
            return;
        }
        try {
            final String[] items = new String[]{
                    "Progress announce: " + progressStepLabel(),
                    "Voice quality: " + voiceQualityLabel()
            };
            new AlertDialog.Builder(activity)
                    .setTitle("Accessible settings")
                    .setItems(items, (dialog, which) -> {
                        if (which == 0) {
                            showProgressStepPicker(activity);
                        } else if (which == 1) {
                            showVoiceQualityPicker(activity);
                        }
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
        } catch (Throwable ignore) {
        }
    }

    private static void showProgressStepPicker(Activity activity) {
        final int[] steps = new int[]{1, 5, 10, 20};
        final String[] labels = new String[]{"1%", "5%", "10%", "20%"};
        int cur = getProgressStep();
        int checked = 1;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] == cur) checked = i;
        }
        new AlertDialog.Builder(activity)
                .setTitle("Progress announce step")
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setProgressStep(steps[which]);
                    d.dismiss();
                    try {
                        activity.getWindow().getDecorView().announceForAccessibility("Progress step " + steps[which] + " percent");
                    } catch (Throwable ignore) {
                    }
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }

    private static void showVoiceQualityPicker(Activity activity) {
        final String[] labels = new String[]{"Low", "Medium", "High"};
        int checked = getVoiceQuality();
        if (checked < 0 || checked > 2) checked = 1;
        new AlertDialog.Builder(activity)
                .setTitle("Voice message quality")
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setVoiceQuality(which);
                    d.dismiss();
                    try {
                        activity.getWindow().getDecorView().announceForAccessibility("Voice quality " + labels[which]);
                    } catch (Throwable ignore) {
                    }
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }
}
