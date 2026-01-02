package fr.arthurbr02.wotscraper;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;

import com.google.android.material.bottomnavigation.BottomNavigationView;

import fr.arthurbr02.wotscraper.ui.LogsFragment;
import fr.arthurbr02.wotscraper.ui.MainFragment;
import fr.arthurbr02.wotscraper.ui.SettingsFragment;
import fr.arthurbr02.wotscraper.ui.exports.ExportDetailFragment;
import fr.arthurbr02.wotscraper.ui.exports.ExportsFragment;

public class MainActivity extends AppCompatActivity {

    private static final int REQ_POST_NOTIFICATIONS = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        requestNotificationsPermissionIfNeeded();

        BottomNavigationView bottomNav = findViewById(R.id.bottom_nav);
        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                showFragment(new MainFragment());
                return true;
            }
            if (id == R.id.nav_logs) {
                showFragment(new LogsFragment());
                return true;
            }
            if (id == R.id.nav_exports) {
                showFragment(new ExportsFragment());
                return true;
            }
            if (id == R.id.nav_settings) {
                showFragment(new SettingsFragment());
                return true;
            }
            return false;
        });

        if (savedInstanceState == null) {
            if (!handleViewIntent(getIntent(), bottomNav)) {
                bottomNav.setSelectedItemId(R.id.nav_home);
            }
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        BottomNavigationView bottomNav = findViewById(R.id.bottom_nav);
        handleViewIntent(intent, bottomNav);
    }

    private boolean handleViewIntent(Intent intent, BottomNavigationView bottomNav) {
        if (intent == null) return false;
        if (!Intent.ACTION_VIEW.equals(intent.getAction())) return false;

        Uri uri = intent.getData();
        if (uri == null) return false;

        // Prefer showing inside Exports section.
        if (bottomNav != null) {
            bottomNav.setSelectedItemId(R.id.nav_exports);
        }
        navigateTo(ExportDetailFragment.newInstance(uri), true);
        return true;
    }

    private void showFragment(@NonNull Fragment fragment) {
        showFragment(fragment, false);
    }

    public void navigateTo(@NonNull Fragment fragment, boolean addToBackStack) {
        showFragment(fragment, addToBackStack);
    }

    private void showFragment(@NonNull Fragment fragment, boolean addToBackStack) {
        androidx.fragment.app.FragmentTransaction tx = getSupportFragmentManager()
                .beginTransaction()
                .replace(R.id.fragment_container, fragment);

        if (addToBackStack) {
            tx.addToBackStack(null);
        }

        tx.commit();
    }

    private void requestNotificationsPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            return;
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
            return;
        }
        ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_POST_NOTIFICATIONS);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        // Phase 1: we don't hard-fail if notifications are denied.
    }
}
