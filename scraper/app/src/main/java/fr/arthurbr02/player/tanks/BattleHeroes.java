package fr.arthurbr02.player.tanks;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class BattleHeroes {
    private int highCaliber;
    private int confederate;
    private int tankSniper;
    private int scout;

    public int getHighCaliber() {
        return highCaliber;
    }

    public void setHighCaliber(int highCaliber) {
        this.highCaliber = highCaliber;
    }

    public int getConfederate() {
        return confederate;
    }

    public void setConfederate(int confederate) {
        this.confederate = confederate;
    }

    public int getTankSniper() {
        return tankSniper;
    }

    public void setTankSniper(int tankSniper) {
        this.tankSniper = tankSniper;
    }

    public int getScout() {
        return scout;
    }

    public void setScout(int scout) {
        this.scout = scout;
    }
}
