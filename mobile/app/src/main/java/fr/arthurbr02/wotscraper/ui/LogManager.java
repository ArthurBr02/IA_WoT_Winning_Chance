package fr.arthurbr02.wotscraper.ui;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import fr.arthurbr02.wotscraper.scraper.LogLevel;

public class LogManager {

    private static final int MAX_LOGS = 500;

    private static final LogManager INSTANCE = new LogManager();

    private final Object lock = new Object();
    private final ArrayList<LogEntry> buffer = new ArrayList<>();
    private final MutableLiveData<List<LogEntry>> liveData = new MutableLiveData<>(Collections.emptyList());

    private LogManager() {
    }

    @NonNull
    public static LogManager getInstance() {
        return INSTANCE;
    }

    @NonNull
    public LiveData<List<LogEntry>> getLogs() {
        return liveData;
    }

    public void add(@NonNull LogLevel level, @NonNull String message) {
        List<LogEntry> snapshot;
        synchronized (lock) {
            buffer.add(new LogEntry(System.currentTimeMillis(), level, message));
            if (buffer.size() > MAX_LOGS) {
                buffer.subList(0, buffer.size() - MAX_LOGS).clear();
            }
            snapshot = new ArrayList<>(buffer);
        }
        liveData.postValue(snapshot);
    }

    public void clear() {
        synchronized (lock) {
            buffer.clear();
        }
        liveData.postValue(Collections.emptyList());
    }
}
