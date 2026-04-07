package com.zhangrichard.myintelligence.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.zhangrichard.myintelligence.service.QaService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;

@Service
public class QaServiceImpl implements QaService {

    private static final Logger log = LoggerFactory.getLogger(QaServiceImpl.class);

    @Value("${app.python.base-url:http://localhost:8081}")
    private String pythonBaseUrl;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public SseEmitter chatStream(
            String query,
            String historyJson,
            String mode,
            Integer documentId,
            String aiPersonaTitle,
            String aiCustomInstruction
    ) {
        SseEmitter emitter = new SseEmitter(300_000L);

        new Thread(() -> {
            HttpURLConnection conn = null;
            try {
                ObjectNode root = objectMapper.createObjectNode();
                root.put("query", query);
                if (historyJson != null && !historyJson.isBlank()) {
                    root.set("history", objectMapper.readTree(historyJson));
                }
                if (mode != null && !mode.isBlank()) {
                    root.put("mode", mode);
                }
                if (documentId != null) {
                    root.put("documentId", documentId);
                }
                if (aiPersonaTitle != null && !aiPersonaTitle.isBlank()) {
                    root.put("aiPersonaTitle", aiPersonaTitle.trim());
                }
                if (aiCustomInstruction != null && !aiCustomInstruction.isBlank()) {
                    root.put("aiCustomInstruction", aiCustomInstruction.trim());
                }
                String requestBody = objectMapper.writeValueAsString(root);

                URI uri = URI.create(pythonBaseUrl + "/chat/stream");
                conn = (HttpURLConnection) uri.toURL().openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                conn.setRequestProperty("Accept", "text/event-stream");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10_000);
                conn.setReadTimeout(300_000);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(requestBody.getBytes(StandardCharsets.UTF_8));
                }

                int responseCode = conn.getResponseCode();
                log.info("Python 响应码: {}", responseCode);
                if (responseCode != 200) {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data("{\"message\":\"Python 服务返回 " + responseCode + "\"}", MediaType.APPLICATION_JSON));
                    emitter.complete();
                    return;
                }

                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String currentEvent = null;
                    StringBuilder dataBuffer = new StringBuilder();

                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("event: ")) {
                            currentEvent = line.substring(7).trim();
                        } else if (line.startsWith("data: ")) {
                            dataBuffer.append(line.substring(6));
                        } else if (line.isEmpty() && currentEvent != null) {
                            log.debug("转发 SSE: event={}, data={}", currentEvent, dataBuffer);
                            emitter.send(SseEmitter.event()
                                    .name(currentEvent)
                                    .data(dataBuffer.toString(), MediaType.APPLICATION_JSON));
                            currentEvent = null;
                            dataBuffer.setLength(0);
                        }
                    }
                }

                log.info("Python SSE 流读取完毕");
                emitter.complete();
            } catch (Exception e) {
                log.error("转发 chat stream 异常", e);
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data("{\"message\":\"" + e.getMessage() + "\"}", MediaType.APPLICATION_JSON));
                    emitter.complete();
                } catch (Exception ignored) {
                }
            } finally {
                if (conn != null) {
                    conn.disconnect();
                }
            }
        }).start();

        return emitter;
    }
}
