#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验相关路由
"""

import logging
from flask import Blueprint, request
from datetime import datetime

from services.experience_service import ExperienceService
from utils.response import ResponseBuilder
from utils.validators import RequestValidator
from database import DatabaseManager

logger = logging.getLogger(__name__)

# 创建蓝图
experience_bp = Blueprint('experience', __name__, url_prefix='/api')

# 初始化服务
db_manager = DatabaseManager('default')
experience_service = ExperienceService(db_manager)


@experience_bp.route('/charts/experience', methods=['GET'])
def get_experience_analysis():
    """获取经验招聘分布数据"""
    try:
        # 验证参数 - 默认返回所有数据
        limit_valid, limit = RequestValidator.validate_limit(request.args.get('limit', 1000, type=int))
        min_jobs_valid, min_jobs = RequestValidator.validate_min_jobs(request.args.get('min_jobs', 0, type=int))
        
        if not limit_valid or not min_jobs_valid:
            return ResponseBuilder.bad_request("参数验证失败")
        
        # 获取经验统计数据
        experience_stats = experience_service.get_experience_statistics(limit, min_jobs)
        
        # 构建图表配置
        chart_config = {
            "type": "horizontal_bar",
            "title": "经验要求分布",
            "subtitle": f"显示所有经验级别" if limit >= 1000 else f"显示前{limit}个经验级别",
            "x_axis": {
                "field": "job_count",
                "label": "职位数量"
            },
            "y_axis": {
                "field": "experience",
                "label": "经验要求"
            },
            "data": [
                {
                    "experience": stat.experience,
                    "job_count": stat.job_count,
                    "percentage": stat.percentage,
                    "avg_salary": stat.avg_salary,
                    "company_count": stat.company_count
                }
                for stat in experience_stats
            ],
            "total": sum(stat.job_count for stat in experience_stats),
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取经验分析数据成功", {"chart_config": chart_config})
        
    except Exception as e:
        logger.error(f"获取经验分析数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@experience_bp.route('/charts/experience/detail/<experience_name>', methods=['GET'])
def get_experience_detail(experience_name):
    """获取特定经验级别的详细分析数据"""
    try:
        experience_detail = experience_service.get_experience_detail(experience_name)
        
        if not experience_detail:
            return ResponseBuilder.not_found(f"未找到经验级别 {experience_name} 的数据")
        
        # 转换为字典格式
        experience_detail_dict = {
            "experience_name": experience_detail.experience_name,
            "basic_info": experience_detail.basic_info,
            "salary_distribution": [
                {
                    "salary_range": dist.salary_range,
                    "count": dist.count,
                    "percentage": dist.percentage
                }
                for dist in experience_detail.salary_distribution
            ],
            "city_distribution": [
                {
                    "city": dist.city,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in experience_detail.city_distribution
            ],
            "industry_distribution": [
                {
                    "industry": dist.industry,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in experience_detail.industry_distribution
            ]
        }
        
        return ResponseBuilder.success(f"获取经验级别 {experience_name} 详细数据成功", experience_detail_dict)
        
    except Exception as e:
        logger.error(f"获取经验详细数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@experience_bp.route('/charts/experience/compare', methods=['POST'])
def compare_experiences():
    """比较多个经验级别的数据"""
    try:
        data = request.get_json()
        
        # 验证参数
        is_valid, error_msg = RequestValidator.validate_city_list(data.get('experiences') if data else None)
        if not is_valid:
            return ResponseBuilder.bad_request(error_msg.replace('cities', 'experiences'))
        
        experiences = data['experiences']
        
        # 获取经验比较数据
        comparison_data = experience_service.compare_experiences(experiences)
        
        if not comparison_data:
            return ResponseBuilder.not_found("未找到指定经验级别的数据")
        
        # 转换为字典格式
        comparison_list = [
            {
                "experience": exp.experience,
                "job_count": exp.job_count,
                "avg_salary": exp.avg_salary,
                "company_count": exp.company_count,
                "city_count": exp.city_count,
                "industry_count": exp.industry_count,
                "job_rank": exp.job_rank,
                "salary_rank": exp.salary_rank
            }
            for exp in comparison_data
        ]
        
        # 计算比较摘要
        comparison_summary = {
            "total_experiences": len(comparison_list),
            "highest_job_count": max(comparison_list, key=lambda x: x['job_count']),
            "highest_avg_salary": max(comparison_list, key=lambda x: x['avg_salary']),
            "most_companies": max(comparison_list, key=lambda x: x['company_count'])
        }
        
        comparison_result = {
            "experiences": comparison_list,
            "comparison_summary": comparison_summary
        }
        
        return ResponseBuilder.success("经验级别比较数据获取成功", comparison_result)
        
    except Exception as e:
        logger.error(f"获取经验比较数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@experience_bp.route('/charts/experience/overview', methods=['GET'])
def get_experience_overview():
    """获取经验概览数据"""
    try:
        overview_data = experience_service.get_experience_overview()
        
        # 转换为字典格式
        overview_dict = {
            "total_experience_levels": overview_data.total_experience_levels,
            "total_jobs": overview_data.total_jobs,
            "avg_salary_overall": overview_data.avg_salary_overall,
            "top_experience_levels": [
                {
                    "experience": exp.experience,
                    "job_count": exp.job_count,
                    "avg_salary": exp.avg_salary,
                    "percentage": exp.percentage
                }
                for exp in overview_data.top_experience_levels
            ],
            "salary_ranges": overview_data.salary_ranges,
            "experience_distribution": overview_data.experience_distribution,
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取经验概览数据成功", overview_dict)
        
    except Exception as e:
        logger.error(f"获取经验概览数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@experience_bp.route('/charts/experience/salary', methods=['GET'])
def get_experience_salary_analysis():
    """获取各经验级别平均薪资分析"""
    try:
        # 验证参数 - 默认返回所有数据
        limit_valid, limit = RequestValidator.validate_limit(request.args.get('limit', 1000, type=int))
        min_jobs_valid, min_jobs = RequestValidator.validate_min_jobs(request.args.get('min_jobs', 0, type=int))
        
        if not limit_valid or not min_jobs_valid:
            return ResponseBuilder.bad_request("参数验证失败")
        
        # 获取经验统计数据
        experience_stats = experience_service.get_experience_statistics(limit, min_jobs)
        
        # 按平均薪资排序
        sorted_experiences = sorted(experience_stats, key=lambda x: x.avg_salary, reverse=True)
        
        # 构建薪资分析数据
        salary_analysis = {
            "type": "bar",
            "title": "各经验级别平均薪资分析",
            "subtitle": f"显示所有经验级别" if limit >= 1000 else f"显示前{limit}个经验级别",
            "x_axis": {
                "field": "avg_salary",
                "label": "平均薪资 (K)"
            },
            "y_axis": {
                "field": "experience",
                "label": "经验要求"
            },
            "data": [
                {
                    "experience": stat.experience,
                    "avg_salary": stat.avg_salary,
                    "job_count": stat.job_count,
                    "company_count": stat.company_count,
                    "percentage": stat.percentage
                }
                for stat in sorted_experiences
            ],
            "summary": {
                "highest_salary": {
                    "experience": sorted_experiences[0].experience if sorted_experiences else None,
                    "avg_salary": sorted_experiences[0].avg_salary if sorted_experiences else 0
                },
                "lowest_salary": {
                    "experience": sorted_experiences[-1].experience if sorted_experiences else None,
                    "avg_salary": sorted_experiences[-1].avg_salary if sorted_experiences else 0
                },
                "overall_avg": round(sum(stat.avg_salary for stat in sorted_experiences) / len(sorted_experiences), 2) if sorted_experiences else 0
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取经验薪资分析数据成功", {"chart_config": salary_analysis})
        
    except Exception as e:
        logger.error(f"获取经验薪资分析数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})
