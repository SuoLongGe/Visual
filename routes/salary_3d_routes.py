#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三维柱状图相关路由
用于展示经验-学历-薪资组合的三维柱状图
"""

import logging
from flask import Blueprint, request
from database import DatabaseManager
from utils.response import ResponseBuilder
from services.salary_3d_service import Salary3DService

logger = logging.getLogger(__name__)

# 创建蓝图
salary_3d_bp = Blueprint('salary_3d', __name__, url_prefix='/api')

# 初始化数据库管理器和服务
db_manager = DatabaseManager('default')
salary_3d_service = Salary3DService(db_manager)


@salary_3d_bp.route('/charts/3d/experience-education-salary', methods=['GET'])
def get_experience_education_salary_3d():
    """获取经验-学历-薪资三维柱状图数据"""
    try:
        # 获取原始数据
        results = db_manager.get_experience_education_salary()
        
        # 获取所有唯一的经验和学历值
        experience_set = set()
        education_set = set()
        data_map = {}
        
        for row in results:
            experience, education, avg_salary, job_count = row
            experience_set.add(experience)
            education_set.add(education)
            key = f"{experience}_{education}"
            data_map[key] = {
                'experience': experience,
                'education': education,
                'avg_salary': round(float(avg_salary), 2) if avg_salary else 0,
                'job_count': job_count
            }
        
        # 排序经验和学历列表
        experience_list = sorted(list(experience_set))
        education_list = sorted(list(education_set))
        
        # 构建三维数据数组 [x, y, z]
        # x: 经验索引, y: 学历索引, z: 平均薪资
        data_3d = []
        for exp_idx, exp in enumerate(experience_list):
            for edu_idx, edu in enumerate(education_list):
                key = f"{exp}_{edu}"
                if key in data_map:
                    avg_salary = data_map[key]['avg_salary']
                    data_3d.append([exp_idx, edu_idx, avg_salary])
                else:
                    # 如果没有数据，设置为0
                    data_3d.append([exp_idx, edu_idx, 0])
        
        # 构建返回数据
        chart_data = {
            'experiences': experience_list,
            'educations': education_list,
            'data_3d': data_3d,
            'data_detail': [
                {
                    'experience': item['experience'],
                    'education': item['education'],
                    'avg_salary': item['avg_salary'],
                    'job_count': item['job_count']
                }
                for item in data_map.values()
            ]
        }
        
        return ResponseBuilder.success("获取三维柱状图数据成功", chart_data)
        
    except Exception as e:
        logger.error(f"获取三维柱状图数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


@salary_3d_bp.route('/charts/boxplot/salary-distribution', methods=['GET'])
def get_boxplot_data():
    """获取箱线图数据"""
    try:
        # 获取查询参数
        experience = request.args.get('experience', None)
        education = request.args.get('education', None)
        city = request.args.get('city', None)
        company_type = request.args.get('company_type', None)
        
        # 参数验证：至少需要指定experience和education
        if not experience or not education:
            return ResponseBuilder.bad_request(
                "参数错误",
                {"message": "必须指定experience（工作经验）和education（学历）参数"}
            )
        
        # 获取箱线图统计数据
        boxplot_data = salary_3d_service.get_boxplot_statistics(
            experience=experience,
            education=education,
            city=city,
            company_type=company_type
        )
        
        return ResponseBuilder.success("获取箱线图数据成功", boxplot_data)
        
    except Exception as e:
        logger.error(f"获取箱线图数据失败: {e}", exc_info=True)
        return ResponseBuilder.internal_error("服务器内部错误", {"type": "INTERNAL_ERROR", "details": str(e)})


