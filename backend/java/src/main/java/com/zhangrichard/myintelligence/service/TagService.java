package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.Tag;

import java.util.List;

public interface TagService {

    List<Tag> listTags(String keyword);

    Tag getTagById(Long id);

    Tag createTag(Tag tag);

    Tag updateTag(Long id, Tag input);

    void deleteTag(Long id);
}
