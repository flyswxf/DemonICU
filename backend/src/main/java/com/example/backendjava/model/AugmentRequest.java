package com.example.backendjava.model;

public class AugmentRequest {
    private String session_id;
    private String text;

    public AugmentRequest() {}

    public String getSession_id() { return session_id; }
    public void setSession_id(String session_id) { this.session_id = session_id; }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
}

// 说明：AugmentRequest 表示前端发送的补充信息请求体，包含 session_id 与 text，
// 与 Python 中的 AugmentRequest 等价。
