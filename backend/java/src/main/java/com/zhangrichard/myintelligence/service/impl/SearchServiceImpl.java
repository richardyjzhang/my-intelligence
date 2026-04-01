package com.zhangrichard.myintelligence.service.impl;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch._types.FieldValue;
import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.HighlightField;
import co.elastic.clients.elasticsearch.core.search.HighlighterType;
import co.elastic.clients.elasticsearch.core.search.Hit;
import com.zhangrichard.myintelligence.entity.Fragment;
import com.zhangrichard.myintelligence.entity.Tag;
import com.zhangrichard.myintelligence.repository.FragmentRepository;
import com.zhangrichard.myintelligence.repository.TagRepository;
import com.zhangrichard.myintelligence.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class SearchServiceImpl implements SearchService {

    private static final String INDEX_NAME = "documents";

    @Autowired
    private ElasticsearchClient esClient;

    @Autowired
    private FragmentRepository fragmentRepository;

    @Autowired
    private TagRepository tagRepository;

    @Override
    public Map<String, Object> search(String keyword, List<Long> tagIds) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("documents", searchDocuments(keyword, tagIds));
        result.put("fragments", searchFragments(keyword, tagIds));
        return result;
    }

    private List<Map<String, Object>> searchDocuments(String keyword, List<Long> tagIds) {
        if (keyword == null || keyword.isBlank()) {
            return List.of();
        }

        List<String> tagNames = resolveTagNames(tagIds);

        try {
            Query query = buildDocumentQuery(keyword, tagNames);

            Query highlightQuery = Query.of(q -> q.multiMatch(mm -> mm
                    .query(keyword)
                    .fields("title", "content")
                    .analyzer("ik_smart")
            ));

            SearchResponse<Map> response = esClient.search(s -> s
                    .index(INDEX_NAME)
                    .size(20)
                    .query(query)
                    .highlight(h -> h
                            .type(HighlighterType.Plain)
                            .fields("title", HighlightField.of(hf -> hf
                                    .highlightQuery(highlightQuery)))
                            .fields("content", HighlightField.of(hf -> hf
                                    .fragmentSize(200)
                                    .numberOfFragments(3)
                                    .highlightQuery(highlightQuery)))
                            .preTags("<mark>")
                            .postTags("</mark>")
                    )
                    .source(sc -> sc.filter(f -> f
                            .includes("documentId", "title", "tags", "fileName"))),
                    Map.class);

            List<Map<String, Object>> documents = new ArrayList<>();
            for (Hit<Map> hit : response.hits().hits()) {
                Map<String, Object> source = hit.source();
                if (source == null) continue;

                Map<String, Object> doc = new LinkedHashMap<>();
                doc.put("documentId", source.get("documentId"));
                doc.put("title", source.get("title"));
                doc.put("tags", source.get("tags"));
                doc.put("fileName", source.get("fileName"));
                doc.put("score", hit.score());

                Map<String, List<String>> highlights = hit.highlight();
                if (highlights.containsKey("title")) {
                    doc.put("titleHighlight", String.join("", highlights.get("title")));
                }
                if (highlights.containsKey("content")) {
                    doc.put("contentHighlights", highlights.get("content"));
                }

                documents.add(doc);
            }
            return documents;

        } catch (IOException e) {
            throw new RuntimeException("ES 检索失败", e);
        }
    }

    /**
     * 相关性：标题短语匹配优先，其次标题分词，再次正文短语，最后正文分词（由 boost 体现）。
     */
    private Query buildDocumentQuery(String keyword, List<String> tagNames) {
        BoolQuery.Builder outer = new BoolQuery.Builder();

        outer.must(m -> m.bool(b -> b
                .minimumShouldMatch("1")
                .should(s -> s.matchPhrase(mp -> mp
                        .field("title")
                        .query(keyword)
                        .boost(10.0f)))
                .should(s -> s.match(mt -> mt
                        .field("title")
                        .query(keyword)
                        .analyzer("ik_smart")
                        .boost(5.0f)))
                .should(s -> s.matchPhrase(mp -> mp
                        .field("content")
                        .query(keyword)
                        .boost(2.0f)))
                .should(s -> s.match(mt -> mt
                        .field("content")
                        .query(keyword)
                        .analyzer("ik_smart")
                        .boost(1.0f)))));

        if (tagNames != null && !tagNames.isEmpty()) {
            outer.filter(f -> f.terms(t -> t
                    .field("tags")
                    .terms(tv -> tv.value(tagNames.stream()
                            .map(FieldValue::of)
                            .toList()))
            ));
        }

        return outer.build()._toQuery();
    }

    private List<Map<String, Object>> searchFragments(String keyword, List<Long> tagIds) {
        if (keyword == null || keyword.isBlank()) {
            return List.of();
        }

        List<Fragment> fragments = fragmentRepository.searchByKeywordAndTags(keyword, tagIds);
        return fragments.stream().map(f -> {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("fragmentId", f.getId());
            item.put("title", f.getTitle());

            String content = f.getContent();
            if (content != null && content.length() > 200) {
                content = content.substring(0, 200) + "...";
            }
            item.put("content", content);

            item.put("tags", f.getTags().stream()
                    .map(Tag::getName)
                    .collect(Collectors.toList()));

            return item;
        }).collect(Collectors.toList());
    }

    private List<String> resolveTagNames(List<Long> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return null;
        }
        return tagRepository.findAllById(tagIds).stream()
                .map(Tag::getName)
                .toList();
    }
}
