package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.dto.LoginResponse;
import com.zhangrichard.myintelligence.entity.User;

public interface AuthService {

    LoginResponse login(User user);

    void logout();

    User getCurrentUser();
}
