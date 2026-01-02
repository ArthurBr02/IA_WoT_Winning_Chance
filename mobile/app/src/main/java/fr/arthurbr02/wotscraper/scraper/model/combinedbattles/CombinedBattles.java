package fr.arthurbr02.wotscraper.scraper.model.combinedbattles;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class CombinedBattles {
    private Meta meta;
    private Data data;

    public Meta getMeta() {
        return meta;
    }

    public void setMeta(Meta meta) {
        this.meta = meta;
    }

    public Data getData() {
        return data;
    }

    public void setData(Data data) {
        this.data = data;
    }

    public List<Long> getArenaIds() {
        if (data == null || data.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> ids = new ArrayList<>(data.size());
        for (Battle battle : data) {
            if (battle == null || battle.getArenaId() == null) {
                continue;
            }
            try {
                ids.add(Long.parseLong(battle.getArenaId()));
            } catch (NumberFormatException ignored) {
                // ignore malformed arena ids
            }
        }
        return ids;
    }
}
