package fr.arthurbr02.wotscraper.scraper.model.battledetail;

import java.util.ArrayList;
import java.util.Collections;
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
        if (players == null || players.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> ids = new ArrayList<>(players.size());
        for (BattlePlayer p : players) {
            if (p != null && p.getPlayerId() != null) {
                ids.add(p.getPlayerId());
            }
        }
        return ids;
    }
}
