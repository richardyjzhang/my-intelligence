package com.zhangrichard.myintelligence.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

/**
 * 用户个性化。user_id 与 {@link User} 主键逻辑对应，数据库不建外键约束。
 * theme_title / ai_persona_title 存内置项的中文标题。
 */
@Data
@Entity
@Table(name = "user_personalization")
public class UserPersonalization {

    @Id
    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "theme_title", nullable = false, length = 64)
    private String themeTitle;

    @Column(name = "ai_persona_title", nullable = false, length = 64)
    private String aiPersonaTitle;

    @Column(columnDefinition = "TEXT")
    private String aiCustomInstruction;
}
