package fr.arthurbr02.wotscraper.export;

import android.content.Context;

import androidx.annotation.NonNull;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.SyncFailedException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class ExportManager {

    private static final String EXPORT_DIR_NAME = "exports";
    private static final String LATEST_EXPORT_FILE = "export_latest.json";

    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    private ExportManager() {
    }

    @NonNull
    public static File exportLatest(@NonNull Context context, @NonNull ExportData data) throws IOException {
        File dir = ensureExportDir(context);
        File target = new File(dir, LATEST_EXPORT_FILE);
        writeAtomicJson(target, data);
        return target;
    }

    @NonNull
    public static List<ExportFileItem> listExports(@NonNull Context context) {
        File dir = getExportsDir(context);
        File[] files = dir.listFiles((d, name) -> name != null && name.toLowerCase().endsWith(".json"));
        if (files == null || files.length == 0) {
            return Collections.emptyList();
        }

        List<ExportFileItem> items = new ArrayList<>();
        for (File f : files) {
            if (f == null || !f.isFile()) continue;
            items.add(new ExportFileItem(
                    f.getName(),
                    f.getAbsolutePath(),
                    f.length(),
                    f.lastModified()
            ));
        }

        items.sort(Comparator.comparingLong((ExportFileItem i) -> i.lastModifiedMs).reversed());
        return items;
    }

    @NonNull
    public static File exportSnapshot(@NonNull Context context, @NonNull ExportData data) throws IOException {
        File dir = ensureExportDir(context);
        String filename = "export_data_" + System.currentTimeMillis() + ".json";
        File target = new File(dir, filename);
        writeAtomicJson(target, data);
        return target;
    }

    @NonNull
    public static File getExportsDir(@NonNull Context context) {
        try {
            return ensureExportDir(context);
        } catch (IOException e) {
            File dir = new File(context.getFilesDir(), EXPORT_DIR_NAME);
            //noinspection ResultOfMethodCallIgnored
            dir.mkdirs();
            return dir;
        }
    }

    @NonNull
    private static File ensureExportDir(@NonNull Context context) throws IOException {
        File base = context.getExternalFilesDir(null);
        if (base == null) {
            // Extremely rare; fallback to internal files.
            base = context.getFilesDir();
        }
        File dir = new File(base, EXPORT_DIR_NAME);
        if (!dir.exists() && !dir.mkdirs()) {
            throw new IOException("Failed to create export dir: " + dir.getAbsolutePath());
        }
        return dir;
    }

    private static void writeAtomicJson(@NonNull File target, @NonNull Object data) throws IOException {
        File dir = target.getParentFile();
        if (dir == null) {
            throw new IOException("Invalid export target: " + target.getAbsolutePath());
        }

        File tmp = new File(dir, target.getName() + ".tmp");
        try (FileOutputStream fos = new FileOutputStream(tmp, false)) {
            try (OutputStreamWriter osw = new OutputStreamWriter(fos, StandardCharsets.UTF_8)) {
                gson.toJson(data, osw);
                osw.flush();
            }
            fos.flush();
            try {
                fos.getFD().sync();
            } catch (SyncFailedException ignored) {
                // Best-effort
            }
        }

        if (!tmp.renameTo(target)) {
            // Fallback: copy then delete tmp.
            try (FileInputStream in = new FileInputStream(tmp);
                 FileOutputStream out = new FileOutputStream(target, false)) {
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
            //noinspection ResultOfMethodCallIgnored
            tmp.delete();
        }
    }
}
