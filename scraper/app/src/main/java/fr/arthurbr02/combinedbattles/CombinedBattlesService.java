package fr.arthurbr02.combinedbattles;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

import static fr.arthurbr02.battledetail.BattleDetailService.fetchBattleDetail;

public class CombinedBattlesService {
    private static final Logger logger = LoggerFactory.getLogger(CombinedBattlesService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/combined-battles/{player_id}?page=0&days=36500&pageSize=50&sortBy=battle_time&sortDirection=desc&platoon=in-and-outside-platoon&spawn=all&won=all&classes=&nations=&roles=&tiers=&tankType=all";
    private static final int MAX_429_RETRIES = 1000;

    public static CombinedBattles fetchCombinedBattles(String playerId) {
        String url = API_URL.replace("{player_id}", playerId);

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
                    return mapper.readValue(result, CombinedBattles.class);
                }
            }

            logger.error("Still rate-limited after {} attempts for {}", MAX_429_RETRIES, url);
            return null;
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            logger.error("Interrupted while waiting after 429 for playerId: {}", playerId, ie);
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
