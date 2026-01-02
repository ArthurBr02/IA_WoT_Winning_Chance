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
import androidx.fragment.app.FragmentManager;

import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.appbar.MaterialToolbar;

import fr.arthurbr02.wotscraper.ui.LogsFragment;
import fr.arthurbr02.wotscraper.ui.MainFragment;
import fr.arthurbr02.wotscraper.ui.SettingsFragment;
import fr.arthurbr02.wotscraper.ui.exports.ExportDetailFragment;
import fr.arthurbr02.wotscraper.ui.exports.ExportsFragment;

public class MainActivity extends AppCompatActivity {

    private static final int REQ_POST_NOTIFICATIONS = 1001;

    private static final String TAG_HOME = "tab_home";
    private static final String TAG_LOGS = "tab_logs";
    private static final String TAG_EXPORTS = "tab_exports";
    private static final String TAG_SETTINGS = "tab_settings";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        MaterialToolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        requestNotificationsPermissionIfNeeded();

        BottomNavigationView bottomNav = findViewById(R.id.bottom_nav);
        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                if (getSupportActionBar() != null) getSupportActionBar().setTitle(R.string.nav_home);
                showRootTab(TAG_HOME);
                return true;
            }
            if (id == R.id.nav_logs) {
                if (getSupportActionBar() != null) getSupportActionBar().setTitle(R.string.nav_logs);
                showRootTab(TAG_LOGS);
                return true;
            }
            if (id == R.id.nav_exports) {
                if (getSupportActionBar() != null) getSupportActionBar().setTitle(R.string.nav_exports);
                showRootTab(TAG_EXPORTS);
                return true;
            }
            if (id == R.id.nav_settings) {
                if (getSupportActionBar() != null) getSupportActionBar().setTitle(R.string.nav_settings);
                showRootTab(TAG_SETTINGS);
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
        if (getSupportActionBar() != null) getSupportActionBar().setTitle(R.string.nav_exports);
        navigateTo(ExportDetailFragment.newInstance(uri), true);
        return true;
    }

    private void showFragment(@NonNull Fragment fragment) {
        showRoot(fragment);
    }

    public void navigateTo(@NonNull Fragment fragment, boolean addToBackStack) {
        if (!addToBackStack) {
            showRoot(fragment);
            return;
        }

        FragmentManager fm = getSupportFragmentManager();
        Fragment current = findVisibleFragment(fm);

        androidx.fragment.app.FragmentTransaction tx = fm.beginTransaction();
        if (current != null) {
            tx.hide(current);
        }
        tx.add(R.id.fragment_container, fragment);
        tx.addToBackStack(null);
        tx.commit();
    }

    private void showRoot(@NonNull Fragment fragment) {
        // Non-tab root content: replace without keeping old view state.
        getSupportFragmentManager().popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);
        getSupportFragmentManager()
                .beginTransaction()
                .replace(R.id.fragment_container, fragment)
                .commit();
    }

    private void showRootTab(@NonNull String tag) {
        FragmentManager fm = getSupportFragmentManager();
        // Selecting a tab should go back to the root of that tab.
        fm.popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);

        Fragment home = fm.findFragmentByTag(TAG_HOME);
        Fragment logs = fm.findFragmentByTag(TAG_LOGS);
        Fragment exports = fm.findFragmentByTag(TAG_EXPORTS);
        Fragment settings = fm.findFragmentByTag(TAG_SETTINGS);

        Fragment target = fm.findFragmentByTag(tag);
        if (target == null) {
            if (TAG_HOME.equals(tag)) target = new MainFragment();
            else if (TAG_LOGS.equals(tag)) target = new LogsFragment();
            else if (TAG_EXPORTS.equals(tag)) target = new ExportsFragment();
            else if (TAG_SETTINGS.equals(tag)) target = new SettingsFragment();
        }

        androidx.fragment.app.FragmentTransaction tx = fm.beginTransaction();
        if (home != null) tx.hide(home);
        if (logs != null) tx.hide(logs);
        if (exports != null) tx.hide(exports);
        if (settings != null) tx.hide(settings);

        if (target != null) {
            if (target.isAdded()) {
                tx.show(target);
            } else {
                tx.add(R.id.fragment_container, target, tag);
            }
        }
        tx.commit();
    }

    @NonNull
    private static Fragment findVisibleFragment(@NonNull FragmentManager fm) {
        for (Fragment f : fm.getFragments()) {
            if (f != null && f.isAdded() && !f.isHidden() && f.getView() != null) {
                return f;
            }
        }
        // Fallback: return any added fragment.
        for (Fragment f : fm.getFragments()) {
            if (f != null && f.isAdded() && !f.isHidden()) {
                return f;
            }
        }
        return null;
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
