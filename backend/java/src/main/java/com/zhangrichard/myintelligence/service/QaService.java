package com.zhangrichard.myintelligence.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface QaService {

    SseEmitter chatStream(
            String query,
            String historyJson,
            String mode,
            Integer documentId,
            String aiPersonaTitle,
            String aiCustomInstruction
    );
}
