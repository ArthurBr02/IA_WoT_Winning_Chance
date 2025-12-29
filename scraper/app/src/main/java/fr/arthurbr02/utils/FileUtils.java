package fr.arthurbr02.utils;

import java.io.File;

public class FileUtils {
    public static final String DIRECTORY_PATH = "exports";

    public static File getNewFile(String fileName) {
        File directory = new File(DIRECTORY_PATH);
        if (!directory.exists()) {
            directory.mkdirs();
        }
        return new File(directory, fileName);
    }
}
