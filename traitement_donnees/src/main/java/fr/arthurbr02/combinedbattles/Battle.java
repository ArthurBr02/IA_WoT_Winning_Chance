package fr.arthurbr02.combinedbattles;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Battle {

    // Map and battle information
    private String map;

    @JsonProperty("geometry_name")
    private String geometryName;

    @JsonProperty("map_id")
    private Long mapId;

    @JsonProperty("tank_id")
    private Long tankId;

    @JsonProperty("arena_gui")
    private Integer arenaGui;

    @JsonProperty("battle_type")
    private Integer battleType;

    private Integer spawn;

    @JsonProperty("game_version")
    private String gameVersion;

    private Boolean won;

    @JsonProperty("finish_reason")
    private Integer finishReason;

    // Battle statistics
    private Integer damage;

    @JsonProperty("shots_fired")
    private Integer shotsFired;

    @JsonProperty("direct_hits")
    private Integer directHits;

    private Integer penetrations;

    @JsonProperty("hits_with_splash_damage")
    private Integer hitsWithSplashDamage;

    @JsonProperty("sniper_damage")
    private Integer sniperDamage;

    @JsonProperty("hits_received")
    private Integer hitsReceived;

    @JsonProperty("penetrations_received")
    private Integer penetrationsReceived;

    @JsonProperty("splash_hits_received")
    private Integer splashHitsReceived;

    @JsonProperty("damage_blocked")
    private Integer damageBlocked;

    private Integer spots;

    @JsonProperty("enemies_damaged")
    private Integer enemiesDamaged;

    @JsonProperty("enemies_stunned")
    private Integer enemiesStunned;

    private Integer frags;

    @JsonProperty("tracking_assist")
    private Integer trackingAssist;

    @JsonProperty("spotting_assist")
    private Integer spottingAssist;

    @JsonProperty("stun_assist")
    private Integer stunAssist;

    @JsonProperty("base_capture_points")
    private Integer baseCapturePoints;

    @JsonProperty("base_defense_points")
    private Integer baseDefensePoints;

    // Player information
    @JsonProperty("battle_time")
    private String battleTime;

    private String username;

    private String clan;

    @JsonProperty("damage_received_from_invisible")
    private Integer damageReceivedFromInvisible;

    @JsonProperty("potential_damage_received")
    private Integer potentialDamageReceived;

    @JsonProperty("periphery_id")
    private Integer peripheryId;

    @JsonProperty("base_xp")
    private Integer baseXp;

    private Integer platoon;

    // Tank information
    private Long id;

    private Integer tier;

    private String type;

    private String nation;

    @JsonProperty("is_gift")
    private Boolean isGift;

    @JsonProperty("is_premium")
    private Boolean isPremium;

    @JsonProperty("short_name")
    private String shortName;

    private String name;

    @JsonProperty("small_icon")
    private String smallIcon;

    @JsonProperty("contour_icon")
    private String contourIcon;

    @JsonProperty("big_icon")
    private String bigIcon;

    private String role;

    private String image;

    private Boolean isAdvanced;

    // Additional battle statistics
    @JsonProperty("life_time")
    private Integer lifeTime;

    private Integer duration;

    @JsonProperty("player_id")
    private Long playerId;

    @JsonProperty("arena_id")
    private String arenaId;

    @JsonProperty("distance_traveled")
    private Integer distanceTraveled;

    private Boolean survived;

    @JsonProperty("max_health")
    private Integer maxHealth;

    @JsonProperty("damage_received")
    private Integer damageReceived;

    private Integer wn8;

    private Integer wnx;

    // Collections
    private List<Object> equipment;

    private List<Object> consumables;

    private List<Object> fieldMods;

    private List<Object> shells;

    // Getters and Setters

    public String getMap() {
        return map;
    }

    public void setMap(String map) {
        this.map = map;
    }

    public String getGeometryName() {
        return geometryName;
    }

    public void setGeometryName(String geometryName) {
        this.geometryName = geometryName;
    }

    public Long getMapId() {
        return mapId;
    }

    public void setMapId(Long mapId) {
        this.mapId = mapId;
    }

    public Long getTankId() {
        return tankId;
    }

    public void setTankId(Long tankId) {
        this.tankId = tankId;
    }

    public Integer getArenaGui() {
        return arenaGui;
    }

    public void setArenaGui(Integer arenaGui) {
        this.arenaGui = arenaGui;
    }

    public Integer getBattleType() {
        return battleType;
    }

    public void setBattleType(Integer battleType) {
        this.battleType = battleType;
    }

    public Integer getSpawn() {
        return spawn;
    }

    public void setSpawn(Integer spawn) {
        this.spawn = spawn;
    }

    public String getGameVersion() {
        return gameVersion;
    }

    public void setGameVersion(String gameVersion) {
        this.gameVersion = gameVersion;
    }

    public Boolean getWon() {
        return won;
    }

    public void setWon(Boolean won) {
        this.won = won;
    }

    public Integer getFinishReason() {
        return finishReason;
    }

    public void setFinishReason(Integer finishReason) {
        this.finishReason = finishReason;
    }

    public Integer getDamage() {
        return damage;
    }

    public void setDamage(Integer damage) {
        this.damage = damage;
    }

    public Integer getShotsFired() {
        return shotsFired;
    }

    public void setShotsFired(Integer shotsFired) {
        this.shotsFired = shotsFired;
    }

    public Integer getDirectHits() {
        return directHits;
    }

    public void setDirectHits(Integer directHits) {
        this.directHits = directHits;
    }

    public Integer getPenetrations() {
        return penetrations;
    }

    public void setPenetrations(Integer penetrations) {
        this.penetrations = penetrations;
    }

    public Integer getHitsWithSplashDamage() {
        return hitsWithSplashDamage;
    }

    public void setHitsWithSplashDamage(Integer hitsWithSplashDamage) {
        this.hitsWithSplashDamage = hitsWithSplashDamage;
    }

    public Integer getSniperDamage() {
        return sniperDamage;
    }

    public void setSniperDamage(Integer sniperDamage) {
        this.sniperDamage = sniperDamage;
    }

    public Integer getHitsReceived() {
        return hitsReceived;
    }

    public void setHitsReceived(Integer hitsReceived) {
        this.hitsReceived = hitsReceived;
    }

    public Integer getPenetrationsReceived() {
        return penetrationsReceived;
    }

    public void setPenetrationsReceived(Integer penetrationsReceived) {
        this.penetrationsReceived = penetrationsReceived;
    }

    public Integer getSplashHitsReceived() {
        return splashHitsReceived;
    }

    public void setSplashHitsReceived(Integer splashHitsReceived) {
        this.splashHitsReceived = splashHitsReceived;
    }

    public Integer getDamageBlocked() {
        return damageBlocked;
    }

    public void setDamageBlocked(Integer damageBlocked) {
        this.damageBlocked = damageBlocked;
    }

    public Integer getSpots() {
        return spots;
    }

    public void setSpots(Integer spots) {
        this.spots = spots;
    }

    public Integer getEnemiesDamaged() {
        return enemiesDamaged;
    }

    public void setEnemiesDamaged(Integer enemiesDamaged) {
        this.enemiesDamaged = enemiesDamaged;
    }

    public Integer getEnemiesStunned() {
        return enemiesStunned;
    }

    public void setEnemiesStunned(Integer enemiesStunned) {
        this.enemiesStunned = enemiesStunned;
    }

    public Integer getFrags() {
        return frags;
    }

    public void setFrags(Integer frags) {
        this.frags = frags;
    }

    public Integer getTrackingAssist() {
        return trackingAssist;
    }

    public void setTrackingAssist(Integer trackingAssist) {
        this.trackingAssist = trackingAssist;
    }

    public Integer getSpottingAssist() {
        return spottingAssist;
    }

    public void setSpottingAssist(Integer spottingAssist) {
        this.spottingAssist = spottingAssist;
    }

    public Integer getStunAssist() {
        return stunAssist;
    }

    public void setStunAssist(Integer stunAssist) {
        this.stunAssist = stunAssist;
    }

    public Integer getBaseCapturePoints() {
        return baseCapturePoints;
    }

    public void setBaseCapturePoints(Integer baseCapturePoints) {
        this.baseCapturePoints = baseCapturePoints;
    }

    public Integer getBaseDefensePoints() {
        return baseDefensePoints;
    }

    public void setBaseDefensePoints(Integer baseDefensePoints) {
        this.baseDefensePoints = baseDefensePoints;
    }

    public String getBattleTime() {
        return battleTime;
    }

    public void setBattleTime(String battleTime) {
        this.battleTime = battleTime;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getClan() {
        return clan;
    }

    public void setClan(String clan) {
        this.clan = clan;
    }

    public Integer getDamageReceivedFromInvisible() {
        return damageReceivedFromInvisible;
    }

    public void setDamageReceivedFromInvisible(Integer damageReceivedFromInvisible) {
        this.damageReceivedFromInvisible = damageReceivedFromInvisible;
    }

    public Integer getPotentialDamageReceived() {
        return potentialDamageReceived;
    }

    public void setPotentialDamageReceived(Integer potentialDamageReceived) {
        this.potentialDamageReceived = potentialDamageReceived;
    }

    public Integer getPeripheryId() {
        return peripheryId;
    }

    public void setPeripheryId(Integer peripheryId) {
        this.peripheryId = peripheryId;
    }

    public Integer getBaseXp() {
        return baseXp;
    }

    public void setBaseXp(Integer baseXp) {
        this.baseXp = baseXp;
    }

    public Integer getPlatoon() {
        return platoon;
    }

    public void setPlatoon(Integer platoon) {
        this.platoon = platoon;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Integer getTier() {
        return tier;
    }

    public void setTier(Integer tier) {
        this.tier = tier;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getNation() {
        return nation;
    }

    public void setNation(String nation) {
        this.nation = nation;
    }

    public Boolean getIsGift() {
        return isGift;
    }

    public void setIsGift(Boolean isGift) {
        this.isGift = isGift;
    }

    public Boolean getIsPremium() {
        return isPremium;
    }

    public void setIsPremium(Boolean isPremium) {
        this.isPremium = isPremium;
    }

    public String getShortName() {
        return shortName;
    }

    public void setShortName(String shortName) {
        this.shortName = shortName;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getSmallIcon() {
        return smallIcon;
    }

    public void setSmallIcon(String smallIcon) {
        this.smallIcon = smallIcon;
    }

    public String getContourIcon() {
        return contourIcon;
    }

    public void setContourIcon(String contourIcon) {
        this.contourIcon = contourIcon;
    }

    public String getBigIcon() {
        return bigIcon;
    }

    public void setBigIcon(String bigIcon) {
        this.bigIcon = bigIcon;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getImage() {
        return image;
    }

    public void setImage(String image) {
        this.image = image;
    }

    public Boolean getIsAdvanced() {
        return isAdvanced;
    }

    public void setIsAdvanced(Boolean isAdvanced) {
        this.isAdvanced = isAdvanced;
    }

    public Integer getLifeTime() {
        return lifeTime;
    }

    public void setLifeTime(Integer lifeTime) {
        this.lifeTime = lifeTime;
    }

    public Integer getDuration() {
        return duration;
    }

    public void setDuration(Integer duration) {
        this.duration = duration;
    }

    public Long getPlayerId() {
        return playerId;
    }

    public void setPlayerId(Long playerId) {
        this.playerId = playerId;
    }

    public String getArenaId() {
        return arenaId;
    }

    public void setArenaId(String arenaId) {
        this.arenaId = arenaId;
    }

    public Integer getDistanceTraveled() {
        return distanceTraveled;
    }

    public void setDistanceTraveled(Integer distanceTraveled) {
        this.distanceTraveled = distanceTraveled;
    }

    public Boolean getSurvived() {
        return survived;
    }

    public void setSurvived(Boolean survived) {
        this.survived = survived;
    }

    public Integer getMaxHealth() {
        return maxHealth;
    }

    public void setMaxHealth(Integer maxHealth) {
        this.maxHealth = maxHealth;
    }

    public Integer getDamageReceived() {
        return damageReceived;
    }

    public void setDamageReceived(Integer damageReceived) {
        this.damageReceived = damageReceived;
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

    public List<Object> getEquipment() {
        return equipment;
    }

    public void setEquipment(List<Object> equipment) {
        this.equipment = equipment;
    }

    public List<Object> getConsumables() {
        return consumables;
    }

    public void setConsumables(List<Object> consumables) {
        this.consumables = consumables;
    }

    public List<Object> getFieldMods() {
        return fieldMods;
    }

    public void setFieldMods(List<Object> fieldMods) {
        this.fieldMods = fieldMods;
    }

    public List<Object> getShells() {
        return shells;
    }

    public void setShells(List<Object> shells) {
        this.shells = shells;
    }
}
