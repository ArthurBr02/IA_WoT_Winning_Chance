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

    public static final String CHANNEL_ID = "wot_scraper_channel";
    public static final int NOTIFICATION_ID = 42;

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
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                context.getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
        );
        channel.setDescription(context.getString(R.string.notification_channel_desc));
        notificationManager.createNotificationChannel(channel);
    }

    @NonNull
    public Notification buildOngoing(@NonNull String title, @NonNull String content, int progress, int max, boolean indeterminate) {
        Intent stopIntent = new Intent(context, ScraperService.class);
        stopIntent.setAction(ScraperService.ACTION_STOP);
        PendingIntent stopPendingIntent = PendingIntent.getService(
                context,
                0,
                stopIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(content)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
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
    public Notification buildAlert(@NonNull String title, @NonNull String content) {
        Intent openIntent = new Intent(context, MainActivity.class);
        PendingIntent openPending = PendingIntent.getActivity(
                context,
                0,
                openIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(content)
                .setContentIntent(openPending)
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .build();
    }
}
