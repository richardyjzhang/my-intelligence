package com.zhangrichard.myintelligence.service;

import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Path;

public interface FileService {

    String store(MultipartFile file, String subDir);

    Resource loadAsResource(String relativePath);

    void delete(String relativePath);

    Path resolve(String relativePath);
}
