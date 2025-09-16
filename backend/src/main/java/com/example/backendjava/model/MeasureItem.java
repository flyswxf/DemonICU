package com.example.backendjava.model;

public class MeasureItem {
    private String measure;
    private String reason;

    public MeasureItem() {}

    public MeasureItem(String measure, String reason) {
        this.measure = measure;
        this.reason = reason;
    }

    public String getMeasure() { return measure; }
    public void setMeasure(String measure) { this.measure = measure; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
}

// 说明：MeasureItem 表示一条推荐措施，与 Python 中的 MeasureItem 等价，
// 包含 measure（措施名称）和 reason（推荐理由）。
