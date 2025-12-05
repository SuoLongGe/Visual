#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多维度行业气泡图业务逻辑服务
基于 city_type_statistics 表，构建“全国规模 × 区位商 × 城市等级”的气泡图数据
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class IndustryBubbleService:
    """多维度行业气泡图服务"""

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

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_industry_location_bubble(
        self,
        city_tiers: Optional[List[str]] = None,
        industry_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取多维度行业气泡图数据

        Args:
            city_tiers: 前端传入的城市等级英文键列表（first_tier/second_tier/...），为空则默认全选
            industry_filter: 行业筛选/高亮标签，对应 industry_label（目前等于 company_type）

        Returns:
            {
              "national_total_jobs": int,
              "bubble_data": [...],
              "industry_list": [...],
              "city_tier_list": [...]
            }
        """
        # 1. 归一化城市等级列表
        normalized_tiers = self._normalize_city_tiers(city_tiers)
        db_tier_values = [self.TIER_VALUE_MAP[tier] for tier in normalized_tiers]

        # 2. 查询 city_type_statistics 基础数据
        records = self.db_manager.get_city_type_statistics_by_tiers(db_tier_values)
        if not records:
            logger.warning(f"city_type_statistics 未找到城市等级 {normalized_tiers} 的数据")
            return {
                "national_total_jobs": 0,
                "bubble_data": [],
                "industry_list": [],
                "city_tier_list": [],
            }

        # 3. 计算全国总岗位数（基于 national_job_count 聚合）
        national_total_jobs = self._calculate_national_total_jobs(records)

        # 4. 组装 bubble_data
        bubble_data: List[Dict[str, Any]] = []
        industry_set: Set[str] = set()
        tier_set: Set[str] = set()

        for row in records:
            try:
                city = row.get("city")
                db_tier = row.get("city_tier")
                company_type = row.get("company_type")

                if not city or not db_tier or not company_type:
                    continue

                # 将数据库中的 city_tier 中文值映射为英文键，便于前端统一配色
                city_tier_key = self._db_tier_to_key(db_tier)
                if not city_tier_key:
                    continue

                job_count = self._to_int(row.get("job_count"))
                total_jobs_in_city = self._to_int(row.get("total_jobs_in_city"))
                national_job_count = self._to_int(row.get("national_job_count"))
                location_quotient = self._to_float(row.get("location_quotient"))
                industry_ratio = self._to_float(row.get("industry_ratio"))

                if national_total_jobs > 0 and national_job_count > 0:
                    national_job_percentage = national_job_count / national_total_jobs
                else:
                    national_job_percentage = 0.0

                industry_label = company_type  # 目前直接使用 company_type，后续可接字典表映射

                item: Dict[str, Any] = {
                    "city": city,
                    "city_tier": city_tier_key,
                    "industry_label": industry_label,
                    "national_job_count": national_job_count,
                    "national_job_percentage": national_job_percentage,
                    "location_quotient": location_quotient,
                    "local_job_count": job_count,
                    "city_total_jobs": total_jobs_in_city,
                    "industry_ratio": industry_ratio,
                    "is_in_ten": self._to_int(row.get("is_in_ten")),
                    "avg_education_rank": self._to_float(row.get("avg_education_rank")),
                    "avg_experience_rank": self._to_float(row.get("avg_experience_rank")),
                }

                # 可选：根据 industry_filter 标记高亮
                if industry_filter:
                    item["is_highlight"] = industry_label == industry_filter

                bubble_data.append(item)
                industry_set.add(industry_label)
                tier_set.add(city_tier_key)
            except Exception as row_error:
                logger.warning(f"处理多维气泡图数据行失败: {row}, 错误: {row_error}")
                continue

        response = {
            "national_total_jobs": national_total_jobs,
            "bubble_data": bubble_data,
            "industry_list": sorted(list(industry_set)),
            "city_tier_list": sorted(list(tier_set)),
        }
        return response

    def _normalize_city_tiers(self, city_tiers: Optional[List[str]]) -> List[str]:
        """
        归一化前端传入的城市等级列表，返回合法的英文键列表
        """
        if not city_tiers:
            # 默认全选
            return ["first_tier", "second_tier", "third_tier", "other"]

        result: List[str] = []
        for tier in city_tiers:
            if not tier:
                continue
            key = tier.strip()
            if key in self.TIER_VALUE_MAP:
                result.append(key)
            else:
                # 兼容直接传中文值（如 “一线”）
                for k, v in self.TIER_VALUE_MAP.items():
                    if key == v:
                        result.append(k)
                        break
        # 如果全部非法，则回退到全选
        if not result:
            return ["first_tier", "second_tier", "third_tier", "other"]
        return result

    @staticmethod
    def _calculate_national_total_jobs(records: List[Dict[str, Any]]) -> int:
        """
        基于 national_job_count 聚合计算全国总岗位数：
        对每个 company_type 取一份 national_job_count 再求和，避免重复累计
        """
        type_to_national: Dict[str, int] = {}
        for row in records:
            company_type = row.get("company_type")
            if not company_type:
                continue
            national_job_count = row.get("national_job_count")
            if isinstance(national_job_count, Decimal):
                national_job_count = int(national_job_count)
            try:
                national_value = int(national_job_count) if national_job_count is not None else 0
            except (TypeError, ValueError):
                national_value = 0
            # 如果同一 company_type 在不同城市重复出现 national_job_count，一般是相同的，取最大值更安全
            if company_type not in type_to_national:
                type_to_national[company_type] = national_value
            else:
                type_to_national[company_type] = max(type_to_national[company_type], national_value)

        return sum(type_to_national.values())

    def _db_tier_to_key(self, db_tier: str) -> Optional[str]:
        """
        将数据库中的 city_tier 中文值映射为前端使用的英文键
        """
        if not db_tier:
            return None
        value = db_tier.strip()
        for key, v in self.TIER_VALUE_MAP.items():
            if value == v:
                return key
        return None

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

    @staticmethod
    def _to_int(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, Decimal):
            return int(value)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


