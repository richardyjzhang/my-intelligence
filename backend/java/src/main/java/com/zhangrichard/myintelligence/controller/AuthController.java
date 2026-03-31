package com.zhangrichard.myintelligence.controller;

import com.zhangrichard.myintelligence.common.Result;
import com.zhangrichard.myintelligence.dto.LoginResponse;
import com.zhangrichard.myintelligence.entity.User;
import com.zhangrichard.myintelligence.service.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

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
}
