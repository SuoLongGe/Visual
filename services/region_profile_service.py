#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地域招聘画像与相似地域分析服务（基于城市行业词云数据）
"""

import json
import logging
import math
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RegionProfileService:
    """基于 city_wordcloud_data.json 计算城市画像与相似地域"""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(base_dir)
            data_path = os.path.join(
                project_root, "dataset", "dataset", "第四题", "city_wordcloud_data.json"
            )
        self.data_path = data_path
        self._data: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def _load_data(self) -> None:
        if self._data is not None:
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"地域画像数据已加载，城市数量: {len(self._data)}")
        except Exception as e:
            logger.error(f"加载地域画像数据失败: {e}", exc_info=True)
            self._data = {}

    def _build_vector(self, city_code: str) -> Tuple[Dict[str, float], float]:
        """
        为城市构建 (company_type -> value) 向量，并返回向量长度
        """
        self._load_data()
        items = (self._data or {}).get(city_code, [])
        vec: Dict[str, float] = {}
        for item in items:
            name = item.get("name")
            value = float(item.get("value", 0) or 0)
            if not name:
                continue
            vec[name] = value
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return vec, norm

    def _cosine_similarity(
        self,
        base_vec: Dict[str, float],
        base_norm: float,
        other_vec: Dict[str, float],
        other_norm: float,
    ) -> float:
        if not base_vec or not other_vec:
            return 0.0
        dot = 0.0
        for key, v in base_vec.items():
            if key in other_vec:
                dot += v * other_vec[key]
        return float(dot / (base_norm * other_norm)) if base_norm and other_norm else 0.0

    def get_region_profile(self, city_code: str, top_similar: int = 5) -> Dict[str, Any]:
        """
        获取城市的地域招聘画像与相似地域列表

        返回字段:
        - city: 城市编码
        - top_industries: 前10个行业分布（直接复用词云数据）
        - similar_regions: 按相似度排序的城市列表
        """
        self._load_data()
        if not self._data:
            return {}

        if city_code not in self._data:
            logger.warning(f"未找到城市 {city_code} 的地域画像数据")
            return {}

        base_vec, base_norm = self._build_vector(city_code)

        similarities: List[Tuple[str, float]] = []
        for other_city in self._data.keys():
            if other_city == city_code:
                continue
            other_vec, other_norm = self._build_vector(other_city)
            sim = self._cosine_similarity(base_vec, base_norm, other_vec, other_norm)
            if sim > 0:
                similarities.append((other_city, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_sim = similarities[: top_similar if top_similar > 0 else None]

        return {
            "city": city_code,
            "top_industries": self._data.get(city_code, [])[:10],
            "similar_regions": [
                {"city": c, "similarity": float(f"{s:.4f}")}
                for c, s in top_sim
            ],
        }


