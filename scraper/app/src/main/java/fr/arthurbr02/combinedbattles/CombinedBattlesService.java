package fr.arthurbr02.combinedbattles;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.battledetail.BattleDetail;
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

import static fr.arthurbr02.battledetail.BattleDetailService.fetchBattleDetail;

public class CombinedBattlesService {
    private static final Logger logger = LoggerFactory.getLogger(CombinedBattlesService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/combined-battles/{player_id}?page=0&days=36500&pageSize=10&sortBy=battle_time&sortDirection=desc&platoon=in-and-outside-platoon&spawn=all&won=all&classes=&nations=&roles=&tiers=&tankType=all";

    public static CombinedBattles fetchCombinedBattles(String playerId) {
        String url = API_URL.replace("{player_id}", playerId);

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

                return mapper.readValue(result, CombinedBattles.class);
            });
        } catch (Exception e) {
            logger.error("Error fetching CombinedBattles for playerId: {}", playerId, e);
        }

        return null;
    }

    public static List<BattleDetail> fetchBattleDetails(List<Long> arenaIds) {
        List<BattleDetail> battleDetails = new ArrayList<>();

        for (Long arenaId : arenaIds) {
            BattleDetail detail = fetchBattleDetail(arenaId);
            if (detail != null) {
                battleDetails.add(detail);
            }
        }

        return battleDetails;
    }
}
