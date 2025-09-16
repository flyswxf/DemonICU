package com.example.backendjava.service.model;

import com.example.backendjava.model.ModelResponse;
import java.util.Map;

/**
 * 模型客户端接口：后续可以实现 HttpModelClient 调用真实模型服务
 */
public interface ModelClient {
    ModelResponse predict(Map<String, Object> patient, java.util.List<String> notes);
}
