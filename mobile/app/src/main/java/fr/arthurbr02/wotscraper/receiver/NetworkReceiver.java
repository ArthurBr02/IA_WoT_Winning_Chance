package fr.arthurbr02.wotscraper.receiver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class NetworkReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        // Phase 1: placeholder.
        // On modern Android versions, connectivity broadcasts are restricted.
        // Phase 2/3 will handle connectivity via ConnectivityManager.NetworkCallback.
    }
}
