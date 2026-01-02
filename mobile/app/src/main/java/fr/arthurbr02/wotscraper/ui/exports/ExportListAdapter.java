package fr.arthurbr02.wotscraper.ui.exports;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import fr.arthurbr02.wotscraper.R;
import fr.arthurbr02.wotscraper.export.ExportFileItem;

public class ExportListAdapter extends RecyclerView.Adapter<ExportListAdapter.VH> {

    public interface Listener {
        void onOpenDetail(@NonNull ExportFileItem item);
        void onShare(@NonNull ExportFileItem item);
        void onOpenExternal(@NonNull ExportFileItem item);
        void onDelete(@NonNull ExportFileItem item);
    }

    @NonNull private final List<ExportFileItem> items = new ArrayList<>();
    @NonNull private final Listener listener;
    @NonNull private final DateFormat dateFormat = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.MEDIUM);

    public ExportListAdapter(@NonNull Listener listener) {
        this.listener = listener;
        setHasStableIds(true);
    }

    public void setItems(@NonNull List<ExportFileItem> newItems) {
        items.clear();
        items.addAll(newItems);
        notifyDataSetChanged();
    }

    @Override
    public long getItemId(int position) {
        return items.get(position).stableId();
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_export_file, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        ExportFileItem item = items.get(position);
        holder.title.setText(item.name);
        holder.subtitle.setText(dateFormat.format(new Date(item.lastModifiedMs)) + " • " + humanSize(item.sizeBytes));

        holder.itemView.setOnClickListener(v -> listener.onOpenDetail(item));
        holder.btnShare.setOnClickListener(v -> listener.onShare(item));
        holder.btnOpen.setOnClickListener(v -> listener.onOpenDetail(item));
        holder.btnDelete.setOnClickListener(v -> listener.onDelete(item));
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        final TextView title;
        final TextView subtitle;
        final Button btnShare;
        final Button btnOpen;
        final Button btnDelete;

        VH(@NonNull View itemView) {
            super(itemView);
            title = itemView.findViewById(R.id.title);
            subtitle = itemView.findViewById(R.id.subtitle);
            btnShare = itemView.findViewById(R.id.btn_share);
            btnOpen = itemView.findViewById(R.id.btn_open);
            btnDelete = itemView.findViewById(R.id.btn_delete);
        }
    }

    @NonNull
    private static String humanSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        double kb = bytes / 1024.0;
        if (kb < 1024) return String.format("%.1f KB", kb);
        double mb = kb / 1024.0;
        if (mb < 1024) return String.format("%.1f MB", mb);
        double gb = mb / 1024.0;
        return String.format("%.1f GB", gb);
    }
}
