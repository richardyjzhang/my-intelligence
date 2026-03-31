package com.zhangrichard.myintelligence.service;

import java.util.List;
import java.util.Map;

public interface SearchService {

    Map<String, Object> search(String keyword, List<Long> tagIds);
}
