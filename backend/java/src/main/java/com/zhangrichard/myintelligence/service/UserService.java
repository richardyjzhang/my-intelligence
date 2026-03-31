package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.User;
import org.springframework.data.domain.Page;

public interface UserService {

    Page<User> listUsers(String keyword, int page, int size);

    User getUserById(Long id);

    User createUser(User user);

    User updateUser(Long id, User input);

    void deleteUser(Long id);
}
