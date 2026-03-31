package com.zhangrichard.myintelligence.service.impl;

import com.zhangrichard.myintelligence.entity.Fragment;
import com.zhangrichard.myintelligence.entity.Tag;
import com.zhangrichard.myintelligence.entity.User;
import com.zhangrichard.myintelligence.repository.FragmentRepository;
import com.zhangrichard.myintelligence.repository.TagRepository;
import com.zhangrichard.myintelligence.service.AuthService;
import com.zhangrichard.myintelligence.service.FragmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
public class FragmentServiceImpl implements FragmentService {

    @Autowired
    private FragmentRepository fragmentRepository;

    @Autowired
    private TagRepository tagRepository;

    @Autowired
    private AuthService authService;

    @Override
    public List<Fragment> listFragments(String keyword, List<Long> tagIds) {
        return fragmentRepository.searchByKeywordAndTags(keyword, tagIds);
    }

    @Override
    public Fragment getFragmentById(Long id) {
        return fragmentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("碎片知识不存在"));
    }

    @Override
    @Transactional
    public Fragment createFragment(Fragment fragment, List<Long> tagIds) {
        User currentUser = authService.getCurrentUser();
        fragment.setId(null);
        fragment.setCreator(currentUser);
        fragment.setTags(resolveTagSet(tagIds));
        return fragmentRepository.save(fragment);
    }

    @Override
    @Transactional
    public Fragment updateFragment(Long id, Fragment input, List<Long> tagIds) {
        Fragment fragment = fragmentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("碎片知识不存在"));

        fragment.setTitle(input.getTitle());
        fragment.setContent(input.getContent());
        fragment.setTags(resolveTagSet(tagIds));
        return fragmentRepository.save(fragment);
    }

    @Override
    @Transactional
    public void deleteFragment(Long id) {
        if (!fragmentRepository.existsById(id)) {
            throw new IllegalArgumentException("碎片知识不存在");
        }
        fragmentRepository.deleteById(id);
    }

    private Set<Tag> resolveTagSet(List<Long> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return new HashSet<>();
        }
        List<Tag> tags = tagRepository.findAllById(tagIds);
        return new HashSet<>(tags);
    }
}
