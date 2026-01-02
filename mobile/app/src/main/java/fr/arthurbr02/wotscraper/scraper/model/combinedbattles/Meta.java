package fr.arthurbr02.wotscraper.scraper.model.combinedbattles;

import com.google.gson.annotations.SerializedName;

public class Meta {
    private String status;

    @SerializedName("player_id")
    private Long playerId;

    private int page;

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Long getPlayerId() {
        return playerId;
    }

    public void setPlayerId(Long playerId) {
        this.playerId = playerId;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }
}
