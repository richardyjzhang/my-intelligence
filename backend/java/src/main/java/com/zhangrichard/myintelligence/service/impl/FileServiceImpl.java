package com.zhangrichard.myintelligence.service.impl;

import com.zhangrichard.myintelligence.service.FileService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

@Service
public class FileServiceImpl implements FileService {

    @Value("${app.file.root-path}")
    private String rootPath;

    @Override
    public String store(MultipartFile file, String subDir) {
        String originalFilename = StringUtils.cleanPath(file.getOriginalFilename());
        String extension = "";
        int dotIndex = originalFilename.lastIndexOf('.');
        if (dotIndex > 0) {
            extension = originalFilename.substring(dotIndex);
        }
        String storedName = UUID.randomUUID() + extension;
        String relativePath = subDir + "/" + storedName;

        try {
            Path targetDir = Paths.get(rootPath, subDir);
            Files.createDirectories(targetDir);
            Path targetFile = targetDir.resolve(storedName);
            Files.copy(file.getInputStream(), targetFile, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new RuntimeException("文件存储失败: " + originalFilename, e);
        }

        return relativePath;
    }

    @Override
    public Resource loadAsResource(String relativePath) {
        try {
            Path file = resolve(relativePath);
            Resource resource = new UrlResource(file.toUri());
            if (!resource.exists() || !resource.isReadable()) {
                throw new RuntimeException("文件不存在或不可读: " + relativePath);
            }
            return resource;
        } catch (IOException e) {
            throw new RuntimeException("文件加载失败: " + relativePath, e);
        }
    }

    @Override
    public void delete(String relativePath) {
        try {
            Path file = resolve(relativePath);
            Files.deleteIfExists(file);
        } catch (IOException e) {
            throw new RuntimeException("文件删除失败: " + relativePath, e);
        }
    }

    @Override
    public Path resolve(String relativePath) {
        return Paths.get(rootPath).resolve(relativePath);
    }
}
