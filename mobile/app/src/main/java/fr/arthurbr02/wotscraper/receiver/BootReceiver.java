package fr.arthurbr02.wotscraper.receiver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import androidx.core.content.ContextCompat;

import fr.arthurbr02.wotscraper.service.ScraperService;
import fr.arthurbr02.wotscraper.util.PreferencesManager;

public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            return;
        }

        PreferencesManager prefs = new PreferencesManager(context);
        if (!prefs.wasScraperRunning()) {
            return;
        }

        Intent serviceIntent = new Intent(context, ScraperService.class);
        serviceIntent.setAction(ScraperService.ACTION_START);
        ContextCompat.startForegroundService(context, serviceIntent);
    }
}
