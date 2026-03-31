package com.zhangrichard.myintelligence.service.impl;

import com.zhangrichard.myintelligence.entity.Document;
import com.zhangrichard.myintelligence.entity.Tag;
import com.zhangrichard.myintelligence.entity.User;
import com.zhangrichard.myintelligence.repository.DocumentRepository;
import com.zhangrichard.myintelligence.repository.TagRepository;
import com.zhangrichard.myintelligence.service.AuthService;
import com.zhangrichard.myintelligence.service.DocumentParseService;
import com.zhangrichard.myintelligence.service.DocumentService;
import com.zhangrichard.myintelligence.service.FileService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
public class DocumentServiceImpl implements DocumentService {

    private static final String SUB_DIR = "documents";

    @Autowired
    private DocumentRepository documentRepository;

    @Autowired
    private TagRepository tagRepository;

    @Autowired
    private AuthService authService;

    @Autowired
    private FileService fileService;

    @Autowired
    private DocumentParseService documentParseService;

    @Override
    public List<Document> listDocuments(String keyword, List<Long> tagIds) {
        return documentRepository.searchByKeywordAndTags(keyword, tagIds);
    }

    @Override
    public Document getDocumentById(Long id) {
        return documentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("文档不存在"));
    }

    @Override
    @Transactional
    public Document createDocument(Document document, List<Long> tagIds, MultipartFile file) {
        User currentUser = authService.getCurrentUser();
        document.setId(null);
        document.setCreator(currentUser);
        document.setTags(resolveTagSet(tagIds));

        String relativePath = fileService.store(file, SUB_DIR);
        document.setFileName(StringUtils.cleanPath(file.getOriginalFilename()));
        document.setFilePath(relativePath);
        document.setFileSize(file.getSize());

        Document saved = documentRepository.save(document);
        documentParseService.submitParseTask(saved);
        return saved;
    }

    @Override
    @Transactional
    public Document updateDocument(Long id, Document input, List<Long> tagIds) {
        Document document = documentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("文档不存在"));

        document.setTitle(input.getTitle());
        document.setCode(input.getCode());
        document.setPublishDate(input.getPublishDate());
        document.setStatus(input.getStatus());
        document.setUrl(input.getUrl());
        document.setRemark(input.getRemark());
        document.setTags(resolveTagSet(tagIds));

        return documentRepository.save(document);
    }

    @Override
    @Transactional
    public void deleteDocument(Long id) {
        Document document = documentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("文档不存在"));

        fileService.delete(document.getFilePath());
        documentRepository.deleteById(id);
    }

    @Override
    public Resource downloadDocument(Long id) {
        Document document = documentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("文档不存在"));

        return fileService.loadAsResource(document.getFilePath());
    }

    private Set<Tag> resolveTagSet(List<Long> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return new HashSet<>();
        }
        List<Tag> tags = tagRepository.findAllById(tagIds);
        return new HashSet<>(tags);
    }
}
