package fr.arthurbr02.combinedbattles;

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
        return data != null ? data.stream().map(battle -> Long.valueOf(battle.getArenaId())).toList() : List.of();
    }
}
