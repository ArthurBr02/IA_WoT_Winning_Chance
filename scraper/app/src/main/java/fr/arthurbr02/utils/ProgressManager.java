package fr.arthurbr02.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.Date;

/**
 * Gestionnaire de progression pour sauvegarder et charger l'état du scraping
 */
public class ProgressManager {
    private static final Logger logger = LoggerFactory.getLogger(ProgressManager.class);
    private static final String PROGRESS_FILE = "scraper_progress.json";
    private static final String PROGRESS_BACKUP_FILE = "scraper_progress.backup.json";
    private static final ObjectMapper mapper = new ObjectMapper();

    static {
        mapper.enable(SerializationFeature.INDENT_OUTPUT);
    }

    /**
     * Sauvegarde l'état de progression
     * Crée une copie de sauvegarde avant d'écraser le fichier existant
     */
    public static synchronized void saveProgress(ProgressState state) {
        state.setLastUpdateTime(new Date());

        File progressFile = FileUtils.getNewFile(PROGRESS_FILE);
        File backupFile = FileUtils.getNewFile(PROGRESS_BACKUP_FILE);

        try {
            // Créer une sauvegarde du fichier existant
            if (progressFile.exists()) {
                Files.copy(progressFile.toPath(), backupFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                logger.debug("Backup created: {}", backupFile.getAbsolutePath());
            }

            // Sauvegarder l'état actuel
            mapper.writeValue(progressFile, state);
            logger.info("Progress saved: {} battles, {} players processed, {}/{} players total",
                    state.getBattleDetails().size(),
                    state.getProcessedPlayerIds().size(),
                    state.getCurrentPlayerIndex(),
                    state.getTotalPlayersToFetch());
        } catch (IOException e) {
            logger.error("Error saving progress", e);
            // Tenter de restaurer depuis la sauvegarde
            if (backupFile.exists()) {
                try {
                    Files.copy(backupFile.toPath(), progressFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    logger.info("Progress file restored from backup");
                } catch (IOException ex) {
                    logger.error("Error restoring backup", ex);
                }
            }
        }
    }

    /**
     * Charge l'état de progression depuis le fichier
     * Retourne null si aucune progression n'existe
     */
    public static ProgressState loadProgress() {
        File progressFile = FileUtils.getNewFile(PROGRESS_FILE);

        if (!progressFile.exists()) {
            logger.info("No existing progress file found. Starting fresh.");
            return null;
        }

        try {
            ProgressState state = mapper.readValue(progressFile, ProgressState.class);
            logger.info("Progress loaded: {} battles, {} players processed, {}/{} players total",
                    state.getBattleDetails().size(),
                    state.getProcessedPlayerIds().size(),
                    state.getCurrentPlayerIndex(),
                    state.getTotalPlayersToFetch());
            logger.info("Last update: {}", state.getLastUpdateTime());
            return state;
        } catch (IOException e) {
            logger.error("Error loading progress file", e);

            // Tenter de charger depuis la sauvegarde
            File backupFile = FileUtils.getNewFile(PROGRESS_BACKUP_FILE);
            if (backupFile.exists()) {
                logger.info("Attempting to load from backup file");
                try {
                    ProgressState state = mapper.readValue(backupFile, ProgressState.class);
                    logger.info("Progress loaded from backup");
                    // Restaurer le fichier principal depuis la sauvegarde
                    Files.copy(backupFile.toPath(), progressFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    return state;
                } catch (IOException ex) {
                    logger.error("Error loading backup file", ex);
                }
            }
        }

        return null;
    }

    /**
     * Supprime les fichiers de progression
     */
    public static void clearProgress() {
        File progressFile = FileUtils.getNewFile(PROGRESS_FILE);
        File backupFile = FileUtils.getNewFile(PROGRESS_BACKUP_FILE);

        if (progressFile.exists()) {
            if (progressFile.delete()) {
                logger.info("Progress file deleted");
            } else {
                logger.warn("Failed to delete progress file");
            }
        }

        if (backupFile.exists()) {
            if (backupFile.delete()) {
                logger.info("Backup file deleted");
            } else {
                logger.warn("Failed to delete backup file");
            }
        }
    }

    /**
     * Vérifie si une progression existe
     */
    public static boolean hasProgress() {
        File progressFile = FileUtils.getNewFile(PROGRESS_FILE);
        return progressFile.exists();
    }
}

