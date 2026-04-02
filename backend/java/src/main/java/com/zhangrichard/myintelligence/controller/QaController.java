package com.zhangrichard.myintelligence.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.zhangrichard.myintelligence.service.QaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;

@RestController
@RequestMapping("/qa")
public class QaController {

    @Autowired
    private QaService qaService;

    @Autowired
    private ObjectMapper objectMapper;

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatStream(@RequestBody Map<String, Object> body) throws JsonProcessingException {
        String query = (String) body.getOrDefault("query", "");
        Object historyObj = body.get("history");
        String historyJson = null;
        if (historyObj != null) {
            historyJson = objectMapper.writeValueAsString(historyObj);
        }
        Object modeObj = body.get("mode");
        String mode = modeObj != null ? String.valueOf(modeObj) : null;
        return qaService.chatStream(query, historyJson, mode);
    }
}
