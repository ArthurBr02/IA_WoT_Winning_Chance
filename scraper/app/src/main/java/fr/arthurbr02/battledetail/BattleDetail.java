package fr.arthurbr02.battledetail;

import java.util.List;

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
        return players != null ? players.stream().map(Player::getPlayerId).toList() : List.of();
    }
}
