#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业相关路由
"""

import logging
from flask import Blueprint, request
from datetime import datetime

from services.industry_service import IndustryService
from services.trend_service import TrendService
from utils.response import ResponseBuilder
from utils.validators import RequestValidator
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)

# 创建蓝图
industry_bp = Blueprint('industry', __name__, url_prefix='/api')

# 初始化服务
db_manager = DatabaseManager('default')
industry_service = IndustryService(db_manager)
trend_service = TrendService()


@industry_bp.route('/charts/industry', methods=['GET'])
def get_industry_analysis():
    """获取行业招聘分布数据"""
    try:
        # 验证参数 - 默认返回所有数据
        limit_valid, limit = RequestValidator.validate_limit(request.args.get('limit', 1000, type=int))
        min_jobs_valid, min_jobs = RequestValidator.validate_min_jobs(request.args.get('min_jobs', 0, type=int))
        
        if not limit_valid or not min_jobs_valid:
            return ResponseBuilder.bad_request("参数验证失败")
        
        # 获取行业统计数据
        industry_stats = industry_service.get_industry_statistics(limit, min_jobs)
        
        # 构建图表配置
        chart_config = {
            "type": "horizontal_bar",
            "title": "行业招聘分布",
            "subtitle": f"显示所有行业" if limit >= 1000 else f"显示前{limit}个行业",
            "x_axis": {
                "field": "job_count",
                "label": "职位数量"
            },
            "y_axis": {
                "field": "industry",
                "label": "行业类型"
            },
            "data": [
                {
                    "industry": stat.industry,
                    "job_count": stat.job_count,
                    "percentage": stat.percentage,
                    "avg_salary": stat.avg_salary,
                    "company_count": stat.company_count
                }
                for stat in industry_stats
            ],
            "total": sum(stat.job_count for stat in industry_stats),
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取行业分析数据成功", {"chart_config": chart_config})
        
    except Exception as e:
        logger.error(f"获取行业分析数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/charts/industry/detail/<industry_name>', methods=['GET'])
def get_industry_detail(industry_name):
    """获取特定行业的详细分析数据"""
    try:
        industry_detail = industry_service.get_industry_detail(industry_name)
        
        if not industry_detail:
            return ResponseBuilder.not_found(f"未找到行业 {industry_name} 的数据")
        
        # 转换为字典格式
        industry_detail_dict = {
            "industry_name": industry_detail.industry_name,
            "basic_info": industry_detail.basic_info,
            "salary_distribution": [
                {
                    "salary_range": dist.salary_range,
                    "count": dist.count,
                    "percentage": dist.percentage
                }
                for dist in industry_detail.salary_distribution
            ],
            "city_distribution": [
                {
                    "city": dist.city,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in industry_detail.city_distribution
            ],
            "experience_distribution": [
                {
                    "experience": dist.experience,
                    "count": dist.count,
                    "avg_salary": dist.avg_salary,
                    "percentage": dist.percentage
                }
                for dist in industry_detail.experience_distribution
            ]
        }
        
        return ResponseBuilder.success(f"获取行业 {industry_name} 详细数据成功", industry_detail_dict)
        
    except Exception as e:
        logger.error(f"获取行业详细数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/charts/industry/compare', methods=['POST'])
def compare_industries():
    """比较多个行业的数据"""
    try:
        data = request.get_json()
        
        # 验证参数
        is_valid, error_msg = RequestValidator.validate_city_list(data.get('industries') if data else None)
        if not is_valid:
            return ResponseBuilder.bad_request(error_msg.replace('cities', 'industries'))
        
        industries = data['industries']
        
        # 获取行业比较数据
        comparison_data = industry_service.compare_industries(industries)
        
        if not comparison_data:
            return ResponseBuilder.not_found("未找到指定行业的数据")
        
        # 转换为字典格式
        comparison_list = [
            {
                "industry": industry.industry,
                "job_count": industry.job_count,
                "avg_salary": industry.avg_salary,
                "company_count": industry.company_count,
                "city_count": industry.city_count,
                "job_rank": industry.job_rank,
                "salary_rank": industry.salary_rank
            }
            for industry in comparison_data
        ]
        
        # 计算比较摘要
        comparison_summary = {
            "total_industries": len(comparison_list),
            "highest_job_count": max(comparison_list, key=lambda x: x['job_count']),
            "highest_avg_salary": max(comparison_list, key=lambda x: x['avg_salary']),
            "most_companies": max(comparison_list, key=lambda x: x['company_count'])
        }
        
        comparison_result = {
            "industries": comparison_list,
            "comparison_summary": comparison_summary
        }
        
        return ResponseBuilder.success("行业比较数据获取成功", comparison_result)
        
    except Exception as e:
        logger.error(f"获取行业比较数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/charts/industry/overview', methods=['GET'])
def get_industry_overview():
    """获取行业概览数据"""
    try:
        overview_data = industry_service.get_industry_overview()
        
        # 转换为字典格式
        overview_dict = {
            "total_industries": overview_data.total_industries,
            "total_jobs": overview_data.total_jobs,
            "avg_salary_overall": overview_data.avg_salary_overall,
            "top_industries": [
                {
                    "industry": industry.industry,
                    "job_count": industry.job_count,
                    "avg_salary": industry.avg_salary,
                    "percentage": industry.percentage
                }
                for industry in overview_data.top_industries
            ],
            "salary_ranges": overview_data.salary_ranges,
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取行业概览数据成功", overview_dict)
        
    except Exception as e:
        logger.error(f"获取行业概览数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/charts/industry/salary', methods=['GET'])
def get_industry_salary_analysis():
    """获取各行业平均薪资分析"""
    try:
        # 验证参数 - 默认返回所有数据
        limit_valid, limit = RequestValidator.validate_limit(request.args.get('limit', 1000, type=int))
        min_jobs_valid, min_jobs = RequestValidator.validate_min_jobs(request.args.get('min_jobs', 0, type=int))
        
        if not limit_valid or not min_jobs_valid:
            return ResponseBuilder.bad_request("参数验证失败")
        
        # 获取行业统计数据
        industry_stats = industry_service.get_industry_statistics(limit, min_jobs)
        
        # 按平均薪资排序
        sorted_industries = sorted(industry_stats, key=lambda x: x.avg_salary, reverse=True)
        
        # 构建薪资分析数据
        salary_analysis = {
            "type": "bar",
            "title": "各行业平均薪资分析",
            "subtitle": f"显示所有行业" if limit >= 1000 else f"显示前{limit}个行业",
            "x_axis": {
                "field": "avg_salary",
                "label": "平均薪资 (K)"
            },
            "y_axis": {
                "field": "industry",
                "label": "行业类型"
            },
            "data": [
                {
                    "industry": stat.industry,
                    "avg_salary": stat.avg_salary,
                    "job_count": stat.job_count,
                    "company_count": stat.company_count,
                    "percentage": stat.percentage
                }
                for stat in sorted_industries
            ],
            "summary": {
                "highest_salary": {
                    "industry": sorted_industries[0].industry if sorted_industries else None,
                    "avg_salary": sorted_industries[0].avg_salary if sorted_industries else 0
                },
                "lowest_salary": {
                    "industry": sorted_industries[-1].industry if sorted_industries else None,
                    "avg_salary": sorted_industries[-1].avg_salary if sorted_industries else 0
                },
                "overall_avg": round(sum(stat.avg_salary for stat in sorted_industries) / len(sorted_industries), 2) if sorted_industries else 0
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseBuilder.success("获取行业薪资分析数据成功", {"chart_config": salary_analysis})
        
    except Exception as e:
        logger.error(f"获取行业薪资分析数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/industry/ranking/jobs', methods=['GET'])
def get_job_ranking():
    """获取职位综合排名柱状图数据"""
    try:
        # 获取职位排名数据（默认返回前5名）
        job_rankings = trend_service.get_job_ranking(top_n=5)
        
        # 转换为字典格式
        jobs_data = [
            {
                "job_title": job.job_title,
                "records_count_norm": job.records_count_norm,
                "education_rank": job.education_rank,
                "experience_rank": job.experience_rank,
                "composite_score": job.composite_score
            }
            for job in job_rankings
        ]
        
        return ResponseBuilder.success("获取职位综合排名数据成功", {"jobs": jobs_data})
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        return ResponseBuilder.not_found(f"数据文件不存在: {str(e)}")
    except Exception as e:
        logger.error(f"获取职位综合排名数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@industry_bp.route('/industry/trend/rose', methods=['GET'])
def get_industry_trend_rose():
    """获取行业双环嵌套玫瑰图数据"""
    try:
        # 获取行业趋势数据
        industry_trends = trend_service.get_industry_trend_rose()
        
        # 转换为字典格式
        industries_data = [
            {
                "company_type": industry.company_type,
                "industry_name": industry.industry_name,  # 添加可读的行业名称
                "national_job_count": industry.national_job_count,
                "avg_median_salary": industry.avg_median_salary,
                "avg_experience_rank": industry.avg_experience_rank,
                "avg_education_rank": industry.avg_education_rank
            }
            for industry in industry_trends
        ]
        
        return ResponseBuilder.success("获取行业趋势玫瑰图数据成功", {"industries": industries_data})
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        return ResponseBuilder.not_found(f"数据文件不存在: {str(e)}")
    except Exception as e:
        logger.error(f"获取行业趋势玫瑰图数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})
