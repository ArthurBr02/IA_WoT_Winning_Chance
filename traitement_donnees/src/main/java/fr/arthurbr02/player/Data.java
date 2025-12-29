package fr.arthurbr02.player;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Data {

    private String server;

    private Long id;

    private Integer battles;

    private Integer overallWN8;

    private Integer overallWNX;

    private Double avgTier;

    private Integer wins;

    private Integer losses;

    private Integer draws;

    private Long totalDamage;

    private Long totalDamageReceived;

    private Long totalAssist;

    private Integer totalFrags;

    private Integer totalDestroyed;

    private Integer totalSurvived;

    private Integer totalSpotted;

    private Integer totalCap;

    private Integer totalDef;

    private Long totalXp;

    private Double winrate;

    private Double lossrate;

    private Double drawrate;

    private Integer dpg;

    private Integer assist;

    private Double frags;

    private Double survival;

    private Double spots;

    private Double cap;

    private Double def;

    private Integer xp;

    private Double kd;

    // Getters and Setters

    public String getServer() {
        return server;
    }

    public void setServer(String server) {
        this.server = server;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Integer getBattles() {
        return battles;
    }

    public void setBattles(Integer battles) {
        this.battles = battles;
    }

    public Integer getOverallWN8() {
        return overallWN8;
    }

    public void setOverallWN8(Integer overallWN8) {
        this.overallWN8 = overallWN8;
    }

    public Integer getOverallWNX() {
        return overallWNX;
    }

    public void setOverallWNX(Integer overallWNX) {
        this.overallWNX = overallWNX;
    }

    public Double getAvgTier() {
        return avgTier;
    }

    public void setAvgTier(Double avgTier) {
        this.avgTier = avgTier;
    }

    public Integer getWins() {
        return wins;
    }

    public void setWins(Integer wins) {
        this.wins = wins;
    }

    public Integer getLosses() {
        return losses;
    }

    public void setLosses(Integer losses) {
        this.losses = losses;
    }

    public Integer getDraws() {
        return draws;
    }

    public void setDraws(Integer draws) {
        this.draws = draws;
    }

    public Long getTotalDamage() {
        return totalDamage;
    }

    public void setTotalDamage(Long totalDamage) {
        this.totalDamage = totalDamage;
    }

    public Long getTotalDamageReceived() {
        return totalDamageReceived;
    }

    public void setTotalDamageReceived(Long totalDamageReceived) {
        this.totalDamageReceived = totalDamageReceived;
    }

    public Long getTotalAssist() {
        return totalAssist;
    }

    public void setTotalAssist(Long totalAssist) {
        this.totalAssist = totalAssist;
    }

    public Integer getTotalFrags() {
        return totalFrags;
    }

    public void setTotalFrags(Integer totalFrags) {
        this.totalFrags = totalFrags;
    }

    public Integer getTotalDestroyed() {
        return totalDestroyed;
    }

    public void setTotalDestroyed(Integer totalDestroyed) {
        this.totalDestroyed = totalDestroyed;
    }

    public Integer getTotalSurvived() {
        return totalSurvived;
    }

    public void setTotalSurvived(Integer totalSurvived) {
        this.totalSurvived = totalSurvived;
    }

    public Integer getTotalSpotted() {
        return totalSpotted;
    }

    public void setTotalSpotted(Integer totalSpotted) {
        this.totalSpotted = totalSpotted;
    }

    public Integer getTotalCap() {
        return totalCap;
    }

    public void setTotalCap(Integer totalCap) {
        this.totalCap = totalCap;
    }

    public Integer getTotalDef() {
        return totalDef;
    }

    public void setTotalDef(Integer totalDef) {
        this.totalDef = totalDef;
    }

    public Long getTotalXp() {
        return totalXp;
    }

    public void setTotalXp(Long totalXp) {
        this.totalXp = totalXp;
    }

    public Double getWinrate() {
        return winrate;
    }

    public void setWinrate(Double winrate) {
        this.winrate = winrate;
    }

    public Double getLossrate() {
        return lossrate;
    }

    public void setLossrate(Double lossrate) {
        this.lossrate = lossrate;
    }

    public Double getDrawrate() {
        return drawrate;
    }

    public void setDrawrate(Double drawrate) {
        this.drawrate = drawrate;
    }

    public Integer getDpg() {
        return dpg;
    }

    public void setDpg(Integer dpg) {
        this.dpg = dpg;
    }

    public Integer getAssist() {
        return assist;
    }

    public void setAssist(Integer assist) {
        this.assist = assist;
    }

    public Double getFrags() {
        return frags;
    }

    public void setFrags(Double frags) {
        this.frags = frags;
    }

    public Double getSurvival() {
        return survival;
    }

    public void setSurvival(Double survival) {
        this.survival = survival;
    }

    public Double getSpots() {
        return spots;
    }

    public void setSpots(Double spots) {
        this.spots = spots;
    }

    public Double getCap() {
        return cap;
    }

    public void setCap(Double cap) {
        this.cap = cap;
    }

    public Double getDef() {
        return def;
    }

    public void setDef(Double def) {
        this.def = def;
    }

    public Integer getXp() {
        return xp;
    }

    public void setXp(Integer xp) {
        this.xp = xp;
    }

    public Double getKd() {
        return kd;
    }

    public void setKd(Double kd) {
        this.kd = kd;
    }
}
