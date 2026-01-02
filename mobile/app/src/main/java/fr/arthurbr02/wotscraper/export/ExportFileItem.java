package fr.arthurbr02.wotscraper.export;

import androidx.annotation.NonNull;

public class ExportFileItem {

    @NonNull public final String name;
    @NonNull public final String absolutePath;
    public final long sizeBytes;
    public final long lastModifiedMs;

    public ExportFileItem(
            @NonNull String name,
            @NonNull String absolutePath,
            long sizeBytes,
            long lastModifiedMs
    ) {
        this.name = name;
        this.absolutePath = absolutePath;
        this.sizeBytes = sizeBytes;
        this.lastModifiedMs = lastModifiedMs;
    }

    public long stableId() {
        return (absolutePath + ":" + lastModifiedMs + ":" + sizeBytes).hashCode();
    }
}
