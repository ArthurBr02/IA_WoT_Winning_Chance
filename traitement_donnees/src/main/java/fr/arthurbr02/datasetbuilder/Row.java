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
            "target",
            "tankId",
            "tankWN8",
            "tankWNX",
            "tankRole",
            "tankWinrate",
            "tankVehicleClass",
            "tankNation",
            "tankDpg",
            "tankAssist",
            "tankKpg",
            "tankDmgRatio",
            "tankSurvival",
            "tankXp",
            "tankHitratio",
            "tankSpots",
            "tankArmoreff",
            "tankMoe",
            "tankMastery",
            "tankKd"
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

    // TANK stats
    private long tankId;
    private int tankWN8;
    private int tankWNX;
    private String tankRole;
    private double tankWinrate;
    private String tankVehicleClass;
    private String tankNation;
    private int tankDpg;
    private int tankAssist;
    private double tankKpg;
    private double tankDmgRatio;
    private double tankSurvival;
    private int tankXp;
    private int tankHitratio;
    private double tankSpots;
    private int tankArmoreff;
    private int tankMoe;
    private int tankMastery;
    private double tankKd;


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


    public long getTankId() {
        return tankId;
    }

    public void setTankId(long tankId) {
        this.tankId = tankId;
    }

    public int getTankWN8() {
        return tankWN8;
    }

    public void setTankWN8(int tankWN8) {
        this.tankWN8 = tankWN8;
    }

    public int getTankWNX() {
        return tankWNX;
    }

    public void setTankWNX(int tankWNX) {
        this.tankWNX = tankWNX;
    }

    public String getTankRole() {
        return tankRole;
    }

    public void setTankRole(String tankRole) {
        this.tankRole = tankRole;
    }

    public double getTankWinrate() {
        return tankWinrate;
    }

    public void setTankWinrate(double tankWinrate) {
        this.tankWinrate = tankWinrate;
    }

    public String getTankVehicleClass() {
        return tankVehicleClass;
    }

    public void setTankVehicleClass(String tankVehicleClass) {
        this.tankVehicleClass = tankVehicleClass;
    }

    public String getTankNation() {
        return tankNation;
    }

    public void setTankNation(String tankNation) {
        this.tankNation = tankNation;
    }

    public int getTankDpg() {
        return tankDpg;
    }

    public void setTankDpg(int tankDpg) {
        this.tankDpg = tankDpg;
    }

    public int getTankAssist() {
        return tankAssist;
    }

    public void setTankAssist(int tankAssist) {
        this.tankAssist = tankAssist;
    }

    public double getTankKpg() {
        return tankKpg;
    }

    public void setTankKpg(double tankKpg) {
        this.tankKpg = tankKpg;
    }

    public double getTankDmgRatio() {
        return tankDmgRatio;
    }

    public void setTankDmgRatio(double tankDmgRatio) {
        this.tankDmgRatio = tankDmgRatio;
    }

    public double getTankSurvival() {
        return tankSurvival;
    }

    public void setTankSurvival(double tankSurvival) {
        this.tankSurvival = tankSurvival;
    }

    public int getTankXp() {
        return tankXp;
    }

    public void setTankXp(int tankXp) {
        this.tankXp = tankXp;
    }

    public int getTankHitratio() {
        return tankHitratio;
    }

    public void setTankHitratio(int tankHitratio) {
        this.tankHitratio = tankHitratio;
    }

    public double getTankSpots() {
        return tankSpots;
    }

    public void setTankSpots(double tankSpots) {
        this.tankSpots = tankSpots;
    }

    public int getTankArmoreff() {
        return tankArmoreff;
    }

    public void setTankArmoreff(int tankArmoreff) {
        this.tankArmoreff = tankArmoreff;
    }

    public int getTankMoe() {
        return tankMoe;
    }

    public void setTankMoe(int tankMoe) {
        this.tankMoe = tankMoe;
    }

    public int getTankMastery() {
        return tankMastery;
    }

    public void setTankMastery(int tankMastery) {
        this.tankMastery = tankMastery;
    }

    public double getTankKd() {
        return tankKd;
    }

    public void setTankKd(double tankKd) {
        this.tankKd = tankKd;
    }

    public char[] toCsvLine() {
        return String.format("%d;%d;%d;%.2f;%d;%d;%.2f;%.2f;%.2f;%.2f;%.2f;%d;%.2f;%d;%d;%d;%d;%d;%d;%s;%.2f;%s;%s;%d;%d;%.2f;%.2f;%.2f;%d;%d;%.2f;%d;%d;%d;%.2f",
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
                target,
                tankId,
                tankWN8,
                tankWNX,
                tankRole,
                tankWinrate,
                tankVehicleClass,
                tankNation,
                tankDpg,
                tankAssist,
                tankKpg,
                tankDmgRatio,
                tankSurvival,
                tankXp,
                tankHitratio,
                tankSpots,
                tankArmoreff,
                tankMoe,
                tankMastery,
                tankKd
        ).toCharArray();
    }
}
