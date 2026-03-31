package com.zhangrichard.myintelligence.controller;

import cn.dev33.satoken.annotation.SaCheckRole;
import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.entity.Tag;
import com.zhangrichard.myintelligence.service.TagService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/tags")
public class TagController {

    @Autowired
    private TagService tagService;

    @GetMapping
    public Result<List<Tag>> list(@RequestParam(required = false) String keyword) {
        return Result.ok(tagService.listTags(keyword));
    }

    @GetMapping("/{id}")
    public Result<Tag> get(@PathVariable Long id) {
        return Result.ok(tagService.getTagById(id));
    }

    @SaCheckRole("admin")
    @PostMapping
    public Result<Tag> create(@RequestBody Tag tag) {
        return Result.ok(tagService.createTag(tag));
    }

    @SaCheckRole("admin")
    @PutMapping("/{id}")
    public Result<Tag> update(@PathVariable Long id, @RequestBody Tag tag) {
        return Result.ok(tagService.updateTag(id, tag));
    }

    @SaCheckRole("admin")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        tagService.deleteTag(id);
        return Result.ok();
    }
}
