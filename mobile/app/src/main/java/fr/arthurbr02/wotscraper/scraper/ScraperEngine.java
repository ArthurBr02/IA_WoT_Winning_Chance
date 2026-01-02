package fr.arthurbr02.wotscraper.scraper;

import android.content.Context;

import androidx.annotation.NonNull;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import fr.arthurbr02.wotscraper.export.ExportData;
import fr.arthurbr02.wotscraper.export.ExportManager;
import fr.arthurbr02.wotscraper.scraper.api.ApiClient;
import fr.arthurbr02.wotscraper.scraper.api.BattleDetailService;
import fr.arthurbr02.wotscraper.scraper.api.CombinedBattlesService;
import fr.arthurbr02.wotscraper.scraper.api.PlayerService;
import fr.arthurbr02.wotscraper.scraper.model.battledetail.BattleDetail;
import fr.arthurbr02.wotscraper.scraper.model.combinedbattles.CombinedBattles;
import fr.arthurbr02.wotscraper.scraper.model.player.Player;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressManager;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressState;
import fr.arthurbr02.wotscraper.util.PreferencesManager;

public class ScraperEngine {

    private final Context context;
    private final PreferencesManager preferences;
    private final ScraperCallback callback;

    private final CombinedBattlesService combinedBattlesService;
    private final BattleDetailService battleDetailService;
    private final PlayerService playerService;

    private volatile boolean stopRequested = false;

    public ScraperEngine(@NonNull Context context, @NonNull ScraperCallback callback) {
        this.context = context.getApplicationContext();
        this.preferences = new PreferencesManager(this.context);
        this.callback = callback;

        ApiClient apiClient = ApiClient.createDefault(
                () -> preferences.getRequestDelayMs(),
                () -> preferences.getTimeoutSeconds()
        );
        this.combinedBattlesService = new CombinedBattlesService(apiClient);
        this.battleDetailService = new BattleDetailService(apiClient);
        this.playerService = new PlayerService(apiClient);
    }

    public void requestStop() {
        stopRequested = true;
    }

    public void run() throws Exception {
        callback.onLog(LogLevel.INFO, "=== Starting scraper ===");

        ProgressState state = ProgressManager.loadProgress(context);
        if (state == null) {
            callback.onLog(LogLevel.INFO, "Starting new scraping session");
            state = new ProgressState();
            state.setSessionId("session_" + System.currentTimeMillis());
            state.setInitialPlayerId(preferences.getInitialPlayerId());
            state.setTotalPlayersToFetch(preferences.getMaxPlayers());
            state.setCurrentPhase(ScrapingPhase.COMBINED_BATTLES);
            ProgressManager.saveProgress(context, state);
        } else {
            callback.onLog(LogLevel.INFO, "Resuming from previous session");
            state.ensureInitialized();
        }

        // Always log exact resume indices so the Logs screen answers "where am I?" precisely.
        try {
            int arenaTotal = state.getPendingArenaIds() != null ? state.getPendingArenaIds().size() : 0;
            int playerPoolTotal = state.getPendingPlayerIds() != null ? state.getPendingPlayerIds().size() : 0;
            int playerDetailTotal = state.getPendingPlayerDetailIds() != null ? state.getPendingPlayerDetailIds().size() : 0;

            callback.onLog(
                    LogLevel.INFO,
                    "Resume snapshot: phase=" + state.getCurrentPhase()
                            + ", battleDetailsIndex=" + state.getCurrentArenaIndex() + "/" + arenaTotal
                            + ", playerPoolIndex=" + state.getCurrentPlayerIndex() + "/" + playerPoolTotal
                            + ", playerDetailsIndex=" + state.getCurrentPlayerDetailIndex() + "/" + playerDetailTotal
                            + ", battleDetailsCount=" + (state.getBattleDetails() != null ? state.getBattleDetails().size() : 0)
                            + ", playersCount=" + (state.getPlayers() != null ? state.getPlayers().size() : 0)
            );
        } catch (Exception ignored) {
        }

        try {
            executeScraping(state);

            state.setCurrentPhase(ScrapingPhase.COMPLETED);
            ProgressManager.saveProgress(context, state);

            ExportData finalData = new ExportData(state.getCombinedBattles(), state.getBattleDetails(), state.getPlayers());
            if (preferences.isAutoExportEnabled()) {
                try {
                    ExportManager.exportSnapshot(context, finalData);
                } catch (IOException ignored) {
                }
            }
            callback.onComplete(finalData);
        } catch (InterruptedException | InterruptedIOException e) {
            state.setCurrentPhase(ScrapingPhase.PAUSED);
            try {
                ProgressManager.saveProgress(context, state);
                if (preferences.isAutoExportEnabled()) {
                    ExportManager.exportLatest(context, new ExportData(state.getCombinedBattles(), state.getBattleDetails(), state.getPlayers()));
                }
            } catch (IOException ignored) {
            }
            callback.onLog(LogLevel.INFO, "Scraper paused");
        } catch (Exception e) {
            if (shouldStop()) {
                state.setCurrentPhase(ScrapingPhase.PAUSED);
                try {
                    ProgressManager.saveProgress(context, state);
                    if (preferences.isAutoExportEnabled()) {
                        ExportManager.exportLatest(context, new ExportData(state.getCombinedBattles(), state.getBattleDetails(), state.getPlayers()));
                    }
                } catch (IOException ignored) {
                }
                callback.onLog(LogLevel.INFO, "Scraper paused");
                return;
            }

            state.setCurrentPhase(ScrapingPhase.ERROR);
            try {
                ProgressManager.saveProgress(context, state);
                if (preferences.isAutoExportEnabled()) {
                    ExportManager.exportLatest(context, new ExportData(state.getCombinedBattles(), state.getBattleDetails(), state.getPlayers()));
                }
            } catch (IOException ignored) {
            }
            callback.onError(e, true);
            throw e;
        }
    }

