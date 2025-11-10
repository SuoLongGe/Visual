#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1 职位差异度分析服务
"""

import logging
from typing import List, Dict, Any, Optional
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class Q1Service:
    """Q1 职位差异度分析服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_representative_cities(self, limit: int = 20) -> List[str]:
        """
        获取20个代表性城市
        按职位数量排序选取前20个城市
        """
        query = """
            SELECT city
            FROM data
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        
        results = self.db_manager.execute_query(query, (limit,))
        return [row[0] for row in results]
    
    def _parse_experience(self, experience: str) -> float:
        """
        将经验要求转换为数值
        例: "1-3年" -> 2, "3-5年" -> 4, "应届生" -> 0, "经验不限" -> 0
        """
        if not experience or experience in ['应届生', '经验不限', '在校生']:
            return 0
        
        # 处理"X年以上"的情况
        if '年以上' in experience:
            try:
                years = int(experience.replace('年以上', ''))
                return years + 2  # 例如："5年以上" -> 7
            except:
                return 0
        
        # 处理"X-Y年"的情况
        if '-' in experience and '年' in experience:
            try:
                parts = experience.replace('年', '').split('-')
                if len(parts) == 2:
                    start = int(parts[0])
                    end = int(parts[1])
                    return (start + end) / 2
            except:
                pass
        
        return 0
    
    def _parse_salary(self, salary: str) -> float:
        """
        计算薪资中位数/平均数
        例: "5-10K" -> 7.5, "10-15K" -> 12.5
        """
        if not salary:
            return 0
        
        try:
            # 移除"K"并按"-"分割
            salary = salary.upper().replace('K', '')
            if '-' in salary:
                parts = salary.split('-')
                if len(parts) == 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    return (low + high) / 2
        except:
            pass
        
        return 0
    
    def get_scatter_data(self, city: str) -> Dict[str, Any]:
        """
        获取指定城市的散点气泡图数据
        返回招聘人数前200的职位
        """
        query = """
            SELECT 
                job_title,
                experience,
                experience_rank,
                education,
                education_rank,
                salary,
                job_level,
                company_type,
                job_in_city_cnt,
                city_level
            FROM data
            WHERE city = %s
                AND is_in_top200 = 1
                AND experience IS NOT NULL
                AND salary IS NOT NULL
                AND job_level IS NOT NULL
                AND job_in_city_cnt IS NOT NULL
                AND experience_rank IS NOT NULL
                AND education_rank IS NOT NULL
            ORDER BY job_in_city_cnt DESC
            LIMIT 200
        """
        
        results = self.db_manager.execute_query(query, (city,))
        
        # 处理数据并计算归一化的气泡大小
        scatter_points = []
        recruit_counts = []
        
        for row in results:
            job_title = row[0]
            experience = row[1]
            experience_rank = row[2] if row[2] is not None else 5
            education = row[3]
            education_rank = row[4] if row[4] is not None else 5
            salary = row[5]
            job_level = row[6]
            company_type = row[7]
            recruit_count = row[8]
            city_level = row[9]
            
            salary_value = self._parse_salary(salary)
            recruit_counts.append(recruit_count)
            
            scatter_points.append({
                "job_title": job_title,
                "experience": experience,
                "experience_rank": experience_rank,
                "education": education,
                "education_rank": education_rank,
                "salary": salary,
                "salary_value": salary_value,
                "job_level": job_level,
                "company_type": company_type if company_type else "未知",
                "recruit_count": recruit_count,
                "city_level": city_level if city_level else "未知"
            })
        
        # 计算归一化的招聘人数（用于气泡大小）
        if recruit_counts:
            min_count = min(recruit_counts)
            max_count = max(recruit_counts)
            count_range = max_count - min_count if max_count > min_count else 1
            
            for point in scatter_points:
                # 归一化到0-1范围
                normalized = (point["recruit_count"] - min_count) / count_range
                # 映射到合理的气泡大小范围（10-50）
                point["normalized_size"] = 10 + normalized * 40
        
        return {
            "city": city,
            "total_jobs": len(scatter_points),
            "data": scatter_points
        }
    
    def get_job_levels(self) -> List[str]:
        """获取所有职位层级（聚类类别）"""
        query = """
            SELECT DISTINCT job_level
            FROM data
            WHERE job_level IS NOT NULL
            ORDER BY job_level
        """
        
        results = self.db_manager.execute_query(query)
        return [row[0] for row in results]
    
    def get_industries(self, city: Optional[str] = None) -> List[str]:
        """获取行业类别"""
        if city:
            query = """
                SELECT DISTINCT company_type
                FROM data
                WHERE company_type IS NOT NULL
                    AND city = %s
                ORDER BY company_type
            """
            results = self.db_manager.execute_query(query, (city,))
        else:
            query = """
                SELECT DISTINCT company_type
                FROM data
                WHERE company_type IS NOT NULL
                ORDER BY company_type
            """
            results = self.db_manager.execute_query(query)
        
        return [row[0] for row in results]

