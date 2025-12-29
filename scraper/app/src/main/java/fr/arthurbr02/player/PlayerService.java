package fr.arthurbr02.player;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class PlayerService {
    private static final Logger logger = LoggerFactory.getLogger(PlayerService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/overall/eu/{player_id}";

    public static Player fetchPlayer(Long playerId) {
        logger.info("Fetching player with ID: {}", playerId);
        String url = API_URL.replace("{player_id}", playerId.toString());

        // 1. Create the client
        try (CloseableHttpClient httpClient = HttpClientsUtils.getHttpClientWithRetry()) {

            // 2. Define the request
            HttpGet request = new HttpGet(url);

            // 3. Execute and handle the response
            return httpClient.execute(request, response -> {
                HttpEntity entity = response.getEntity();
                if (entity == null) {
                    try {
                        throw new Exception("Erreur lors de la requête initiale.");
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                }

                String result = EntityUtils.toString(entity);

                ObjectMapper mapper = new ObjectMapper();

                return mapper.readValue(result, Player.class);
            });

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
