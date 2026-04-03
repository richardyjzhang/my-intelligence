package com.zhangrichard.myintelligence.personalization;

import java.util.Arrays;

/**
 * 内置 AI 人设；持久化字段存 {@link #getTitle()} 中文标题。
 */
public enum AiPersonaPreset {

    PROFESSIONAL("专业助手", "默认：清晰、务实、克制"),
    SEDUCTIVE_ONEE("魅惑御姐", "低哑、停顿、钩子话；撩在分寸里"),
    SWEET_CATGIRL("甜萌猫娘", "「喵~」贴贴，但数字不耍萌"),
    TIEBA_BRO("爱膜贴吧老哥", "蚌埠住了、这合理吗，典中典张口就来"),
    COLD_TOP_STUDENT("高冷学霸", "「结论：」打头，拒绝废话"),
    GENTLE_SISTER("温柔姐姐", "「没关系」「我们一步步来」"),
    ROCK_KING("摇滚骚皇", "先抖一句，马上「书归正传」"),
    SEMI_CLASSICAL("半文言腔", "「顾」「大抵」「未可」偶尔冒头"),
    GEEK_FRIEND("极客损友", "栈、线程、404、背锅，张口就来"),
    REPUBLIC_GENTLEMAN("民国先生", "「您」「鄙意」「不妨一观」");

    private final String title;
    private final String description;

    AiPersonaPreset(String title, String description) {
        this.title = title;
        this.description = description;
    }

    public String getTitle() {
        return title;
    }

    public String getDescription() {
        return description;
    }

    public static AiPersonaPreset fromTitle(String title) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("AI 人设不能为空");
        }
        String t = title.trim();
        return Arrays.stream(values())
                .filter(x -> x.title.equals(t))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("未知的 AI 人设：" + t));
    }

    public static AiPersonaPreset defaultPreset() {
        return PROFESSIONAL;
    }
}
