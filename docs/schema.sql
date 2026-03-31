-- ============================================
-- My Intelligence 数据库结构
-- 数据库: my_intelligence
-- 字符集: utf8mb4
-- ============================================

CREATE DATABASE IF NOT EXISTS `my_intelligence`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `my_intelligence`;

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS `user` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT,
    `username`    VARCHAR(50)  NOT NULL COMMENT '登录名',
    `nickname`    VARCHAR(50)  NOT NULL COMMENT '昵称',
    `phone`       VARCHAR(20)  NULL     COMMENT '手机号（可选）',
    `email`       VARCHAR(100) NULL     COMMENT '邮箱（可选）',
    `password`    VARCHAR(255) NOT NULL COMMENT '密码（BCrypt 加密）',
    `admin`       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否管理员',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
