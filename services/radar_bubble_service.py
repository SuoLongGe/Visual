#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雷达气泡图业务逻辑服务
用于处理多维雷达气泡图相关的业务逻辑，包括香农熵计算
"""
import logging
import math
from typing import List, Dict, Any
from collections import Counter

from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class RadarBubbleService:
    """雷达气泡图业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def calculate_shannon_entropy(self, job_titles: str) -> float:
        """
        计算香农熵
        公式: H(X) = -Σ p(x) log₂ p(x)
        
        Args:
            job_titles: 职位名称字符串，用逗号分隔
        
        Returns:
            香农熵值
        """
        if not job_titles:
            return 0.0
        
        # 分割职位名称
        titles = [title.strip() for title in job_titles.split(',') if title.strip()]
        
        if len(titles) == 0:
            return 0.0
        
        # 计算每个职位类型的频率
        title_counts = Counter(titles)
        total = len(titles)
        
        # 计算香农熵
        entropy = 0.0
        for count in title_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def get_radar_bubble_statistics(self) -> Dict[str, Any]:
        """
        获取雷达气泡图统计数据
        返回按经验等级分组的数据，每个经验等级包含各城市的气泡信息
        
        Returns:
            包含经验等级、城市、岗位数量、平均薪资、香农熵等信息的字典
        """
        try:
            # 获取原始数据
            raw_data = self.db_manager.get_radar_bubble_data()
            
            if not raw_data:
                return {
                    'experiences': [],
                    'data': []
                }
            
            # 按经验等级分组
            experience_groups: Dict[str, List[Dict]] = {}
            all_experiences = set()
            
            for row in raw_data:
                experience, city, job_count, avg_salary, job_titles = row
                
                if not experience or not city:
                    continue
                
                all_experiences.add(experience)
                
                # 计算香农熵
                shannon_entropy = self.calculate_shannon_entropy(job_titles if job_titles else '')
                
                # 处理薪资（如果为None，使用0）
                avg_salary_value = float(avg_salary) if avg_salary else 0.0
                job_count_value = int(job_count) if job_count else 0
                
                city_data = {
                    'city': city,
                    'job_count': job_count_value,
                    'avg_salary': round(avg_salary_value, 2),
                    'shannon_entropy': round(shannon_entropy, 4),
                    'job_titles': job_titles if job_titles else ''
                }
                
                if experience not in experience_groups:
                    experience_groups[experience] = []
                
                experience_groups[experience].append(city_data)
            
            # 对每个经验等级的城市数据按岗位数量排序（取前N个，避免图表过于拥挤）
            max_cities_per_experience = 15  # 每个经验等级最多显示15个城市
            
            result_data = []
            sorted_experiences = sorted(list(all_experiences))
            
            for experience in sorted_experiences:
                cities = experience_groups[experience]
                # 按岗位数量降序排序，取前N个
                cities_sorted = sorted(cities, key=lambda x: x['job_count'], reverse=True)[:max_cities_per_experience]
                
                result_data.append({
                    'experience': experience,
                    'cities': cities_sorted,
                    'total_cities': len(experience_groups[experience]),
                    'total_jobs': sum(c['job_count'] for c in cities_sorted)
                })
            
            return {
                'experiences': sorted_experiences,
                'data': result_data
            }
            
        except Exception as e:
            logger.error(f"获取雷达气泡图数据失败: {e}", exc_info=True)
            raise
    
    def get_parallel_coordinates_statistics(self) -> Dict[str, Any]:
        """
        获取平行坐标图统计数据
        返回包含所有维度的扁平数据，用于绘制平行坐标图
        
        Returns:
            包含城市、经验、学历、薪资、公司类型、岗位多样性等信息的列表
        """
        try:
            # 获取原始数据
            raw_data = self.db_manager.get_parallel_coordinates_data()
            
            if not raw_data:
                return {
                    'data': []
                }
            
            # 转换为字典格式
            result_data = []
            for row in raw_data:
                city, experience, education, company_type, avg_salary, avg_shannon_entropy, job_count = row
                
                if not city or not experience:
                    continue
                
                # 直接使用数据库中的香农熵值（已聚合为平均值）
                shannon_entropy = float(avg_shannon_entropy) if avg_shannon_entropy else 0.0
                
                # 处理数据
                avg_salary_value = float(avg_salary) if avg_salary else 0.0
                job_count_value = int(job_count) if job_count else 0
                
                result_data.append({
                    'city': city,
                    'experience': experience,
                    'education': education if education else '未知',
                    'company_type': company_type if company_type else '未知',
                    'salary': round(avg_salary_value, 2),
                    'entropy': round(shannon_entropy, 4),
                    'job_count': job_count_value
                })
            
            return {
                'data': result_data
            }
            
        except Exception as e:
            logger.error(f"获取平行坐标图数据失败: {e}", exc_info=True)
            raise

