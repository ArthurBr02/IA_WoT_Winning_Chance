package fr.arthurbr02.wotscraper.ui.exports;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

public class JsonTreeNode {

    public enum Kind {
        OBJECT,
        ARRAY,
        VALUE
    }

    public final int index;
    public final int depth;
    @Nullable public final String key;
    @NonNull public final Kind kind;
    @Nullable public final String valuePreview;

    public boolean expanded;
    public int endIndex; // inclusive in full list

    public JsonTreeNode(
            int index,
            int depth,
            @Nullable String key,
            @NonNull Kind kind,
            @Nullable String valuePreview
    ) {
        this.index = index;
        this.depth = depth;
        this.key = key;
        this.kind = kind;
        this.valuePreview = valuePreview;
        this.expanded = false;
        this.endIndex = index;
    }

    public boolean isExpandable() {
        return kind == Kind.OBJECT || kind == Kind.ARRAY;
    }
}
