package org.telegram.messenger;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;

/**
 * Accessibility-fork user preferences + bilingual settings dialog.
 */
public class A11yConfig {

    public static final String PREF_PROGRESS_STEP = "a11y_progress_step";
    public static final String PREF_VOICE_QUALITY = "a11y_voice_quality";
    public static final String PREF_HIDE_PROXY_SPONSOR = "a11y_hide_proxy_sponsor";
    public static final String PREF_ANNOUNCE_MUTED = "a11y_announce_muted";
    public static final String PREF_SHOW_PROXY_NEAR_CHATS = "a11y_show_proxy_near_chats";
    public static final String PREF_GHOST_MODE = "a11y_ghost_mode";
    public static final String PREF_ANNOUNCE_USER_STATUS = "a11y_announce_user_status";

    private static boolean isPersianUi() {
        try {
            LocaleController.LocaleInfo info = LocaleController.getInstance().getCurrentLocaleInfo();
            if (info != null && info.shortName != null) {
                String s = info.shortName.toLowerCase();
                return s.startsWith("fa") || s.contains("persian") || s.contains("farsi");
            }
        } catch (Throwable ignore) {
        }
        try {
            String lang = LocaleController.getInstance().getCurrentLocale().getLanguage();
            return lang != null && lang.toLowerCase().startsWith("fa");
        } catch (Throwable ignore) {
        }
        return false;
    }

    private static String onOff(boolean on) {
        if (isPersianUi()) {
            return on ? "\u0631\u0648\u0634\u0646" : "\u062e\u0627\u0645\u0648\u0634";
        }
        return on ? "On" : "Off";
    }

