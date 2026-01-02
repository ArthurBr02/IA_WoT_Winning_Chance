package fr.arthurbr02.wotscraper.ui.exports;

import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.io.File;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.export.ExportFileItem;
import fr.arthurbr02.wotscraper.export.ExportIntentUtils;
import fr.arthurbr02.wotscraper.export.ExportManager;
import fr.arthurbr02.wotscraper.MainActivity;

public class ExportsFragment extends Fragment {

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private RecyclerView recycler;
    private ProgressBar progress;
    private TextView empty;
    private ExportListAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_exports, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        recycler = view.findViewById(R.id.recycler);
        progress = view.findViewById(R.id.progress);
        empty = view.findViewById(R.id.empty);

        recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        adapter = new ExportListAdapter(new ExportListAdapter.Listener() {
            @Override
            public void onOpenDetail(@NonNull ExportFileItem item) {
                if (getActivity() instanceof MainActivity) {
                    ((MainActivity) getActivity()).navigateTo(ExportDetailFragment.newInstance(item.absolutePath), true);
                }
            }

            @Override
            public void onShare(@NonNull ExportFileItem item) {
                File f = new File(item.absolutePath);
                Intent intent = ExportIntentUtils.buildShareIntent(requireContext(), f);
                try {
                    startActivity(intent);
                } catch (ActivityNotFoundException e) {
                    Toast.makeText(requireContext(), "Aucune app pour partager", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onOpenExternal(@NonNull ExportFileItem item) {
                // Open inside app (JSON viewer)
                if (getActivity() instanceof MainActivity) {
                    ((MainActivity) getActivity()).navigateTo(ExportDetailFragment.newInstance(item.absolutePath), true);
                }
            }

            @Override
            public void onDelete(@NonNull ExportFileItem item) {
                executor.execute(() -> {
                    boolean ok;
                    try {
                        ok = new File(item.absolutePath).delete();
                    } catch (Exception e) {
                        ok = false;
                    }

                    boolean finalOk = ok;
                    if (getActivity() == null) {
                        return;
                    }
                    requireActivity().runOnUiThread(() -> {
                        Toast.makeText(
                                requireContext(),
                                finalOk ? "Export supprimé" : "Suppression échouée",
                                Toast.LENGTH_SHORT
                        ).show();
                        load();
                    });
                });
            }
        });
        recycler.setAdapter(adapter);

        load();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }

    private void load() {
        showLoading(true);
        executor.execute(() -> {
            List<ExportFileItem> items;
            try {
                items = ExportManager.listExports(requireContext());
            } catch (Exception e) {
                items = Collections.emptyList();
            }

            List<ExportFileItem> finalItems = items;
            requireActivity().runOnUiThread(() -> {
                adapter.setItems(finalItems);
                showLoading(false);
                empty.setVisibility(finalItems.isEmpty() ? View.VISIBLE : View.GONE);
                recycler.setVisibility(finalItems.isEmpty() ? View.GONE : View.VISIBLE);
            });
        });
    }

    private void showLoading(boolean isLoading) {
        progress.setVisibility(isLoading ? View.VISIBLE : View.GONE);
    }
}
