package fr.arthurbr02.wotscraper.scraper.progress;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import fr.arthurbr02.wotscraper.scraper.ScrapingPhase;
import fr.arthurbr02.wotscraper.scraper.model.battledetail.BattleDetail;
import fr.arthurbr02.wotscraper.scraper.model.combinedbattles.CombinedBattles;
import fr.arthurbr02.wotscraper.scraper.model.player.Player;

public class ProgressState {

    private String sessionId;
    private String initialPlayerId;

    private long startTimeMs;
    private long lastUpdateTimeMs;

    private ScrapingPhase currentPhase;

    private CombinedBattles combinedBattles;

    // Battle details fetching can be resumed mid-stream
    private List<Long> pendingArenaIds;
    private int currentArenaIndex;
    private Set<Long> queuedArenaIds;

    private List<BattleDetail> battleDetails;
    private Set<Long> processedArenaIds;

    private Set<Long> processedPlayerIds;
    private List<Long> pendingPlayerIds;

    private List<Player> players;

    // Player details fetching can be resumed mid-stream
    private List<Long> pendingPlayerDetailIds;
    private Set<Long> processedPlayerDetailIds;
    private int currentPlayerDetailIndex;

    private int currentPlayerIndex;
    private int totalPlayersToFetch;

    public ProgressState() {
        this.pendingArenaIds = new ArrayList<>();
        this.battleDetails = new ArrayList<>();
        this.processedArenaIds = new HashSet<>();
        this.queuedArenaIds = new HashSet<>();
        this.processedPlayerIds = new HashSet<>();
        this.pendingPlayerIds = new ArrayList<>();
        this.players = new ArrayList<>();
        this.pendingPlayerDetailIds = new ArrayList<>();
        this.processedPlayerDetailIds = new HashSet<>();

        long now = System.currentTimeMillis();
        this.startTimeMs = now;
        this.lastUpdateTimeMs = now;
        this.currentPhase = ScrapingPhase.NOT_STARTED;
    }

    public void ensureInitialized() {
        if (currentPhase == null) {
            currentPhase = ScrapingPhase.NOT_STARTED;
        }
        if (pendingArenaIds == null) {
            pendingArenaIds = new ArrayList<>();
        }
        if (battleDetails == null) {
            battleDetails = new ArrayList<>();
        }
        if (processedArenaIds == null) {
            processedArenaIds = new HashSet<>();
        }
        if (queuedArenaIds == null) {
            queuedArenaIds = new HashSet<>();
        }
        queuedArenaIds.addAll(processedArenaIds);
        queuedArenaIds.addAll(pendingArenaIds);
        if (processedPlayerIds == null) {
            processedPlayerIds = new HashSet<>();
        }
        if (pendingPlayerIds == null) {
            pendingPlayerIds = new ArrayList<>();
        }
        if (players == null) {
            players = new ArrayList<>();
        }
        if (pendingPlayerDetailIds == null) {
            pendingPlayerDetailIds = new ArrayList<>();
        }
        if (processedPlayerDetailIds == null) {
            processedPlayerDetailIds = new HashSet<>();
        }
        if (currentArenaIndex < 0) {
            currentArenaIndex = 0;
        }
        if (currentPlayerIndex < 0) {
            currentPlayerIndex = 0;
        }
        if (currentPlayerDetailIndex < 0) {
            currentPlayerDetailIndex = 0;
        }
        if (totalPlayersToFetch < 0) {
            totalPlayersToFetch = 0;
        }
    }

