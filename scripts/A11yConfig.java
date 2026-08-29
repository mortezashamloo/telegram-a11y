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
    public static final String PREF_SHOW_PROXY_NEAR_CHATS = "a11y_show_proxy_near_chats";
    public static final String PREF_GHOST_MODE = "a11y_ghost_mode";

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

    /** Always show Proxy entry near chat list menu (default: true). */
    public static boolean isShowProxyNearChats() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_SHOW_PROXY_NEAR_CHATS, true);
        } catch (Throwable ignore) {
            return true;
        }
    }

    public static void setShowProxyNearChats(boolean show) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_SHOW_PROXY_NEAR_CHATS, show).apply();
        } catch (Throwable ignore) {
        }
    }

    /**
     * Ghost mode: no read receipts to server, no typing indicator.
     * Local unread badges still clear when you open a chat.
     */
    public static boolean isGhostMode() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_GHOST_MODE, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setGhostMode(boolean on) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_GHOST_MODE, on).apply();
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
                    "Announce muted: " + (isAnnounceMuted() ? "On" : "Off"),
                    "Show proxy near chats: " + (isShowProxyNearChats() ? "On" : "Off"),
                    "Ghost mode: " + (isGhostMode() ? "On" : "Off"),
                    "Open proxy settings"
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
                            announce(activity, next ? "Hide proxy channel sponsor on" : "Hide proxy channel sponsor off");
                        } else if (which == 3) {
                            boolean next = !isAnnounceMuted();
                            setAnnounceMuted(next);
                            announce(activity, next ? "Announce muted on" : "Announce muted off");
                        } else if (which == 4) {
                            boolean next = !isShowProxyNearChats();
                            setShowProxyNearChats(next);
                            announce(activity, next ? "Show proxy near chats on" : "Show proxy near chats off");
                        } else if (which == 5) {
                            boolean next = !isGhostMode();
                            setGhostMode(next);
                            announce(activity, next ? "Ghost mode on" : "Ghost mode off");
                        } else if (which == 6) {
                            openProxySettings(activity);
                        }
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
        } catch (Throwable ignore) {
        }
    }

    private static void announce(Activity activity, String msg) {
        try {
            activity.getWindow().getDecorView().announceForAccessibility(msg);
        } catch (Throwable ignore) {
        }
    }

    private static void openProxySettings(Activity activity) {
        try {
            if (activity instanceof org.telegram.ui.LaunchActivity) {
                ((org.telegram.ui.LaunchActivity) activity).presentFragment(new org.telegram.ui.ProxyListActivity());
                return;
            }
        } catch (Throwable ignore) {
        }
        announce(activity, "Open proxy from the chat list menu");
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
                    announce(activity, "Progress step " + steps[which] + " percent");
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
                    announce(activity, "Voice quality " + labels[which]);
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }
}
