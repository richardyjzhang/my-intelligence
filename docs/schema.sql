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

-- ============================================
-- 标签表
-- ============================================
CREATE TABLE IF NOT EXISTS `tag` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(50)  NOT NULL COMMENT '标签名称',
    `color`       VARCHAR(7)   NOT NULL COMMENT '颜色（十六进制，如 #FF5733）',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- ============================================
-- 碎片知识表
-- ============================================
CREATE TABLE IF NOT EXISTS `fragment` (
    `id`          BIGINT        NOT NULL AUTO_INCREMENT,
    `title`       VARCHAR(200)  NOT NULL COMMENT '标题',
    `content`     TEXT          NOT NULL COMMENT '内容',
    `creator_id`  BIGINT        NOT NULL COMMENT '创建人ID',
    `create_time` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='碎片知识表';

-- ============================================
-- 碎片知识-标签关联表
-- ============================================
CREATE TABLE IF NOT EXISTS `fragment_tag` (
    `fragment_id` BIGINT NOT NULL,
    `tag_id`      BIGINT NOT NULL,
    PRIMARY KEY (`fragment_id`, `tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='碎片知识-标签关联表';
