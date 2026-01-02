package fr.arthurbr02.wotscraper.scraper.model.battledetail;

import com.google.gson.annotations.SerializedName;

public class BattlePlayer {

    // Map and battle information
    private String map;

    @SerializedName("tank_id")
    private Long tankId;

    private Integer spawn;

    @SerializedName("game_version")
    private String gameVersion;

    private Boolean won;

    // Battle statistics
    private Integer damage;

    @SerializedName("shots_fired")
    private Integer shotsFired;

    @SerializedName("direct_hits")
    private Integer directHits;

    private Integer penetrations;

    @SerializedName("hits_with_splash_damage")
    private Integer hitsWithSplashDamage;

    @SerializedName("sniper_damage")
    private Integer sniperDamage;

    @SerializedName("hits_received")
    private Integer hitsReceived;

    @SerializedName("penetrations_received")
    private Integer penetrationsReceived;

    @SerializedName("splash_hits_received")
    private Integer splashHitsReceived;

    @SerializedName("damage_blocked")
    private Integer damageBlocked;

    private Integer spots;

    @SerializedName("enemies_damaged")
    private Integer enemiesDamaged;

    @SerializedName("enemies_stunned")
    private Integer enemiesStunned;

    private Integer frags;

    @SerializedName("tracking_assist")
    private Integer trackingAssist;

    @SerializedName("spotting_assist")
    private Integer spottingAssist;

    @SerializedName("stun_assist")
    private Integer stunAssist;

    @SerializedName("base_capture_points")
    private Integer baseCapturePoints;

    @SerializedName("base_defense_points")
    private Integer baseDefensePoints;

    // Player information
    private String username;

    @SerializedName("damage_received_from_invisible")
    private Integer damageReceivedFromInvisible;

    @SerializedName("potential_damage_received")
    private Integer potentialDamageReceived;

    @SerializedName("periphery_id")
    private Integer peripheryId;

    @SerializedName("base_xp")
    private Integer baseXp;

    private Integer platoon;

    // Tank information
    private Long id;

    private Integer tier;

    private String type;

    private String nation;

    @SerializedName("is_gift")
    private Boolean isGift;

    @SerializedName("is_premium")
    private Boolean isPremium;

    @SerializedName("short_name")
    private String shortName;

    private String role;

    private String name;

    @SerializedName("small_icon")
    private String smallIcon;

    @SerializedName("contour_icon")
    private String contourIcon;

    @SerializedName("big_icon")
    private String bigIcon;

    private String image;

    // Additional player statistics
    @SerializedName("player_id")
    private Long playerId;

    private String clan;

    @SerializedName("distance_traveled")
    private Integer distanceTraveled;

    private Boolean survived;

    @SerializedName("max_health")
    private Integer maxHealth;

    @SerializedName("damage_received")
    private Integer damageReceived;

    @SerializedName("life_time")
    private Integer lifeTime;

    private Integer duration;

    public Long getPlayerId() {
        return playerId;
    }

    public void setPlayerId(Long playerId) {
        this.playerId = playerId;
    }
}
