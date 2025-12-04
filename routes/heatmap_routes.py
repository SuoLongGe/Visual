#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矩形热力图相关路由
"""

import logging
from flask import Blueprint, request

from services.heatmap_service import HeatmapService
from utils.response import ResponseBuilder
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)

heatmap_bp = Blueprint('heatmap', __name__, url_prefix='/api')

db_manager = DatabaseManager('default')
heatmap_service = HeatmapService(db_manager)


@heatmap_bp.route('/charts/heatmap/city-tier', methods=['GET'])
def get_city_tier_heatmap():
    """获取城市等级矩形热力图数据"""
    try:
        tier = request.args.get('tier')
        dimension_y = request.args.get('dimension_y', 'company_type')
        metric = request.args.get('metric', 'job_count')

        if not tier:
            return ResponseBuilder.bad_request("缺少必需参数: tier")

        heatmap_payload = heatmap_service.get_city_tier_heatmap(tier, dimension_y, metric)
        if not heatmap_payload:
            return ResponseBuilder.not_found("未找到对应城市等级的数据")

        message = f"获取{heatmap_payload.get('tier_name', '')}热力图数据成功"
        return ResponseBuilder.success(message, heatmap_payload)
    except ValueError as validation_error:
        return ResponseBuilder.bad_request(str(validation_error))
    except Exception as e:
        logger.error(f"获取城市等级热力图数据失败: {e}")
        return ResponseBuilder.internal_error(
            "服务器内部错误",
            {"type": "INTERNAL_ERROR", "details": str(e)},
        )



