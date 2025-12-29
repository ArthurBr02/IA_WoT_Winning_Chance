package fr.arthurbr02;

import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.combinedbattles.CombinedBattles;
import fr.arthurbr02.combinedbattles.CombinedBattlesService;
import fr.arthurbr02.export.ExportData;
import fr.arthurbr02.export.ExportService;
import fr.arthurbr02.player.PlayerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    private static final String INITIAL_PLAYER_ID = "532440001";
    private static final int PLAYERS_TO_FETCH = 50;

    public static void main(String[] args) {
        CombinedBattles combinedBattles = CombinedBattlesService.fetchCombinedBattles(INITIAL_PLAYER_ID);

        if (combinedBattles == null) {
            logger.warn("No data retrieved.");
            return;
        }

        List<Long> arenaIds = combinedBattles.getArenaIds();

        logger.info("Arena IDs: {}", arenaIds);

        List<BattleDetail> battleDetails = CombinedBattlesService.fetchBattleDetails(arenaIds);

        logger.info("Battle Details: {}", battleDetails);

        Set<Long> playerIds = new HashSet<>();

        for (BattleDetail detail : battleDetails) {
            playerIds.addAll(detail.getPlayerIds());
        }

        // On récupère 50 identifiants de joueurs au hasard pour récupérer des données variées
        List<Long> playerIdList = new ArrayList<>(playerIds);
        Collections.shuffle(playerIdList);
        playerIds = new HashSet<>(playerIdList.subList(0, Math.min(PLAYERS_TO_FETCH, playerIdList.size())));
        logger.info("Player IDs: {}", playerIds);

        // On récupère les CombinedBattles des joueurs identifiés
        for (Long playerId : playerIds) {
            CombinedBattles playerCombinedBattles = CombinedBattlesService.fetchCombinedBattles(playerId.toString());
            logger.debug("Combined Battles for Player {}: {}", playerId, playerCombinedBattles);

            // On récupères les arenaIds de ces CombinedBattles

            if (playerCombinedBattles == null) {
                logger.warn("No CombinedBattles data for Player {}", playerId);
                continue;
            }

            logger.debug("Arena IDs for Player {}: {}", playerId, playerCombinedBattles.getArenaIds());
            List<Long> playerArenaIds = playerCombinedBattles.getArenaIds();
            Set<Long> uniqueArenaIds = new HashSet<>(playerArenaIds);

            // On récupère les BattleDetails associés
            List<BattleDetail> playerBattleDetails = CombinedBattlesService.fetchBattleDetails(new ArrayList<>(uniqueArenaIds));
            logger.debug("Battle Details for Player {}: {}", playerId, playerBattleDetails);

            // On les ajoute à la liste principale si ce ne sont pas des doublons
            for (BattleDetail bd : playerBattleDetails) {
                if (!battleDetails.contains(bd)) {
                    battleDetails.add(bd);
                    logger.debug("Added BattleDetail: {}", bd);
                }
            }
        }


        List<fr.arthurbr02.player.Player> players = PlayerService.fetchPlayers(new ArrayList<>(playerIds));

        logger.info("Players: {}", players);

        Date now = new Date();
        ExportService.exportData(new ExportData(combinedBattles, battleDetails, players), now);
    }
}