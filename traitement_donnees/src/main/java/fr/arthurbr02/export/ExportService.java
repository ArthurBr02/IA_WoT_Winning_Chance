package fr.arthurbr02.export;

import com.fasterxml.jackson.databind.ObjectMapper;
import fr.arthurbr02.utils.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;

public class ExportService {
    private static final Logger logger = LoggerFactory.getLogger(ExportService.class);
    private static final String FILE_NAME = "export_data.json";

    public static ExportData getExportDateFromFile() {
        File file = FileUtils.getExportDataFile(FILE_NAME);

        if (!file.exists()) {
            logger.warn("Export data file does not exist: {}", file.getAbsolutePath());
            return null;
        }

        ObjectMapper mapper = new ObjectMapper();
        try {
            return mapper.readValue(file, ExportData.class);
        } catch (Exception e) {
            logger.error("Error reading export data from file", e);
            return null;
        }
    }
}
