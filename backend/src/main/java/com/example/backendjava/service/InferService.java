package com.example.backendjava.service;

import com.example.backendjava.model.*;
import com.example.backendjava.service.model.ModelClient;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import java.io.InputStream;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.*;

@Service
public class InferService {

    private final Map<String, Map<String, Object>> SESSIONS = new HashMap<>();
    private final ObjectMapper mapper = new ObjectMapper();

    // 模型客户端（通过 Spring 注入，可配置为 Mock 或 Http 实现）
    private final ModelClient modelClient;
    // mapping.json 内容
    private Map<String, Map<String, Object>> mapping = new HashMap<>();

    public InferService(ModelClient modelClient) {
        this.modelClient = modelClient;
        // 加载 resources/mapping.json
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("mapping.json")) {
            if (is != null) {
                mapping = mapper.readValue(is, new TypeReference<Map<String, Map<String, Object>>>(){});
            }
        } catch (Exception e) {
            // 若加载失败，保持空映射
            mapping = new HashMap<>();
        }
    }

    public InferResponse handleUpload(MultipartFile file) throws IOException {
    // 解析上传的 JSON 文件，转换为 Map 结构（等价于 Python 中的 payload）
    JsonNode payload = mapper.readTree(file.getInputStream());
    Map<String, Object> patient = mapper.convertValue(payload, Map.class);

    // 生成 session_id（UUID），计算基线概率（使用迁移自 Python 的启发式函数）
    String sessionId = UUID.randomUUID().toString();
    // 调用模型客户端获取标签/分数（当前为 MockModelClient）
    com.example.backendjava.model.ModelResponse modelResp = modelClient.predict(patient, Collections.emptyList());
    double prob = modelResp.getScore();

    // 使用 mapping.json 把模型标签映射为 recommended / similar_cases
    List<MeasureItem> recs = mapLabelsToRecommendations(modelResp);
    List<SimilarCaseItem> sims = mapLabelsToSimilarCases(modelResp);

    // 会话保存在内存字典中，字段与 Python 版本一致：patient, notes, prob
    Map<String, Object> session = new HashMap<>();
    session.put("patient", patient);
    session.put("notes", new ArrayList<String>());
    session.put("prob", prob);
    SESSIONS.put(sessionId, session);

    // 返回与 Python 程序兼容的 JSON 结构，并附带模型 labels 以供前端调试展示
    return new com.example.backendjava.model.InferResponse(sessionId, round(prob), recs, sims, modelResp.getLabels());
    }

    public InferResponse handleAugment(AugmentRequest req) {
    // 从会话中取出已有数据，并把新 text 添加到 notes 列表中（与 Python 等价）
    Map<String, Object> session = SESSIONS.get(req.getSession_id());
    if (session == null) return null; // 会话不存在则返回 404
    List<String> notes = (List<String>) session.get("notes");
    notes.add(req.getText());

    // 重新计算概率：基于 patient 的基线 + notes 中每条文本的累积影响
    Map<String, Object> patient = (Map<String, Object>) session.get("patient");
        // 调用模型 clients，传入 patient 和 notes（notes 在会话里）
    ModelResponse mresp = modelClient.predict(patient, notes);
    double prob = mresp.getScore();
    // apply lightweight text-based adjustment so that augment text affects the returned probability
    double textDelta = analyzeTextAdjustment(req.getText());
    double finalProb = clamp(prob + textDelta, 0.01, 0.98);
    // debug logging to help diagnose augmentation behavior
    System.out.println("[InferService] augment text='" + req.getText() + "' modelScore=" + prob + " textDelta=" + textDelta + " finalProb=" + finalProb);
    prob = finalProb;
    session.put("prob", prob);

    List<MeasureItem> recs = mapLabelsToRecommendations(mresp);
    List<SimilarCaseItem> sims = mapLabelsToSimilarCases(mresp);

    return new com.example.backendjava.model.InferResponse(req.getSession_id(), round(prob), recs, sims, mresp.getLabels());
    }

    /**
     * Demo helper: load bundled sample_patient.json from resources and run inference.
     * This avoids multipart upload and is useful for quick local demos.
     */
    public InferResponse runDemo() {
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("static/sample_patient.json")) {
            if (is == null) return new com.example.backendjava.model.InferResponse("", 0.0, new ArrayList<>(), new ArrayList<>(), new ArrayList<>());
            JsonNode payload = mapper.readTree(is);
            Map<String, Object> patient = mapper.convertValue(payload, Map.class);

            String sessionId = UUID.randomUUID().toString();
            com.example.backendjava.model.ModelResponse modelResp = modelClient.predict(patient, Collections.emptyList());
            double prob = modelResp.getScore();

            List<MeasureItem> recs = mapLabelsToRecommendations(modelResp);
            List<SimilarCaseItem> sims = mapLabelsToSimilarCases(modelResp);

            Map<String, Object> session = new HashMap<>();
            session.put("patient", patient);
            session.put("notes", new ArrayList<String>());
            session.put("prob", prob);
            SESSIONS.put(sessionId, session);

            return new com.example.backendjava.model.InferResponse(sessionId, round(prob), recs, sims, modelResp.getLabels());
        } catch (Exception e) {
            return new com.example.backendjava.model.InferResponse("", 0.0, new ArrayList<>(), new ArrayList<>(), new ArrayList<>());
        }
    }

    /**
     * Reload mapping.json from resources (or external path if provided).
     * Returns true if reloaded successfully.
     */
    public boolean reloadMapping() {
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("mapping.json")) {
            if (is == null) return false;
            Map<String, Map<String, Object>> newMapping = mapper.readValue(is, new TypeReference<Map<String, Map<String, Object>>>(){});
            if (newMapping != null) {
                this.mapping = newMapping;
                return true;
            }
        } catch (Exception e) {
            // ignore
        }
        return false;
    }

    /**
     * Generate a minimal mapping template given a list of label ids.
     */
    public Map<String, Object> generateMappingTemplate(java.util.List<String> labels) {
        Map<String, Object> template = new HashMap<>();
        Map<String, Object> labelsNode = new HashMap<>();
        for (String l : labels) {
            Map<String, Object> entry = new HashMap<>();
            entry.put("description", "TODO: describe label '" + l + "'");
            entry.put("recommended", new ArrayList<>());
            entry.put("similar_cases", new ArrayList<>());
            labelsNode.put(l, entry);
        }
        template.put("mapping_version", "auto-generated");
        template.put("labels", labelsNode);
        return template;
    }

    // 根据模型返回的 labels 查 mapping.json，生成 recommended 列表
    private List<MeasureItem> mapLabelsToRecommendations(com.example.backendjava.model.ModelResponse mresp) {
        List<MeasureItem> out = new ArrayList<>();
        if (mresp == null || mresp.getLabels() == null) return out;
        for (LabelItem li : mresp.getLabels()) {
            String id = li.getId();
            Map<String, Object> info = mapping.get("labels") == null ? null : (Map) mapping.get("labels").get(id);
            if (info != null && info.get("recommended") instanceof List) {
                List<Map<String, String>> recs = (List<Map<String, String>>) info.get("recommended");
                for (Map<String, String> r : recs) {
                    out.add(new MeasureItem(r.get("measure"), r.get("reason")));
                }
            }
        }
        if (out.isEmpty()) {
            // 回退到原始启发式推荐
            double fallbackProb = mresp == null ? 0.25 : mresp.getScore();
            Map<String, Object> patient = Collections.emptyMap();
            out = makeRecommendations(fallbackProb, patient);
        }
        return out;
    }

    private List<SimilarCaseItem> mapLabelsToSimilarCases(com.example.backendjava.model.ModelResponse mresp) {
        List<SimilarCaseItem> out = new ArrayList<>();
        if (mresp == null || mresp.getLabels() == null) return out;
        for (LabelItem li : mresp.getLabels()) {
            String id = li.getId();
            Map<String, Object> info = mapping.get("labels") == null ? null : (Map) mapping.get("labels").get(id);
            if (info != null && info.get("similar_cases") instanceof List) {
                List<Map<String, Object>> sims = (List<Map<String, Object>>) info.get("similar_cases");
                for (Map<String, Object> s : sims) {
                    String measure = (String) s.get("measure");
                    double freq = s.get("default_frequency") instanceof Number ? ((Number) s.get("default_frequency")).doubleValue() : 0.2;
                    out.add(new SimilarCaseItem(measure, freq));
                }
            }
        }
        if (out.isEmpty()) {
            double fallbackProb = mresp == null ? 0.25 : mresp.getScore();
            out = makeSimilarCases(fallbackProb, UUID.randomUUID().toString());
        }
        return out;
    }

    private double round(double v) { return Math.round(v * 1000.0) / 1000.0; }

    // Helper utilities ported from main.py heuristics
    private double computeBaseProbability(Map<String, Object> patient) {
        // 迁移自 Python 的启发式评分函数（compute_base_probability）
        // 基本思路：根据一组生命体征和化验指标累加权重，得到一个 0.01-0.98 之间的概率值
        double score = 0.25;
        Map<String, Object> vitals = asMap(patient.get("vitals"));
        Map<String, Object> labs = asMap(patient.get("labs"));
        Map<String, Object> history = asMap(patient.get("history"));

        // 从 vitals/labs/history 中提取关键指标（与 Python 中一样的字段名）
        Double mapVal = asDouble(vitals.get("MAP"));
        Double ci = asDouble(vitals.get("CI"));
        Double pawp = asDouble(vitals.get("PAWP"));
        Double hr = asDouble(vitals.get("HR"));
        Double lact = asDouble(labs.get("lactate"));
        Double ef = asDouble(labs.get("EF"));
        Double urine = asDouble(labs.get("urine_output_6h"));
        if (urine == null) urine = asDouble(labs.get("urine_output_24h"));

        // 根据阈值累加不同的分数权重，这些数值来自原 Python 实现
        if (mapVal != null && mapVal < 65) score += 0.18;
        if (ci != null && ci < 2.2) score += 0.17;
        if (pawp != null && pawp > 18) score += 0.10;
        if (hr != null && hr > 110) score += 0.05;
        if (lact != null && lact >= 2) score += 0.12;
        if (ef != null && ef < 35) score += 0.12;
        if (urine != null) {
            try { if (urine < 0.5) score += 0.08; } catch (Exception ignored) {}
        }
        // 病史相关标志位（AMI_recent/STEMI/MI）也会增加风险分数
        if ((history.get("AMI_recent") != null && truthy(history.get("AMI_recent"))) ||
            truthy(history.get("STEMI")) || truthy(history.get("MI"))) {
            score += 0.08;
        }
        // 将分值限制在 0.01-0.98 范围内，避免极值
        return Math.max(0.01, Math.min(0.98, score));
    }

    private double analyzeTextAdjustment(String text) {
        if (text == null || text.isEmpty()) return 0.0;
    String raw = text;
    String rawLower = raw.toLowerCase();
    String noDigits = raw.replaceAll("\\d+", "");
        String[] inc = new String[]{"低血压","血压下降","心率过快","尿量减少","少尿","乳酸","皮肤冰冷","四肢冰冷","皮肤湿冷","st段抬高","心肌梗死","mi","左室功能不全","ef降低","灌注不足","意识模糊"};
        String[] dec = new String[]{"好转","稳定","无胸痛","症状缓解","灌注改善","意识清醒","血压稳定"};
    double delta = 0.0;
    StringBuilder found = new StringBuilder();
        for (String kw : inc) {
            if (raw.contains(kw) || rawLower.contains(kw) || noDigits.contains(kw)) { delta += 0.04; found.append(kw).append(","); }
        }
        for (String kw : dec) {
            if (raw.contains(kw) || rawLower.contains(kw) || noDigits.contains(kw)) { delta -= 0.03; found.append(kw).append(","); }
        }
        System.out.println("[InferService] analyzeText raw='" + raw + "' matched='" + found.toString() + "' delta=" + delta);
        return Math.max(-0.25, Math.min(0.25, delta));
    }

    private List<MeasureItem> makeRecommendations(double prob, Map<String, Object> patient) {
        List<MeasureItem> recs = new ArrayList<>();
        Map<String, Object> vitals = asMap(patient.get("vitals"));
        Map<String, Object> labs = asMap(patient.get("labs"));

        if (prob >= 0.7) {
            recs.add(new MeasureItem("紧急升压支持（去甲肾上腺素优先）","高风险休克：需快速恢复灌注压力"));
            recs.add(new MeasureItem("完善血流动力学监测（动脉置管/有创血压）","实时评估MAP与用药反应"));
            recs.add(new MeasureItem("床旁超声/心电图，评估心功能与机械并发症","明确病因指导治疗"));
            recs.add(new MeasureItem("评估机械循环支持（IABP/Impella/VA-ECMO）","药物反应差时的升级策略"));
        } else if (prob >= 0.4) {
            recs.add(new MeasureItem("升压药滴定维持MAP≥65 mmHg","灌注保护"));
            recs.add(new MeasureItem("利尿剂/血管活性药物个体化调整","容量与后负荷管理"));
            recs.add(new MeasureItem("动态监测乳酸与尿量","判断组织灌注变化"));
            recs.add(new MeasureItem("心超评估泵功能","决定是否需正性肌力药物"));
        } else {
            recs.add(new MeasureItem("密切观察+基础监测","当前风险较低"));
            recs.add(new MeasureItem("优化液体管理与镇痛/镇静","避免诱发因素"));
            recs.add(new MeasureItem("必要时复查乳酸与心超","动态评估风险"));
        }

        Object pa = vitals.get("PAWP");
        Object bnp = labs.get("BNP");
        if ((pa instanceof Number && ((Number) pa).doubleValue() > 18) || (bnp instanceof Number && ((Number) bnp).doubleValue() > 400)) {
            recs.add(new MeasureItem("利尿与后负荷降低","静脉淤血提示前负荷/后负荷过高"));
        }
        return recs.size() > 6 ? recs.subList(0,6) : recs;
    }

    private List<SimilarCaseItem> makeSimilarCases(double prob, String seed) {
        Random rng = new Random(seed.hashCode());
        double base = prob;
        List<Map.Entry<String, Double>> items = new ArrayList<>();
        items.add(new AbstractMap.SimpleEntry<>("去甲肾上腺素滴定", clamp(base + uniform(rng, -0.1, 0.1), 0.15, 0.95)));
        items.add(new AbstractMap.SimpleEntry<>("正性肌力（多巴酚丁胺/米力农）", clamp(base - 0.1 + uniform(rng, -0.1, 0.1), 0.05, 0.85)));
        items.add(new AbstractMap.SimpleEntry<>("IABP 评估/使用", clamp(base - 0.2 + uniform(rng, -0.1, 0.1), 0.05, 0.7)));
        items.add(new AbstractMap.SimpleEntry<>("VA-ECMO 转诊/启动", clamp(base - 0.3 + uniform(rng, -0.1, 0.1), 0.02, 0.5)));

        double total = items.stream().mapToDouble(Map.Entry::getValue).sum();
        if (total <= 0) total = 1.0;
        List<SimilarCaseItem> out = new ArrayList<>();
        for (Map.Entry<String, Double> e : items) {
            out.add(new SimilarCaseItem(e.getKey(), Math.round((e.getValue()/total) * 1000.0) / 1000.0));
        }
        return out;
    }

    // small helpers
    private Map<String, Object> asMap(Object o) {
        if (o instanceof Map) return (Map<String, Object>) o;
        return Collections.emptyMap();
    }
    private Double asDouble(Object o) {
        if (o == null) return null;
        if (o instanceof Number) return ((Number) o).doubleValue();
        try { return Double.parseDouble(o.toString()); } catch (Exception e) { return null; }
    }
    private boolean truthy(Object o) {
        if (o == null) return false;
        if (o instanceof Boolean) return (Boolean) o;
        return !o.toString().equalsIgnoreCase("false") && !o.toString().isEmpty();
    }
    private double clamp(double v, double lo, double hi) { return Math.max(lo, Math.min(hi, v)); }
    private double uniform(Random r, double a, double b) { return a + r.nextDouble()*(b-a); }
}

/*
    注释说明（帮助不会 Java 的同学理解）：
    - asMap / asDouble / truthy 是用于从通用 Map/JSON 数据中安全提取字段的工具函数，目的与 Python 中直接通过 dict 访问类似。
    - makeSimilarCases 使用 seed 随机数来模拟相似病例中不同措施的频率分布，最后做归一化以便前端按比例显示。
    - 整体逻辑直接对应于原 Python 的实现，方便未来替换为真实模型调用逻辑。
 */
