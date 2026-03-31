package com.zhangrichard.myintelligence.controller;

import cn.dev33.satoken.annotation.SaCheckRole;
import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.entity.Fragment;
import com.zhangrichard.myintelligence.service.FragmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/fragments")
public class FragmentController {

    @Autowired
    private FragmentService fragmentService;

    @GetMapping
    public Result<List<Fragment>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Long tagId) {
        return Result.ok(fragmentService.listFragments(keyword, tagId));
    }

    @GetMapping("/{id}")
    public Result<Fragment> get(@PathVariable Long id) {
        return Result.ok(fragmentService.getFragmentById(id));
    }

    @PostMapping
    public Result<Fragment> create(@RequestBody Map<String, Object> body) {
        Fragment fragment = new Fragment();
        fragment.setTitle((String) body.get("title"));
        fragment.setContent((String) body.get("content"));

        @SuppressWarnings("unchecked")
        List<Integer> rawTagIds = (List<Integer>) body.get("tagIds");
        List<Long> tagIds = rawTagIds != null
                ? rawTagIds.stream().map(Integer::longValue).toList()
                : List.of();

        return Result.ok(fragmentService.createFragment(fragment, tagIds));
    }

    @SaCheckRole("admin")
    @PutMapping("/{id}")
    public Result<Fragment> update(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        Fragment fragment = new Fragment();
        fragment.setTitle((String) body.get("title"));
        fragment.setContent((String) body.get("content"));

        @SuppressWarnings("unchecked")
        List<Integer> rawTagIds = (List<Integer>) body.get("tagIds");
        List<Long> tagIds = rawTagIds != null
                ? rawTagIds.stream().map(Integer::longValue).toList()
                : List.of();

        return Result.ok(fragmentService.updateFragment(id, fragment, tagIds));
    }

    @SaCheckRole("admin")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        fragmentService.deleteFragment(id);
        return Result.ok();
    }
}
