#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地域招聘画像与相似地域分析路由
"""

import logging
from flask import Blueprint, request

from services.region_profile_service import RegionProfileService
from utils.response import ResponseBuilder

logger = logging.getLogger(__name__)

region_profile_bp = Blueprint("region_profile", __name__, url_prefix="/api")

service = RegionProfileService()


@region_profile_bp.route("/charts/region/profile", methods=["GET"])
def get_region_profile():
    """
    获取指定城市的地域招聘画像与相似地域信息

    查询参数:
    - city: 城市编码（必填，与热力图 X 轴编码一致）
    - top_similar: 返回相似城市个数（默认 5）
    """
    try:
        city = request.args.get("city")
        top_similar = request.args.get("top_similar", default=5, type=int)

        if not city:
            return ResponseBuilder.bad_request("缺少必需参数: city")

        profile = service.get_region_profile(city, top_similar=top_similar)
        if not profile:
            return ResponseBuilder.not_found(f"未找到城市 {city} 的地域画像数据")

        return ResponseBuilder.success(f"获取城市 {city} 地域招聘画像成功", profile)
    except Exception as e:
        logger.error(f"获取地域招聘画像失败: {e}", exc_info=True)
        return ResponseBuilder.internal_error(
            "服务器内部错误",
            {"type": "INTERNAL_ERROR", "details": str(e)},
        )


