package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface DocumentRepository extends JpaRepository<Document, Long> {

    @Query("SELECT DISTINCT d FROM Document d LEFT JOIN d.tags t " +
            "WHERE (:keyword IS NULL OR :keyword = '' OR d.title LIKE %:keyword% OR d.code LIKE %:keyword% OR d.remark LIKE %:keyword%) " +
            "AND (:tagId IS NULL OR t.id = :tagId) " +
            "ORDER BY d.createTime ASC")
    List<Document> searchByKeywordAndTag(@Param("keyword") String keyword, @Param("tagId") Long tagId);
}
