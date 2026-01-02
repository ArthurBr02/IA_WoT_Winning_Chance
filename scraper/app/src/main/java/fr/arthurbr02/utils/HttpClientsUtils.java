package fr.arthurbr02.utils;

import org.apache.hc.client5.http.impl.DefaultHttpRequestRetryStrategy;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ClassicHttpResponse;
import org.apache.hc.core5.http.Header;
import org.apache.hc.core5.util.TimeValue;

import java.time.Duration;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Locale;

public class HttpClientsUtils {
    private static final long DEFAULT_RETRY_AFTER_MS = Duration.ofSeconds(60).toMillis();
    private static final long MAX_RETRY_AFTER_MS = Duration.ofMinutes(5).toMillis();

    public static CloseableHttpClient getHttpClientWithRetry() {
        return HttpClients.custom()
                .setRetryStrategy(new DefaultHttpRequestRetryStrategy(20000, TimeValue.ofSeconds(60)))
                .build();
    }

    /**
     * Computes how long to wait before retrying after a 429 response.
     * Prefers the Retry-After header when present.
     */
    public static long computeRetryAfterMs(ClassicHttpResponse response, int attempt) {
        long retryAfterMs = parseRetryAfterHeaderMs(response);

        // If header is missing/unparseable, use exponential backoff capped to MAX_RETRY_AFTER_MS.
        if (retryAfterMs <= 0) {
            // 1m, 2m, 4m, ... capped.
            long backoff = DEFAULT_RETRY_AFTER_MS * (1L << Math.min(Math.max(attempt - 1, 0), 8));
            retryAfterMs = Math.min(backoff, MAX_RETRY_AFTER_MS);
        }

        return Math.min(Math.max(retryAfterMs, 0), MAX_RETRY_AFTER_MS);
    }

    private static long parseRetryAfterHeaderMs(ClassicHttpResponse response) {
        if (response == null) {
            return -1;
        }

        Header header = response.getFirstHeader("Retry-After");
        if (header == null) {
            return -1;
        }

        String value = header.getValue();
        if (value == null) {
            return -1;
        }

        String trimmed = value.trim();
        if (trimmed.isEmpty()) {
            return -1;
        }

        // Most common: delta-seconds.
        try {
            long seconds = Long.parseLong(trimmed);
            return Duration.ofSeconds(Math.max(seconds, 0)).toMillis();
        } catch (NumberFormatException ignored) {
            // Fall through to HTTP-date parsing.
        }

        // RFC 7231: Retry-After can be an HTTP-date.
        try {
            ZonedDateTime date = ZonedDateTime.parse(trimmed, DateTimeFormatter.RFC_1123_DATE_TIME.withLocale(Locale.US));
            long ms = Duration.between(ZonedDateTime.now(date.getZone()), date).toMillis();
            return Math.max(ms, 0);
        } catch (DateTimeParseException ignored) {
            return -1;
        }
    }
}
