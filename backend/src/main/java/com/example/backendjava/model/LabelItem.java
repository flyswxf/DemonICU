package com.example.backendjava.model;

/**
 * 表示模型返回的单个标签（label）及其置信度。
 *
 * 字段说明：
 * - id: 标签标识符（例如 "cardiogenic_shock_high"），用于在 mapping.json 中查找推荐项。
 * - score: 该标签的置信度或评分（范围通常在 0.0 到 1.0 之间）。
 */
public class LabelItem {
    /** 标签 id，用于映射到前端展示或推荐策略 */
    private String id;

    /** 标签的置信度/分数（double） */
    private double score;

    // 无参构造器，供反序列化框架（如 Jackson）使用
    public LabelItem() {}

    // 便捷构造器，方便在代码中快速创建 LabelItem
    public LabelItem(String id, double score) { this.id = id; this.score = score; }

    // Getter/Setter 方法用于序列化与访问字段
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public double getScore() { return score; }
    public void setScore(double score) { this.score = score; }
}