    private static String t(String en, String fa) {
        return isPersianUi() ? fa : en;
    }

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
        if (isPersianUi()) {
            if (q <= 0) return "\u06a9\u0645";
            if (q == 1) return "\u0645\u062a\u0648\u0633\u0637";
            return "\u0628\u0627\u0644\u0627";
        }
        if (q <= 0) return "Low";
        if (q == 1) return "Medium";
        return "High";
    }

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

    public static boolean isAnnounceUserStatus() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_ANNOUNCE_USER_STATUS, true);
        } catch (Throwable ignore) {
            return true;
        }
    }

    public static void setAnnounceUserStatus(boolean on) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_ANNOUNCE_USER_STATUS, on).apply();
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
                    t("Progress announcements", "\u0627\u0639\u0644\u0627\u0645 \u067e\u06cc\u0634\u0631\u0641\u062a") + ": " + progressStepLabel(),
                    t("Voice quality", "\u06a9\u06cc\u0641\u06cc\u062a \u067e\u06cc\u0627\u0645 \u0635\u0648\u062a\u06cc") + ": " + voiceQualityLabel(),
                    t("Hide proxy sponsor channel", "\u0645\u062e\u0641\u06cc \u06a9\u0627\u0646\u0627\u0644 \u0627\u0633\u067e\u0627\u0646\u0633\u0631 \u067e\u0631\u0648\u06a9\u0633\u06cc") + ": " + onOff(isHideProxySponsor()),
                    t("Announce muted", "\u0627\u0639\u0644\u0627\u0645 \u0645\u06cc\u0648\u062a") + ": " + onOff(isAnnounceMuted()),
                    t("Proxy next to chats", "\u067e\u0631\u0648\u06a9\u0633\u06cc \u06a9\u0646\u0627\u0631 \u0686\u062a\u200c\u0647\u0627") + ": " + onOff(isShowProxyNearChats()),
                    t("Ghost mode", "\u062d\u0627\u0644\u062a \u0631\u0648\u062d") + ": " + onOff(isGhostMode()),
                    t("Announce status (online / last seen)", "\u0627\u0639\u0644\u0627\u0645 \u0648\u0636\u0639\u06cc\u062a (\u0622\u0646\u0644\u0627\u06cc\u0646 / \u0622\u062e\u0631\u06cc\u0646 \u0628\u0627\u0632\u062f\u06cc\u062f)") + ": " + onOff(isAnnounceUserStatus()),
                    t("Open proxy settings", "\u0628\u0627\u0632 \u06a9\u0631\u062f\u0646 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u067e\u0631\u0648\u06a9\u0633\u06cc")
            };
            new AlertDialog.Builder(activity)
                    .setTitle(t("Accessible settings", "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u062f\u0633\u062a\u0631\u0633\u200c\u067e\u0630\u06cc\u0631\u06cc"))
                    .setItems(items, (dialog, which) -> {
                        if (which == 0) {
                            showProgressStepPicker(activity);
                        } else if (which == 1) {
                            showVoiceQualityPicker(activity);
                        } else if (which == 2) {
                            boolean next = !isHideProxySponsor();
                            setHideProxySponsor(next);
                            announce(activity, t("Hide proxy sponsor channel", "\u0645\u062e\u0641\u06cc \u06a9\u0627\u0646\u0627\u0644 \u0627\u0633\u067e\u0627\u0646\u0633\u0631") + " " + onOff(next));
                        } else if (which == 3) {
                            boolean next = !isAnnounceMuted();
                            setAnnounceMuted(next);
                            announce(activity, t("Announce muted", "\u0627\u0639\u0644\u0627\u0645 \u0645\u06cc\u0648\u062a") + " " + onOff(next));
                        } else if (which == 4) {
                            boolean next = !isShowProxyNearChats();
                            setShowProxyNearChats(next);
                            announce(activity, t("Proxy next to chats", "\u067e\u0631\u0648\u06a9\u0633\u06cc \u06a9\u0646\u0627\u0631 \u0686\u062a\u200c\u0647\u0627") + " " + onOff(next));
                        } else if (which == 5) {
                            boolean next = !isGhostMode();
                            setGhostMode(next);
                            announce(activity, t("Ghost mode", "\u062d\u0627\u0644\u062a \u0631\u0648\u062d") + " " + onOff(next));
                        } else if (which == 6) {
                            boolean next = !isAnnounceUserStatus();
                            setAnnounceUserStatus(next);
                            announce(activity, t("Announce status", "\u0627\u0639\u0644\u0627\u0645 \u0648\u0636\u0639\u06cc\u062a") + " " + onOff(next));
                        } else if (which == 7) {
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
        announce(activity, t("Open proxy from the chat list menu", "\u067e\u0631\u0648\u06a9\u0633\u06cc \u0631\u0627 \u0627\u0632 \u0645\u0646\u0648\u06cc \u0644\u06cc\u0633\u062a \u0686\u062a \u0628\u0627\u0632 \u06a9\u0646\u06cc\u062f"));
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
                .setTitle(t("Progress step", "\u06af\u0627\u0645 \u0627\u0639\u0644\u0627\u0645 \u067e\u06cc\u0634\u0631\u0641\u062a"))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setProgressStep(steps[which]);
                    d.dismiss();
                    announce(activity, t("Progress step", "\u06af\u0627\u0645 \u067e\u06cc\u0634\u0631\u0641\u062a") + " " + steps[which] + "%");
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }

    private static void showVoiceQualityPicker(Activity activity) {
        final String[] labels = isPersianUi()
                ? new String[]{"\u06a9\u0645", "\u0645\u062a\u0648\u0633\u0637", "\u0628\u0627\u0644\u0627"}
                : new String[]{"Low", "Medium", "High"};
        int checked = getVoiceQuality();
        if (checked < 0 || checked > 2) checked = 1;
        new AlertDialog.Builder(activity)
                .setTitle(t("Voice quality", "\u06a9\u06cc\u0641\u06cc\u062a \u067e\u06cc\u0627\u0645 \u0635\u0648\u062a\u06cc"))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setVoiceQuality(which);
                    d.dismiss();
                    announce(activity, t("Voice quality", "\u06a9\u06cc\u0641\u06cc\u062a \u0635\u062f\u0627") + " " + labels[which]);
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }
}
