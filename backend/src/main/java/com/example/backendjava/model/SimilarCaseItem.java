package com.example.backendjava.model;

public class SimilarCaseItem {
    private String measure;
    private double frequency;

    public SimilarCaseItem() {}

    public SimilarCaseItem(String measure, double frequency) {
        this.measure = measure;
        this.frequency = frequency;
    }

    public String getMeasure() { return measure; }
    public void setMeasure(String measure) { this.measure = measure; }
    public double getFrequency() { return frequency; }
    public void setFrequency(double frequency) { this.frequency = frequency; }
}

// 说明：SimilarCaseItem 表示相似病例中某个处理措施的出现频率，
// 与 Python 中返回的 similar_cases 对象等价（measure, frequency）。
