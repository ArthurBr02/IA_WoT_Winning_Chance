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
}
