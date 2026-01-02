package fr.arthurbr02.wotscraper.scraper.api;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import fr.arthurbr02.wotscraper.scraper.model.player.Player;

public class PlayerService {

    private static final String API_URL = "https://api.tomato.gg/api/player/overall/eu/{player_id}";

    private final ApiClient apiClient;

    public PlayerService(@NonNull ApiClient apiClient) {
        this.apiClient = apiClient;
    }

    @Nullable
    public Player fetchPlayer(long playerId) throws IOException {
        String url = API_URL.replace("{player_id}", String.valueOf(playerId));
        return apiClient.getJson(url, Player.class);
    }

    @NonNull
    public List<Player> fetchPlayers(@NonNull List<Long> playerIds) throws IOException {
        List<Player> players = new ArrayList<>();
        for (Long playerId : playerIds) {
            if (playerId == null) {
                continue;
            }
            players.add(fetchPlayer(playerId));
        }
        return players;
    }
}
