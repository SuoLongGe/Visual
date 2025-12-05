#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热力图业务逻辑服务
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List

from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class HeatmapService:
    """城市等级矩形热力图服务"""

    TIER_NAME_MAP: Dict[str, str] = {
        "first_tier": "一线城市",
        "second_tier": "二线城市",
        "third_tier": "三线城市",
        "other": "其他城市",
    }

    TIER_VALUE_MAP: Dict[str, str] = {
        "first_tier": "一线",
        "second_tier": "二线",
        "third_tier": "三线",
        "other": "其他",
    }

    METRIC_CONFIG: Dict[str, Dict[str, str]] = {
        "job_count": {"field": "job_count", "label": "职位数量"},
        "industry_ratio": {"field": "industry_ratio", "label": "行业占比"},
        "location_quotient": {"field": "location_quotient", "label": "区位商"},
    }

    DIMENSION_CONFIG: Dict[str, Dict[str, str]] = {
        "company_type": {"field": "company_type", "label": "公司类型"},
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_city_tier_heatmap(
        self,
        tier: str,
        dimension_y: str = "company_type",
        metric: str = "job_count",
    ) -> Dict[str, Any]:
        """获取城市等级矩形热力图数据"""
        try:
            tier_key = self._normalize_tier(tier)
            dimension_key = self._normalize_dimension(dimension_y)
            metric_key = self._normalize_metric(metric)

            db_tier_value = self.TIER_VALUE_MAP[tier_key]
            records = self.db_manager.get_city_tier_heatmap(db_tier_value)
            if not records:
                logger.warning(f"未找到城市等级 {tier_key} ({db_tier_value}) 的数据")
                return {}
        except Exception as e:
            logger.error(f"获取热力图数据失败 - tier: {tier}, dimension_y: {dimension_y}, metric: {metric}, 错误: {e}")
            raise

        try:
            dimension_field = self.DIMENSION_CONFIG[dimension_key]["field"]
            metric_field = self.METRIC_CONFIG[metric_key]["field"]
            metric_label = self.METRIC_CONFIG[metric_key]["label"]
            tier_name = self.TIER_NAME_MAP[tier_key]

            x_axis: List[str] = []
            y_axis: List[str] = []
            heatmap_data: List[Dict[str, Any]] = []

            for row in records:
                try:
                    city_label = row.get("city")
                    if city_label and city_label not in x_axis:
                        x_axis.append(city_label)

                    y_label = row.get(dimension_field)
                    if y_label and y_label not in y_axis:
                        y_axis.append(y_label)

                    metric_value = self._to_float(row.get(metric_field))
                    heatmap_data.append(
                        {
                            "x": city_label,
                            "y": y_label,
                            "value": metric_value,
                            "count": int(row.get("job_count", 0)) if row.get("job_count") is not None else 0,
                            "detail_info": {
                                "industry_ratio": self._to_float(row.get("industry_ratio")),
                                "location_quotient": self._to_float(row.get("location_quotient")),
                                "avg_education_rank": self._to_float(row.get("avg_education_rank")),
                                "avg_experience_rank": self._to_float(row.get("avg_experience_rank")),
                                "company_count_in_city": int(row.get("company_count_in_city", 0)) if row.get("company_count_in_city") is not None else 0,
                                "national_job_count": int(row.get("national_job_count", 0)) if row.get("national_job_count") is not None else 0,
                            },
                        }
                    )
                except Exception as row_error:
                    logger.warning(f"处理数据行失败: {row}, 错误: {row_error}")
                    continue

            response = {
                "tier": tier_key,
                "tier_name": tier_name,
                "city_count": len(x_axis),
                "dimensions": {
                    "x_axis": x_axis,
                    "y_axis": y_axis,
                },
                "heatmap_data": heatmap_data,
                "metric": metric_key,
                "title": f"{tier_name}-{self.DIMENSION_CONFIG[dimension_key]['label']}{metric_label}热力图",
            }

            return response
        except Exception as e:
            logger.error(f"构建热力图响应数据失败 - tier: {tier_key}, 错误: {e}", exc_info=True)
            raise

    def _normalize_tier(self, tier: str) -> str:
        if not tier:
            raise ValueError("缺少必需参数: tier")
        tier_key = tier.strip()
        # 允许传入英文键或中文值
        if tier_key in self.TIER_NAME_MAP:
            return tier_key
        for key, label in self.TIER_VALUE_MAP.items():
            if tier_key == label:
                return key
        allowed = ", ".join(
            list(self.TIER_NAME_MAP.keys()) + list(self.TIER_VALUE_MAP.values())
        )
        raise ValueError(f"tier参数错误，可选值：{allowed}")

    def _normalize_metric(self, metric: str) -> str:
        metric_key = (metric or "job_count").strip()
        if metric_key not in self.METRIC_CONFIG:
            allowed = ", ".join(self.METRIC_CONFIG.keys())
            raise ValueError(f"metric参数错误，可选值：{allowed}")
        return metric_key

    def _normalize_dimension(self, dimension: str) -> str:
        dimension_key = (dimension or "company_type").strip()
        if dimension_key not in self.DIMENSION_CONFIG:
            allowed = ", ".join(self.DIMENSION_CONFIG.keys())
            raise ValueError(f"dimension_y参数错误，可选值：{allowed}")
        return dimension_key

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

