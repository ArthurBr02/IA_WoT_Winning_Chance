package fr.arthurbr02;

import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.combinedbattles.CombinedBattles;
import fr.arthurbr02.combinedbattles.CombinedBattlesService;
import fr.arthurbr02.export.ExportData;
import fr.arthurbr02.export.ExportService;
import fr.arthurbr02.player.PlayerService;
import fr.arthurbr02.utils.ProgressManager;
import fr.arthurbr02.utils.ProgressState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    private static final String INITIAL_PLAYER_ID = "532440001";
    private static final int PLAYERS_TO_FETCH = 100;

    public static void main(String[] args) {
        logger.info("=== Starting scraper ===");

        // Vérifier s'il existe une progression sauvegardée
        ProgressState state = ProgressManager.loadProgress();

        if (state == null) {
            // Nouvelle exécution - initialiser l'état
            logger.info("Starting new scraping session");
            state = initializeNewProgress();
        } else {
            // Reprise depuis une sauvegarde
            logger.info("Resuming from previous session");
            logger.info("Start time: {}", state.getStartTime());
            logger.info("Last update: {}", state.getLastUpdateTime());
        }

        try {
            // Exécuter le scraping avec gestion de progression
            executeScraping(state);

            // Exporter les données finales
            Date now = new Date();
            ExportService.exportData(
                new ExportData(null, state.getBattleDetails(), state.getPlayers()),
                now
            );

            // Nettoyer les fichiers de progression après succès
            logger.info("Scraping completed successfully!");
            ProgressManager.clearProgress();

        } catch (Exception e) {
            logger.error("Error during scraping - progress has been saved", e);
            ProgressManager.saveProgress(state);
            System.exit(1);
        }
    }

    /**
     * Initialise un nouvel état de progression
     */
    private static ProgressState initializeNewProgress() {
        ProgressState state = new ProgressState();
        state.setInitialPlayerId(INITIAL_PLAYER_ID);
        state.setTotalPlayersToFetch(PLAYERS_TO_FETCH);

        logger.info("Fetching initial CombinedBattles for player {}", INITIAL_PLAYER_ID);
        CombinedBattles combinedBattles = CombinedBattlesService.fetchCombinedBattles(INITIAL_PLAYER_ID);

        if (combinedBattles == null) {
            logger.error("No data retrieved for initial player");
            throw new RuntimeException("Failed to fetch initial data");
        }

        List<Long> arenaIds = combinedBattles.getArenaIds();
        logger.info("Found {} arena IDs", arenaIds.size());

        // Récupérer les détails des batailles initiales
        logger.info("Fetching initial battle details");
        List<BattleDetail> battleDetails = CombinedBattlesService.fetchBattleDetails(arenaIds);
        state.setBattleDetails(battleDetails);

        // Marquer les arenas comme traitées
        state.getProcessedArenaIds().addAll(arenaIds);

        // Extraire les IDs des joueurs
        Set<Long> playerIds = new HashSet<>();
        for (BattleDetail detail : battleDetails) {
            playerIds.addAll(detail.getPlayerIds());
        }

        // Mélanger et limiter le nombre de joueurs
        List<Long> playerIdList = new ArrayList<>(playerIds);
        Collections.shuffle(playerIdList);
        int playersToProcess = Math.min(PLAYERS_TO_FETCH, playerIdList.size());
        state.setPendingPlayerIds(playerIdList.subList(0, playersToProcess));

        logger.info("Initialized with {} battles and {} players to process",
                battleDetails.size(), playersToProcess);

        // Sauvegarder l'état initial
        ProgressManager.saveProgress(state);

        return state;
    }

    /**
     * Exécute le scraping en sauvegardant la progression régulièrement
     */
    private static void executeScraping(ProgressState state) {
        List<Long> pendingPlayerIds = state.getPendingPlayerIds();
        int startIndex = state.getCurrentPlayerIndex();

        logger.info("Processing players from index {} to {}", startIndex, pendingPlayerIds.size());

        for (int i = startIndex; i < pendingPlayerIds.size(); i++) {
            Long playerId = pendingPlayerIds.get(i);

            // Vérifier si déjà traité
            if (state.getProcessedPlayerIds().contains(playerId)) {
                logger.debug("Player {} already processed, skipping", playerId);
                continue;
            }

            logger.info("Processing player {}/{}: {}",
                    i + 1, pendingPlayerIds.size(), playerId);

            try {
                // Récupérer les CombinedBattles du joueur
                CombinedBattles playerCombinedBattles =
                    CombinedBattlesService.fetchCombinedBattles(playerId.toString());

                if (playerCombinedBattles == null) {
                    logger.warn("No CombinedBattles data for Player {}", playerId);
                    state.getProcessedPlayerIds().add(playerId);
                    state.setCurrentPlayerIndex(i + 1);
                    ProgressManager.saveProgress(state);
                    continue;
                }

                // Récupérer les arenas non encore traitées
                List<Long> playerArenaIds = playerCombinedBattles.getArenaIds();
                Set<Long> newArenaIds = new HashSet<>();

                for (Long arenaId : playerArenaIds) {
                    if (!state.getProcessedArenaIds().contains(arenaId)) {
                        newArenaIds.add(arenaId);
                    }
                }

                logger.debug("Found {} new arenas for player {}", newArenaIds.size(), playerId);

                // Récupérer les BattleDetails des nouvelles arenas
                if (!newArenaIds.isEmpty()) {
                    List<BattleDetail> newBattleDetails =
                        CombinedBattlesService.fetchBattleDetails(new ArrayList<>(newArenaIds));

                    // Ajouter les nouvelles batailles (éviter les doublons)
                    for (BattleDetail bd : newBattleDetails) {
                        if (bd != null && !state.getBattleDetails().contains(bd)) {
                            state.getBattleDetails().add(bd);
                        }
                    }

                    // Marquer les arenas comme traitées
                    state.getProcessedArenaIds().addAll(newArenaIds);
                }

                // Marquer le joueur comme traité
                state.getProcessedPlayerIds().add(playerId);
                state.setCurrentPlayerIndex(i + 1);

                // Sauvegarder la progression toutes les 5 itérations
                if ((i + 1) % 5 == 0) {
                    ProgressManager.saveProgress(state);
                }

            } catch (Exception e) {
                logger.error("Error processing player {}", playerId, e);
                // Sauvegarder avant de propager l'exception
                state.setCurrentPlayerIndex(i);
                ProgressManager.saveProgress(state);
                throw e;
            }
        }

        // On récupère les IDs de tous les joueurs de tous les BattleDetails
        Set<Long> allPlayerIds = new HashSet<>();
        for (BattleDetail detail : state.getBattleDetails()) {
            allPlayerIds.addAll(detail.getPlayerIds());
        }

        logger.info("Total unique players to fetch details for: {}", allPlayerIds.size());

        // Récupérer les informations détaillées des joueurs traités
        logger.info("Fetching detailed player information");
        List<fr.arthurbr02.player.Player> players =
            PlayerService.fetchPlayers(new ArrayList<>(allPlayerIds));
        state.setPlayers(players);

        // Sauvegarde finale
        ProgressManager.saveProgress(state);

        logger.info("Scraping completed: {} battles, {} players",
                state.getBattleDetails().size(), state.getPlayers().size());
    }
}