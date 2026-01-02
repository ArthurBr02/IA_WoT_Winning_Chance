package fr.arthurbr02.wotscraper.ui.exports;

import android.content.Context;
import android.util.JsonReader;

import androidx.annotation.Nullable;

import androidx.annotation.NonNull;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

import android.net.Uri;

public class JsonTreeParser {

    private static class Frame {
        @NonNull final JsonTreeNode.Kind kind;
        final int nodeIndex;
        int arrayIndex;

        Frame(@NonNull JsonTreeNode.Kind kind, int nodeIndex) {
            this.kind = kind;
            this.nodeIndex = nodeIndex;
            this.arrayIndex = 0;
        }
    }

    @NonNull
    public List<JsonTreeNode> parse(@NonNull File file) throws IOException {
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(file))) {
            return parseStream(bis);
        }
    }

    @NonNull
    public List<JsonTreeNode> parse(@NonNull Context context, @NonNull Uri uri) throws IOException {
        InputStream in = context.getContentResolver().openInputStream(uri);
        if (in == null) {
            throw new IOException("Unable to open stream for uri: " + uri);
        }
        try (BufferedInputStream bis = new BufferedInputStream(in)) {
            return parseStream(bis);
        }
    }

    @NonNull
    private List<JsonTreeNode> parseStream(@NonNull InputStream inputStream) throws IOException {
        List<JsonTreeNode> nodes = new ArrayList<>();
        Deque<Frame> stack = new ArrayDeque<>();

        try (JsonReader reader = new JsonReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
            reader.setLenient(true);

            switch (reader.peek()) {
                case BEGIN_OBJECT: {
                    int rootIndex = addNode(nodes, 0, null, JsonTreeNode.Kind.OBJECT, "{…}");
                    nodes.get(rootIndex).expanded = true;
                    stack.push(new Frame(JsonTreeNode.Kind.OBJECT, rootIndex));
                    reader.beginObject();
                    readObject(reader, nodes, stack, 1);
                    reader.endObject();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                case BEGIN_ARRAY: {
                    int rootIndex = addNode(nodes, 0, null, JsonTreeNode.Kind.ARRAY, "[…]");
                    nodes.get(rootIndex).expanded = true;
                    stack.push(new Frame(JsonTreeNode.Kind.ARRAY, rootIndex));
                    reader.beginArray();
                    readArray(reader, nodes, stack, 1);
                    reader.endArray();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                default: {
                    // Single primitive JSON
                    addNode(nodes, 0, null, JsonTreeNode.Kind.VALUE, previewPrimitive(reader));
                    break;
                }
            }
        }

        while (!stack.isEmpty()) {
            closeContainer(nodes, stack.pop());
        }

        return nodes;
    }

    private void readObject(
            @NonNull JsonReader reader,
            @NonNull List<JsonTreeNode> nodes,
            @NonNull Deque<Frame> stack,
            int depth
    ) throws IOException {
        while (reader.hasNext()) {
            String name = reader.nextName();
            switch (reader.peek()) {
                case BEGIN_OBJECT: {
                    int idx = addNode(nodes, depth, name, JsonTreeNode.Kind.OBJECT, "{…}");
                    stack.push(new Frame(JsonTreeNode.Kind.OBJECT, idx));
                    reader.beginObject();
                    readObject(reader, nodes, stack, depth + 1);
                    reader.endObject();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                case BEGIN_ARRAY: {
                    int idx = addNode(nodes, depth, name, JsonTreeNode.Kind.ARRAY, "[…]");
                    stack.push(new Frame(JsonTreeNode.Kind.ARRAY, idx));
                    reader.beginArray();
                    readArray(reader, nodes, stack, depth + 1);
                    reader.endArray();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                default: {
                    String value = previewPrimitive(reader);
                    addNode(nodes, depth, name, JsonTreeNode.Kind.VALUE, value);
                    break;
                }
            }
        }
    }

    private void readArray(
            @NonNull JsonReader reader,
            @NonNull List<JsonTreeNode> nodes,
            @NonNull Deque<Frame> stack,
            int depth
    ) throws IOException {
        Frame current = stack.peek();
        if (current == null) return;

        while (reader.hasNext()) {
            String key = "[" + current.arrayIndex + "]";
            switch (reader.peek()) {
                case BEGIN_OBJECT: {
                    int idx = addNode(nodes, depth, key, JsonTreeNode.Kind.OBJECT, "{…}");
                    current.arrayIndex++;
                    stack.push(new Frame(JsonTreeNode.Kind.OBJECT, idx));
                    reader.beginObject();
                    readObject(reader, nodes, stack, depth + 1);
                    reader.endObject();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                case BEGIN_ARRAY: {
                    int idx = addNode(nodes, depth, key, JsonTreeNode.Kind.ARRAY, "[…]");
                    current.arrayIndex++;
                    stack.push(new Frame(JsonTreeNode.Kind.ARRAY, idx));
                    reader.beginArray();
                    readArray(reader, nodes, stack, depth + 1);
                    reader.endArray();
                    closeContainer(nodes, stack.pop());
                    break;
                }
                default: {
                    String value = previewPrimitive(reader);
                    addNode(nodes, depth, key, JsonTreeNode.Kind.VALUE, value);
                    current.arrayIndex++;
                    break;
                }
            }
        }
    }

    private static int addNode(
            @NonNull List<JsonTreeNode> nodes,
            int depth,
            String key,
            @NonNull JsonTreeNode.Kind kind,
            String valuePreview
    ) {
        int index = nodes.size();
        nodes.add(new JsonTreeNode(index, depth, key, kind, valuePreview));
        return index;
    }

    private static void closeContainer(@NonNull List<JsonTreeNode> nodes, @NonNull Frame frame) {
        if (frame.nodeIndex >= 0 && frame.nodeIndex < nodes.size()) {
            nodes.get(frame.nodeIndex).endIndex = nodes.size() - 1;
        }
    }

    @NonNull
    private static String previewPrimitive(@NonNull JsonReader reader) throws IOException {
        switch (reader.peek()) {
            case STRING:
                String s = reader.nextString();
                return quoteAndTruncate(s);
            case NUMBER:
                return reader.nextString();
            case BOOLEAN:
                return String.valueOf(reader.nextBoolean());
            case NULL:
                reader.nextNull();
                return "null";
            default:
                // Fallback: try to skip.
                reader.skipValue();
                return "";
        }
    }

    @NonNull
    private static String quoteAndTruncate(@NonNull String s) {
        int max = 120;
        String trimmed = s.length() > max ? (s.substring(0, max) + "…") : s;
        return "\"" + trimmed.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "\"";
    }
}
