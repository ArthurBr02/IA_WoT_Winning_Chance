package fr.arthurbr02.player.tanks;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Tank {
    private String image;

    @JsonProperty("bigImage")
    private String bigImage;

    private Long id;

    private String name;

    private String nation;

    private String role;

    private Integer tier;

    @JsonProperty("class")
    private String vehicleClass;

    private Integer battles;

    private Double winrate;

    private Integer wn8;

    private Integer wnx;

    private Integer dpg;

    private Integer assist;

    private Double kpg;

    private Double dmgratio;

    private Double kd;

    private Double survival;

    private Integer xp;

    private Integer hitratio;

    private Double spots;

    private Integer armoreff;

    private Integer moe;

    private Integer mastery;

    @JsonProperty("isPrem")
    private Boolean isPrem;

    @JsonProperty("dpgRanking")
    private List<Integer> dpgRanking;

    private Awards awards;

    // New getters and setters
    public String getImage() {
        return image;
    }

    public void setImage(String image) {
        this.image = image;
    }

    public String getBigImage() {
        return bigImage;
    }

    public void setBigImage(String bigImage) {
        this.bigImage = bigImage;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getNation() {
        return nation;
    }

    public void setNation(String nation) {
        this.nation = nation;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public Integer getTier() {
        return tier;
    }

    public void setTier(Integer tier) {
        this.tier = tier;
    }

    public String getVehicleClass() {
        return vehicleClass;
    }

    public void setVehicleClass(String vehicleClass) {
        this.vehicleClass = vehicleClass;
    }

    public Integer getBattles() {
        return battles;
    }

    public void setBattles(Integer battles) {
        this.battles = battles;
    }

    public Double getWinrate() {
        return winrate;
    }

    public void setWinrate(Double winrate) {
        this.winrate = winrate;
    }

    public Integer getWn8() {
        return wn8;
    }

    public void setWn8(Integer wn8) {
        this.wn8 = wn8;
    }

    public Integer getWnx() {
        return wnx;
    }

    public void setWnx(Integer wnx) {
        this.wnx = wnx;
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

    public Double getKpg() {
        return kpg;
    }

    public void setKpg(Double kpg) {
        this.kpg = kpg;
    }

    public Double getDmgratio() {
        return dmgratio;
    }

    public void setDmgratio(Double dmgratio) {
        this.dmgratio = dmgratio;
    }

    public Double getKd() {
        return kd;
    }

    public void setKd(Double kd) {
        this.kd = kd;
    }

    public Double getSurvival() {
        return survival;
    }

    public void setSurvival(Double survival) {
        this.survival = survival;
    }

    public Integer getXp() {
        return xp;
    }

    public void setXp(Integer xp) {
        this.xp = xp;
    }

    public Integer getHitratio() {
        return hitratio;
    }

    public void setHitratio(Integer hitratio) {
        this.hitratio = hitratio;
    }

    public Double getSpots() {
        return spots;
    }

    public void setSpots(Double spots) {
        this.spots = spots;
    }

    public Integer getArmoreff() {
        return armoreff;
    }

    public void setArmoreff(Integer armoreff) {
        this.armoreff = armoreff;
    }

    public Integer getMoe() {
        return moe;
    }

    public void setMoe(Integer moe) {
        this.moe = moe;
    }

    public Integer getMastery() {
        return mastery;
    }

    public void setMastery(Integer mastery) {
        this.mastery = mastery;
    }

    public Boolean getIsPrem() {
        return isPrem;
    }

    public void setIsPrem(Boolean isPrem) {
        this.isPrem = isPrem;
    }

    public List<Integer> getDpgRanking() {
        return dpgRanking;
    }

    public void setDpgRanking(List<Integer> dpgRanking) {
        this.dpgRanking = dpgRanking;
    }

    // Existing getters and setters
    public Awards getAwards() {
        return awards;
    }

    public void setAwards(Awards awards) {
        this.awards = awards;
    }
}
