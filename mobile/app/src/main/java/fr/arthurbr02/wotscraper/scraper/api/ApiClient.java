package fr.arthurbr02.wotscraper.scraper.api;

import androidx.annotation.NonNull;

import com.google.gson.Gson;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.Reader;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

import okhttp3.Interceptor;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class ApiClient {

    public interface DelayProvider {
        long getDelayMs();
    }

    public interface TimeoutProvider {
        int getTimeoutSeconds();
    }

    private final OkHttpClient httpClient;
    private final Gson gson;

    public ApiClient(@NonNull OkHttpClient httpClient, @NonNull Gson gson) {
        this.httpClient = httpClient;
        this.gson = gson;
    }

    @NonNull
    public static ApiClient createDefault() {
        return createDefault(() -> 0L, () -> 30);
    }

    @NonNull
    public static ApiClient createDefault(@NonNull DelayProvider delayProvider) {
        return createDefault(delayProvider, () -> 30);
    }

    @NonNull
    public static ApiClient createDefault(@NonNull DelayProvider delayProvider, @NonNull TimeoutProvider timeoutProvider) {
        int timeoutSeconds = Math.max(5, timeoutProvider.getTimeoutSeconds());
        OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .readTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .writeTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .addInterceptor(new ThrottlingInterceptor(delayProvider))
                .addInterceptor(new RetryInterceptor())
                .build();
        return new ApiClient(client, new Gson());
    }

    @NonNull
    public <T> T getJson(@NonNull String url, @NonNull Class<T> clazz) throws IOException {
        Request request = new Request.Builder()
                .url(url)
                .header("User-Agent", "wotscraper-mobile")
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("HTTP " + response.code() + " for " + url);
            }
            if (response.body() == null) {
                throw new IOException("Empty body for " + url);
            }

            // Parse in streaming mode to avoid loading the whole response in memory.
            try (Reader reader = response.body().charStream()) {
                T parsed = gson.fromJson(reader, clazz);
                if (parsed == null) {
                    throw new IOException("Failed to parse JSON for " + url);
                }
                return parsed;
            }
        }
    }

    private static final class ThrottlingInterceptor implements Interceptor {
        private final DelayProvider delayProvider;

        private final Object lock = new Object();
        private long lastRequestStartMs = 0L;

        private ThrottlingInterceptor(@NonNull DelayProvider delayProvider) {
            this.delayProvider = delayProvider;
        }

        @NonNull
        @Override
        public Response intercept(@NonNull Chain chain) throws IOException {
            long delayMs = Math.max(0L, delayProvider.getDelayMs());
            if (delayMs > 0L) {
                synchronized (lock) {
                    long now = System.currentTimeMillis();
                    long elapsed = now - lastRequestStartMs;
                    long wait = delayMs - elapsed;
                    if (wait > 0L) {
                        sleepInterruptibly(wait);
                    }
                    lastRequestStartMs = System.currentTimeMillis();
                }
            }
            return chain.proceed(chain.request());
        }
    }

    private static final class RetryInterceptor implements Interceptor {
        private static final int MAX_RETRIES = 5;
        private static final long BASE_DELAY_MS = 500L;
        private static final long MAX_DELAY_MS = 10_000L;

        @NonNull
        @Override
        public Response intercept(@NonNull Chain chain) throws IOException {
            Request request = chain.request();

            // Only retry idempotent GETs.
            if (!"GET".equalsIgnoreCase(request.method())) {
                return chain.proceed(request);
            }

            IOException lastException = null;

            for (int attempt = 0; attempt <= MAX_RETRIES; attempt++) {
                try {
                    Response response = chain.proceed(request);
                    if (!shouldRetry(response)) {
                        return response;
                    }

                    long wait = computeWaitMs(attempt, response);
                    response.close();
                    sleepInterruptibly(wait);
                } catch (IOException e) {
                    lastException = e;
                    if (attempt >= MAX_RETRIES) {
                        break;
                    }
                    sleepInterruptibly(computeWaitMs(attempt, null));
                }
            }

            if (lastException != null) {
                throw lastException;
            }
            throw new IOException("Retry attempts exhausted");
        }

        private static boolean shouldRetry(@NonNull Response response) {
            int code = response.code();
            return code == 429 || code == 500 || code == 502 || code == 503 || code == 504;
        }

        private static long computeWaitMs(int attempt, Response response) {
            // Respect Retry-After when present for 429.
            if (response != null && response.code() == 429) {
                String retryAfter = response.header("Retry-After");
                if (retryAfter != null) {
                    try {
                        long seconds = Long.parseLong(retryAfter.trim());
                        return clamp(seconds * 1000L);
                    } catch (NumberFormatException ignored) {
                        // ignore
                    }
                }
            }

            // Exponential backoff with simple jitter.
            long exp = BASE_DELAY_MS * (1L << Math.min(6, Math.max(0, attempt)));
            long jitter = (long) (Math.random() * 250L);
            return clamp(exp + jitter);
        }

        private static long clamp(long ms) {
            return Math.max(0L, Math.min(MAX_DELAY_MS, ms));
        }
    }

    private static void sleepInterruptibly(long ms) throws IOException {
        if (ms <= 0L) {
            return;
        }
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            InterruptedIOException ioe = new InterruptedIOException("Interrupted while waiting");
            ioe.initCause(e);
            throw ioe;
        }
    }
}
