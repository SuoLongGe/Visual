#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职位画像分析相关路由
"""

import logging
from flask import Blueprint, request
from services.position_service import PositionService
from utils.response import ResponseBuilder
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)

# 创建蓝图
position_bp = Blueprint('position', __name__, url_prefix='/api/positions')

# 初始化服务
db_manager = DatabaseManager('default')
position_service = PositionService(db_manager)


@position_bp.route('/parallel', methods=['GET'])
def get_parallel_coordinates():
    """
    获取平行坐标图数据
    参数:
    - job_titles: 职位名称数组，最多3个职位（通过query参数传递，如?job_titles=xxx&job_titles=yyy）
    """
    try:
        # 获取所有job_titles参数（Flask支持同名参数）
        job_titles = request.args.getlist('job_titles')
        
        if not job_titles or len(job_titles) == 0:
            return ResponseBuilder.bad_request("缺少参数: job_titles")
        
        if len(job_titles) > 3:
            return ResponseBuilder.bad_request("最多只能选择3个职位")
        
        # 获取数据
        data = position_service.get_parallel_coordinates_data(job_titles)
        
        return ResponseBuilder.success("获取平行坐标数据成功", data)
        
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        return ResponseBuilder.bad_request(str(e))
    except Exception as e:
        logger.error(f"获取平行坐标数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {
            "type": "INTERNAL_ERROR",
            "details": str(e)
        })


@position_bp.route('/nested_bar', methods=['GET'])
def get_nested_bar():
    """
    获取多维度嵌套柱状图数据
    参数:
    - job_titles: 职位名称数组，最多3个职位（必填）
    - detail_job: 详细分析的单个职位名称（可选）
    """
    try:
        # 获取参数
        job_titles = request.args.getlist('job_titles')
        detail_job = request.args.get('detail_job', None)
        
        # 验证job_titles参数
        if not job_titles or len(job_titles) == 0:
            return ResponseBuilder.bad_request("缺少参数: job_titles")
        
        if len(job_titles) > 3:
            return ResponseBuilder.bad_request("最多只能选择3个职位")
        
        # 获取数据
        data = position_service.get_nested_bar_data(job_titles, detail_job)
        
        return ResponseBuilder.success("获取嵌套柱状图数据成功", data)
        
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        return ResponseBuilder.bad_request(str(e))
    except Exception as e:
        logger.error(f"获取嵌套柱状图数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {
            "type": "INTERNAL_ERROR",
            "details": str(e)
        })


@position_bp.route('/sankey', methods=['GET'])
def get_sankey():
    """
    获取桑基图数据
    参数:
    - mode: 显示模式，'all'(整体)或'compare'(对比)，默认'all'
    - job_titles: 对比模式下指定的职位名称数组（可选）
    - dimensions: 选择的维度数组，可选值：skill_level, industry_spread, market_demand（可选，默认全部）
    """
    try:
        # 获取参数
        mode = request.args.get('mode', 'all')
        job_titles = request.args.getlist('job_titles')
        dimensions = request.args.getlist('dimensions')
        
        # 验证mode参数
        if mode not in ['all', 'compare']:
            return ResponseBuilder.bad_request("mode参数必须是'all'或'compare'")
        
        # 对比模式下验证job_titles
        if mode == 'compare' and (not job_titles or len(job_titles) == 0):
            return ResponseBuilder.bad_request("对比模式下必须提供job_titles参数")
        
        # 验证dimensions参数
        valid_dimensions = ['skill_level', 'industry_spread', 'market_demand']
        if dimensions:
            for dim in dimensions:
                if dim not in valid_dimensions:
                    return ResponseBuilder.bad_request(f"无效的维度: {dim}，可选值: {', '.join(valid_dimensions)}")
            if len(dimensions) < 2:
                return ResponseBuilder.bad_request("至少需要选择2个维度")
        else:
            # 默认使用全部维度
            dimensions = valid_dimensions
        
        # 获取数据
        data = position_service.get_sankey_data(mode, job_titles if job_titles else None, dimensions)
        
        return ResponseBuilder.success("获取桑基图数据成功", data)
        
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        return ResponseBuilder.bad_request(str(e))
    except Exception as e:
        logger.error(f"获取桑基图数据失败: {e}")
        return ResponseBuilder.internal_error("服务器内部错误", {
            "type": "INTERNAL_ERROR",
            "details": str(e)
        })

