package com.zhangrichard.myintelligence.controller;

import cn.dev33.satoken.annotation.SaCheckRole;
import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.entity.Document;
import com.zhangrichard.myintelligence.service.DocumentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/documents")
public class DocumentController {

    @Autowired
    private DocumentService documentService;

    @GetMapping
    public Result<List<Document>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) List<Long> tagIds) {
        return Result.ok(documentService.listDocuments(keyword, tagIds));
    }

    @GetMapping("/{id}")
    public Result<Document> get(@PathVariable Long id) {
        return Result.ok(documentService.getDocumentById(id));
    }

    @PostMapping
    public Result<Document> create(
            @RequestParam String title,
            @RequestParam(required = false) String code,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate publishDate,
            @RequestParam(required = false, defaultValue = "1") Integer status,
            @RequestParam(required = false) String url,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) List<Long> tagIds,
            @RequestParam MultipartFile file) {

        Document document = new Document();
        document.setTitle(title);
        document.setCode(code);
        document.setPublishDate(publishDate);
        document.setStatus(status);
        document.setUrl(url);
        document.setRemark(remark);

        return Result.ok(documentService.createDocument(document, tagIds, file));
    }

    @SaCheckRole("admin")
    @PutMapping("/{id}")
    public Result<Document> update(
            @PathVariable Long id,
            @RequestParam String title,
            @RequestParam(required = false) String code,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate publishDate,
            @RequestParam(required = false, defaultValue = "1") Integer status,
            @RequestParam(required = false) String url,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) List<Long> tagIds) {

        Document document = new Document();
        document.setTitle(title);
        document.setCode(code);
        document.setPublishDate(publishDate);
        document.setStatus(status);
        document.setUrl(url);
        document.setRemark(remark);

        return Result.ok(documentService.updateDocument(id, document, tagIds));
    }

    @SaCheckRole("admin")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        documentService.deleteDocument(id);
        return Result.ok();
    }

    @GetMapping("/{id}/preview")
    public ResponseEntity<Resource> preview(@PathVariable Long id) {
        Document document = documentService.getDocumentById(id);
        Resource resource = documentService.downloadDocument(id);

        String encodedFileName = URLEncoder.encode(document.getFileName(), StandardCharsets.UTF_8);

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "inline; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    @GetMapping("/{id}/download")
    public ResponseEntity<Resource> download(@PathVariable Long id) {
        Document document = documentService.getDocumentById(id);
        Resource resource = documentService.downloadDocument(id);

        String encodedFileName = URLEncoder.encode(document.getFileName(), StandardCharsets.UTF_8);

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }
}
