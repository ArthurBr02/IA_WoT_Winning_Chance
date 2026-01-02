package fr.arthurbr02.player;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

public class PlayerService {
    private static final Logger logger = LoggerFactory.getLogger(PlayerService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/overall/eu/{player_id}";
    private static final int MAX_429_RETRIES = 1000;

    public static Player fetchPlayer(Long playerId) {
        logger.info("Fetching player with ID: {}", playerId);
        String url = API_URL.replace("{player_id}", playerId.toString());

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
                    return mapper.readValue(result, Player.class);
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

    public static List<Player> fetchPlayers(List<Long> playerIds) {
        List<Player> players = new ArrayList<>();
        for (Long playerId : playerIds) {
            Player player = fetchPlayer(playerId);
            players.add(player);
        }
        return players;
    }
}
