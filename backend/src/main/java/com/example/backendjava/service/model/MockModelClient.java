package com.example.backendjava.service.model;

import com.example.backendjava.model.LabelItem;
import com.example.backendjava.model.ModelResponse;
import java.util.*;

/**
 * Mock 实现：根据简单规则返回 label（用于本地演示）
 */
public class MockModelClient implements ModelClient {
    @Override
    public ModelResponse predict(Map<String, Object> patient, java.util.List<String> notes) {
        // 简单规则：基于某些字段判断高/中/低风险标签
        double score = 0.25;
        Map<String, Object> vitals = patient.getOrDefault("vitals", Collections.emptyMap()) instanceof Map ? (Map)patient.get("vitals") : Collections.emptyMap();
        Map<String, Object> labs = patient.getOrDefault("labs", Collections.emptyMap()) instanceof Map ? (Map)patient.get("labs") : Collections.emptyMap();
        Double mapVal = toDouble(vitals.get("MAP"));
        Double lact = toDouble(labs.get("lactate"));
        if (mapVal != null && mapVal < 65) score += 0.3;
        if (lact != null && lact >= 2) score += 0.2;
        // consider notes (natural language augmentations) to modestly adjust score
        if (notes != null && !notes.isEmpty()) {
            String joined = String.join(" ", notes).toLowerCase();
            // keywords in Chinese and English fallback
            String[] inc = new String[]{"低血压","血压下降","乳酸","lactate","尿量减少","少尿","皮肤冰冷","心率过快","心肌梗死"};
            for (String kw : inc) {
                if (joined.contains(kw)) {
                    score += 0.04; // small increment per matched keyword
                }
            }
        }
        String label = score >= 0.7 ? "cardiogenic_shock_high" : (score >= 0.4 ? "cardiogenic_shock_moderate" : "cardiogenic_shock_low");
        return new ModelResponse(Arrays.asList(new LabelItem(label, score)), score);
    }

    private Double toDouble(Object o) {
        if (o == null) return null;
        if (o instanceof Number) return ((Number)o).doubleValue();
        try { return Double.parseDouble(o.toString()); } catch (Exception e) { return null; }
    }
}
