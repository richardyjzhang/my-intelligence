package com.zhangrichard.myintelligence.personalization;

import java.util.Arrays;

/**
 * 内置主题色；持久化字段存 {@link #getTitle()} 中文标题。
 */
public enum ThemePreset {

    CYBER_NEON("赛博霓虹青", "#0891b2"),
    GAY_PURPLE("基佬紫", "#7c3aed"),
    FORGIVE_GREEN("原谅绿", "#22c55e"),
    MACHO_PINK("猛男粉", "#db2777"),
    TIFFANY_BLUE("蒂芙尼蓝", "#0d9488"),
    RAMPAGE_ORANGE("暴走橙", "#ea580c"),
    DEEP_SEA_BLUE("深海忧郁蓝", "#2563eb"),
    CHEESE_GOLD("芝士奶酪金", "#ca8a04");

    private final String title;
    private final String primaryHex;

    ThemePreset(String title, String primaryHex) {
        this.title = title;
        this.primaryHex = primaryHex;
    }

    public String getTitle() {
        return title;
    }

    public String getPrimaryHex() {
        return primaryHex;
    }

    public static ThemePreset fromTitle(String title) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("主题不能为空");
        }
        String t = title.trim();
        return Arrays.stream(values())
                .filter(x -> x.title.equals(t))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("未知的主题：" + t));
    }

    public static ThemePreset defaultPreset() {
        return CYBER_NEON;
    }
}
