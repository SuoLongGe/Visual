#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市行业词云相关路由（Q4）
"""

import logging
from flask import Blueprint, request

from services.wordcloud_service import CityWordcloudService
from utils.response import ResponseBuilder

logger = logging.getLogger(__name__)

wordcloud_bp = Blueprint("wordcloud", __name__, url_prefix="/api")

# 初始化服务（数据为预处理 JSON，不依赖数据库）
city_wordcloud_service = CityWordcloudService()


@wordcloud_bp.route("/charts/wordcloud/city", methods=["GET"])
def get_city_wordcloud():
    """
    获取指定城市的行业分布词云数据

    查询参数:
    - city: 城市编码（必填，与热力图 x 轴编码一致，如 A050）
    - top_n: 返回前 N 个词，默认 10
    """
    try:
        city = request.args.get("city")
        top_n = request.args.get("top_n", default=10, type=int)

        if not city:
            return ResponseBuilder.bad_request("缺少必需参数: city")

        words = city_wordcloud_service.get_city_wordcloud(city, top_n=top_n)
        if not words:
            return ResponseBuilder.not_found(f"未找到城市 {city} 的词云数据")

        payload = {
            "city": city,
            "top_n": len(words),
            "words": words,
        }

        return ResponseBuilder.success(f"获取城市 {city} 词云数据成功", payload)
    except Exception as e:
        logger.error(f"获取城市词云数据失败: {e}", exc_info=True)
        return ResponseBuilder.internal_error(
            "服务器内部错误",
            {"type": "INTERNAL_ERROR", "details": str(e)},
        )


