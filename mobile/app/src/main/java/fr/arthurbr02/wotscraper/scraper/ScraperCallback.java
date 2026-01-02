package fr.arthurbr02.wotscraper.scraper;

import androidx.annotation.NonNull;

import fr.arthurbr02.wotscraper.export.ExportData;

public interface ScraperCallback {
    void onPhaseChanged(@NonNull ScrapingPhase phase);

    void onProgressUpdate(int current, int total, @NonNull String message);

    void onLog(@NonNull LogLevel level, @NonNull String message);

    void onError(@NonNull Exception e, boolean fatal);

    void onDataCollected(@NonNull ExportData partialData);

    void onComplete(@NonNull ExportData finalData);
}
