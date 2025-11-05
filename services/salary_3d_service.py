#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三维薪资分析业务逻辑服务
用于处理三维柱状图和箱线图相关的业务逻辑
"""
import logging
from typing import List, Dict, Any, Optional
import statistics

from database import DatabaseManager

logger = logging.getLogger(__name__)


class Salary3DService:
    """三维薪资分析业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_boxplot_statistics(self, experience: str = None, education: str = None,
                               city: str = None, company_type: str = None) -> Dict[str, Any]:
        """
        获取箱线图统计数据
        返回按城市和公司类型分组的薪资分布统计量
        
        Args:
            experience: 工作经验筛选条件
            education: 学历筛选条件
            city: 城市筛选条件
            company_type: 公司类型筛选条件
        
        Returns:
            包含城市和公司类型分组统计数据的字典
        """
        try:
            # 获取原始数据
            raw_data = self.db_manager.get_boxplot_data(
                experience=experience,
                education=education,
                city=city,
                company_type=company_type
            )
            
            if not raw_data:
                return {
                    'city_data': [],
                    'company_type_data': [],
                    'cities': [],
                    'company_types': []
                }
            
            # 按城市分组
            city_salaries = {}
            company_type_salaries = {}
            cities_set = set()
            company_types_set = set()
            
            for row in raw_data:
                city_val, company_type_val, salary = row
                if city_val and company_type_val and salary:
                    # 按城市分组
                    if city_val not in city_salaries:
                        city_salaries[city_val] = []
                    city_salaries[city_val].append(float(salary))
                    cities_set.add(city_val)
                    
                    # 按公司类型分组
                    if company_type_val not in company_type_salaries:
                        company_type_salaries[company_type_val] = []
                    company_type_salaries[company_type_val].append(float(salary))
                    company_types_set.add(company_type_val)
            
            # 计算统计量：按城市
            city_data = []
            for city_name, salaries in sorted(city_salaries.items()):
                if len(salaries) > 0:
                    stats = self._calculate_statistics(salaries)
                    city_data.append({
                        'name': city_name,
                        'stats': stats,
                        'count': len(salaries)
                    })
            
            # 计算统计量：按公司类型
            company_type_data = []
            for company_type_name, salaries in sorted(company_type_salaries.items()):
                if len(salaries) > 0:
                    stats = self._calculate_statistics(salaries)
                    company_type_data.append({
                        'name': company_type_name,
                        'stats': stats,
                        'count': len(salaries)
                    })
            
            return {
                'city_data': city_data,
                'company_type_data': company_type_data,
                'cities': sorted(list(cities_set)),
                'company_types': sorted(list(company_types_set))
            }
            
        except Exception as e:
            logger.error(f"获取箱线图统计数据失败: {e}", exc_info=True)
            raise
    
    def _calculate_statistics(self, salaries: List[float]) -> Dict[str, float]:
        """
        计算箱线图统计量
        包括：最小值、下四分位数(Q1)、中位数(median)、上四分位数(Q3)、最大值
        
        Args:
            salaries: 薪资列表
        
        Returns:
            包含统计量的字典
        """
        if not salaries or len(salaries) == 0:
            return {
                'min': 0,
                'q1': 0,
                'median': 0,
                'q3': 0,
                'max': 0,
                'count': 0
            }
        
        # 排序
        sorted_salaries = sorted(salaries)
        n = len(sorted_salaries)
        
        # 最小值
        min_val = sorted_salaries[0]
        
        # 最大值
        max_val = sorted_salaries[-1]
        
        # 中位数
        if n % 2 == 0:
            median = (sorted_salaries[n // 2 - 1] + sorted_salaries[n // 2]) / 2
        else:
            median = sorted_salaries[n // 2]
        
        # 下四分位数 (Q1) - 使用标准方法
        # Q1位置 = (n + 1) * 0.25
        q1_pos = (n + 1) * 0.25
        if q1_pos == int(q1_pos):
            # 整数位置
            q1 = sorted_salaries[int(q1_pos) - 1]
        else:
            # 非整数位置，使用线性插值
            lower_idx = int(q1_pos) - 1
            upper_idx = int(q1_pos)
            if upper_idx >= n:
                q1 = sorted_salaries[lower_idx]
            else:
                weight = q1_pos - int(q1_pos)
                q1 = sorted_salaries[lower_idx] * (1 - weight) + sorted_salaries[upper_idx] * weight
        
        # 上四分位数 (Q3) - 使用标准方法
        # Q3位置 = (n + 1) * 0.75
        q3_pos = (n + 1) * 0.75
        if q3_pos == int(q3_pos):
            # 整数位置
            q3 = sorted_salaries[int(q3_pos) - 1]
        else:
            # 非整数位置，使用线性插值
            lower_idx = int(q3_pos) - 1
            upper_idx = int(q3_pos)
            if upper_idx >= n:
                q3 = sorted_salaries[lower_idx]
            else:
                weight = q3_pos - int(q3_pos)
                q3 = sorted_salaries[lower_idx] * (1 - weight) + sorted_salaries[upper_idx] * weight
        
        # 尝试使用statistics模块的更精确方法（Python 3.8+）
        try:
            quantiles = statistics.quantiles(sorted_salaries, n=4, method='inclusive')
            if len(quantiles) >= 3:
                q1 = quantiles[0]
                q3 = quantiles[2]
        except:
            # 如果statistics.quantiles不可用或失败，使用上面的计算方法
            pass
        
        return {
            'min': round(float(min_val), 2),
            'q1': round(float(q1), 2),
            'median': round(float(median), 2),
            'q3': round(float(q3), 2),
            'max': round(float(max_val), 2),
            'count': n
        }

