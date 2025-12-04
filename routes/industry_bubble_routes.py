#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多维度行业气泡图相关路由
用于展示“全国规模 × 区位商 × 城市等级”的多维度气泡图
"""

import logging
from flask import Blueprint, request

from database.Q3 import DatabaseManager
from services.industry_bubble_service import IndustryBubbleService
from utils.response import ResponseBuilder

logger = logging.getLogger(__name__)

industry_bubble_bp = Blueprint("industry_bubble", __name__, url_prefix="/api")

db_manager = DatabaseManager("default")
industry_bubble_service = IndustryBubbleService(db_manager)


@industry_bubble_bp.route("/charts/bubble/industry-location", methods=["GET"])
def get_industry_location_bubble():
    """
    获取多维度行业气泡图数据

    请求参数：
        city_tiers: string[]，可多选，例如 ?city_tiers=first_tier&city_tiers=second_tier
        industry_filter: string，用于高亮特定行业
    """
    try:
        # 处理城市等级参数，支持多选
        city_tiers = request.args.getlist("city_tiers")
        # 如果前端以逗号拼接传递，也做一下拆分兼容
        if len(city_tiers) == 1 and "," in city_tiers[0]:
            city_tiers = [item.strip() for item in city_tiers[0].split(",") if item.strip()]

        industry_filter = request.args.get("industry_filter")

        bubble_payload = industry_bubble_service.get_industry_location_bubble(
            city_tiers=city_tiers,
            industry_filter=industry_filter,
        )

        return ResponseBuilder.success("获取多维度行业气泡图数据成功", bubble_payload)
    except ValueError as validation_error:
        logger.warning(f"获取多维度行业气泡图数据参数错误: {validation_error}")
        return ResponseBuilder.bad_request(str(validation_error))
    except Exception as e:
        logger.error(f"获取多维度行业气泡图数据失败: {e}", exc_info=True)
        return ResponseBuilder.internal_error(
            "服务器内部错误",
            {"type": "INTERNAL_ERROR", "details": str(e)},
        )


