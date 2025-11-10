#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1 职位差异度分析相关路由
"""

import logging
from flask import Blueprint, request
from datetime import datetime

from services.q1_service import Q1Service
from utils.response import ResponseBuilder
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)

# 创建蓝图
q1_bp = Blueprint('q1', __name__, url_prefix='/api/q1')

# 初始化服务
db_manager = DatabaseManager('default')
q1_service = Q1Service(db_manager)


@q1_bp.route('/cities', methods=['GET'])
def get_representative_cities():
    """获取20个代表性城市列表"""
    try:
        cities = q1_service.get_representative_cities()
        return ResponseBuilder.success("获取代表性城市成功", {"cities": cities})
    except Exception as e:
        logger.error(f"获取代表性城市失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@q1_bp.route('/scatter', methods=['GET'])
def get_scatter_data():
    """
    获取散点气泡图数据
    参数:
    - city: 城市名称（必选）
    """
    try:
        city = request.args.get('city')
        
        if not city:
            return ResponseBuilder.bad_request("缺少参数: city")
        
        # 获取散点图数据
        scatter_data = q1_service.get_scatter_data(city)
        
        if not scatter_data:
            return ResponseBuilder.not_found(f"未找到城市 {city} 的数据")
        
        return ResponseBuilder.success(f"获取城市 {city} 散点图数据成功", scatter_data)
        
    except Exception as e:
        logger.error(f"获取散点图数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@q1_bp.route('/job-levels', methods=['GET'])
def get_job_levels():
    """获取所有职位层级（聚类类别）"""
    try:
        job_levels = q1_service.get_job_levels()
        return ResponseBuilder.success("获取职位层级成功", {"job_levels": job_levels})
    except Exception as e:
        logger.error(f"获取职位层级失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@q1_bp.route('/industries', methods=['GET'])
def get_industries():
    """获取所有行业类别"""
    try:
        city = request.args.get('city')
        industries = q1_service.get_industries(city)
        return ResponseBuilder.success("获取行业类别成功", {"industries": industries})
    except Exception as e:
        logger.error(f"获取行业类别失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})

