package fr.arthurbr02.wotscraper.ui;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import fr.arthurbr02.wotscraper.scraper.ScrapingPhase;

public class ScraperStateRepository {

    private static final ScraperStateRepository INSTANCE = new ScraperStateRepository();

    private final MutableLiveData<ScraperUiState> state = new MutableLiveData<>(ScraperUiState.idle());

    private ScraperStateRepository() {
    }

    @NonNull
    public static ScraperStateRepository getInstance() {
        return INSTANCE;
    }

    @NonNull
    public LiveData<ScraperUiState> getState() {
        return state;
    }

    @NonNull
    public ScraperUiState getCurrent() {
        ScraperUiState current = state.getValue();
        return current != null ? current : ScraperUiState.idle();
    }

    public void setRunning(boolean running, long startedAtMs) {
        ScraperUiState next = getCurrent().withRunning(running, startedAtMs);
        if (android.os.Looper.myLooper() == android.os.Looper.getMainLooper()) {
            state.setValue(next);
        } else {
            state.postValue(next);
        }
    }

    public void setPhase(@NonNull ScrapingPhase phase) {
        state.postValue(getCurrent().withPhase(phase));
    }

    public void setStep1(int current, int total, @NonNull String details) {
        state.postValue(getCurrent().withStep1(current, total, details));
    }

    public void setStep2(int current, int total, @NonNull String details) {
        state.postValue(getCurrent().withStep2(current, total, details));
    }

    public void setStep3(int current, int total, @NonNull String details) {
        state.postValue(getCurrent().withStep3(current, total, details));
    }

    public void setCounts(int battleDetailsCount, int playersCount) {
        state.postValue(getCurrent().withCounts(battleDetailsCount, playersCount));
    }
}
