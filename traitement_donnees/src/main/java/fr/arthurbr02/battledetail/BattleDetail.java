package fr.arthurbr02.battledetail;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class BattleDetail {
    private Meta meta;
    private General general;
    private Players players;

    public Meta getMeta() {
        return meta;
    }

    public void setMeta(Meta meta) {
        this.meta = meta;
    }

    public General getGeneral() {
        return general;
    }

    public void setGeneral(General general) {
        this.general = general;
    }

    public Players getPlayers() {
        return players;
    }

    public void setPlayers(Players players) {
        this.players = players;
    }

    public List<Long> getPlayerIds() {
        if (players == null) {
            return new ArrayList<>();
        }

        Set<Long> playerIds = new HashSet<>();
        for (Player player : players) {
            playerIds.add(player.getPlayerId());
        }

        return new ArrayList<>(playerIds);
    }

    public String getId() {
        return general != null ? general.getGeometryName() + "_" + general.getBattleTime().replaceAll(":", "_") : null;
    }

    public boolean isTeam1Won() {
        // (BattleDetail > Player avec spawn == 1 && won == true)
        if (players == null) {
            return false;
        }

        for (Player player : players) {
            if (player.getSpawn() == 1) {
                return player.getWon();
            }
        }

        return false;
    }
}
