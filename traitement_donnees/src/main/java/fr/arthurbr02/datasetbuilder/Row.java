package fr.arthurbr02.datasetbuilder;

public class Row {
    public static final String[] HEADERS = {
            "battles",
            "overallWN8",
            "overallWNX",
            "winrate",
            "dpg",
            "assist",
            "frags",
            "survival",
            "spots",
            "cap",
            "def",
            "xp",
            "kd",
            "map",
            "spawn",
            "target"
    };

    // Features
    private int battles;
    private int overallWN8;
    private int overallWNX;
    private double winrate;
    private int dpg;
    private int assist;
    private double frags;
    private double survival;
    private double spots;
    private double cap;
    private double def;
    private long xp;
    private double kd;
    private long map;
    private int spawn;

    // Target
    private int target;

    public int getBattles() {
        return battles;
    }

    public void setBattles(int battles) {
        this.battles = battles;
    }

    public int getOverallWN8() {
        return overallWN8;
    }

    public void setOverallWN8(int overallWN8) {
        this.overallWN8 = overallWN8;
    }

    public int getOverallWNX() {
        return overallWNX;
    }

    public void setOverallWNX(int overallWNX) {
        this.overallWNX = overallWNX;
    }

    public double getWinrate() {
        return winrate;
    }

    public void setWinrate(double winrate) {
        this.winrate = winrate;
    }

    public int getDpg() {
        return dpg;
    }

    public void setDpg(int dpg) {
        this.dpg = dpg;
    }

    public int getAssist() {
        return assist;
    }

    public void setAssist(int assist) {
        this.assist = assist;
    }

    public double getFrags() {
        return frags;
    }

    public void setFrags(double frags) {
        this.frags = frags;
    }

    public double getSurvival() {
        return survival;
    }

    public void setSurvival(double survival) {
        this.survival = survival;
    }

    public double getSpots() {
        return spots;
    }

    public void setSpots(double spots) {
        this.spots = spots;
    }

    public double getCap() {
        return cap;
    }

    public void setCap(double cap) {
        this.cap = cap;
    }

    public double getDef() {
        return def;
    }

    public void setDef(double def) {
        this.def = def;
    }

    public long getXp() {
        return xp;
    }

    public void setXp(long xp) {
        this.xp = xp;
    }

    public double getKd() {
        return kd;
    }

    public void setKd(double kd) {
        this.kd = kd;
    }

    public long getMap() {
        return map;
    }

    public void setMap(long map) {
        this.map = map;
    }

    public int getSpawn() {
        return spawn;
    }

    public void setSpawn(int spawn) {
        this.spawn = spawn;
    }

    public int getTarget() {
        return target;
    }

    public void setTarget(int target) {
        this.target = target;
    }

    public char[] toCsvLine() {
        return String.format("%d;%d;%d;%.2f;%d;%d;%.2f;%.2f;%.2f;%.2f;%.2f;%d;%.2f;%d;%d;%d",
                battles,
                overallWN8,
                overallWNX,
                winrate,
                dpg,
                assist,
                frags,
                survival,
                spots,
                cap,
                def,
                xp,
                kd,
                map,
                spawn,
                target
        ).toCharArray();
    }
}
