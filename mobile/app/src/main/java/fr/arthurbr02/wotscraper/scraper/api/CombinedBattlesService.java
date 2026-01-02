package fr.arthurbr02.wotscraper.scraper.api;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import fr.arthurbr02.wotscraper.scraper.model.battledetail.BattleDetail;
import fr.arthurbr02.wotscraper.scraper.model.combinedbattles.CombinedBattles;

public class CombinedBattlesService {

    private static final String API_URL = "https://api.tomato.gg/api/player/combined-battles/{player_id}?page=0&days=36500&pageSize={page_size}&sortBy=battle_time&sortDirection=desc&platoon=in-and-outside-platoon&spawn=all&won=all&classes=&nations=&roles=&tiers=&tankType=all";

    private final ApiClient apiClient;

    public CombinedBattlesService(@NonNull ApiClient apiClient) {
        this.apiClient = apiClient;
    }

    @Nullable
    public CombinedBattles fetchCombinedBattles(@NonNull String playerId) throws IOException {
        return fetchCombinedBattles(playerId, 50);
    }

    @Nullable
    public CombinedBattles fetchCombinedBattles(@NonNull String playerId, int pageSize) throws IOException {
        int safePageSize = Math.max(1, Math.min(500, pageSize));
        String url = API_URL
                .replace("{player_id}", playerId)
                .replace("{page_size}", String.valueOf(safePageSize));
        return apiClient.getJson(url, CombinedBattles.class);
    }

    @NonNull
    public List<BattleDetail> fetchBattleDetails(@NonNull List<Long> arenaIds, @NonNull BattleDetailService battleDetailService) throws IOException {
        List<BattleDetail> details = new ArrayList<>();
        for (Long arenaId : arenaIds) {
            if (arenaId == null) {
                continue;
            }
            BattleDetail detail = battleDetailService.fetchBattleDetail(arenaId);
            if (detail != null) {
                details.add(detail);
            }
        }
        return details;
    }
}
