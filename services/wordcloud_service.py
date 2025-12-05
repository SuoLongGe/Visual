#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市行业词云服务
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CityWordcloudService:
    """
    从预处理的 JSON 文件中读取城市行业词云数据
    数据文件: dataset/dataset/第四题/city_wordcloud_data.json
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            # 默认路径：相对于项目根目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # services/ -> 项目根目录
            project_root = os.path.dirname(base_dir)
            data_path = os.path.join(
                project_root, "dataset", "dataset", "第四题", "city_wordcloud_data.json"
            )
        self.data_path = data_path
        self._data: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def _load_data(self) -> None:
        """懒加载 JSON 数据"""
        if self._data is not None:
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"城市词云数据已加载，城市数量: {len(self._data)}")
        except FileNotFoundError:
            logger.error(f"城市词云数据文件不存在: {self.data_path}")
            self._data = {}
        except Exception as e:
            logger.error(f"加载城市词云数据失败: {e}", exc_info=True)
            self._data = {}

    def get_city_wordcloud(self, city_code: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        获取指定城市的行业词云数据

        :param city_code: 城市编码（如 A050、B170 等，与热力图中的 x 轴编码一致）
        :param top_n: 返回前 N 个词
        """
        if not city_code:
            return []

        self._load_data()
        if not self._data:
            return []

        items = self._data.get(city_code)
        if not items:
            logger.warning(f"未找到城市 {city_code} 的词云数据")
            return []

        # 按 value 从大到小排序，截取前 top_n
        sorted_items = sorted(
            items,
            key=lambda x: float(x.get("value", 0) or 0),
            reverse=True,
        )
        return sorted_items[: top_n if top_n > 0 else None]


