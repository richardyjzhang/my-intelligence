package com.zhangrichard.myintelligence.repository;

import com.zhangrichard.myintelligence.entity.UserPersonalization;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserPersonalizationRepository extends JpaRepository<UserPersonalization, Long> {
}
