#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业统计相关路由
"""

import logging
from flask import Blueprint
from database.Q3 import DatabaseManager
from utils.response import ResponseBuilder

logger = logging.getLogger(__name__)

# 创建蓝图
industry_stats_bp = Blueprint('industry_stats', __name__, url_prefix='/api')

# 初始化数据库管理器
db_manager = DatabaseManager('default')


@industry_stats_bp.route('/industry-stats/national', methods=['GET'])
def get_national_industry_stats():
    """获取全国行业统计数据"""
    try:
        query = """
            SELECT 
                company_type,
                national_job_count,
                avg_median_salary,
                avg_experience_rank,
                avg_education_rank
            FROM national_industry_stats
            WHERE company_type IS NOT NULL
            ORDER BY national_job_count DESC
        """
        
        results = db_manager.execute_query(query)
        
        industry_stats = []
        for row in results:
            industry_stats.append({
                "company_type": row[0],
                "job_count": row[1],
                "avg_salary": round(float(row[2]), 2) if row[2] else 0,
                "avg_experience_rank": round(float(row[3]), 2) if row[3] else 0,
                "avg_education_rank": round(float(row[4]), 2) if row[4] else 0
            })
        
        return ResponseBuilder.success("获取行业统计数据成功", {
            "total_industries": len(industry_stats),
            "data": industry_stats
        })
        
    except Exception as e:
        logger.error(f"获取行业统计数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


