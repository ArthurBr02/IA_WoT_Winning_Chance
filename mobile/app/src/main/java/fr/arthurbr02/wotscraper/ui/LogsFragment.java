package fr.arthurbr02.wotscraper.ui;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import fr.arthurbr02.wotscraper.R;

public class LogsFragment extends Fragment {

    private LogAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_logs, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        RecyclerView recycler = view.findViewById(R.id.recycler_logs);
        recycler.setLayoutManager(new LinearLayoutManager(requireContext()));

        adapter = new LogAdapter();
        recycler.setAdapter(adapter);

        ScraperViewModel vm = new ViewModelProvider(requireActivity()).get(ScraperViewModel.class);
        vm.getLogs().observe(getViewLifecycleOwner(), logs -> {
            if (logs == null) {
                return;
            }
            adapter.submit(logs);
            if (!logs.isEmpty()) {
                recycler.scrollToPosition(logs.size() - 1);
            }
        });
    }
}
