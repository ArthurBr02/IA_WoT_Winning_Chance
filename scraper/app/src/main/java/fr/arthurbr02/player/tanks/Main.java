package fr.arthurbr02.player.tanks;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Main {
    private int fireForEffect;
    private int duelist;
    private int fighter;
    private int spotter;
    private int reaper;
    private int masterGunner;
    private int sharpShooter;

    public int getFireForEffect() {
        return fireForEffect;
    }

    public void setFireForEffect(int fireForEffect) {
        this.fireForEffect = fireForEffect;
    }

    public int getDuelist() {
        return duelist;
    }

    public void setDuelist(int duelist) {
        this.duelist = duelist;
    }

    public int getFighter() {
        return fighter;
    }

    public void setFighter(int fighter) {
        this.fighter = fighter;
    }

    public int getSpotter() {
        return spotter;
    }

    public void setSpotter(int spotter) {
        this.spotter = spotter;
    }

    public int getReaper() {
        return reaper;
    }

    public void setReaper(int reaper) {
        this.reaper = reaper;
    }

    public int getMasterGunner() {
        return masterGunner;
    }

    public void setMasterGunner(int masterGunner) {
        this.masterGunner = masterGunner;
    }

    public int getSharpShooter() {
        return sharpShooter;
    }

    public void setSharpShooter(int sharpShooter) {
        this.sharpShooter = sharpShooter;
    }
}
