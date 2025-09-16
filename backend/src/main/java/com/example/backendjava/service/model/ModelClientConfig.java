package com.example.backendjava.service.model;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.Nullable;

/**
 * 根据 application.properties 中的 model.client 配置选择 Mock 或 Http 实现。
 * - model.client=mock (默认)
 * - model.client=http
 */
@Configuration
public class ModelClientConfig {

    @Value("${model.client:mock}")
    private String clientType;

    @Bean
    public ModelClient modelClient(@Nullable HttpModelClient httpClient) {
        if ("http".equalsIgnoreCase(clientType)) {
            if (httpClient != null) return httpClient;
            // if http selected but bean not available, fall back to mock
        }
        return new MockModelClient();
    }
}
