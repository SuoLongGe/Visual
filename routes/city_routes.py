#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市相关路由
"""

import logging
from flask import Blueprint, request
from datetime import datetime

from services.city_service import CityService
from utils.response import ResponseBuilder
from utils.validators import RequestValidator
from database import DatabaseManager

logger = logging.getLogger(__name__)

# 创建蓝图
city_bp = Blueprint('city', __name__, url_prefix='/api')

# 初始化服务
db_manager = DatabaseManager('default')
city_service = CityService(db_manager)


@city_bp.route('/overview', methods=['GET'])
def get_overview():
    """获取数据概览"""
    try:
        overview_data = city_service.get_overview_data()
        
        # 转换为字典格式
        overview_dict = {
            "total_records": overview_data.total_records,
            "data_quality": overview_data.data_quality,
            "last_updated": overview_data.last_updated,
            "data_sources": overview_data.data_sources,
            "statistics": overview_data.statistics
        }
        
        return ResponseBuilder.success("获取数据概览成功", overview_dict)
        
    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@city_bp.route('/charts/city', methods=['GET'])
def get_city_analysis():
    """获取城市招聘分布数据"""
    try:
        # 验证参数 - 默认返回所有数据
        limit_valid, limit = RequestValidator.validate_limit(request.args.get('limit', 1000, type=int))
        min_jobs_valid, min_jobs = RequestValidator.validate_min_jobs(request.args.get('min_jobs', 0, type=int))
        
        if not limit_valid or not min_jobs_valid:
            return ResponseBuilder.bad_request("参数验证失败")
        
        # 获取城市统计数据
        city_stats = city_service.get_city_statistics(limit, min_jobs)
        
        # 构建图表配置
        chart_config = {
            "type": "horizontal_bar",
            "title": "城市招聘分布",
            "subtitle": f"显示所有城市" if limit >= 1000 else f"显示前{limit}个城市",
            "x_axis": {
                "field": "job_count",
                "label": "职位数量"
            },
            "y_axis": {
                "field": "city",
                "label": "城市"
            },
            "data": [
                {
                    "city": stat.city,
                    "job_count": stat.job_count,
                    "percentage": stat.percentage,
                    "avg_salary": stat.avg_salary,
                    "company_count": stat.company_count
                }
                for stat in city_stats
            ],
            "total": sum(stat.job_count for stat in city_stats),
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取城市分析数据成功", {"chart_config": chart_config})
        
    except Exception as e:
        logger.error(f"获取城市分析数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@city_bp.route('/charts/city/detail/<city_name>', methods=['GET'])
def get_city_detail(city_name):
    """获取特定城市的详细分析数据"""
    try:
        city_detail = city_service.get_city_detail(city_name)
        
        if not city_detail:
            return ResponseBuilder.not_found(f"未找到城市 {city_name} 的数据")
        
        # 转换为字典格式
        city_detail_dict = {
            "city_name": city_detail.city_name,
            "basic_info": {
                "total_jobs": city_detail.basic_info.total_jobs,
                "avg_salary": city_detail.basic_info.avg_salary,
                "company_count": city_detail.basic_info.company_count,
                "industry_count": city_detail.basic_info.industry_count
            },
            "salary_distribution": [
                {
                    "range": dist.range,
                    "count": dist.count,
                    "percentage": dist.percentage
                }
                for dist in city_detail.salary_distribution
            ],
            "industry_distribution": [
                {
                    "industry": dist.industry,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in city_detail.industry_distribution
            ],
            "experience_distribution": [
                {
                    "experience": dist.experience,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in city_detail.experience_distribution
            ]
        }
        
        return ResponseBuilder.success(f"获取城市 {city_name} 详细数据成功", city_detail_dict)
        
    except Exception as e:
        logger.error(f"获取城市详细数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@city_bp.route('/charts/city/compare', methods=['POST'])
def compare_cities():
    """比较多个城市的数据"""
    try:
        data = request.get_json()
        
        # 验证参数
        is_valid, error_msg = RequestValidator.validate_city_list(data.get('cities') if data else None)
        if not is_valid:
            return ResponseBuilder.bad_request(error_msg)
        
        cities = data['cities']
        
        # 获取城市比较数据
        comparison_data = city_service.compare_cities(cities)
        
        if not comparison_data:
            return ResponseBuilder.not_found("未找到指定城市的数据")
        
        # 转换为字典格式
        comparison_list = [
            {
                "city": city.city,
                "job_count": city.job_count,
                "avg_salary": city.avg_salary,
                "company_count": city.company_count,
                "industry_count": city.industry_count,
                "job_rank": city.job_rank,
                "salary_rank": city.salary_rank
            }
            for city in comparison_data
        ]
        
        # 计算比较摘要
        comparison_summary = {
            "total_cities": len(comparison_list),
            "highest_job_count": max(comparison_list, key=lambda x: x['job_count']),
            "highest_avg_salary": max(comparison_list, key=lambda x: x['avg_salary']),
            "most_companies": max(comparison_list, key=lambda x: x['company_count'])
        }
        
        comparison_result = {
            "cities": comparison_list,
            "comparison_summary": comparison_summary
        }
        
        return ResponseBuilder.success("城市比较数据获取成功", comparison_result)
        
    except Exception as e:
        logger.error(f"获取城市比较数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})
