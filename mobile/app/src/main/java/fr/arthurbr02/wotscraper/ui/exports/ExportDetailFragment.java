package fr.arthurbr02.wotscraper.ui.exports;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.io.File;
import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import android.provider.OpenableColumns;

import fr.arthurbr02.wotscraper.R;

public class ExportDetailFragment extends Fragment {

    private static final String ARG_PATH = "path";
    private static final String ARG_URI = "uri";

    public static ExportDetailFragment newInstance(@NonNull String absolutePath) {
        ExportDetailFragment f = new ExportDetailFragment();
        Bundle b = new Bundle();
        b.putString(ARG_PATH, absolutePath);
        f.setArguments(b);
        return f;
    }

    public static ExportDetailFragment newInstance(@NonNull Uri uri) {
        ExportDetailFragment f = new ExportDetailFragment();
        Bundle b = new Bundle();
        b.putString(ARG_URI, uri.toString());
        f.setArguments(b);
        return f;
    }

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private TextView title;
    private TextView meta;
    private ProgressBar progress;
    private RecyclerView recycler;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_export_detail, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        title = view.findViewById(R.id.title);
        meta = view.findViewById(R.id.meta);
        progress = view.findViewById(R.id.progress);
        recycler = view.findViewById(R.id.recycler);

        recycler.setLayoutManager(new LinearLayoutManager(requireContext()));

        Bundle args = getArguments();
        String path = args != null ? args.getString(ARG_PATH) : null;
        String uriStr = args != null ? args.getString(ARG_URI) : null;

        if (path != null) {
            File file = new File(path);
            title.setText(file.getName());

            DateFormat df = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.MEDIUM);
            meta.setText(df.format(new Date(file.lastModified())) + " • " + file.length() + " bytes");
            parse(file);
            return;
        }

        if (uriStr != null) {
            Uri uri = Uri.parse(uriStr);
            Context ctx = getContext();
            if (ctx == null) {
                title.setText("Export");
                meta.setText("Fichier introuvable");
                return;
            }
            title.setText(tryResolveDisplayName(ctx, uri));
            meta.setText(uri.toString());
            parse(ctx, uri);
            return;
        }

        title.setText("Export");
        meta.setText("Fichier introuvable");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }

    private void parse(@NonNull File file) {
        progress.setVisibility(View.VISIBLE);
        executor.execute(() -> {
            try {
                List<JsonTreeNode> nodes = new JsonTreeParser().parse(file);
                requireActivity().runOnUiThread(() -> {
                    progress.setVisibility(View.GONE);
                    final JsonTreeAdapter[] ref = new JsonTreeAdapter[1];
                    ref[0] = new JsonTreeAdapter(nodes, node -> {
                        if (ref[0] != null) {
                            ref[0].toggle(node);
                        }
                    });
                    recycler.setAdapter(ref[0]);
                });
            } catch (Exception e) {
                requireActivity().runOnUiThread(() -> {
                    progress.setVisibility(View.GONE);
                    meta.setText(meta.getText() + "\nErreur parsing JSON");
                });
            }
        });
    }

    private void parse(@NonNull Context context, @NonNull Uri uri) {
        progress.setVisibility(View.VISIBLE);
        executor.execute(() -> {
            try {
                List<JsonTreeNode> nodes = new JsonTreeParser().parse(context, uri);
                requireActivity().runOnUiThread(() -> {
                    progress.setVisibility(View.GONE);
                    final JsonTreeAdapter[] ref = new JsonTreeAdapter[1];
                    ref[0] = new JsonTreeAdapter(nodes, node -> {
                        if (ref[0] != null) {
                            ref[0].toggle(node);
                        }
                    });
                    recycler.setAdapter(ref[0]);
                });
            } catch (Exception e) {
                requireActivity().runOnUiThread(() -> {
                    progress.setVisibility(View.GONE);
                    meta.setText(meta.getText() + "\nErreur parsing JSON");
                });
            }
        });
    }

    @NonNull
    private static String tryResolveDisplayName(@NonNull Context context, @NonNull Uri uri) {
        try (Cursor cursor = context.getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) {
                    String name = cursor.getString(idx);
                    if (name != null && !name.trim().isEmpty()) {
                        return name;
                    }
                }
            }
        } catch (Exception ignored) {
        }

        String last = uri.getLastPathSegment();
        return last != null ? last : "Export";
    }
}
