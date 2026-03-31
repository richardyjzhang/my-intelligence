package com.zhangrichard.myintelligence.controller;

import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/search")
public class SearchController {

    @Autowired
    private SearchService searchService;

    @GetMapping
    public Result<Map<String, Object>> search(
            @RequestParam(defaultValue = "") String keyword,
            @RequestParam(required = false) List<Long> tagIds) {
        return Result.ok(searchService.search(keyword, tagIds));
    }
}
