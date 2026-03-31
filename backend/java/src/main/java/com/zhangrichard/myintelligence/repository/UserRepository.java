package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    boolean existsByUsername(String username);

    @Query("SELECT u FROM User u WHERE (:keyword IS NULL OR :keyword = '' OR u.username LIKE %:keyword% OR u.nickname LIKE %:keyword%) ORDER BY u.createTime ASC")
    List<User> searchByKeyword(@Param("keyword") String keyword);
}
