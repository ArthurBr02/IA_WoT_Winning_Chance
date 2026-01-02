package fr.arthurbr02.wotscraper.service;

import android.app.Notification;
import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import fr.arthurbr02.wotscraper.export.ExportData;
import fr.arthurbr02.wotscraper.scraper.LogLevel;
import fr.arthurbr02.wotscraper.scraper.ScraperCallback;
import fr.arthurbr02.wotscraper.scraper.ScraperEngine;
import fr.arthurbr02.wotscraper.scraper.ScrapingPhase;

import fr.arthurbr02.wotscraper.util.PreferencesManager;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressManager;
import fr.arthurbr02.wotscraper.scraper.progress.ProgressState;
import fr.arthurbr02.wotscraper.ui.LogManager;
import fr.arthurbr02.wotscraper.ui.ScraperStateRepository;

public class ScraperService extends Service {

    public static final String ACTION_START = "fr.arthurbr02.wotscraper.action.START";
    public static final String ACTION_STOP = "fr.arthurbr02.wotscraper.action.STOP";

    private static final String TAG = "ScraperService";

    private final IBinder binder = new LocalBinder();
    private ExecutorService executor;
    private Future<?> runningTask;

    private ScraperNotificationManager notificationManager;
    private PreferencesManager preferencesManager;

    private ScraperEngine scraperEngine;

    private volatile boolean isRunning = false;

    private volatile ScrapingPhase lastPhase = ScrapingPhase.NOT_STARTED;

    public class LocalBinder extends Binder {
        public ScraperService getService() {
            return ScraperService.this;
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        notificationManager = new ScraperNotificationManager(this);
        preferencesManager = new PreferencesManager(this);
        executor = Executors.newSingleThreadExecutor();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return binder;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (ACTION_STOP.equals(action)) {
            stopScraper();
            stopSelf();
            return START_NOT_STICKY;
        }

        // Default behavior: start.
        startScraper();
        return START_STICKY;
    }

    public boolean isRunning() {
        return isRunning;
    }

