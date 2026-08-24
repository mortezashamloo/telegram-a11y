package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Accessibility-fork user preferences.
 * Stored in global main settings.
 */
public class A11yConfig {

    public static final String PREF_PROGRESS_STEP = "a11y_progress_step";
    public static final String PREF_VOICE_QUALITY = "a11y_voice_quality"; // 0 low, 1 medium, 2 high

    /** Progress announce step in percent: 1, 5, 10, 20 */
    public static int getProgressStep() {
        try {
            SharedPreferences p = MessagesController.getGlobalMainSettings();
            int step = p.getInt(PREF_PROGRESS_STEP, 5);
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

    /** 0=low ~16kbps, 1=medium ~32kbps, 2=high max */
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
        } catch (Throwable ignore) {
        }
    }

    public static int voiceBitrateForQuality(int q) {
        if (q <= 0) return 16000;
        if (q == 1) return 32000;
        return 64000; // high; still far below OPUS_BITRATE_MAX but clear speech
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
}
