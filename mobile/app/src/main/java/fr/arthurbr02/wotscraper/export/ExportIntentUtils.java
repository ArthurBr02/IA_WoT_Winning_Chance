package fr.arthurbr02.wotscraper.export;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;

import androidx.annotation.NonNull;
import androidx.core.content.FileProvider;

import java.io.File;

public class ExportIntentUtils {

    private ExportIntentUtils() {
    }

    @NonNull
    public static Uri toContentUri(@NonNull Context context, @NonNull File file) {
        String authority = context.getPackageName() + ".fileprovider";
        return FileProvider.getUriForFile(context, authority, file);
    }

    @NonNull
    public static Intent buildShareIntent(@NonNull Context context, @NonNull File file) {
        Uri uri = toContentUri(context, file);
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_STREAM, uri);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return Intent.createChooser(intent, "Partager l'export");
    }

    @NonNull
    public static Intent buildOpenIntent(@NonNull Context context, @NonNull File file) {
        Uri uri = toContentUri(context, file);
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(uri, "application/json");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return intent;
    }
}
