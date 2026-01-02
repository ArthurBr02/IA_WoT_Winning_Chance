package fr.arthurbr02.wotscraper.ui;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.export.ExportData;
import fr.arthurbr02.wotscraper.export.ExportManager;
import fr.arthurbr02.wotscraper.scraper.ScrapingPhase;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressManager;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressState;
import fr.arthurbr02.wotscraper.service.ScraperService;

public class MainFragment extends Fragment {

    private TextView tvStatus;
    private TextView tvElapsed;

    private ProgressBar pb1;
    private ProgressBar pb2;
    private ProgressBar pb3;

    private TextView tv1;
    private TextView tv2;
    private TextView tv3;

    private Button btnStart;
    private Button btnStop;
    private Button btnViewLogs;
    private Button btnExport;
    private Button btnReset;

    private ScraperUiState lastState = ScraperUiState.idle();
    private final Handler handler = new Handler(Looper.getMainLooper());

    private final ExecutorService ioExecutor = Executors.newSingleThreadExecutor();
    private volatile int refreshToken = 0;
    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            updateElapsed();
            handler.postDelayed(this, 1000);
        }
    };

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_main, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        tvStatus = view.findViewById(R.id.tvStatus);
        tvElapsed = view.findViewById(R.id.tvElapsedTime);

        pb1 = view.findViewById(R.id.progressStep1);
        pb2 = view.findViewById(R.id.progressStep2);
        pb3 = view.findViewById(R.id.progressStep3);

        tv1 = view.findViewById(R.id.tvStep1Details);
        tv2 = view.findViewById(R.id.tvStep2Details);
        tv3 = view.findViewById(R.id.tvStep3Details);

        btnStart = view.findViewById(R.id.btnStart);
        btnStop = view.findViewById(R.id.btnStop);
        btnViewLogs = view.findViewById(R.id.btnViewLogs);
        btnExport = view.findViewById(R.id.btnExport);
        btnReset = view.findViewById(R.id.btnReset);

        ScraperViewModel vm = new ViewModelProvider(requireActivity()).get(ScraperViewModel.class);
        vm.getState().observe(getViewLifecycleOwner(), this::render);

        btnStart.setOnClickListener(v -> {
            Context context = requireContext();
            Intent intent = new Intent(context, ScraperService.class);
            intent.setAction(ScraperService.ACTION_START);
            ContextCompat.startForegroundService(context, intent);
        });

        btnStop.setOnClickListener(v -> {
            Context context = getContext();
            if (context == null) {
                return;
            }
            Intent intent = new Intent(context, ScraperService.class);
            intent.setAction(ScraperService.ACTION_STOP);
            // Do NOT use startForegroundService() for STOP: it may not call startForeground().
            context.startService(intent);
        });

        btnViewLogs.setOnClickListener(v -> {
            View bottom = requireActivity().findViewById(R.id.bottom_nav);
            if (bottom instanceof com.google.android.material.bottomnavigation.BottomNavigationView) {
                ((com.google.android.material.bottomnavigation.BottomNavigationView) bottom).setSelectedItemId(R.id.nav_logs);
            }
        });

        btnExport.setOnClickListener(v -> exportSnapshotAndOpen());

        btnReset.setOnClickListener(v -> resetScraping());

        // Best-effort: load last progress from disk so the UI is useful even before the service runs.
        // Done async in onStart to avoid blocking navigation/first render.
    }

    @Override
    public void onStart() {
        super.onStart();
        handler.post(tick);
        refreshFromDiskAsync();
    }

    @Override
    public void onStop() {
        super.onStop();
        handler.removeCallbacks(tick);
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        ioExecutor.shutdownNow();
    }

    private void render(@NonNull ScraperUiState state) {
        Context context = getContext();
        if (context == null) {
            return;
        }
        lastState = state;

        String status;
        if (state.running) {
            status = context.getString(R.string.status_running) + " (" + state.phase.name() + ")";
        } else {
            status = context.getString(R.string.status_stopped) + (state.phase != ScrapingPhase.NOT_STARTED ? " (" + state.phase.name() + ")" : "");
        }
        tvStatus.setText(status);

        pb1.setMax(Math.max(1, state.step1Total));
        pb1.setProgress(Math.max(0, state.step1Current));
        tv1.setText(state.step1Details);

        pb2.setMax(Math.max(0, state.step2Total));
        pb2.setProgress(Math.max(0, state.step2Current));
        tv2.setText(state.step2Details);

        pb3.setMax(Math.max(0, state.step3Total));
        pb3.setProgress(Math.max(0, state.step3Current));
        tv3.setText(state.step3Details);

        btnStart.setEnabled(!state.running);
        btnStop.setEnabled(state.running);

        updateElapsed();
    }

    private void updateElapsed() {
        if (tvElapsed == null) {
            return;
        }

        if (!lastState.running || lastState.startedAtMs <= 0L) {
            tvElapsed.setText("");
            return;
        }

        long elapsedMs = Math.max(0L, System.currentTimeMillis() - lastState.startedAtMs);
        long totalSeconds = elapsedMs / 1000L;
        long h = totalSeconds / 3600L;
        long m = (totalSeconds % 3600L) / 60L;
        long s = totalSeconds % 60L;
        tvElapsed.setText(String.format("%s %02d:%02d:%02d", "Temps écoulé:", h, m, s));
    }

    private void refreshFromDiskAsync() {
        final Context context = getContext();
        if (context == null) {
            return;
        }

        final int token = ++refreshToken;

        ioExecutor.execute(() -> {
            try {
                ProgressState ps = ProgressManager.loadProgress(context);
                if (ps == null) {
                    return;
                }
                ps.ensureInitialized();

                final ScrapingPhase phase = ps.getCurrentPhase() != null ? ps.getCurrentPhase() : ScrapingPhase.NOT_STARTED;
                final int step1 = ps.getCombinedBattles() != null ? 1 : 0;
                final String step1Details = ps.getCombinedBattles() != null ? "OK" : "";

                final int step2Total = ps.getPendingArenaIds() != null ? ps.getPendingArenaIds().size() : 0;
                final int step2Current = Math.min(step2Total, Math.max(0, ps.getCurrentArenaIndex()));
                final int battleDetailsCount = ps.getBattleDetails() != null ? ps.getBattleDetails().size() : 0;

                final int step3Total = ps.getPendingPlayerDetailIds() != null ? ps.getPendingPlayerDetailIds().size() : 0;
                final int step3Current = Math.min(step3Total, Math.max(0, ps.getCurrentPlayerDetailIndex()));
                final int playersCount = ps.getPlayers() != null ? ps.getPlayers().size() : 0;

                handler.post(() -> {
                    if (!isAdded() || token != refreshToken) {
                        return;
                    }
                    ScraperStateRepository repo = ScraperStateRepository.getInstance();
                    repo.setPhase(phase);
                    repo.setStep1(step1, 1, step1Details);
                    repo.setStep2(step2Current, step2Total, "BattleDetails: " + battleDetailsCount);
                    repo.setStep3(step3Current, step3Total, "Players: " + playersCount);
                    repo.setCounts(battleDetailsCount, playersCount);
                });
            } catch (Exception ignored) {
            }
        });
    }

    private void exportSnapshotAndOpen() {
        try {
            Context context = getContext();
            if (context == null) {
                return;
            }

            ProgressState ps = ProgressManager.loadProgress(context);
            if (ps == null) {
                Toast.makeText(context, "Aucune donnée à exporter", Toast.LENGTH_SHORT).show();
                return;
            }
            ps.ensureInitialized();
            ExportData data = new ExportData(ps.getCombinedBattles(), ps.getBattleDetails(), ps.getPlayers());
            ExportManager.exportSnapshot(context, data);
            Toast.makeText(context, "Export créé dans exports/", Toast.LENGTH_SHORT).show();

            View bottom = requireActivity().findViewById(R.id.bottom_nav);
            if (bottom instanceof com.google.android.material.bottomnavigation.BottomNavigationView) {
                ((com.google.android.material.bottomnavigation.BottomNavigationView) bottom).setSelectedItemId(R.id.nav_exports);
            } else if (getActivity() instanceof fr.arthurbr02.wotscraper.MainActivity) {
                // Fallback if bottom nav isn't present for some reason.
                ((fr.arthurbr02.wotscraper.MainActivity) getActivity())
                        .navigateTo(new fr.arthurbr02.wotscraper.ui.exports.ExportsFragment(), true);
            }
        } catch (Exception e) {
            Context context = getContext();
            if (context != null) {
                Toast.makeText(context, "Export échoué", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void resetScraping() {
        try {
            // Stop running work first.
            Context context = getContext();
            if (context == null) {
                return;
            }
            Intent stop = new Intent(context, ScraperService.class);
            stop.setAction(ScraperService.ACTION_STOP);
            // Do NOT use startForegroundService() for STOP: it may not call startForeground().
            context.startService(stop);

            ProgressManager.clearProgress(context);
            LogManager.getInstance().clear();

            ScraperStateRepository repo = ScraperStateRepository.getInstance();
            repo.setRunning(false, 0L);
            repo.setPhase(ScrapingPhase.NOT_STARTED);
            repo.setStep1(0, 1, "");
            repo.setStep2(0, 0, "");
            repo.setStep3(0, 0, "");
            repo.setCounts(0, 0);

            Toast.makeText(context, "Scraping reset", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Context context = getContext();
            if (context != null) {
                Toast.makeText(context, "Reset échoué", Toast.LENGTH_SHORT).show();
            }
        }
    }
}
