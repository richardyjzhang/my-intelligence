package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.Tag;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface TagRepository extends JpaRepository<Tag, Long> {

    boolean existsByName(String name);

    boolean existsByNameAndIdNot(String name, Long id);

    @Query("SELECT t FROM Tag t WHERE (:keyword IS NULL OR :keyword = '' OR t.name LIKE %:keyword%) ORDER BY t.createTime ASC")
    List<Tag> searchByKeyword(@Param("keyword") String keyword);
}
