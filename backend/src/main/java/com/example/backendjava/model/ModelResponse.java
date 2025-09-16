package com.example.backendjava.model;

import java.util.List;

/**
 * 包装模型推理返回值的简单数据结构。
 *
 * 字段说明：
 * - labels: 模型返回的标签列表（LabelItem），每个标签包含 id 与 score。
 * - score: 模型给出的整体概率/分数（可选），若模型不返回则上层可使用 labels 的第一个 score 或本地启发式回退。
 */
public class ModelResponse {
    /** 模型返回的标签数组，用于后续的映射与展示 */
    private List<LabelItem> labels;

    /** 模型的整体得分（可选） */
    private double score;

    // 无参构造器，供序列化框架使用
    public ModelResponse() {}

    // 便捷构造器，用于在代码中创建测试/返回值
    public ModelResponse(List<LabelItem> labels, double score) { this.labels = labels; this.score = score; }

    // Getter/Setter
    public List<LabelItem> getLabels() { return labels; }
    public void setLabels(List<LabelItem> labels) { this.labels = labels; }
    public double getScore() { return score; }
    public void setScore(double score) { this.score = score; }
}
