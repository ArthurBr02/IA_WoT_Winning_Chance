package fr.arthurbr02.battledetail;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.DefaultHttpRequestRetryStrategy;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.util.TimeValue;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BattleDetailService {
    private static final Logger logger = LoggerFactory.getLogger(BattleDetailService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/battle-detail/{arena_id}";

    public static BattleDetail fetchBattleDetail(Long arenaId) {
        logger.info("Fetching BattleDetail for arenaId: {}", arenaId);
        String url = API_URL.replace("{arena_id}", arenaId.toString());

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

                return mapper.readValue(result, BattleDetail.class);
            });

        } catch (Exception e) {
            logger.error("Error fetching BattleDetail for arenaId: {}", arenaId, e);
        }

        return null;
    }
}