    public void startScraper() {
        if (isRunning) {
            // The service may already be running while the UI process just (re)attached.
            // Ensure the UI state is refreshed.
            long startedAtMs = System.currentTimeMillis();
            ProgressState ps = ProgressManager.loadProgress(this);
            if (ps != null) {
                startedAtMs = ps.getStartTimeMs();
            }
            ScraperStateRepository.getInstance().setRunning(true, startedAtMs);
            return;
        }
        isRunning = true;
        preferencesManager.setScraperWasRunning(true);

        long startedAtMs = System.currentTimeMillis();
        ProgressState ps = ProgressManager.loadProgress(this);
        if (ps != null) {
            startedAtMs = ps.getStartTimeMs();
        }
        final long startedAtMsFinal = startedAtMs;
        ScraperStateRepository.getInstance().setRunning(true, startedAtMs);

        Notification notification = notificationManager.buildOngoing(
                "WoT Scraper",
                "Scraping en cours…",
            startedAtMsFinal,
                0,
                0,
                true
        );
        startForeground(ScraperNotificationManager.NOTIFICATION_ID, notification);

        ScraperCallback callback = new ScraperCallback() {
            @Override
            public void onPhaseChanged(@NonNull ScrapingPhase phase) {
                Log.i(TAG, "Phase changed: " + phase);
                lastPhase = phase;
                ScraperStateRepository.getInstance().setPhase(phase);
                if (preferencesManager.isPhaseNotificationEnabled()) {
                    notificationManager.notifyAlert(ScraperNotificationManager.NOTIFICATION_ID + 1,
                            notificationManager.buildInfoAlert("WoT Scraper", "Étape: " + phase.name()));
                }
            }

            @Override
            public void onProgressUpdate(int current, int total, @NonNull String message) {
                Notification updated = notificationManager.buildOngoing(
                        "WoT Scraper",
                        message,
                    startedAtMsFinal,
                        current,
                        total,
                        total <= 0
                );
                notificationManager.notify(updated);

                if (lastPhase == ScrapingPhase.COMBINED_BATTLES) {
                    ScraperStateRepository.getInstance().setStep1(current, Math.max(1, total), message);
                } else if (lastPhase == ScrapingPhase.PLAYERS) {
                    ScraperStateRepository.getInstance().setStep3(current, Math.max(0, total), message);
                } else {
                    ScraperStateRepository.getInstance().setStep2(current, Math.max(0, total), message);
                }

                ProgressState ps = ProgressManager.loadProgress(ScraperService.this);
                if (ps != null) {
                    ps.ensureInitialized();
                    ScraperStateRepository.getInstance().setCounts(ps.getBattleDetails().size(), ps.getPlayers().size());
                }
            }

            @Override
            public void onLog(@NonNull LogLevel level, @NonNull String message) {
                LogManager.getInstance().add(level, message);
                switch (level) {
                    case DEBUG:
                        Log.d(TAG, message);
                        break;
                    case INFO:
                        Log.i(TAG, message);
                        break;
                    case WARN:
                        Log.w(TAG, message);
                        break;
                    case ERROR:
                    default:
                        Log.e(TAG, message);
                        break;
                }
            }

            @Override
            public void onError(@NonNull Exception e, boolean fatal) {
                Log.e(TAG, fatal ? "Fatal error" : "Non-fatal error", e);
                LogManager.getInstance().add(LogLevel.ERROR, (fatal ? "Fatal: " : "Error: ") + e.getMessage());
                if (preferencesManager.isErrorNotificationEnabled()) {
                    notificationManager.notifyAlert(ScraperNotificationManager.NOTIFICATION_ID + 2,
                            notificationManager.buildErrorAlert("WoT Scraper", "Erreur: " + e.getClass().getSimpleName() + "\n" + (e.getMessage() != null ? e.getMessage() : "")));
                }
            }

            @Override
            public void onDataCollected(@NonNull ExportData partialData) {
                // Phase 2: data is persisted via ProgressManager; UI export comes later.
            }

            @Override
            public void onComplete(@NonNull ExportData finalData) {
                Log.i(TAG, "Scraper completed");
                ScraperStateRepository.getInstance().setPhase(ScrapingPhase.COMPLETED);
                if (preferencesManager.isCompleteNotificationEnabled()) {
                    notificationManager.notifyAlert(ScraperNotificationManager.NOTIFICATION_ID + 3,
                            notificationManager.buildInfoAlert("WoT Scraper", "Scraping terminé"));
                }
            }
        };

        scraperEngine = new ScraperEngine(this, callback);
        runningTask = executor.submit(() -> {
            try {
                scraperEngine.run();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                Log.e(TAG, "Fatal error in scraper engine", e);
            } finally {
                isRunning = false;
                preferencesManager.setScraperWasRunning(false);
                ScraperStateRepository.getInstance().setRunning(false, 0L);
                stopForeground(STOP_FOREGROUND_REMOVE);
                stopSelf();
            }
        });
    }

    public void stopScraper() {
        isRunning = false;
        preferencesManager.setScraperWasRunning(false);
        ScraperStateRepository.getInstance().setRunning(false, 0L);
        if (scraperEngine != null) {
            scraperEngine.requestStop();
        }
        if (runningTask != null) {
            runningTask.cancel(true);
            runningTask = null;
        }
        stopForeground(STOP_FOREGROUND_REMOVE);
    }

    @Override
    public void onDestroy() {
        stopScraper();
        if (executor != null) {
            executor.shutdownNow();
            executor = null;
        }
        super.onDestroy();
    }

    public static void startForegroundServiceCompat(Service caller) {
        Intent intent = new Intent(caller, ScraperService.class);
        intent.setAction(ACTION_START);
        ContextCompat.startForegroundService(caller, intent);
    }
}
