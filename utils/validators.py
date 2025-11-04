#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具类
"""

from typing import List, Any, Optional


class RequestValidator:
    """请求验证器"""
    
    @staticmethod
    def validate_city_list(cities: Any) -> tuple[bool, str]:
        """验证城市列表参数"""
        if not cities:
            return False, "缺少必需参数: cities"
        
        if not isinstance(cities, list):
            return False, "cities 必须是一个数组"
        
        if len(cities) < 2:
            return False, "cities 必须包含至少2个城市"
        
        if not all(isinstance(city, str) and city.strip() for city in cities):
            return False, "cities 中的每个元素都必须是非空字符串"
        
        return True, ""
    
    @staticmethod
    def validate_limit(limit: Any) -> tuple[bool, int]:
        """验证limit参数"""
        if limit is None:
            return True, 20
        
        try:
            limit_int = int(limit)
            if limit_int < 1:
                return False, 20
            return True, min(limit_int, 100)  # 限制最大值为100
        except (ValueError, TypeError):
            return False, 20
    
    @staticmethod
    def validate_min_jobs(min_jobs: Any) -> tuple[bool, int]:
        """验证min_jobs参数"""
        if min_jobs is None:
            return True, 0
        
        try:
            min_jobs_int = int(min_jobs)
            return True, max(0, min_jobs_int)  # 确保非负数
        except (ValueError, TypeError):
            return False, 0
