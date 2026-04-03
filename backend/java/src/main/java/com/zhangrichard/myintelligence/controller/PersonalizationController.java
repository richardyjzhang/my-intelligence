package com.zhangrichard.myintelligence.controller;

import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.entity.UserPersonalization;
import com.zhangrichard.myintelligence.service.PersonalizationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/personalization")
public class PersonalizationController {

    @Autowired
    private PersonalizationService personalizationService;

    @GetMapping("/options/themes")
    public Result<List<Map<String, String>>> listThemeOptions() {
        return Result.ok(personalizationService.listThemeOptions());
    }

    @GetMapping("/options/ai-personas")
    public Result<List<Map<String, String>>> listAiPersonaOptions() {
        return Result.ok(personalizationService.listAiPersonaOptions());
    }

    @GetMapping
    public Result<UserPersonalization> get() {
        return Result.ok(personalizationService.getForCurrentUser());
    }

    @PutMapping("/theme")
    public Result<UserPersonalization> saveTheme(@RequestBody Map<String, String> body) {
        String themeTitle = body != null ? body.get("themeTitle") : null;
        return Result.ok(personalizationService.saveThemeForCurrentUser(themeTitle));
    }

    @PutMapping("/ai-assistant")
    public Result<UserPersonalization> saveAiAssistant(@RequestBody Map<String, String> body) {
        if (body == null) {
            body = Map.of();
        }
        String aiPersonaTitle = body.get("aiPersonaTitle");
        String aiCustomInstruction = body.get("aiCustomInstruction");
        return Result.ok(personalizationService.saveAiAssistantForCurrentUser(aiPersonaTitle, aiCustomInstruction));
    }
}
