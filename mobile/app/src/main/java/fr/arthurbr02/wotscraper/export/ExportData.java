package fr.arthurbr02.wotscraper.export;

import java.util.List;

import fr.arthurbr02.wotscraper.scraper.model.battledetail.BattleDetail;
import fr.arthurbr02.wotscraper.scraper.model.combinedbattles.CombinedBattles;
import fr.arthurbr02.wotscraper.scraper.model.player.Player;

public class ExportData {
    private CombinedBattles combinedBattles;
    private List<BattleDetail> battleDetails;
    private List<Player> players;

    public ExportData(CombinedBattles combinedBattles, List<BattleDetail> battleDetails, List<Player> players) {
        this.combinedBattles = combinedBattles;
        this.battleDetails = battleDetails;
        this.players = players;
    }

    public CombinedBattles getCombinedBattles() {
        return combinedBattles;
    }

    public void setCombinedBattles(CombinedBattles combinedBattles) {
        this.combinedBattles = combinedBattles;
    }

    public List<BattleDetail> getBattleDetails() {
        return battleDetails;
    }

    public void setBattleDetails(List<BattleDetail> battleDetails) {
        this.battleDetails = battleDetails;
    }

    public List<Player> getPlayers() {
        return players;
    }

    public void setPlayers(List<Player> players) {
        this.players = players;
    }
}
