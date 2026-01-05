package fr.arthurbr02.battledetail;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.HttpClientsUtils;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BattleDetailService {
    private static final Logger logger = LoggerFactory.getLogger(BattleDetailService.class);
    private static final String API_URL = "https://api.tomato.gg/api/player/battle-detail/{arena_id}";
    private static final int MAX_429_RETRIES = 1000;

    public static BattleDetail fetchBattleDetail(Long arenaId) {
        logger.info("Fetching BattleDetail for arenaId: {}", arenaId);
        String url = API_URL.replace("{arena_id}", arenaId.toString());

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
                    return mapper.readValue(result, BattleDetail.class);
                }
            }

            logger.error("Still rate-limited after {} attempts for {}", MAX_429_RETRIES, url);
            return null;

        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            logger.error("Interrupted while waiting after 429 for arenaId: {}", arenaId, ie);
        } catch (Exception e) {
            logger.error("Error fetching BattleDetail for arenaId: {}", arenaId, e);
        }

        return null;
    }
}
