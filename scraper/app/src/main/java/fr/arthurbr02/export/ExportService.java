package fr.arthurbr02.export;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.Date;

public class ExportService {
    private static final Logger logger = LoggerFactory.getLogger(ExportService.class);
    private static final String FILE_NAME = "export_data_{date}.json";
    private static final String CURRENT_FILE_NAME = "export_data_current.json";

    public static void exportData(ExportData exportData, Date now) {
        File file = FileUtils.getNewFile(
                FILE_NAME.replace("{date}", String.valueOf(now.getTime()))
        );

        ObjectMapper mapper = new ObjectMapper();
        try {
            mapper.writerWithDefaultPrettyPrinter().writeValue(file, exportData);
            logger.info("Exported data to {}", file.getAbsolutePath());
        } catch (Exception e) {
            logger.error("Error exporting data to file", e);
        }
    }

    /**
     * Exporte les données en cours dans un fichier fixe (écrasé à chaque export)
     */
    public static void exportCurrentData(ExportData exportData) {
        File file = FileUtils.getNewFile(CURRENT_FILE_NAME);

        ObjectMapper mapper = new ObjectMapper();
        try {
            mapper.writerWithDefaultPrettyPrinter().writeValue(file, exportData);
            logger.info("Exported current data to {} ({} battles, {} players)",
                    file.getAbsolutePath(),
                    exportData.getBattleDetails() != null ? exportData.getBattleDetails().size() : 0,
                    exportData.getPlayers() != null ? exportData.getPlayers().size() : 0);
        } catch (Exception e) {
            logger.error("Error exporting current data to file", e);
        }
    }
}
