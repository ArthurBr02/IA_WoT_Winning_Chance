package fr.arthurbr02.wotscraper.ui;

import androidx.annotation.NonNull;

import fr.arthurbr02.wotscraper.scraper.ScrapingPhase;

public class ScraperUiState {

    public final boolean running;
    @NonNull public final ScrapingPhase phase;

    public final long startedAtMs;

    public final int step1Current;
    public final int step1Total;
    @NonNull public final String step1Details;

    public final int step2Current;
    public final int step2Total;
    @NonNull public final String step2Details;

    public final int step3Current;
    public final int step3Total;
    @NonNull public final String step3Details;

    public final int battleDetailsCount;
    public final int playersCount;

    private ScraperUiState(
            boolean running,
            @NonNull ScrapingPhase phase,
            long startedAtMs,
            int step1Current,
            int step1Total,
            @NonNull String step1Details,
            int step2Current,
            int step2Total,
            @NonNull String step2Details,
            int step3Current,
            int step3Total,
            @NonNull String step3Details,
            int battleDetailsCount,
            int playersCount
    ) {
        this.running = running;
        this.phase = phase;
        this.startedAtMs = startedAtMs;
        this.step1Current = step1Current;
        this.step1Total = step1Total;
        this.step1Details = step1Details;
        this.step2Current = step2Current;
        this.step2Total = step2Total;
        this.step2Details = step2Details;
        this.step3Current = step3Current;
        this.step3Total = step3Total;
        this.step3Details = step3Details;
        this.battleDetailsCount = battleDetailsCount;
        this.playersCount = playersCount;
    }

    @NonNull
    public static ScraperUiState idle() {
        return new ScraperUiState(
                false,
                ScrapingPhase.NOT_STARTED,
                0L,
                0,
                1,
                "",
                0,
                0,
                "",
                0,
                0,
                "",
                0,
                0
        );
    }

    @NonNull
    public ScraperUiState withRunning(boolean running, long startedAtMs) {
        return new ScraperUiState(
                running,
                this.phase,
                startedAtMs,
                this.step1Current,
                this.step1Total,
                this.step1Details,
                this.step2Current,
                this.step2Total,
                this.step2Details,
                this.step3Current,
                this.step3Total,
                this.step3Details,
                this.battleDetailsCount,
                this.playersCount
        );
    }

    @NonNull
    public ScraperUiState withPhase(@NonNull ScrapingPhase phase) {
        return new ScraperUiState(
                this.running,
                phase,
                this.startedAtMs,
                this.step1Current,
                this.step1Total,
                this.step1Details,
                this.step2Current,
                this.step2Total,
                this.step2Details,
                this.step3Current,
                this.step3Total,
                this.step3Details,
                this.battleDetailsCount,
                this.playersCount
        );
    }

    @NonNull
    public ScraperUiState withStep1(int current, int total, @NonNull String details) {
        return new ScraperUiState(
                this.running,
                this.phase,
                this.startedAtMs,
                current,
                total,
                details,
                this.step2Current,
                this.step2Total,
                this.step2Details,
                this.step3Current,
                this.step3Total,
                this.step3Details,
                this.battleDetailsCount,
                this.playersCount
        );
    }

    @NonNull
    public ScraperUiState withStep2(int current, int total, @NonNull String details) {
        return new ScraperUiState(
                this.running,
                this.phase,
                this.startedAtMs,
                this.step1Current,
                this.step1Total,
                this.step1Details,
                current,
                total,
                details,
                this.step3Current,
                this.step3Total,
                this.step3Details,
                this.battleDetailsCount,
                this.playersCount
        );
    }

    @NonNull
    public ScraperUiState withStep3(int current, int total, @NonNull String details) {
        return new ScraperUiState(
                this.running,
                this.phase,
                this.startedAtMs,
                this.step1Current,
                this.step1Total,
                this.step1Details,
                this.step2Current,
                this.step2Total,
                this.step2Details,
                current,
                total,
                details,
                this.battleDetailsCount,
                this.playersCount
        );
    }

    @NonNull
    public ScraperUiState withCounts(int battleDetailsCount, int playersCount) {
        return new ScraperUiState(
                this.running,
                this.phase,
                this.startedAtMs,
                this.step1Current,
                this.step1Total,
                this.step1Details,
                this.step2Current,
                this.step2Total,
                this.step2Details,
                this.step3Current,
                this.step3Total,
                this.step3Details,
                battleDetailsCount,
                playersCount
        );
    }
}
