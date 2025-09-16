package com.example.backendjava.model;

import java.util.List;

public class InferResponse {
    private String session_id;
    private double probability;
    private List<MeasureItem> recommended;
    private List<SimilarCaseItem> similar_cases;
    private List<com.example.backendjava.model.LabelItem> labels;

    public InferResponse() {}

    public InferResponse(String session_id, double probability, List<MeasureItem> recommended, List<SimilarCaseItem> similar_cases) {
        this.session_id = session_id;
        this.probability = probability;
        this.recommended = recommended;
        this.similar_cases = similar_cases;
        this.labels = null;
    }

    public InferResponse(String session_id, double probability, List<MeasureItem> recommended, List<SimilarCaseItem> similar_cases, List<com.example.backendjava.model.LabelItem> labels) {
        this.session_id = session_id;
        this.probability = probability;
        this.recommended = recommended;
        this.similar_cases = similar_cases;
        this.labels = labels;
    }

    public String getSession_id() { return session_id; }
    public void setSession_id(String session_id) { this.session_id = session_id; }
    public double getProbability() { return probability; }
    public void setProbability(double probability) { this.probability = probability; }
    public List<MeasureItem> getRecommended() { return recommended; }
    public void setRecommended(List<MeasureItem> recommended) { this.recommended = recommended; }
    public List<SimilarCaseItem> getSimilar_cases() { return similar_cases; }
    public void setSimilar_cases(List<SimilarCaseItem> similar_cases) { this.similar_cases = similar_cases; }
    public List<com.example.backendjava.model.LabelItem> getLabels() { return labels; }
    public void setLabels(List<com.example.backendjava.model.LabelItem> labels) { this.labels = labels; }
}

// 说明：InferResponse 为后端对前端的响应格式，包含：
// - session_id: 会话标识
// - probability: 心源性休克概率（0-1）
// - recommended: 推荐的诊疗措施数组
// - similar_cases: 相似病例处理频率数组
// 该结构与 Python 的响应模型对应，方便前端无侵入替换。
