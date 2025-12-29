package fr.arthurbr02.utils;

import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.player.Player;

import java.util.*;

/**
 * Classe pour stocker l'état de progression du scraping
 */
public class ProgressState {
    private String initialPlayerId;
    private Date startTime;
    private Date lastUpdateTime;

    // Batailles déjà récupérées
    private List<BattleDetail> battleDetails;

    // IDs des arenas déjà traitées
    private Set<Long> processedArenaIds;

    // IDs des joueurs déjà traités
    private Set<Long> processedPlayerIds;

    // IDs des joueurs à traiter
    private List<Long> pendingPlayerIds;

    // Joueurs déjà récupérés
    private List<Player> players;

    // Index du joueur en cours de traitement
    private int currentPlayerIndex;

    // Total de joueurs à récupérer
    private int totalPlayersToFetch;

    public ProgressState() {
        this.battleDetails = new ArrayList<>();
        this.processedArenaIds = new HashSet<>();
        this.processedPlayerIds = new HashSet<>();
        this.pendingPlayerIds = new ArrayList<>();
        this.players = new ArrayList<>();
        this.currentPlayerIndex = 0;
        this.startTime = new Date();
        this.lastUpdateTime = new Date();
    }

    // Getters et Setters
    public String getInitialPlayerId() {
        return initialPlayerId;
    }

    public void setInitialPlayerId(String initialPlayerId) {
        this.initialPlayerId = initialPlayerId;
    }

    public Date getStartTime() {
        return startTime;
    }

    public void setStartTime(Date startTime) {
        this.startTime = startTime;
    }

    public Date getLastUpdateTime() {
        return lastUpdateTime;
    }

    public void setLastUpdateTime(Date lastUpdateTime) {
        this.lastUpdateTime = lastUpdateTime;
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

