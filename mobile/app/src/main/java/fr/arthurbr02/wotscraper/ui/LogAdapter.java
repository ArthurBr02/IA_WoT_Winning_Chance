package fr.arthurbr02.wotscraper.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.color.MaterialColors;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.scraper.LogLevel;

public class LogAdapter extends RecyclerView.Adapter<LogAdapter.VH> {

    private final List<LogEntry> items = new ArrayList<>();
    private final SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss", Locale.getDefault());

    public void submit(@NonNull List<LogEntry> newItems) {
        items.clear();
        items.addAll(newItems);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_log, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        LogEntry entry = items.get(position);
        holder.bind(entry);
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    static final class VH extends RecyclerView.ViewHolder {
        private final TextView text;

        VH(@NonNull View itemView) {
            super(itemView);
            text = itemView.findViewById(R.id.tv_log);
        }

        void bind(@NonNull LogEntry entry) {
            Context context = itemView.getContext();

            String time = new SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(new Date(entry.timestampMs));
            String line = time + " [" + entry.level.name() + "] " + entry.message;
            text.setText(line);

            int colorAttr;
            if (entry.level == LogLevel.ERROR) {
                colorAttr = com.google.android.material.R.attr.colorError;
            } else if (entry.level == LogLevel.WARN) {
                colorAttr = com.google.android.material.R.attr.colorSecondary;
            } else if (entry.level == LogLevel.DEBUG) {
                colorAttr = com.google.android.material.R.attr.colorTertiary;
            } else {
                colorAttr = com.google.android.material.R.attr.colorOnSurface;
            }
            text.setTextColor(MaterialColors.getColor(text, colorAttr));
        }
    }
}
