package com.example.backendjava.model;

public class HealthResponse {
    private String status;
    public HealthResponse() {}
    public HealthResponse(String status) { this.status = status; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}

// 说明：简单的健康检查响应模型，仅用于 /api/health。
