package fr.arthurbr02.wotscraper.ui;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.SeekBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.google.android.material.switchmaterial.SwitchMaterial;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.util.PreferencesManager;

public class SettingsFragment extends Fragment {

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_settings, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        PreferencesManager prefs = new PreferencesManager(requireContext());

        TextView tvDelay = view.findViewById(R.id.tvRequestDelayValue);
        SeekBar seekDelay = view.findViewById(R.id.seekRequestDelay);

        TextView tvTimeout = view.findViewById(R.id.tvTimeoutValue);
        SeekBar seekTimeout = view.findViewById(R.id.seekTimeout);

        EditText etCombinedBattlesPageSize = view.findViewById(R.id.etCombinedBattlesPageSize);

        EditText etPlayers = view.findViewById(R.id.etPlayersCount);
        EditText etInitial = view.findViewById(R.id.etInitialPlayer);

        RadioGroup rgSave = view.findViewById(R.id.rgSaveFrequency);
        RadioButton rb50 = view.findViewById(R.id.rbSave50);
        RadioButton rb100 = view.findViewById(R.id.rbSave100);
        RadioButton rb200 = view.findViewById(R.id.rbSave200);

        SwitchMaterial swAuto = view.findViewById(R.id.swAutoExport);
        SwitchMaterial swComplete = view.findViewById(R.id.swNotifComplete);
        SwitchMaterial swError = view.findViewById(R.id.swNotifError);
        SwitchMaterial swPhase = view.findViewById(R.id.swNotifPhase);

        // Request delay: 100..2000ms mapped to 0..1900
        long delay = prefs.getRequestDelayMs();
        delay = Math.max(100L, Math.min(2000L, delay));
        seekDelay.setProgress((int) (delay - 100L));
        tvDelay.setText(delay + "ms");
        seekDelay.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                long v = 100L + progress;
                tvDelay.setText(v + "ms");
                if (fromUser) {
                    prefs.setRequestDelayMs(v);
                }
            }

            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { }
        });

        // Timeout: 10..60s mapped to 0..50
        int timeout = prefs.getTimeoutSeconds();
        timeout = Math.max(10, Math.min(60, timeout));
        seekTimeout.setProgress(timeout - 10);
        tvTimeout.setText(timeout + "s");
        seekTimeout.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                int v = 10 + progress;
                tvTimeout.setText(v + "s");
                if (fromUser) {
                    prefs.setTimeoutSeconds(v);
                }
            }

            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { }
        });

        etCombinedBattlesPageSize.setText(String.valueOf(prefs.getCombinedBattlesPageSize()));
        etCombinedBattlesPageSize.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                return;
            }
            try {
                int val = Integer.parseInt(etCombinedBattlesPageSize.getText().toString().trim());
                prefs.setCombinedBattlesPageSize(val);
            } catch (Exception ignored) {
            }
        });

        etPlayers.setText(String.valueOf(prefs.getMaxPlayers()));
        etPlayers.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                return;
            }
            try {
                int val = Integer.parseInt(etPlayers.getText().toString().trim());
                prefs.setMaxPlayers(Math.max(1, val));
            } catch (Exception ignored) {
            }
        });

        etInitial.setText(prefs.getInitialPlayerId());
        etInitial.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                return;
            }
            String val = etInitial.getText().toString().trim();
            if (!val.isEmpty()) {
                prefs.setInitialPlayerId(val);
            }
        });

        int saveFreq = prefs.getSaveFrequencyIterations();
        if (saveFreq == 100) {
            rb100.setChecked(true);
        } else if (saveFreq == 200) {
            rb200.setChecked(true);
        } else {
            rb50.setChecked(true);
        }

        rgSave.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.rbSave100) {
                prefs.setSaveFrequencyIterations(100);
            } else if (checkedId == R.id.rbSave200) {
                prefs.setSaveFrequencyIterations(200);
            } else {
                prefs.setSaveFrequencyIterations(50);
            }
        });

        swAuto.setChecked(prefs.isAutoExportEnabled());
        swAuto.setOnCheckedChangeListener((buttonView, isChecked) -> prefs.setAutoExportEnabled(isChecked));

        swComplete.setChecked(prefs.isCompleteNotificationEnabled());
        swComplete.setOnCheckedChangeListener((buttonView, isChecked) -> prefs.setCompleteNotificationEnabled(isChecked));

        swError.setChecked(prefs.isErrorNotificationEnabled());
        swError.setOnCheckedChangeListener((buttonView, isChecked) -> prefs.setErrorNotificationEnabled(isChecked));

        swPhase.setChecked(prefs.isPhaseNotificationEnabled());
        swPhase.setOnCheckedChangeListener((buttonView, isChecked) -> prefs.setPhaseNotificationEnabled(isChecked));
    }
}
