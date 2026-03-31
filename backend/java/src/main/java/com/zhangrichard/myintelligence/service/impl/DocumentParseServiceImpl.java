package com.zhangrichard.myintelligence.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.zhangrichard.myintelligence.entity.Document;
import com.zhangrichard.myintelligence.repository.DocumentRepository;
import com.zhangrichard.myintelligence.service.DocumentParseService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class DocumentParseServiceImpl implements DocumentParseService {

    private static final Logger log = LoggerFactory.getLogger(DocumentParseServiceImpl.class);

    private static final String PARSE_QUEUE = "doc:parse:queue";
    private static final String DELETE_QUEUE = "doc:delete:queue";
    private static final String STATUS_QUEUE = "doc:status:queue";

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private DocumentRepository documentRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public void submitParseTask(Document document) {
        try {
            Map<String, Object> task = new HashMap<>();
            task.put("documentId", document.getId());
            task.put("filePath", document.getFilePath());
            task.put("fileName", document.getFileName());
            task.put("title", document.getTitle());

            List<String> tagNames = document.getTags().stream()
                    .map(tag -> tag.getName())
                    .toList();
            task.put("tags", tagNames);

            String json = objectMapper.writeValueAsString(task);
            redisTemplate.opsForList().leftPush(PARSE_QUEUE, json);
            log.info("已提交文档解析任务: documentId={}, title={}", document.getId(), document.getTitle());
        } catch (Exception e) {
            log.error("提交文档解析任务失败: documentId={}", document.getId(), e);
        }
    }

    @Override
    public void submitDeleteTask(Long documentId) {
        try {
            Map<String, Object> task = new HashMap<>();
            task.put("documentId", documentId);

            String json = objectMapper.writeValueAsString(task);
            redisTemplate.opsForList().leftPush(DELETE_QUEUE, json);
            log.info("已提交文档删除任务: documentId={}", documentId);
        } catch (Exception e) {
            log.error("提交文档删除任务失败: documentId={}", documentId, e);
        }
    }

    @PostConstruct
    @Override
    public void startStatusListener() {
        Thread listener = new Thread(() -> {
            log.info("文档状态监听线程启动，监听队列: {}", STATUS_QUEUE);
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    String json = redisTemplate.opsForList().rightPop(STATUS_QUEUE, Duration.ofSeconds(5));
                    if (json == null) {
                        continue;
                    }
                    processStatusUpdate(json);
                } catch (Exception e) {
                    log.error("监听状态队列异常", e);
                    try {
                        Thread.sleep(5000);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        }, "doc-status-listener");
        listener.setDaemon(true);
        listener.start();
    }

    private void processStatusUpdate(String json) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMsg = objectMapper.readValue(json, Map.class);

            Long documentId = ((Number) statusMsg.get("documentId")).longValue();
            Integer status = ((Number) statusMsg.get("status")).intValue();
            String message = (String) statusMsg.get("message");

            documentRepository.findById(documentId).ifPresentOrElse(document -> {
                document.setStatus(status);
                documentRepository.save(document);
                log.info("文档状态已更新: documentId={}, status={}, message={}", documentId, status, message);
            }, () -> {
                log.warn("文档不存在，忽略状态更新: documentId={}", documentId);
            });
        } catch (Exception e) {
            log.error("处理状态更新失败: {}", json, e);
        }
    }
}
