# GraphCare Demonstrate 演示系统

本演示提供一个模拟 ICU 医生使用场景的前后端应用：
- 前端：拖拽/上传患者资料（JSON），展示心源性休克概率与推荐措施、相似病例处理方法频率；可在结果页继续补充自然语言信息并更新结果。
- 后端：提供两个接口：上传 JSON 推理接口、自然语言补充信息更新接口。内部使用启发式规则进行演示（非医疗用途）。

## 目录结构
```
demonstrate/
  ├── backend/
  │   ├── src/
  │   │   └── main/
  │   │       └── java/
  │   │           └── com/
  │   │               └── example/
  │   │                   └── backendjava/
  │   │                       ├── BackendJavaApplication.java      # Spring Boot 主入口
  │   │                       ├── controller/
  │   │                       │   └── InferController.java         # REST 控制器
  │   │                       ├── service/
  │   │                       │   └── InferService.java            # 业务逻辑
  │   │                       │   └── model/
  │   │                       │       ├── ModelClient.java         # 模型接口
  │   │                       │       └── MockModelClient.java     # 演示用 Mock 实现
  │   ├── src/main/resources/
  │   │   ├── application.properties      # 配置文件
  │   │   └── mapping.json                # 标签映射
  │   ├── pom.xml                         # Maven 构建文件
  └── frontend/
      ├── index.html                      # 前端入口
      ├── style.css                       # 样式
      └── app.js                          # 前端逻辑
```

## 后端启动

先到后端目录：（根据实际路径修改）
```powershell
cd C:\Users\yeyuc\Desktop\大创\demonstrate\backend
```

构建jar并运行
```powershell
mvn -DskipTests package
& java -jar .\target\backend-java-0.0.1-SNAPSHOT.jar --server.port=8000
```

后端默认地址： http://localhost:8000

启动后确认：
```powershell
Invoke-RestMethod http://localhost:8000/api/health
# 期望输出: {"status":"ok"}
```

## 前端启动

前端只是静态文件，启动方式如下：（根据实际路径修改）
```powershell
cd C:\Users\yeyuc\Desktop\大创\demonstrate\frontend
python -m http.server 5173
# 在浏览器打开: http://localhost:5173
```


## 接口说明
- POST /api/infer/upload
  - form-data: file (application/json)
  - resp: { session_id, probability: float[0,1], recommended: [{measure, reason}], similar_cases: [{measure, frequency}] }

- POST /api/infer/augment
  - json: { session_id: string, text: string }
  - resp: 同上

后端使用内存保存 session，若进程重启会丢失，适用于展示场景。

## 样例 JSON 格式（可参考）
```
{
  "id": "demo-patient-001",
  "vitals": { "MAP": 60, "HR": 120, "CI": 1.8, "PAWP": 20 },
  "labs": { "lactate": 3.2, "BNP": 450, "EF": 30 },
  "history": { "MI": true }
}
```

## 说明
- 本演示仅展示交互与可视化流程，非真实医疗决策支持系统。
- 可根据真实模型替换后端推理逻辑，保持接口契约不变即可。