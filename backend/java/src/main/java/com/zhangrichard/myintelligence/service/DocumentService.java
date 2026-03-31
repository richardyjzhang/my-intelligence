package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.Document;
import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface DocumentService {

    List<Document> listDocuments(String keyword, List<Long> tagIds);

    Document getDocumentById(Long id);

    Document createDocument(Document document, List<Long> tagIds, MultipartFile file);

    Document updateDocument(Long id, Document input, List<Long> tagIds);

    void deleteDocument(Long id);

    Resource downloadDocument(Long id);

    Document reparseDocument(Long id);
}