    /**
     * Creates a persistence snapshot so background JSON writes don't iterate over
     * collections being mutated by the scraping thread.
     */
    @NonNull
    public ProgressState snapshot() {
        ProgressState copy = new ProgressState();

        copy.sessionId = this.sessionId;
        copy.initialPlayerId = this.initialPlayerId;
        copy.startTimeMs = this.startTimeMs;
        copy.lastUpdateTimeMs = this.lastUpdateTimeMs;
        copy.currentPhase = this.currentPhase;
        copy.combinedBattles = this.combinedBattles;

        copy.pendingArenaIds = this.pendingArenaIds != null ? new ArrayList<>(this.pendingArenaIds) : new ArrayList<>();
        copy.currentArenaIndex = this.currentArenaIndex;
        copy.queuedArenaIds = this.queuedArenaIds != null ? new HashSet<>(this.queuedArenaIds) : new HashSet<>();

        copy.battleDetails = this.battleDetails != null ? new ArrayList<>(this.battleDetails) : new ArrayList<>();
        copy.processedArenaIds = this.processedArenaIds != null ? new HashSet<>(this.processedArenaIds) : new HashSet<>();

        copy.processedPlayerIds = this.processedPlayerIds != null ? new HashSet<>(this.processedPlayerIds) : new HashSet<>();
        copy.pendingPlayerIds = this.pendingPlayerIds != null ? new ArrayList<>(this.pendingPlayerIds) : new ArrayList<>();

        copy.players = this.players != null ? new ArrayList<>(this.players) : new ArrayList<>();

        copy.pendingPlayerDetailIds = this.pendingPlayerDetailIds != null ? new ArrayList<>(this.pendingPlayerDetailIds) : new ArrayList<>();
        copy.processedPlayerDetailIds = this.processedPlayerDetailIds != null ? new HashSet<>(this.processedPlayerDetailIds) : new HashSet<>();
        copy.currentPlayerDetailIndex = this.currentPlayerDetailIndex;

        copy.currentPlayerIndex = this.currentPlayerIndex;
        copy.totalPlayersToFetch = this.totalPlayersToFetch;

        copy.ensureInitialized();
        return copy;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getInitialPlayerId() {
        return initialPlayerId;
    }

    public void setInitialPlayerId(String initialPlayerId) {
        this.initialPlayerId = initialPlayerId;
    }

    public long getStartTimeMs() {
        return startTimeMs;
    }

    public void setStartTimeMs(long startTimeMs) {
        this.startTimeMs = startTimeMs;
    }

    public long getLastUpdateTimeMs() {
        return lastUpdateTimeMs;
    }

    public void setLastUpdateTimeMs(long lastUpdateTimeMs) {
        this.lastUpdateTimeMs = lastUpdateTimeMs;
    }

    public ScrapingPhase getCurrentPhase() {
        return currentPhase;
    }

    public void setCurrentPhase(ScrapingPhase currentPhase) {
        this.currentPhase = currentPhase;
    }

    public CombinedBattles getCombinedBattles() {
        return combinedBattles;
    }

    public void setCombinedBattles(CombinedBattles combinedBattles) {
        this.combinedBattles = combinedBattles;
    }

    public List<Long> getPendingArenaIds() {
        return pendingArenaIds;
    }

    public void setPendingArenaIds(List<Long> pendingArenaIds) {
        this.pendingArenaIds = pendingArenaIds;
    }

    public int getCurrentArenaIndex() {
        return currentArenaIndex;
    }

    public void setCurrentArenaIndex(int currentArenaIndex) {
        this.currentArenaIndex = currentArenaIndex;
    }

    public Set<Long> getQueuedArenaIds() {
        return queuedArenaIds;
    }

    public void setQueuedArenaIds(Set<Long> queuedArenaIds) {
        this.queuedArenaIds = queuedArenaIds;
    }

    public List<BattleDetail> getBattleDetails() {
        return battleDetails;
    }

    public void setBattleDetails(List<BattleDetail> battleDetails) {
        this.battleDetails = battleDetails;
    }

    public Set<Long> getProcessedArenaIds() {
        return processedArenaIds;
    }

    public void setProcessedArenaIds(Set<Long> processedArenaIds) {
        this.processedArenaIds = processedArenaIds;
    }

    public Set<Long> getProcessedPlayerIds() {
        return processedPlayerIds;
    }

    public void setProcessedPlayerIds(Set<Long> processedPlayerIds) {
        this.processedPlayerIds = processedPlayerIds;
    }

    public List<Long> getPendingPlayerIds() {
        return pendingPlayerIds;
    }

    public void setPendingPlayerIds(List<Long> pendingPlayerIds) {
        this.pendingPlayerIds = pendingPlayerIds;
    }

    public List<Player> getPlayers() {
        return players;
    }

    public void setPlayers(List<Player> players) {
        this.players = players;
    }

    public List<Long> getPendingPlayerDetailIds() {
        return pendingPlayerDetailIds;
    }

    public void setPendingPlayerDetailIds(List<Long> pendingPlayerDetailIds) {
        this.pendingPlayerDetailIds = pendingPlayerDetailIds;
    }

    public Set<Long> getProcessedPlayerDetailIds() {
        return processedPlayerDetailIds;
    }

    public void setProcessedPlayerDetailIds(Set<Long> processedPlayerDetailIds) {
        this.processedPlayerDetailIds = processedPlayerDetailIds;
    }

    public int getCurrentPlayerDetailIndex() {
        return currentPlayerDetailIndex;
    }

    public void setCurrentPlayerDetailIndex(int currentPlayerDetailIndex) {
        this.currentPlayerDetailIndex = currentPlayerDetailIndex;
    }

    public int getCurrentPlayerIndex() {
        return currentPlayerIndex;
    }

    public void setCurrentPlayerIndex(int currentPlayerIndex) {
        this.currentPlayerIndex = currentPlayerIndex;
    }

    public int getTotalPlayersToFetch() {
        return totalPlayersToFetch;
    }

    public void setTotalPlayersToFetch(int totalPlayersToFetch) {
        this.totalPlayersToFetch = totalPlayersToFetch;
    }
}
