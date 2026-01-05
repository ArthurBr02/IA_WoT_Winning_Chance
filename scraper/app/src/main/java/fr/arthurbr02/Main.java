package fr.arthurbr02;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.battledetail.Player;
import fr.arthurbr02.battledetail.Players;
import fr.arthurbr02.combinedbattles.CombinedBattles;
import fr.arthurbr02.combinedbattles.CombinedBattlesService;
import fr.arthurbr02.export.ExportData;
import fr.arthurbr02.export.ExportService;
import fr.arthurbr02.player.PlayerService;
import fr.arthurbr02.player.playerdata.PlayerData;
import fr.arthurbr02.utils.HttpClientsUtils;
import fr.arthurbr02.utils.ProgressManager;
import fr.arthurbr02.utils.ProgressState;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.*;

public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    private static final String INITIAL_PLAYER_ID = "532440001";
    private static final int PLAYERS_TO_FETCH = 50;
    private static final int MAX_429_RETRIES = 1000;

    private static final boolean TEST_MODE = false;

    public static void main(String[] args) {
        if (TEST_MODE) test();
        else {
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
    }

    private static void test() {
        String testUrl = "https://tomato.gg/stats/ArthuroELMANIFICO-532440001/EU";
        try (CloseableHttpClient httpClient = HttpClientsUtils.getHttpClientWithRetry()) {
            ObjectMapper mapper = new ObjectMapper();
            for (int attempt = 1; attempt <= MAX_429_RETRIES; attempt++) {
                HttpGet request = new HttpGet(testUrl);
                try (CloseableHttpResponse response = httpClient.execute(request)) {
                    int code = response.getCode();
                    InputStream content = response.getEntity().getContent();

                    // Affichage du code de réponse et du contenu
                    System.out.println("HTTP Response Code: " + code);
                    String result = new String(content.readAllBytes());
                    System.out.println("Response Content: " + result);

                    // Il faut récupérer le contenu de la balise script id __NEXT_DATA__ et le parser en JSON
                    int scriptStart = result.indexOf("<script id=\"__NEXT_DATA__\" type=\"application/json\">");
                    int scriptEnd = result.indexOf("</script>", scriptStart);
                    if (scriptStart == -1 || scriptEnd == -1) {
                        System.out.println("Script tag not found");
                        return;
                    }

                    String jsonData = result.substring(
                            scriptStart + "<script id=\"__NEXT_DATA__\" type=\"application/json\">".length(),
                            scriptEnd
                    );
                    System.out.println("Extracted JSON Data: " + jsonData);
                    // Maintenant on peut parser jsonData avec Jackson
                    PlayerData data = mapper.readValue(jsonData, PlayerData.class);
                    System.out.println("Parsed JSON Data: " + data);
                    return;
                }
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
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

        // Export initial des premières données
        logger.info("Exporting initial data");
        ExportService.exportCurrentData(
            new ExportData(null, state.getBattleDetails(), state.getPlayers())
        );

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
        Map<Long, String> playerNames = new HashMap<>();
        for (BattleDetail detail : state.getBattleDetails()) {
            for (Player p : detail.getPlayers()) {
                allPlayerIds.add(p.getPlayerId());
                playerNames.put(p.getPlayerId(), p.getUsername());
            }
        }

        logger.info("Total unique players to fetch details for: {}", allPlayerIds.size());

        // Export avant de récupérer les détails des joueurs (phase longue)
        logger.info("Exporting data before fetching player details");
        ExportService.exportCurrentData(
            new ExportData(null, state.getBattleDetails(), state.getPlayers())
        );

        // Récupérer les informations détaillées des joueurs traités
        logger.info("Fetching detailed player information");
        List<fr.arthurbr02.player.Player> players =
            PlayerService.fetchPlayers(new ArrayList<>(allPlayerIds), playerNames, (currentPlayers) -> {
                // Callback appelé tous les 200 joueurs
                state.setPlayers(currentPlayers);
                ExportService.exportCurrentData(
                    new ExportData(null, state.getBattleDetails(), currentPlayers)
                );
            });
        state.setPlayers(players);

        // Export après la récupération des détails des joueurs
        logger.info("Exporting data after fetching player details");
        ExportService.exportCurrentData(
            new ExportData(null, state.getBattleDetails(), state.getPlayers())
        );

        // Sauvegarde finale
        ProgressManager.saveProgress(state);

        logger.info("Scraping completed: {} battles, {} players",
                state.getBattleDetails().size(), state.getPlayers().size());
    }
}