    private void executeScraping(@NonNull ProgressState state) throws Exception {
        int saveEvery = Math.max(1, preferences.getSaveFrequencyIterations());

        // Step 1: CombinedBattles
        if (state.getCombinedBattles() == null) {
            state.setCurrentPhase(ScrapingPhase.COMBINED_BATTLES);
            callback.onPhaseChanged(ScrapingPhase.COMBINED_BATTLES);
            callback.onProgressUpdate(0, 1, "Fetching CombinedBattles…");
            callback.onLog(LogLevel.INFO, "Fetching initial CombinedBattles for player " + state.getInitialPlayerId());

            int pageSize = preferences.getCombinedBattlesPageSize();
            CombinedBattles combinedBattles = combinedBattlesService.fetchCombinedBattles(state.getInitialPlayerId(), pageSize);
            if (combinedBattles == null) {
                throw new IOException("Failed to fetch initial CombinedBattles");
            }
            state.setCombinedBattles(combinedBattles);
            callback.onProgressUpdate(1, 1, "CombinedBattles récupérées");

            List<Long> arenaIds = combinedBattles.getArenaIds();
            state.getPendingArenaIds().clear();
            state.getQueuedArenaIds().clear();
            state.getQueuedArenaIds().addAll(state.getProcessedArenaIds());
            for (Long arenaId : arenaIds) {
                if (arenaId == null) {
                    continue;
                }
                if (state.getQueuedArenaIds().add(arenaId)) {
                    state.getPendingArenaIds().add(arenaId);
                }
            }
            state.setCurrentArenaIndex(0);

            persist(state);
        }

        // Step 2: BattleDetails (resumable)
        processPendingArenaIds(state, saveEvery);

        // Build initial player pool if needed
        if (state.getPendingPlayerIds().isEmpty()) {
            Set<Long> playerIds = new HashSet<>();
            for (BattleDetail detail : state.getBattleDetails()) {
                if (detail == null) {
                    continue;
                }
                playerIds.addAll(detail.getPlayerIds());
            }

            List<Long> playerIdList = new ArrayList<>(playerIds);
            Collections.shuffle(playerIdList);
            int playersToProcess = Math.min(state.getTotalPlayersToFetch(), playerIdList.size());
            state.setPendingPlayerIds(new ArrayList<>(playerIdList.subList(0, playersToProcess)));
            state.setCurrentPlayerIndex(0);
            persist(state);
        }

        // Step 2 (continued): discover more arenaIds by walking players
        state.setCurrentPhase(ScrapingPhase.BATTLE_DETAILS);
        callback.onPhaseChanged(ScrapingPhase.BATTLE_DETAILS);

        List<Long> pendingPlayerIds = state.getPendingPlayerIds();
        int startIndex = state.getCurrentPlayerIndex();

        callback.onLog(LogLevel.INFO, "Processing players from index " + startIndex + " to " + pendingPlayerIds.size());

        for (int i = startIndex; i < pendingPlayerIds.size(); i++) {
            if (shouldStop()) {
                throw new InterruptedException("Stop requested");
            }

            Long playerId = pendingPlayerIds.get(i);
            if (playerId == null) {
                state.setCurrentPlayerIndex(i + 1);
                continue;
            }

            if (state.getProcessedPlayerIds().contains(playerId)) {
                state.setCurrentPlayerIndex(i + 1);
                continue;
            }

                callback.onProgressUpdate(
                    i + 1,
                    pendingPlayerIds.size(),
                    "PlayerPool [" + (i + 1) + "/" + pendingPlayerIds.size() + "] playerId=" + playerId
                );

            try {
                int pageSize = preferences.getCombinedBattlesPageSize();
                CombinedBattles playerCombinedBattles = combinedBattlesService.fetchCombinedBattles(String.valueOf(playerId), pageSize);
                if (playerCombinedBattles != null) {
                    List<Long> playerArenaIds = playerCombinedBattles.getArenaIds();
                    for (Long arenaId : playerArenaIds) {
                        if (arenaId == null) {
                            continue;
                        }
                        if (state.getProcessedArenaIds().contains(arenaId)) {
                            continue;
                        }
                        if (state.getQueuedArenaIds().add(arenaId)) {
                            state.getPendingArenaIds().add(arenaId);
                        }
                    }
                }

                state.getProcessedPlayerIds().add(playerId);
                state.setCurrentPlayerIndex(i + 1);

                if ((i + 1) % saveEvery == 0) {
                    persist(state);
                    processPendingArenaIds(state, saveEvery);
                }
            } catch (Exception e) {
                state.setCurrentPlayerIndex(i);
                persist(state);
                throw e;
            }
        }

        // Final pass to flush any remaining arenaIds
        persist(state);
        processPendingArenaIds(state, saveEvery);
        persist(state);

        // Step 3: Players (resumable)
        state.setCurrentPhase(ScrapingPhase.PLAYERS);
        callback.onPhaseChanged(ScrapingPhase.PLAYERS);

        if (state.getPendingPlayerDetailIds().isEmpty()) {
            Set<Long> allPlayerIds = new HashSet<>();
            for (BattleDetail detail : state.getBattleDetails()) {
                if (detail == null) {
                    continue;
                }
                allPlayerIds.addAll(detail.getPlayerIds());
            }
            state.setPendingPlayerDetailIds(new ArrayList<>(allPlayerIds));
            state.setCurrentPlayerDetailIndex(0);
            persist(state);
        }

        List<Long> playerIds = state.getPendingPlayerDetailIds();
        int playerStart = state.getCurrentPlayerDetailIndex();
        callback.onLog(LogLevel.INFO, "Fetching detailed players from index " + playerStart + " to " + playerIds.size());

        for (int i = playerStart; i < playerIds.size(); i++) {
            if (shouldStop()) {
                throw new InterruptedException("Stop requested");
            }

            Long playerId = playerIds.get(i);
            if (playerId == null) {
                state.setCurrentPlayerDetailIndex(i + 1);
                continue;
            }

            if (state.getProcessedPlayerDetailIds().contains(playerId)) {
                state.setCurrentPlayerDetailIndex(i + 1);
                continue;
            }

                callback.onProgressUpdate(
                    i + 1,
                    playerIds.size(),
                    "PlayerDetails [" + (i + 1) + "/" + playerIds.size() + "] playerId=" + playerId
                );

            Player player = playerService.fetchPlayer(playerId);
            if (player != null) {
                state.getPlayers().add(player);
                state.getProcessedPlayerDetailIds().add(playerId);
            }
            state.setCurrentPlayerDetailIndex(i + 1);

            if ((i + 1) % saveEvery == 0) {
                persist(state);
            }
        }

        persist(state);
    }

