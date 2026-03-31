package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.Fragment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface FragmentRepository extends JpaRepository<Fragment, Long> {

    @Query("SELECT DISTINCT f FROM Fragment f LEFT JOIN f.tags t " +
            "WHERE (:keyword IS NULL OR :keyword = '' OR f.title LIKE %:keyword% OR f.content LIKE %:keyword%) " +
            "AND (:tagId IS NULL OR t.id = :tagId) " +
            "ORDER BY f.createTime ASC")
    List<Fragment> searchByKeywordAndTag(@Param("keyword") String keyword, @Param("tagId") Long tagId);
}
