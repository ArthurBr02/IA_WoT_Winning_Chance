package fr.arthurbr02.wotscraper.ui.exports;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import fr.arthurbr02.wotscraper.R;

public class JsonTreeAdapter extends RecyclerView.Adapter<JsonTreeAdapter.VH> {

    public interface OnToggleListener {
        void onToggle(@NonNull JsonTreeNode node);
    }

    @NonNull private final List<JsonTreeNode> full;
    @NonNull private final List<JsonTreeNode> visible;
    @NonNull private final Map<Integer, JsonTreeNode> byIndex;
    @NonNull private final OnToggleListener onToggleListener;

    public JsonTreeAdapter(
            @NonNull List<JsonTreeNode> full,
            @NonNull OnToggleListener onToggleListener
    ) {
        this.full = full;
        this.visible = new ArrayList<>();
        this.byIndex = new HashMap<>();
        for (JsonTreeNode n : full) {
            byIndex.put(n.index, n);
        }
        this.onToggleListener = onToggleListener;
        rebuildVisible();
        setHasStableIds(true);
    }

    @NonNull
    public List<JsonTreeNode> getFull() {
        return full;
    }

    public void rebuildVisible() {
        visible.clear();
        if (full.isEmpty()) {
            notifyDataSetChanged();
            return;
        }

        // Always include root.
        visible.add(full.get(0));
        addChildrenIfExpanded(0);
        notifyDataSetChanged();
    }

    private void addChildrenIfExpanded(int fullIndex) {
        JsonTreeNode node = full.get(fullIndex);
        if (!node.isExpandable() || !node.expanded) return;

        int start = fullIndex + 1;
        int end = node.endIndex;

        int i = start;
        while (i <= end) {
            JsonTreeNode child = full.get(i);
            visible.add(child);
            if (child.isExpandable() && child.expanded) {
                // include its subtree too
                addChildrenIfExpanded(i);
                i = child.endIndex + 1;
            } else {
                // skip collapsed subtree quickly
                if (child.isExpandable() && !child.expanded) {
                    i = child.endIndex + 1;
                } else {
                    i++;
                }
            }
        }
    }

    @Override
    public long getItemId(int position) {
        return visible.get(position).index;
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_json_node, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        JsonTreeNode node = visible.get(position);

        int padBase = holder.itemView.getResources().getDimensionPixelSize(R.dimen.json_indent_base);
        int pad = padBase * node.depth;
        holder.itemView.setPadding(pad, holder.itemView.getPaddingTop(), holder.itemView.getPaddingRight(), holder.itemView.getPaddingBottom());

        String label;
        if (node.key == null) {
            label = node.kind == JsonTreeNode.Kind.ARRAY ? "root […]" : (node.kind == JsonTreeNode.Kind.OBJECT ? "root {…}" : "root");
        } else {
            label = node.key;
        }

        holder.key.setText(label);

        if (node.kind == JsonTreeNode.Kind.VALUE) {
            holder.value.setVisibility(View.VISIBLE);
            holder.value.setText(node.valuePreview == null ? "" : node.valuePreview);
        } else {
            holder.value.setVisibility(View.VISIBLE);
            holder.value.setText(node.kind == JsonTreeNode.Kind.ARRAY ? "[…]" : "{…}");
        }

        if (node.isExpandable()) {
            holder.chevron.setVisibility(View.VISIBLE);
            holder.chevron.setRotation(node.expanded ? 90f : 0f);
            holder.itemView.setOnClickListener(v -> onToggleListener.onToggle(node));
        } else {
            holder.chevron.setVisibility(View.INVISIBLE);
            holder.itemView.setOnClickListener(null);
        }
    }

    @Override
    public int getItemCount() {
        return visible.size();
    }

    public void toggle(@NonNull JsonTreeNode node) {
        if (!node.isExpandable()) return;

        node.expanded = !node.expanded;
        rebuildVisible();
    }

    static class VH extends RecyclerView.ViewHolder {
        final ImageView chevron;
        final TextView key;
        final TextView value;

        VH(@NonNull View itemView) {
            super(itemView);
            chevron = itemView.findViewById(R.id.chevron);
            key = itemView.findViewById(R.id.key);
            value = itemView.findViewById(R.id.value);
        }
    }
}
