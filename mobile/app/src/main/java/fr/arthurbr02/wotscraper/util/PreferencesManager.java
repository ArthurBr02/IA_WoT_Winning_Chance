package fr.arthurbr02.wotscraper.util;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.annotation.NonNull;

public class PreferencesManager {

    private static final String PREFS_NAME = "wot_scraper_prefs";

    // Keep keys aligned with PLAN_IMPLEMENTATION.md (Phase 3) for consistency.
    private static final String KEY_REQUEST_DELAY_MS = "pref_request_delay";
    private static final String KEY_TIMEOUT_SECONDS = "pref_timeout";
    private static final String KEY_MAX_PLAYERS = "pref_players_count";
    private static final String KEY_INITIAL_PLAYER_ID = "pref_initial_player";
    private static final String KEY_SAVE_FREQUENCY = "pref_save_frequency";

    private static final String KEY_COMBINED_BATTLES_PAGE_SIZE = "pref_combined_battles_page_size";

    private static final String KEY_AUTO_EXPORT = "pref_auto_export";
    private static final String KEY_NOTIF_COMPLETE = "pref_notif_complete";
    private static final String KEY_NOTIF_ERROR = "pref_notif_error";
    private static final String KEY_NOTIF_PHASE = "pref_notif_phase";

    private static final String KEY_WAS_RUNNING = "was_running";

    private final SharedPreferences prefs;

    public PreferencesManager(@NonNull Context context) {
        this.prefs = context.getApplicationContext().getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public long getRequestDelayMs() {
        return prefs.getLong(KEY_REQUEST_DELAY_MS, 500L);
    }

    public void setRequestDelayMs(long value) {
        prefs.edit().putLong(KEY_REQUEST_DELAY_MS, value).apply();
    }

    public int getMaxPlayers() {
        return prefs.getInt(KEY_MAX_PLAYERS, 100);
    }

    public void setMaxPlayers(int value) {
        prefs.edit().putInt(KEY_MAX_PLAYERS, value).apply();
    }

    @NonNull
    public String getInitialPlayerId() {
        return prefs.getString(KEY_INITIAL_PLAYER_ID, "532440001");
    }

    public void setInitialPlayerId(@NonNull String value) {
        prefs.edit().putString(KEY_INITIAL_PLAYER_ID, value).apply();
    }

    public int getSaveFrequencyIterations() {
        return prefs.getInt(KEY_SAVE_FREQUENCY, 5);
    }

    public void setSaveFrequencyIterations(int value) {
        prefs.edit().putInt(KEY_SAVE_FREQUENCY, value).apply();
    }

    public int getCombinedBattlesPageSize() {
        return prefs.getInt(KEY_COMBINED_BATTLES_PAGE_SIZE, 50);
    }

    public void setCombinedBattlesPageSize(int value) {
        int safe = Math.max(1, Math.min(500, value));
        prefs.edit().putInt(KEY_COMBINED_BATTLES_PAGE_SIZE, safe).apply();
    }

    public boolean wasScraperRunning() {
        return prefs.getBoolean(KEY_WAS_RUNNING, false);
    }

    public void setScraperWasRunning(boolean value) {
        prefs.edit().putBoolean(KEY_WAS_RUNNING, value).apply();
    }

    public int getTimeoutSeconds() {
        return prefs.getInt(KEY_TIMEOUT_SECONDS, 30);
    }

    public void setTimeoutSeconds(int value) {
        prefs.edit().putInt(KEY_TIMEOUT_SECONDS, Math.max(5, value)).apply();
    }

    public boolean isAutoExportEnabled() {
        return prefs.getBoolean(KEY_AUTO_EXPORT, true);
    }

    public void setAutoExportEnabled(boolean value) {
        prefs.edit().putBoolean(KEY_AUTO_EXPORT, value).apply();
    }

    public boolean isCompleteNotificationEnabled() {
        return prefs.getBoolean(KEY_NOTIF_COMPLETE, true);
    }

    public void setCompleteNotificationEnabled(boolean value) {
        prefs.edit().putBoolean(KEY_NOTIF_COMPLETE, value).apply();
    }

    public boolean isErrorNotificationEnabled() {
        return prefs.getBoolean(KEY_NOTIF_ERROR, true);
    }

    public void setErrorNotificationEnabled(boolean value) {
        prefs.edit().putBoolean(KEY_NOTIF_ERROR, value).apply();
    }

    public boolean isPhaseNotificationEnabled() {
        return prefs.getBoolean(KEY_NOTIF_PHASE, false);
    }

    public void setPhaseNotificationEnabled(boolean value) {
        prefs.edit().putBoolean(KEY_NOTIF_PHASE, value).apply();
    }
}
