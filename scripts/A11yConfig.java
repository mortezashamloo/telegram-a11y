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
    public static final String PREF_HIDE_PROXY_SPONSOR = "a11y_hide_proxy_sponsor";
    public static final String PREF_ANNOUNCE_MUTED = "a11y_announce_muted";

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

    /** Hide proxy-sponsored channel from the chat list (default: true). */
    public static boolean isHideProxySponsor() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_HIDE_PROXY_SPONSOR, true);
        } catch (Throwable ignore) {
            return true;
        }
    }

    public static void setHideProxySponsor(boolean hide) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_HIDE_PROXY_SPONSOR, hide).apply();
            if (hide) {
                tryHideCurrentProxyPromo();
            }
        } catch (Throwable ignore) {
        }
    }

    /** If false (default), TalkBack does not say "muted" on chat rows. */
    public static boolean isAnnounceMuted() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_ANNOUNCE_MUTED, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setAnnounceMuted(boolean announce) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_ANNOUNCE_MUTED, announce).apply();
        } catch (Throwable ignore) {
        }
    }

    private static void tryHideCurrentProxyPromo() {
        try {
            for (int i = 0; i < UserConfig.MAX_ACCOUNT_COUNT; i++) {
                if (!UserConfig.getInstance(i).isClientActivated()) {
                    continue;
                }
                MessagesController mc = MessagesController.getInstance(i);
                if (mc.promoDialogType == MessagesController.PROMO_TYPE_PROXY) {
                    mc.hidePromoDialog();
                }
            }
        } catch (Throwable ignore) {
        }
    }

    public static void showSettingsDialog(Activity activity) {
        if (activity == null) {
            return;
        }
        try {
            final String[] items = new String[]{
                    "Progress announce: " + progressStepLabel(),
                    "Voice quality: " + voiceQualityLabel(),
                    "Hide proxy channel sponsor: " + (isHideProxySponsor() ? "On" : "Off"),
                    "Announce muted: " + (isAnnounceMuted() ? "On" : "Off")
            };
            new AlertDialog.Builder(activity)
                    .setTitle("Accessible settings")
                    .setItems(items, (dialog, which) -> {
                        if (which == 0) {
                            showProgressStepPicker(activity);
                        } else if (which == 1) {
                            showVoiceQualityPicker(activity);
                        } else if (which == 2) {
                            boolean next = !isHideProxySponsor();
                            setHideProxySponsor(next);
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        next ? "Hide proxy channel sponsor on" : "Hide proxy channel sponsor off");
                            } catch (Throwable ignore) {
                            }
                        } else if (which == 3) {
                            boolean next = !isAnnounceMuted();
                            setAnnounceMuted(next);
                            try {
                                activity.getWindow().getDecorView().announceForAccessibility(
                                        next ? "Announce muted on" : "Announce muted off");
                            } catch (Throwable ignore) {
                            }
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
