package fr.arthurbr02.player;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.player.playerdata.Data;
import fr.arthurbr02.player.playerdata.PlayerData;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.*;

public class PlayerService {
    private static final Logger logger = LoggerFactory.getLogger(PlayerService.class);
    private static final String API_URL = "https://tomato.gg/stats/{player_name}-{player_id}/EU";
    private static final int MAX_429_RETRIES = 1000;
    private static final int MIN_THREAD_COUNT = 8;

    public static Player fetchPlayer(Long playerId, String name) {
        return fetchPlayer(playerId, name, -1, -1);
    }

    public static Player fetchPlayer(Long playerId, String name, int currentIndex, int totalCount) {
        if (currentIndex >= 0 && totalCount > 0) {
            logger.info("Fetching player {}/{} with ID: {}", currentIndex, totalCount, playerId);
        } else {
            logger.info("Fetching player with ID: {}", playerId);
        }
        String url = API_URL.replace("{player_id}", playerId.toString()).replace("{player_name}", name);

        try (CloseableHttpClient httpClient = HttpClientsUtils.getHttpClientWithRetry()) {
            ObjectMapper mapper = new ObjectMapper();
            for (int attempt = 1; attempt <= MAX_429_RETRIES; attempt++) {
                HttpGet request = new HttpGet(url);
                try (CloseableHttpResponse response = httpClient.execute(request)) {
                    int code = response.getCode();

                    if (code == 429) {
                        long waitMs = HttpClientsUtils.computeRetryAfterMs(response, attempt);
                        logger.warn("429 Too Many Requests for {} (attempt {}/{}). Waiting {} ms before retry.",
                                url, attempt, MAX_429_RETRIES, waitMs);
                        EntityUtils.consumeQuietly(response.getEntity());
                        Thread.sleep(waitMs);
                        continue;
                    }

                    if (code < 200 || code >= 300) {
                        logger.warn("HTTP {} for {}. Skipping.", code, url);
                        EntityUtils.consumeQuietly(response.getEntity());
                        return null;
                    }

                    HttpEntity entity = response.getEntity();
                    if (entity == null) {
                        logger.warn("Empty response entity for {}", url);
                        return null;
                    }

                    String result = EntityUtils.toString(entity);
                    PlayerData playerData = PlayerData.fromHtml(result, mapper);
                    if (playerData == null) {
                        logger.warn("Failed to parse PlayerData from HTML for {}", url);
                        return null;
                    }
                    Data data = playerData.getData();

                    Player player = new Player();
                    player.setData(data);

                    return player;
                }
            }

            logger.error("Still rate-limited after {} attempts for {}", MAX_429_RETRIES, url);
            return null;

        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            logger.error("Interrupted while waiting after 429 for playerId: {}", playerId, ie);
        } catch (Exception e) {
            logger.error("Error fetching player with ID: {}", playerId, e);
        }

        return null;
    }

    public static List<Player> fetchPlayers(List<Long> playerIds, Map<Long, String> playerNames) {
        return fetchPlayers(playerIds, playerNames, null);
    }

    public static List<Player> fetchPlayers(List<Long> playerIds, Map<Long, String> playerNames,
                                            java.util.function.Consumer<List<Player>> progressCallback) {
        List<Player> players = new ArrayList<>();

        if (playerIds.isEmpty()) {
            return players;
        }

        int totalCount = playerIds.size();

        // Créer un ExecutorService avec un nombre de threads = max(8, nombre de CPUs)
        int threadCount = Math.max(MIN_THREAD_COUNT, Runtime.getRuntime().availableProcessors());
        logger.info("Using {} threads for fetching {} players (min: {})", threadCount, totalCount, MIN_THREAD_COUNT);
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        List<Future<Player>> futures = new ArrayList<>();

        // Soumettre toutes les tâches
        int index = 0;
        for (Long playerId : playerIds) {
            String name = playerNames.get(playerId);
            if (name == null) {
                logger.warn("Player name not found for ID: {}. Skipping.", playerId);
                continue;
            }

            int currentIndex = ++index;
            Future<Player> future = executor.submit(() -> fetchPlayer(playerId, name, currentIndex, totalCount));
            futures.add(future);
        }

        // Récupérer les résultats avec export tous les 200 joueurs
        int processedCount = 0;
        for (Future<Player> future : futures) {
            try {
                Player player = future.get();
                if (player != null) {
                    players.add(player);
                    processedCount++;

                    // Appeler le callback tous les 200 joueurs
                    if (progressCallback != null && processedCount % 200 == 0) {
                        logger.info("Progress: {} players fetched so far", processedCount);
                        progressCallback.accept(new ArrayList<>(players));
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.error("Thread interrupted while fetching Player", e);
            } catch (ExecutionException e) {
                logger.error("Error fetching Player", e.getCause());
            }
        }

        // Arrêter l'executor
        executor.shutdown();
        try {
            if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }

        return players;
    }
}
