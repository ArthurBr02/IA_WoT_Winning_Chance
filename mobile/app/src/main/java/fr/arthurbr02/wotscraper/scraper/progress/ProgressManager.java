package fr.arthurbr02.wotscraper.scraper.progress;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.BufferedWriter;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.SyncFailedException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ProgressManager {

    private static final String TAG = "ProgressManager";

    private static final String PROGRESS_FILE = "scraper_progress.json";
    private static final String PROGRESS_BACKUP_FILE = "scraper_progress.backup.json";
    private static final String PROGRESS_TMP_FILE = "scraper_progress.tmp.json";

    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    private static final ExecutorService ASYNC_EXECUTOR = Executors.newSingleThreadExecutor();
    private static final Object ASYNC_LOCK = new Object();
    private static ProgressState pendingAsyncState;
    private static boolean asyncWorkerRunning = false;

    private ProgressManager() {
    }

    @NonNull
    private static File file(@NonNull Context context, @NonNull String name) {
        return new File(context.getFilesDir(), name);
    }

    public static synchronized void saveProgress(@NonNull Context context, @NonNull ProgressState state) throws IOException {
        state.setLastUpdateTimeMs(System.currentTimeMillis());

        File progressFile = file(context, PROGRESS_FILE);
        File backupFile = file(context, PROGRESS_BACKUP_FILE);
        File tmpFile = file(context, PROGRESS_TMP_FILE);

        // backup current
        if (progressFile.exists()) {
            copyFile(progressFile, backupFile);
        }

        // write tmp then rename
        try (FileOutputStream fos = new FileOutputStream(tmpFile, false)) {
            try (OutputStreamWriter osw = new OutputStreamWriter(fos, StandardCharsets.UTF_8);
                 BufferedWriter bw = new BufferedWriter(osw)) {
                gson.toJson(state, bw);
                bw.flush();
            }
            fos.flush();
            try {
                fos.getFD().sync();
            } catch (SyncFailedException ignored) {
                // Best-effort: some Android devices/FS can fail fsync even if the write succeeded.
                // We prefer keeping the scraper running rather than treating this as fatal.
            }
        }

        if (!tmpFile.renameTo(progressFile)) {
            // fallback: copy then delete
            copyFile(tmpFile, progressFile);
            //noinspection ResultOfMethodCallIgnored
            tmpFile.delete();
        }
    }

    /**
     * Non-blocking variant used during scraping loops.
     * Coalesces multiple calls and only writes the latest snapshot.
     */
    public static void saveProgressAsync(@NonNull Context context, @NonNull ProgressState snapshot) {
        final Context appContext = context.getApplicationContext();

        synchronized (ASYNC_LOCK) {
            pendingAsyncState = snapshot;
            if (asyncWorkerRunning) {
                return;
            }
            asyncWorkerRunning = true;
        }

        ASYNC_EXECUTOR.execute(() -> {
            while (true) {
                ProgressState next;
                synchronized (ASYNC_LOCK) {
                    next = pendingAsyncState;
                    pendingAsyncState = null;
                    if (next == null) {
                        asyncWorkerRunning = false;
                        return;
                    }
                }

                try {
                    saveProgress(appContext, next);
                } catch (Exception e) {
                    // Best-effort: never crash the scraper for a background persistence issue.
                    Log.w(TAG, "Async saveProgress failed", e);
                }
            }
        });
    }

    @Nullable
    public static synchronized ProgressState loadProgress(@NonNull Context context) {
        File progressFile = file(context, PROGRESS_FILE);
        File backupFile = file(context, PROGRESS_BACKUP_FILE);

        ProgressState state = tryLoadFile(progressFile);
        if (state != null) {
            return state;
        }

        state = tryLoadFile(backupFile);
        if (state != null) {
            // attempt restore
            try {
                copyFile(backupFile, progressFile);
            } catch (IOException ignored) {
            }
        }
        return state;
    }

    public static synchronized boolean hasProgress(@NonNull Context context) {
        return file(context, PROGRESS_FILE).exists();
    }

    public static synchronized void clearProgress(@NonNull Context context) {
        //noinspection ResultOfMethodCallIgnored
        file(context, PROGRESS_FILE).delete();
        //noinspection ResultOfMethodCallIgnored
        file(context, PROGRESS_BACKUP_FILE).delete();
        //noinspection ResultOfMethodCallIgnored
        file(context, PROGRESS_TMP_FILE).delete();
    }

    @Nullable
    private static ProgressState tryLoadFile(@NonNull File file) {
        if (!file.exists()) {
            return null;
        }
        try (FileInputStream fis = new FileInputStream(file);
             InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8);
             BufferedReader br = new BufferedReader(isr)) {
            ProgressState state = gson.fromJson(br, ProgressState.class);
            if (state != null) {
                state.ensureInitialized();
            }
            return state;
        } catch (Exception ignored) {
            return null;
        }
    }

    private static void copyFile(@NonNull File src, @NonNull File dst) throws IOException {
        try (FileInputStream in = new FileInputStream(src);
             FileOutputStream out = new FileOutputStream(dst, false)) {
            byte[] buf = new byte[8192];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            out.flush();
            try {
                out.getFD().sync();
            } catch (SyncFailedException ignored) {
                // Best-effort
            }
        }
    }
}
