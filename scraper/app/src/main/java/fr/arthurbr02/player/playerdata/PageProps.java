package fr.arthurbr02.player.playerdata;


import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PageProps {
    private OverallStats overallStats;

    public OverallStats getOverallStats() {
        return overallStats;
    }

    public void setOverallStats(OverallStats overallStats) {
        this.overallStats = overallStats;
    }
}
