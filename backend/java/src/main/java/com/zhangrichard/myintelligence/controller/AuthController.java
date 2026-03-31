package com.zhangrichard.myintelligence.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.dto.LoginResponse;
import com.zhangrichard.myintelligence.entity.User;
import com.zhangrichard.myintelligence.service.AuthService;
import com.zhangrichard.myintelligence.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

    @Autowired
    private UserService userService;

    @PostMapping("/login")
    public Result<LoginResponse> login(@RequestBody User user) {
        return Result.ok(authService.login(user));
    }

    @PostMapping("/logout")
    public Result<Void> logout() {
        authService.logout();
        return Result.ok();
    }

    @GetMapping("/me")
    public Result<User> me() {
        return Result.ok(authService.getCurrentUser());
    }

    @PutMapping("/password")
    public Result<Void> changePassword(@RequestBody Map<String, String> body) {
        long userId = StpUtil.getLoginIdAsLong();
        userService.changePassword(userId, body.get("newPassword"));
        return Result.ok();
    }
}
