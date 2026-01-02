package fr.arthurbr02.wotscraper.scraper.api;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.IOException;

import fr.arthurbr02.wotscraper.scraper.model.battledetail.BattleDetail;

public class BattleDetailService {

    private static final String API_URL = "https://api.tomato.gg/api/player/battle-detail/{arena_id}";

    private final ApiClient apiClient;

    public BattleDetailService(@NonNull ApiClient apiClient) {
        this.apiClient = apiClient;
    }

    @Nullable
    public BattleDetail fetchBattleDetail(long arenaId) throws IOException {
        String url = API_URL.replace("{arena_id}", String.valueOf(arenaId));
        return apiClient.getJson(url, BattleDetail.class);
    }
}
