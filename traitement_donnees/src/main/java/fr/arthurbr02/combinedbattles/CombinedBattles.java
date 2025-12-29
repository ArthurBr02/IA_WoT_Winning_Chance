package fr.arthurbr02.combinedbattles;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

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
        if (data == null) {
            return new ArrayList<>();
        }

        Set<Long> arenaIds = new HashSet<>();
        for (Battle battle : data) {
            arenaIds.add(Long.valueOf(battle.getArenaId()));
        }

        return new ArrayList<>(arenaIds);
    }
}