    private void processPendingArenaIds(@NonNull ProgressState state, int saveEvery) throws Exception {
        state.setCurrentPhase(ScrapingPhase.BATTLE_DETAILS);
        callback.onPhaseChanged(ScrapingPhase.BATTLE_DETAILS);

        List<Long> arenaIds = state.getPendingArenaIds();
        int start = state.getCurrentArenaIndex();
        if (arenaIds.isEmpty() || start >= arenaIds.size()) {
            return;
        }

        int initialIndex = start;
        callback.onLog(LogLevel.INFO, "Fetching battle details from index " + start + " to " + arenaIds.size());

        for (int i = start; i < arenaIds.size(); i++) {
            if (shouldStop()) {
                throw new InterruptedException("Stop requested");
            }

            Long arenaId = arenaIds.get(i);
            if (arenaId == null) {
                state.setCurrentArenaIndex(i + 1);
                continue;
            }

            if (state.getProcessedArenaIds().contains(arenaId)) {
                state.setCurrentArenaIndex(i + 1);
                continue;
            }

                callback.onProgressUpdate(
                    i + 1,
                    arenaIds.size(),
                    "BattleDetails [" + (i + 1) + "/" + arenaIds.size() + "] arenaId=" + arenaId
                );

            BattleDetail detail = battleDetailService.fetchBattleDetail(arenaId);
            if (detail == null) {
                throw new IOException("Empty battle detail for arena " + arenaId);
            }

            state.getBattleDetails().add(detail);
            state.getProcessedArenaIds().add(arenaId);
            state.setCurrentArenaIndex(i + 1);

            if ((i + 1) % saveEvery == 0) {
                persist(state);
            }
        }

        if (state.getCurrentArenaIndex() > initialIndex) {
            persist(state);
        }
    }

    private void persist(@NonNull ProgressState state) {
        ProgressState snapshot = state.snapshot();

        // Non-blocking persistence so scraping keeps progressing.
        ProgressManager.saveProgressAsync(context, snapshot);

        ExportData partial = new ExportData(snapshot.getCombinedBattles(), snapshot.getBattleDetails(), snapshot.getPlayers());
        if (preferences.isAutoExportEnabled()) {
            ExportManager.exportLatestAsync(context, partial);
        }

        callback.onDataCollected(partial);
    }

    private boolean shouldStop() {
        return stopRequested || Thread.currentThread().isInterrupted();
    }
}
