package fr.arthurbr02.player.tanks;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Epic {
    private int orlik;

    public int getOrlik() {
        return orlik;
    }

    public void setOrlik(int orlik) {
        this.orlik = orlik;
    }
}
