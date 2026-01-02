package fr.arthurbr02.wotscraper.scraper.model.battledetail;

import com.google.gson.annotations.SerializedName;

public class General {

    private Integer duration;
    private String map;

    @SerializedName("map_id")
    private Long mapId;

    @SerializedName("geometry_name")
    private String geometryName;

    @SerializedName("battle_time")
    private String battleTime;

    @SerializedName("arena_gui")
    private Integer arenaGui;

    @SerializedName("battle_type")
    private String battleType;

    @SerializedName("finish_reason")
    private Integer finishReason;

    public Integer getDuration() {
        return duration;
    }

    public void setDuration(Integer duration) {
        this.duration = duration;
    }

    public String getMap() {
        return map;
    }

    public void setMap(String map) {
        this.map = map;
    }

    public Long getMapId() {
        return mapId;
    }

    public void setMapId(Long mapId) {
        this.mapId = mapId;
    }

    public String getGeometryName() {
        return geometryName;
    }

    public void setGeometryName(String geometryName) {
        this.geometryName = geometryName;
    }

    public String getBattleTime() {
        return battleTime;
    }

    public void setBattleTime(String battleTime) {
        this.battleTime = battleTime;
    }

    public Integer getArenaGui() {
        return arenaGui;
    }

    public void setArenaGui(Integer arenaGui) {
        this.arenaGui = arenaGui;
    }

    public String getBattleType() {
        return battleType;
    }

    public void setBattleType(String battleType) {
        this.battleType = battleType;
    }

    public Integer getFinishReason() {
        return finishReason;
    }

    public void setFinishReason(Integer finishReason) {
        this.finishReason = finishReason;
    }
}
