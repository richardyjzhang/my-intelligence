package com.zhangrichard.myintelligence.controller;

import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.entity.User;
import com.zhangrichard.myintelligence.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public Result<List<User>> list(@RequestParam(required = false) String keyword) {
        return Result.ok(userService.listUsers(keyword));
    }

    @GetMapping("/{id}")
    public Result<User> get(@PathVariable Long id) {
        return Result.ok(userService.getUserById(id));
    }

    @PostMapping
    public Result<User> create(@RequestBody User user) {
        return Result.ok(userService.createUser(user));
    }

    @PutMapping("/{id}")
    public Result<User> update(@PathVariable Long id, @RequestBody User user) {
        return Result.ok(userService.updateUser(id, user));
    }

    @PutMapping("/{id}/password")
    public Result<Void> changePassword(@PathVariable Long id, @RequestBody User user) {
        userService.changePassword(id, user.getPassword());
        return Result.ok();
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        userService.deleteUser(id);
        return Result.ok();
    }
}
