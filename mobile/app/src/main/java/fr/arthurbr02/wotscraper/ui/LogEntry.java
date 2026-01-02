package fr.arthurbr02.wotscraper.ui;

import androidx.annotation.NonNull;

import fr.arthurbr02.wotscraper.scraper.LogLevel;

public class LogEntry {
    public final long timestampMs;
    @NonNull public final LogLevel level;
    @NonNull public final String message;

    public LogEntry(long timestampMs, @NonNull LogLevel level, @NonNull String message) {
        this.timestampMs = timestampMs;
        this.level = level;
        this.message = message;
    }
}
