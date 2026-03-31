package com.zhangrichard.myintelligence.service;

import com.zhangrichard.myintelligence.entity.User;

import java.util.List;

public interface UserService {

    List<User> listUsers(String keyword);

    User getUserById(Long id);

    User createUser(User user);

    User updateUser(Long id, User input);

    void changePassword(Long id, String newPassword);

    void deleteUser(Long id);
}
