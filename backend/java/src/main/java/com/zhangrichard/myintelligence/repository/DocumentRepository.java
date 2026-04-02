package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface DocumentRepository extends JpaRepository<Document, Long> {

    @Query("SELECT DISTINCT d FROM Document d LEFT JOIN d.tags t " +
            "WHERE (:keyword IS NULL OR :keyword = '' OR d.title LIKE %:keyword% OR d.code LIKE %:keyword% OR d.remark LIKE %:keyword%) " +
            "AND (:tagIds IS NULL OR t.id IN :tagIds) " +
            "ORDER BY d.createTime DESC")
    List<Document> searchByKeywordAndTags(@Param("keyword") String keyword, @Param("tagIds") List<Long> tagIds);
}
