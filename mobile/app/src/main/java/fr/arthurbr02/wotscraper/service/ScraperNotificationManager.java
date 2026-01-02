package fr.arthurbr02.wotscraper.service;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.MainActivity;

public class ScraperNotificationManager {

    public static final String CHANNEL_ID_ONGOING = "wot_scraper_ongoing";
    public static final String CHANNEL_ID_ALERTS = "wot_scraper_alerts";
    public static final String CHANNEL_ID_ERRORS = "wot_scraper_errors";
    public static final int NOTIFICATION_ID = 42;
    public static final String GROUP_KEY = "wot_scraper";

    private final Context context;
    private final NotificationManager notificationManager;

    public ScraperNotificationManager(@NonNull Context context) {
        this.context = context.getApplicationContext();
        this.notificationManager = (NotificationManager) this.context.getSystemService(Context.NOTIFICATION_SERVICE);
        ensureChannel();
    }

    private void ensureChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }

        NotificationChannel ongoing = new NotificationChannel(
            CHANNEL_ID_ONGOING,
            context.getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_LOW
        );
        ongoing.setDescription(context.getString(R.string.notification_channel_desc));
        ongoing.setShowBadge(false);

        NotificationChannel alerts = new NotificationChannel(
            CHANNEL_ID_ALERTS,
            context.getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_DEFAULT
        );
        alerts.setDescription(context.getString(R.string.notification_channel_desc));

        NotificationChannel errors = new NotificationChannel(
            CHANNEL_ID_ERRORS,
            context.getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_HIGH
        );
        errors.setDescription(context.getString(R.string.notification_channel_desc));

        notificationManager.createNotificationChannel(ongoing);
        notificationManager.createNotificationChannel(alerts);
        notificationManager.createNotificationChannel(errors);
    }

    @NonNull
        public Notification buildOngoing(@NonNull String title, @NonNull String content, long startedAtMs, int progress, int max, boolean indeterminate) {
        Intent openIntent = new Intent(context, MainActivity.class);
        PendingIntent openPending = PendingIntent.getActivity(
            context,
            1,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Intent stopIntent = new Intent(context, ScraperService.class);
        stopIntent.setAction(ScraperService.ACTION_STOP);
        PendingIntent stopPendingIntent = PendingIntent.getService(
                context,
                0,
                stopIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID_ONGOING)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(content)
            .setContentIntent(openPending)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setGroup(GROUP_KEY)
            .setShowWhen(true)
            .setWhen(startedAtMs > 0L ? startedAtMs : System.currentTimeMillis())
            .setUsesChronometer(startedAtMs > 0L)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .addAction(R.drawable.ic_notification, context.getString(R.string.action_stop), stopPendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW);

        if (max > 0) {
            builder.setProgress(max, Math.max(0, progress), indeterminate);
        }

        return builder.build();
    }

    public void notify(@NonNull Notification notification) {
        notificationManager.notify(NOTIFICATION_ID, notification);
    }

    public void notifyAlert(int id, @NonNull Notification notification) {
        notificationManager.notify(id, notification);
    }

    @NonNull
    public Notification buildAlert(@NonNull String channelId, @NonNull String title, @NonNull String content) {
        Intent openIntent = new Intent(context, MainActivity.class);
        PendingIntent openPending = PendingIntent.getActivity(
                context,
                0,
                openIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(context, channelId)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(content)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(content))
                .setContentIntent(openPending)
                .setAutoCancel(true)
                .setGroup(GROUP_KEY)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .build();
    }

    @NonNull
    public Notification buildInfoAlert(@NonNull String title, @NonNull String content) {
        return buildAlert(CHANNEL_ID_ALERTS, title, content);
    }

    @NonNull
    public Notification buildErrorAlert(@NonNull String title, @NonNull String content) {
        return buildAlert(CHANNEL_ID_ERRORS, title, content);
    }
}
