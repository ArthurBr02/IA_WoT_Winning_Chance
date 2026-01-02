package fr.arthurbr02.wotscraper.ui;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.ViewModel;

public class ScraperViewModel extends ViewModel {

    private final ScraperStateRepository stateRepository = ScraperStateRepository.getInstance();
    private final LogManager logManager = LogManager.getInstance();

    @NonNull
    public LiveData<ScraperUiState> getState() {
        return stateRepository.getState();
    }

    @NonNull
    public LiveData<java.util.List<LogEntry>> getLogs() {
        return logManager.getLogs();
    }
}
