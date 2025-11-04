#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API响应工具类
"""

from flask import jsonify
from datetime import datetime
import uuid
from typing import Any, Dict, Optional


class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def success(message: str, data: Any = None, code: int = 200) -> tuple:
        """创建成功响应"""
        response = {
            "status": "success",
            "code": code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())
        }
        
        if data is not None:
            response["data"] = data
        
        return jsonify(response), code
    
    @staticmethod
    def error(message: str, code: int = 500, error_details: Optional[Dict] = None) -> tuple:
        """创建错误响应"""
        response = {
            "status": "error",
            "code": code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())
        }
        
        if error_details:
            response["error"] = error_details
        
        return jsonify(response), code
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> tuple:
        """创建404响应"""
        return ResponseBuilder.error(message, 404)
    
    @staticmethod
    def bad_request(message: str = "请求参数错误") -> tuple:
        """创建400响应"""
        return ResponseBuilder.error(message, 400)
    
    @staticmethod
    def internal_error(message: str = "服务器内部错误", error_details: Optional[Dict] = None) -> tuple:
        """创建500响应"""
        return ResponseBuilder.error(message, 500, error_details)
