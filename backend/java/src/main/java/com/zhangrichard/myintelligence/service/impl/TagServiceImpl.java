package com.zhangrichard.myintelligence.service.impl;

import com.zhangrichard.myintelligence.entity.Tag;
import com.zhangrichard.myintelligence.repository.TagRepository;
import com.zhangrichard.myintelligence.service.TagService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class TagServiceImpl implements TagService {

    @Autowired
    private TagRepository tagRepository;

    @Override
    public List<Tag> listTags(String keyword) {
        return tagRepository.searchByKeyword(keyword);
    }

    @Override
    public Tag getTagById(Long id) {
        return tagRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("标签不存在"));
    }

    @Override
    @Transactional
    public Tag createTag(Tag tag) {
        if (tagRepository.existsByName(tag.getName())) {
            throw new IllegalArgumentException("标签名称已存在");
        }
        tag.setId(null);
        return tagRepository.save(tag);
    }

    @Override
    @Transactional
    public Tag updateTag(Long id, Tag input) {
        Tag tag = tagRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("标签不存在"));

        if (tagRepository.existsByNameAndIdNot(input.getName(), id)) {
            throw new IllegalArgumentException("标签名称已存在");
        }

        tag.setName(input.getName());
        tag.setColor(input.getColor());
        return tagRepository.save(tag);
    }

    @Override
    @Transactional
    public void deleteTag(Long id) {
        if (!tagRepository.existsById(id)) {
            throw new IllegalArgumentException("标签不存在");
        }
        tagRepository.deleteById(id);
    }
}
