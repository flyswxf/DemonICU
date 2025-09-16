package com.example.backendjava;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 应用入口类
 *
 * 说明：这是 Spring Boot 应用的主类，功能与原 Python 项目中的启动逻辑等价（负责启动 HTTP 服务）。
 * 运行此类会启动后端服务。
 */
@SpringBootApplication
public class BackendJavaApplication {
    public static void main(String[] args) {
        // 启动 Spring Boot 应用
        SpringApplication.run(BackendJavaApplication.class, args);
    }
}
