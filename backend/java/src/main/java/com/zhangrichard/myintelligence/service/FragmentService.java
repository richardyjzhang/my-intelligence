package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.Fragment;

import java.util.List;

public interface FragmentService {

    List<Fragment> listFragments(String keyword, List<Long> tagIds);

    Fragment getFragmentById(Long id);

    Fragment createFragment(Fragment fragment, List<Long> tagIds);

    Fragment updateFragment(Long id, Fragment input, List<Long> tagIds);

    void deleteFragment(Long id);
}
