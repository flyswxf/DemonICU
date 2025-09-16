package com.example.backendjava.service.model;

import com.example.backendjava.model.LabelItem;
import com.example.backendjava.model.ModelResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.client.SimpleClientHttpRequestFactory;

import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * HttpModelClient: 可配置的 HTTP 客户端实现，支持超时、重试和简单的错误处理。
 */
@Component
public class HttpModelClient implements ModelClient {

    private static final Logger logger = LoggerFactory.getLogger(HttpModelClient.class);
    private final ObjectMapper mapper = new ObjectMapper();

    @Value("${model.url:}")
    private String modelUrl;

    @Value("${model.apiKey:}")
    private String apiKey;

    @Value("${model.timeoutSeconds:8}")
    private int timeoutSeconds;

    @Value("${model.retry:2}")
    private int retryCount;

    private RestTemplate rest;

    public HttpModelClient() {
        // rest will be lazily initialized after @Value injection
    }

    private synchronized RestTemplate getRestTemplate() {
        if (rest != null) return rest;
        SimpleClientHttpRequestFactory rf = new SimpleClientHttpRequestFactory();
        rf.setConnectTimeout(timeoutSeconds * 1000);
        rf.setReadTimeout(timeoutSeconds * 1000);
        rest = new RestTemplate(rf);
        return rest;
    }

    @Override
    public ModelResponse predict(Map<String, Object> patient, List<String> notes) {
        if (modelUrl == null || modelUrl.isEmpty()) {
            logger.debug("model.url not configured, falling back to conservative response");
            return new ModelResponse(new ArrayList<>(), 0.25);
        }

        // 构造请求体（默认协议：JSON 包装 patient + notes）
        var body = Map.of("patient", patient, "notes", notes);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (apiKey != null && !apiKey.isEmpty()) headers.set("Authorization", "Bearer " + apiKey);
        HttpEntity<Object> entity = new HttpEntity<>(body, headers);

        Exception lastEx = null;
        for (int attempt = 0; attempt <= retryCount; attempt++) {
            try {
                ResponseEntity<String> resp = getRestTemplate().postForEntity(modelUrl, entity, String.class);
                if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                    Map<String, Object> m = mapper.readValue(resp.getBody(), Map.class);
                    List<Map<String, Object>> labelsRaw = (List<Map<String, Object>>) m.getOrDefault("labels", List.of());
                    List<LabelItem> labels = new ArrayList<>();
                    double score = m.getOrDefault("score", 0.25) instanceof Number ? ((Number) m.getOrDefault("score", 0.25)).doubleValue() : 0.25;
                    for (Map<String, Object> lr : labelsRaw) {
                        String id = lr.getOrDefault("id", "").toString();
                        double s = lr.getOrDefault("score", 0.0) instanceof Number ? ((Number) lr.getOrDefault("score", 0.0)).doubleValue() : 0.0;
                        labels.add(new LabelItem(id, s));
                    }
                    return new ModelResponse(labels, score);
                } else {
                    logger.warn("Model returned non-2xx status: {} body: {}", resp.getStatusCodeValue(), resp.getBody());
                }
            } catch (Exception e) {
                lastEx = e;
                if (e instanceof SocketTimeoutException) {
                    logger.warn("Timeout when calling model (attempt {}/{}): {}", attempt + 1, retryCount + 1, e.getMessage());
                } else {
                    logger.warn("Error when calling model (attempt {}/{}): {}", attempt + 1, retryCount + 1, e.toString());
                }
                // small backoff
                try { Thread.sleep(200L); } catch (InterruptedException ignored) {}
            }
        }

        logger.error("Model call failed after {} attempts, returning conservative result. lastEx={}", retryCount + 1, lastEx == null ? "none" : lastEx.toString());
        return new ModelResponse(new ArrayList<>(), 0.25);
    }
}
