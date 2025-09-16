package com.example.backendjava.controller;

import com.example.backendjava.model.*;
import com.example.backendjava.service.InferService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api")
public class InferController {

    private final InferService inferService;

    public InferController(InferService inferService) {
        this.inferService = inferService;
    }

    /**
     * POST /api/infer/upload
     * 接收前端上传的 JSON 文件（multipart/form-data 的 file 字段），
     * 然后交给 InferService 处理（解析 JSON、计算概率、生成推荐与相似病例）。
     * 该行为与原 Python 项目中的 `infer_from_upload` 等价。
     */
    @PostMapping(value = "/infer/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<InferResponse> inferFromUpload(@RequestPart("file") MultipartFile file) throws IOException {
        if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        InferResponse resp = inferService.handleUpload(file);
        return ResponseEntity.ok(resp);
    }

    /**
     * POST /api/infer/augment
     * 接收前端发送的 JSON { session_id, text }，把 text 存入会话并重新计算概率与推荐。
     * 等价于 Python 中的 `augment_with_text`。
     */
    @PostMapping(value = "/infer/augment", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<InferResponse> augment(@Validated @RequestBody AugmentRequest req) {
        InferResponse resp = inferService.handleAugment(req);
        if (resp == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(resp);
    }

    /**
     * GET /api/health
     * 健康检查接口，前端或部署脚本可用于确认后端存活。
     */
    @GetMapping("/health")
    public ResponseEntity<?> health() {
        return ResponseEntity.ok(new HealthResponse("ok"));
    }

    /**
     * GET /api/infer/demo
     * 便捷演示端点：直接使用后端打包进来的 sample_patient.json 做一次推理，方便在没有 curl 或上传工具时验证前端展示
     */
    @GetMapping("/infer/demo")
    public ResponseEntity<InferResponse> demoInfer() {
        InferResponse resp = inferService.runDemo();
        return ResponseEntity.ok(resp);
    }

    // ---- admin endpoints for mapping management (development/demo use) ----
    @PostMapping("/admin/reload-mapping")
    public ResponseEntity<?> reloadMapping() {
        boolean ok = inferService.reloadMapping();
        if (ok) return ResponseEntity.ok(Map.of("reloaded", true));
        return ResponseEntity.status(500).body(Map.of("reloaded", false));
    }

    @PostMapping(value = "/admin/generate-mapping-template", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> generateMappingTemplate(@RequestBody Map<String, Object> body) {
        java.util.List<String> labels = (java.util.List<String>) body.getOrDefault("labels", new java.util.ArrayList<String>());
        Map<String, Object> tpl = inferService.generateMappingTemplate(labels);
        return ResponseEntity.ok(tpl);
    }
}

