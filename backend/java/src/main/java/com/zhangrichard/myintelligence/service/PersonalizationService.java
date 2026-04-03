package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.UserPersonalization;

import java.util.List;
import java.util.Map;

public interface PersonalizationService {

    List<Map<String, String>> listThemeOptions();

    List<Map<String, String>> listAiPersonaOptions();

    UserPersonalization getForCurrentUser();

    UserPersonalization saveThemeForCurrentUser(String themeTitle);

    UserPersonalization saveAiAssistantForCurrentUser(String aiPersonaTitle, String aiCustomInstruction);
}
