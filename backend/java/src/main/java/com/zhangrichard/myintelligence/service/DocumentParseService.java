package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.Document;

public interface DocumentParseService {

    void submitParseTask(Document document);

    void startStatusListener();
}
