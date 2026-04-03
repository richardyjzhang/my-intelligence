package com.zhangrichard.myintelligence.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.zhangrichard.myintelligence.entity.UserPersonalization;
import com.zhangrichard.myintelligence.personalization.AiPersonaPreset;
import com.zhangrichard.myintelligence.personalization.ThemePreset;
import com.zhangrichard.myintelligence.repository.UserPersonalizationRepository;
import com.zhangrichard.myintelligence.service.PersonalizationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class PersonalizationServiceImpl implements PersonalizationService {

    @Autowired
    private UserPersonalizationRepository userPersonalizationRepository;

    @Override
    public List<Map<String, String>> listThemeOptions() {
        return Arrays.stream(ThemePreset.values()).map(t -> {
            Map<String, String> m = new LinkedHashMap<>();
            m.put("title", t.getTitle());
            m.put("primaryHex", t.getPrimaryHex());
            return m;
        }).toList();
    }

    @Override
    public List<Map<String, String>> listAiPersonaOptions() {
        return Arrays.stream(AiPersonaPreset.values()).map(p -> {
            Map<String, String> m = new LinkedHashMap<>();
            m.put("title", p.getTitle());
            m.put("description", p.getDescription());
            return m;
        }).toList();
    }

    @Override
    public UserPersonalization getForCurrentUser() {
        long userId = StpUtil.getLoginIdAsLong();
        return userPersonalizationRepository.findById(userId)
                .orElseGet(() -> defaultPersonalization(userId));
    }

    @Override
    @Transactional
    public UserPersonalization saveThemeForCurrentUser(String themeTitle) {
        long userId = StpUtil.getLoginIdAsLong();
        ThemePreset.fromTitle(themeTitle);

        UserPersonalization row = userPersonalizationRepository.findById(userId)
                .orElseGet(() -> newPartialRow(userId));
        row.setUserId(userId);
        row.setThemeTitle(themeTitle.trim());
        if (row.getAiPersonaTitle() == null) {
            row.setAiPersonaTitle(AiPersonaPreset.defaultPreset().getTitle());
        }
        return userPersonalizationRepository.save(row);
    }

    @Override
    @Transactional
    public UserPersonalization saveAiAssistantForCurrentUser(String aiPersonaTitle, String aiCustomInstruction) {
        long userId = StpUtil.getLoginIdAsLong();
        AiPersonaPreset.fromTitle(aiPersonaTitle);

        UserPersonalization row = userPersonalizationRepository.findById(userId)
                .orElseGet(() -> newPartialRow(userId));
        row.setUserId(userId);
        row.setAiPersonaTitle(aiPersonaTitle.trim());
        String custom = aiCustomInstruction;
        row.setAiCustomInstruction(custom != null && !custom.isBlank() ? custom.trim() : null);
        if (row.getThemeTitle() == null) {
            row.setThemeTitle(ThemePreset.defaultPreset().getTitle());
        }
        return userPersonalizationRepository.save(row);
    }

    private static UserPersonalization newPartialRow(long userId) {
        UserPersonalization u = new UserPersonalization();
        u.setUserId(userId);
        return u;
    }

    private static UserPersonalization defaultPersonalization(long userId) {
        UserPersonalization u = new UserPersonalization();
        u.setUserId(userId);
        u.setThemeTitle(ThemePreset.defaultPreset().getTitle());
        u.setAiPersonaTitle(AiPersonaPreset.defaultPreset().getTitle());
        u.setAiCustomInstruction(null);
        return u;
    }
}
