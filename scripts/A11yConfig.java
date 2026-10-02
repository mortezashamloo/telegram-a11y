package org.telegram.messenger;

import android.app.Activity;
import android.app.AlertDialog;
import android.text.TextUtils;

/**
 * Accessibility-fork user preferences + settings dialog.
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
    public static final String PREF_LINKS_MENU = "a11y_links_menu";
    public static final String PREF_DOWNLOAD_STATE = "a11y_download_state";
    public static final String PREF_ALBUM_READING = "a11y_album_reading";
    public static final String PREF_USER_STATUS = "a11y_user_status_announce";
    public static final String PREF_CHAT_OPEN_SOUND = "a11y_chat_open_sound";
    public static final String PREF_ANNOUNCE_ADMIN_TAGS = "a11y_announce_admin_tags";

    public static final int SMALL_FILES_AUTO = 0;
    public static final int SMALL_FILES_VOICE_ONLY = 1;
    public static final int SMALL_FILES_OFF = 2;
    public static final long SMALL_FILE_MAX_SIZE = 512 * 1024;
    private static final String PREF_SMALL_FILES_MODE = "a11y_small_files_mode";

    // ------------------------------------------------------------------
    // Progress announce
    // ------------------------------------------------------------------
    public static int getProgressStep() {
        try {
            int step = MessagesController.getGlobalMainSettings().getInt(PREF_PROGRESS_STEP, 1);
            if (step != 1 && step != 5 && step != 10 && step != 20) {
                step = 1;
            }
            return step;
        } catch (Throwable ignore) {
            return 1;
        }
    }

    public static void setProgressStep(int step) {
        try {
            if (step != 1 && step != 5 && step != 10 && step != 20) {
                step = 1;
            }
            MessagesController.getGlobalMainSettings().edit().putInt(PREF_PROGRESS_STEP, step).apply();
        } catch (Throwable ignore) {
        }
    }

    public static String progressStepLabel() {
        return LocaleController.formatString(R.string.A11yProgressStepLabel, getProgressStep());
    }

    // ------------------------------------------------------------------
    // Voice message quality
    // ------------------------------------------------------------------
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

    public static String voiceQualityLabel() {
        int q = getVoiceQuality();
        if (q <= 0) return LocaleController.getString(R.string.A11yVoiceLow);
        if (q == 1) return LocaleController.getString(R.string.A11yVoiceMedium);
        return LocaleController.getString(R.string.A11yVoiceHigh);
    }

    // ------------------------------------------------------------------
    // Settings toggles
    // ------------------------------------------------------------------
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

    public static boolean getLinksMenuEnabled() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_LINKS_MENU, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setLinksMenuEnabled(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_LINKS_MENU, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static boolean getAnnounceDownloadState() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_DOWNLOAD_STATE, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setAnnounceDownloadState(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_DOWNLOAD_STATE, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static boolean getAlbumReading() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_ALBUM_READING, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setAlbumReading(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_ALBUM_READING, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static boolean getUserStatusAnnounce() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_USER_STATUS, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setUserStatusAnnounce(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_USER_STATUS, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static boolean getChatOpenSound() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_CHAT_OPEN_SOUND, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setChatOpenSound(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_CHAT_OPEN_SOUND, value).apply();
        } catch (Throwable ignore) {
        }
    }

    public static void playChatOpenSound() {
        try {
            if (!getChatOpenSound()) {
                return;
            }
            android.media.AudioManager am = (android.media.AudioManager) ApplicationLoader.applicationContext.getSystemService(android.content.Context.AUDIO_SERVICE);
            if (am != null) {
                am.playSoundEffect(android.media.AudioManager.FX_KEY_CLICK);
            }
        } catch (Throwable ignore) {
        }
    }

    public static boolean getAnnounceAdminTags() {
        try {
            return MessagesController.getGlobalMainSettings().getBoolean(PREF_ANNOUNCE_ADMIN_TAGS, false);
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static void setAnnounceAdminTags(boolean value) {
        try {
            MessagesController.getGlobalMainSettings().edit().putBoolean(PREF_ANNOUNCE_ADMIN_TAGS, value).apply();
        } catch (Throwable ignore) {
        }
    }

    // ------------------------------------------------------------------
    // Small files mode
    // ------------------------------------------------------------------
    public static int getSmallFilesAutoDownloadMode() {
        try {
            int mode = MessagesController.getGlobalMainSettings().getInt(PREF_SMALL_FILES_MODE, SMALL_FILES_VOICE_ONLY);
            return mode < SMALL_FILES_AUTO || mode > SMALL_FILES_OFF ? SMALL_FILES_VOICE_ONLY : mode;
        } catch (Throwable ignore) {
            return SMALL_FILES_VOICE_ONLY;
        }
    }

    public static void setSmallFilesAutoDownloadMode(int mode) {
        if (mode < SMALL_FILES_AUTO || mode > SMALL_FILES_OFF) mode = SMALL_FILES_VOICE_ONLY;
        try {
            MessagesController.getGlobalMainSettings().edit().putInt(PREF_SMALL_FILES_MODE, mode).apply();
            try { DownloadController.getInstance(UserConfig.selectedAccount).checkAutodownloadSettings(); } catch (Throwable ignore) {}
        } catch (Throwable ignore) {
        }
    }

    public static String getSmallFilesAutoDownloadModeLabel() {
        switch (getSmallFilesAutoDownloadMode()) {
            case SMALL_FILES_AUTO:
                return LocaleController.getString(R.string.A11ySmallFilesAuto);
            case SMALL_FILES_OFF:
                return LocaleController.getString(R.string.A11ySmallFilesOff);
            default:
                return LocaleController.getString(R.string.A11ySmallFilesVoiceOnly);
        }
    }

    public static String getSmallFilesAutoDownloadModeAnnouncement() {
        return LocaleController.formatString(R.string.A11ySmallFilesModeLabel, getSmallFilesAutoDownloadModeLabel());
    }

    public static boolean blockAutoDownload(int type, long size) {
        try {
            int mode = getSmallFilesAutoDownloadMode();
            if (mode == SMALL_FILES_AUTO || size > SMALL_FILE_MAX_SIZE) {
                return false;
            }
            if (mode == SMALL_FILES_OFF) {
                return true;
            }
            return type != DownloadController.AUTODOWNLOAD_TYPE_AUDIO;
        } catch (Throwable ignore) {
            return false;
        }
    }

    public static boolean allowSmallAutoDownload(int type, long size) {
        try {
            return getSmallFilesAutoDownloadMode() == SMALL_FILES_AUTO && size > 0 && size <= SMALL_FILE_MAX_SIZE;
        } catch (Throwable ignore) {
            return false;
        }
    }

    // ------------------------------------------------------------------
    // Solar calendar helpers
    // ------------------------------------------------------------------
    private static boolean a11yIsPersianUi() {
        try {
            java.util.Locale loc = LocaleController.getInstance().getCurrentLocale();
            if (loc == null) loc = java.util.Locale.getDefault();
            return "fa".equalsIgnoreCase(loc.getLanguage());
        } catch (Throwable ignore) {
            return "fa".equalsIgnoreCase(java.util.Locale.getDefault().getLanguage());
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

    public static String formatSolarDate(long unixSeconds) {
        try {
            java.util.Calendar cal = java.util.Calendar.getInstance();
            cal.setTimeInMillis(unixSeconds * 1000L);
            int gy = cal.get(java.util.Calendar.YEAR);
            int gm = cal.get(java.util.Calendar.MONTH) + 1;
            int gd = cal.get(java.util.Calendar.DAY_OF_MONTH);
            int jy;
            if (gy > 1600) { jy = 979; gy -= 1600; } else { jy = 0; gy -= 621; }
            int[] gdm = {0,31,59,90,120,151,181,212,243,273,304,334};
            int gy2 = gm > 2 ? gy + 1 : gy;
            int days = 365 * gy + (gy2 + 3) / 4 - (gy2 + 99) / 100 + (gy2 + 399) / 400 - 80 + gd + gdm[gm - 1];
            jy += 33 * (days / 12053); days %= 12053;
            jy += 4 * (days / 1461); days %= 1461;
            if (days > 365) { jy += (days - 1) / 365; }
            int jm = days < 186 ? 1 + days / 31 : 7 + (days - 186) / 30;
            int jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
            String[] faMonths = {"فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"};
            String[] enMonths = {"Farvardin","Ordibehesht","Khordad","Tir","Mordad","Shahrivar","Mehr","Aban","Azar","Dey","Bahman","Esfand"};
            boolean isFa = a11yIsPersianUi();
            String month = (isFa ? faMonths : enMonths)[jm - 1];
            java.util.Calendar now = java.util.Calendar.getInstance();
            int nowGy = now.get(java.util.Calendar.YEAR);
            int nowJy = nowGy > 1600 ? nowGy - 621 : nowGy;
            String value = jy == nowJy ? String.format(java.util.Locale.US, "%d %s", jd, month) : String.format(java.util.Locale.US, "%d %s %d", jd, month, jy);
            return LocaleController.formatString(R.string.A11ySolarDate, isFa ? toPersianDigits(value) : value);
        } catch (Throwable ignore) { return ""; }
    }

    public static String formatSolarDateChat(long unixSeconds, boolean checkYear) {
        try {
            long dateMs = unixSeconds * 1000L;
            java.util.Calendar msg = java.util.Calendar.getInstance();
            msg.setTimeInMillis(dateMs);
            int[] j = a11yGregorianToJalali(msg.get(java.util.Calendar.YEAR), msg.get(java.util.Calendar.MONTH) + 1, msg.get(java.util.Calendar.DAY_OF_MONTH));
            boolean shortForm = checkYear ? java.util.Calendar.getInstance().get(java.util.Calendar.YEAR) == msg.get(java.util.Calendar.YEAR) : Math.abs(System.currentTimeMillis() - dateMs) < 31536000000L;
            boolean isFa = a11yIsPersianUi();
            String[] faMonths = {"\u0641\u0631\u0648\u0631\u062f\u06cc\u0646","\u0627\u0631\u062f\u06cc\u0628\u0647\u0634\u062a","\u062e\u0631\u062f\u0627\u062f","\u062a\u06cc\u0631","\u0645\u0631\u062f\u0627\u062f","\u0634\u0647\u0631\u06cc\u0648\u0631","\u0645\u0647\u0631","\u0622\u0628\u0627\u0646","\u0622\u0630\u0631","\u062f\u06cc","\u0628\u0647\u0645\u0646","\u0627\u0633\u0641\u0646\u062f"};
            String[] enMonths = {"Farvardin","Ordibehesht","Khordad","Tir","Mordad","Shahrivar","Mehr","Aban","Azar","Dey","Bahman","Esfand"};
            String month = (isFa ? faMonths : enMonths)[j[1] - 1];
            String value = shortForm ? j[2] + " " + month : j[2] + " " + month + (isFa ? "\u060c " : ", ") + j[0];
            return isFa ? toPersianDigits(value) : value;
        } catch (Throwable ignore) { return ""; }
    }

    private static int[] a11yGregorianToJalali(int gy, int gm, int gd) {
        int jy = gy > 1600 ? 979 + (gy - 1600) : gy - 621;
        int[] gdm = {0,31,59,90,120,151,181,212,243,273,304,334};
        int gy2 = gm > 2 ? gy + 1 : gy;
        int days = 365 * gy + (gy2 + 3) / 4 - (gy2 + 99) / 100 + (gy2 + 399) / 400 - 80 + gd + gdm[gm - 1];
        jy += 33 * (days / 12053); days %= 12053;
        jy += 4 * (days / 1461); days %= 1461;
        if (days > 365) { jy += (days - 1) / 365; days = (days - 1) % 365; }
        int jm = days < 186 ? 1 + days / 31 : 7 + (days - 186) / 30;
        int jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
        return new int[]{jy, jm, jd};
    }

    // ------------------------------------------------------------------
    // Settings dialog (stays open on changes)
    // ------------------------------------------------------------------
    private static String onOff(boolean value) {
        return LocaleController.getString(value ? R.string.A11yOn : R.string.A11yOff);
    }

    private static void announce(Activity activity, String text) {
        try {
            if (activity != null && text != null) {
                activity.getWindow().getDecorView().announceForAccessibility(text);
            }
        } catch (Throwable ignore) {
        }
    }

    private static java.util.ArrayList<String> buildSettingsItems() {
        final java.util.ArrayList<String> items = new java.util.ArrayList<>();
        items.add(LocaleController.formatString(R.string.A11yProgressAnnounceLabel, progressStepLabel()));
        items.add(LocaleController.formatString(R.string.A11yVoiceQualityLabel, voiceQualityLabel()));
        items.add(LocaleController.formatString(R.string.A11yHideSponsorLabel, onOff(getHideSponsorChannel())));
        items.add(LocaleController.formatString(R.string.A11yGhostModeLabel, onOff(getGhostMode())));
        items.add(LocaleController.formatString(R.string.A11yStatusPreviewLabel, onOff(getShowStatusInPreview())));
        items.add(LocaleController.formatString(R.string.A11yForwardSavedNoQuoteLabel, onOff(getForwardSavedNoQuote())));
        items.add(LocaleController.formatString(R.string.A11yRecordingBeepLabel, onOff(getRecordingBeep())));
        items.add(LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar())));
        items.add(LocaleController.formatString(R.string.A11yLinksLabel, onOff(getLinksMenuEnabled())));
        items.add(getSmallFilesAutoDownloadModeAnnouncement());
        items.add(LocaleController.formatString(R.string.A11yDownloadStateLabel, onOff(getAnnounceDownloadState())));
        items.add(LocaleController.formatString(R.string.A11yAlbumReadingLabel, onOff(getAlbumReading())));
        items.add(LocaleController.formatString(R.string.A11yUserStatusLabel, onOff(getUserStatusAnnounce())));
        items.add(LocaleController.formatString(R.string.A11yChatOpenSoundLabel, onOff(getChatOpenSound())));
        items.add(LocaleController.formatString(R.string.A11yAdminTagsLabel, onOff(getAnnounceAdminTags())));
        return items;
    }

    public static void showSettingsDialog(final Activity activity) {
        if (activity == null) {
            return;
        }
        try {
            final java.util.ArrayList<String> items = buildSettingsItems();
            final android.widget.ArrayAdapter<String> adapter =
                    new android.widget.ArrayAdapter<>(activity, android.R.layout.simple_list_item_1, items);
            final Runnable refresh = () -> {
                items.clear();
                items.addAll(buildSettingsItems());
                adapter.notifyDataSetChanged();
            };
            final AlertDialog dialog = new AlertDialog.Builder(activity)
                    .setTitle(LocaleController.getString(R.string.A11yAccessibleSettingsTitle))
                    .setAdapter(adapter, null)
                    .setNegativeButton(LocaleController.getString(R.string.A11yClose), null)
                    .create();
            dialog.show();
            dialog.getListView().setOnItemClickListener((parent, view, which, id) -> handleSettingsClick(activity, which, refresh));
        } catch (Throwable ignore) {
        }
    }

    private static void handleSettingsClick(final Activity activity, int which, final Runnable refresh) {
        try {
            String message = null;
            switch (which) {
                case 0:
                    showProgressStepPicker(activity, refresh);
                    return;
                case 1:
                    showVoiceQualityPicker(activity, refresh);
                    return;
                case 2:
                    setHideSponsorChannel(!getHideSponsorChannel());
                    message = LocaleController.getString(getHideSponsorChannel() ? R.string.A11ySponsorHidden : R.string.A11ySponsorShown);
                    break;
                case 3:
                    setGhostMode(!getGhostMode());
                    message = LocaleController.getString(getGhostMode() ? R.string.A11yGhostOn : R.string.A11yGhostOff);
                    break;
                case 4:
                    setShowStatusInPreview(!getShowStatusInPreview());
                    message = LocaleController.getString(getShowStatusInPreview() ? R.string.A11yStatusOn : R.string.A11yStatusOff);
                    break;
                case 5:
                    setForwardSavedNoQuote(!getForwardSavedNoQuote());
                    message = LocaleController.formatString(R.string.A11yForwardSavedNoQuoteLabel, onOff(getForwardSavedNoQuote()));
                    break;
                case 6:
                    setRecordingBeep(!getRecordingBeep());
                    message = LocaleController.formatString(R.string.A11yRecordingBeepLabel, onOff(getRecordingBeep()));
                    break;
                case 7:
                    setSolarCalendar(!getSolarCalendar());
                    message = LocaleController.formatString(R.string.A11ySolarCalendarLabel, onOff(getSolarCalendar()));
                    break;
                case 8:
                    setLinksMenuEnabled(!getLinksMenuEnabled());
                    message = LocaleController.formatString(R.string.A11yLinksLabel, onOff(getLinksMenuEnabled()));
                    break;
                case 9:
                    showSmallFilesModePicker(activity, refresh);
                    return;
                case 10:
                    setAnnounceDownloadState(!getAnnounceDownloadState());
                    message = LocaleController.formatString(R.string.A11yDownloadStateLabel, onOff(getAnnounceDownloadState()));
                    break;
                case 11:
                    setAlbumReading(!getAlbumReading());
                    message = LocaleController.formatString(R.string.A11yAlbumReadingLabel, onOff(getAlbumReading()));
                    break;
                case 12:
                    setUserStatusAnnounce(!getUserStatusAnnounce());
                    message = LocaleController.formatString(R.string.A11yUserStatusLabel, onOff(getUserStatusAnnounce()));
                    break;
                case 13:
                    setChatOpenSound(!getChatOpenSound());
                    message = LocaleController.formatString(R.string.A11yChatOpenSoundLabel, onOff(getChatOpenSound()));
                    break;
                case 14:
                    setAnnounceAdminTags(!getAnnounceAdminTags());
                    message = LocaleController.formatString(R.string.A11yAdminTagsLabel, onOff(getAnnounceAdminTags()));
                    break;
                default:
                    return;
            }
            refresh.run();
            announce(activity, message);
        } catch (Throwable ignore) {
        }
    }

    private static void showProgressStepPicker(final Activity activity, final Runnable onChanged) {
        final int[] steps = new int[]{1, 5, 10, 20};
        final String[] labels = new String[steps.length];
        for (int i = 0; i < steps.length; i++) {
            labels[i] = LocaleController.formatString(R.string.A11yProgressStepLabel, steps[i]);
        }
        int cur = getProgressStep();
        int checked = 0;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] == cur) checked = i;
        }
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11yProgressStepPickerTitle))
                .setSingleChoiceItems(labels, checked, (d, which) -> {
                    setProgressStep(steps[which]);
                    d.dismiss();
                    if (onChanged != null) onChanged.run();
                    announce(activity, labels[which]);
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }

    private static void showVoiceQualityPicker(final Activity activity, final Runnable onChanged) {
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
                    if (onChanged != null) onChanged.run();
                    announce(activity, labels[which]);
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }

    private static void showSmallFilesModePicker(final Activity activity, final Runnable onChanged) {
        final String[] labels = new String[]{
                LocaleController.getString(R.string.A11ySmallFilesAuto),
                LocaleController.getString(R.string.A11ySmallFilesVoiceOnly),
                LocaleController.getString(R.string.A11ySmallFilesOff)
        };
        new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.A11ySmallFilesPickerTitle))
                .setSingleChoiceItems(labels, getSmallFilesAutoDownloadMode(), (d, which) -> {
                    setSmallFilesAutoDownloadMode(which);
                    d.dismiss();
                    if (onChanged != null) onChanged.run();
                    announce(activity, getSmallFilesAutoDownloadModeAnnouncement());
                })
                .setNegativeButton(LocaleController.getString(R.string.A11yCancel), null)
                .show();
    }
}