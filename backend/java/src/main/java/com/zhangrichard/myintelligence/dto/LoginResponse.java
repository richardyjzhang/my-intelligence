package com.zhangrichard.myintelligence.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LoginResponse {

    private String token;
    private Long id;
    private String username;
    private String nickname;
    private boolean admin;
}
