package fr.arthurbr02.utils;

import java.io.File;
import java.nio.file.Files;

public class FileUtils {
    public static File getResourcesDirectory() {
        File resourcesDir = new File("src/main/resources");
        if (!resourcesDir.exists()) {
            resourcesDir.mkdirs();
        }
        return resourcesDir;
    }

    public static File getExportDataFile(String fileName) {
        return new File(getResourcesDirectory(), fileName);
    }

    public static void writeStringToFile(String fileName, String string) {
        try {
            File file = new File(getResourcesDirectory(), fileName);
            Files.writeString(file.toPath(), string);
            System.out.println("Written to file: " + file.getAbsolutePath());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
