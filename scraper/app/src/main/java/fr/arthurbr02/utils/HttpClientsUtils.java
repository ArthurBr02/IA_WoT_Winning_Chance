package fr.arthurbr02.utils;

import org.apache.hc.client5.http.impl.DefaultHttpRequestRetryStrategy;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.util.TimeValue;

public class HttpClientsUtils {
    public static CloseableHttpClient getHttpClientWithRetry() {
        return HttpClients.custom()
                .setRetryStrategy(new DefaultHttpRequestRetryStrategy(20000, TimeValue.ofSeconds(60)))
                .build();
    }
}
