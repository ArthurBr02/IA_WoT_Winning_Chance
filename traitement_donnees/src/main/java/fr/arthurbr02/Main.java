package fr.arthurbr02;

import fr.arthurbr02.battledetail.BattleDetail;
import fr.arthurbr02.datasetbuilder.Row;
import fr.arthurbr02.export.ExportData;
import fr.arthurbr02.export.ExportService;
import fr.arthurbr02.player.Data;
import fr.arthurbr02.player.Player;
import fr.arthurbr02.utils.FileUtils;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Stream;

public class Main {
    public static void main(String[] args) {
        ExportData data = ExportService.getExportDateFromFile();

        if (data != null) {
            System.out.println("Export data loaded successfully.");
        } else {
            System.out.println("Failed to load export data.");
            return;
        }

        // Pour chaque BattleDetail, je veux faire un fichier csv avec comme données (ce seront les features d'un modèle ML):
        // - battles (Player)
        // - overallWN8 (Player)
        // - overallWNX (Player)
        // - winrate (Player)
        // - dpg (Player)
        // - assist (Player)
        // - frags (Player)
        // - survival (Player)
        // - spots (Player)
        // - cap (Player)
        // - def (Player)
        // - xp (Player)
        // - kd (Player)
        // - mapId (BattleDetail)
        // - spawn (BattleDetail > Player)

        // La target sera la victoire de l'équipe 1 (BattleDetail > Player avec spawn == 1 && won == true)
        // - 1 si l'équipe 1 a gagné
        // - 0 sinon

        // Je commence pas mapper les players par leur id pour y accéder plus facilement
        Map<Long, Player> playerMap = new HashMap<>();
        for (Player player : data.getPlayers()) {
            if (player == null || player.getData() == null) {
                System.out.println("Player data is null");
                continue;
            }
            playerMap.put(player.getData().getId(), player);
        }

        // Ensuite, je map les battledetail.Player par battleDetail id et player id
        Map<String, Map<Long, fr.arthurbr02.battledetail.Player>> battleDetailPlayerMap = new HashMap<>();
        for (BattleDetail battleDetail : data.getBattleDetails()) {
            Map<Long, fr.arthurbr02.battledetail.Player> innerMap = new HashMap<>();
            for (fr.arthurbr02.battledetail.Player bdPlayer : battleDetail.getPlayers()) {
                innerMap.put(bdPlayer.getPlayerId(), bdPlayer);
            }
            battleDetailPlayerMap.put(battleDetail.getId(), innerMap);
        }

        // Maintenant je construis un dataset par battledetail
        for (BattleDetail battleDetail : data.getBattleDetails()) {
            System.out.println("Generating dataset for BattleDetail ID: " + battleDetail.getId());
            StringBuilder csvBuilder = new StringBuilder();

            // Header
            csvBuilder.append(String.join(";", Row.HEADERS)).append("\n");

            for (fr.arthurbr02.battledetail.Player bdPlayer : battleDetail.getPlayers()) {
                Player player = playerMap.get(bdPlayer.getPlayerId());
                if (player == null) {
                    System.out.println("Player not found for ID: " + bdPlayer.getId());
                    continue;
                }

                Data dataPlayer = player.getData();

                // Vérifier si toutes les valeurs nécessaires sont présentes
                boolean hasAllValues = Stream.of(
                    dataPlayer.getBattles(),
                    dataPlayer.getOverallWN8(),
                    dataPlayer.getOverallWNX(),
                    dataPlayer.getWinrate(),
                    dataPlayer.getDpg(),
                    dataPlayer.getAssist(),
                    dataPlayer.getFrags(),
                    dataPlayer.getSurvival(),
                    dataPlayer.getSpots(),
                    dataPlayer.getCap(),
                    dataPlayer.getDef(),
                    dataPlayer.getXp(),
                    dataPlayer.getKd()
                ).noneMatch(Objects::isNull);

                if (!hasAllValues) {
                    System.out.println("Skipping player ID: " + bdPlayer.getPlayerId() + " - missing data");
                    continue;
                }

                Row row = new Row();

                // Features from Player
                row.setBattles(dataPlayer.getBattles());
                row.setOverallWN8(dataPlayer.getOverallWN8());
                row.setOverallWNX(dataPlayer.getOverallWNX());
                row.setWinrate(dataPlayer.getWinrate());
                row.setDpg(dataPlayer.getDpg());
                row.setAssist(dataPlayer.getAssist());
                row.setFrags(dataPlayer.getFrags());
                row.setSurvival(dataPlayer.getSurvival());
                row.setSpots(dataPlayer.getSpots());
                row.setCap(dataPlayer.getCap());
                row.setDef(dataPlayer.getDef());
                row.setXp(dataPlayer.getXp());
                row.setKd(dataPlayer.getKd());

                // Features from BattleDetail.Player
                row.setMap(battleDetail.getGeneral().getMapId());
                row.setSpawn(bdPlayer.getSpawn());

                // Target
                if (bdPlayer.getSpawn() == 1) {
                    row.setTarget(battleDetail.isTeam1Won() ? 1 : 0);
                } else {
                    row.setTarget(battleDetail.isTeam1Won() ? 0 : 1);
                }

                // Append CSV line
                csvBuilder.append(row.toCsvLine()).append("\n");
            }

            // Write to file
            String fileName = "datasets/dataset_battle_" + battleDetail.getId() + ".csv";
            FileUtils.writeStringToFile(fileName, csvBuilder.toString());
        }

        System.out.println("Datasets generated successfully.");
    }
}