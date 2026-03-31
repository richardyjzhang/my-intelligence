package com.zhangrichard.myintelligence.config;

import cn.dev33.satoken.stp.StpInterface;
import com.zhangrichard.myintelligence.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;

@Component
@RequiredArgsConstructor
public class StpInterfaceImpl implements StpInterface {

    private final UserRepository userRepository;

    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        return Collections.emptyList();
    }

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        long userId = Long.parseLong(loginId.toString());
        return userRepository.findById(userId)
                .filter(u -> u.isAdmin())
                .map(u -> List.of("admin"))
                .orElse(Collections.emptyList());
    }
}
