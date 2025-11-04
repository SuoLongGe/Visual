#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业相关业务逻辑服务
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.industry import (
    IndustryStatistics, IndustryDetail, IndustryComparison,
    IndustrySalaryDistribution, IndustryCityDistribution, IndustryExperienceDistribution,
    IndustryOverview
)
from database import DatabaseManager

logger = logging.getLogger(__name__)


class IndustryService:
    """行业业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_industry_statistics(self, limit: int = 20, min_jobs: int = 0) -> List[IndustryStatistics]:
        """获取行业统计数据"""
        try:
            results = self.db_manager.get_industry_statistics(limit, min_jobs)
            total_jobs = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM data WHERE company_type IS NOT NULL", 
                fetch_one=True
            )[0]
            
            industry_stats = []
            for row in results:
                industry, job_count, avg_salary, company_count = row
                percentage = (job_count / total_jobs) * 100 if total_jobs > 0 else 0
                
                industry_stats.append(IndustryStatistics(
                    industry=industry,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count,
                    percentage=round(percentage, 2)
                ))
            
            return industry_stats
        except Exception as e:
            logger.error(f"获取行业统计数据失败: {e}")
            raise
    
    def get_industry_detail(self, industry_name: str) -> Optional[IndustryDetail]:
        """获取行业详细信息"""
        try:
            industry_data = self.db_manager.get_industry_detail(industry_name)
            
            basic_info = industry_data['basic']
            if not basic_info or basic_info[0] == 0:
                return None
            
            # 构建基本信息
            basic = {
                "total_jobs": basic_info[0],
                "avg_salary": round(basic_info[1], 2) if basic_info[1] else 0,
                "company_count": basic_info[2],
                "city_count": basic_info[3]
            }
            
            # 构建薪资分布
            salary_distribution = [
                IndustrySalaryDistribution(
                    salary_range=row[0],
                    count=row[1],
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in industry_data['salary']
            ]
            
            # 构建城市分布
            city_distribution = [
                IndustryCityDistribution(
                    city=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in industry_data['city']
            ]
            
            # 构建经验分布
            experience_distribution = [
                IndustryExperienceDistribution(
                    experience=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in industry_data['experience']
            ]
            
            return IndustryDetail(
                industry_name=industry_name,
                basic_info=basic,
                salary_distribution=salary_distribution,
                city_distribution=city_distribution,
                experience_distribution=experience_distribution
            )
        except Exception as e:
            logger.error(f"获取行业详细数据失败: {e}")
            raise
    
    def compare_industries(self, industries: List[str]) -> List[IndustryComparison]:
        """比较多个行业的数据"""
        try:
            results = self.db_manager.get_industry_comparison(industries)
            
            if not results:
                return []
            
            # 构建比较数据
            comparison_data = []
            for row in results:
                industry, job_count, avg_salary, company_count, city_count = row
                comparison_data.append(IndustryComparison(
                    industry=industry,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count,
                    city_count=city_count,
                    job_rank=0,  # 将在下面计算
                    salary_rank=0  # 将在下面计算
                ))
            
            # 计算排名
            sorted_by_jobs = sorted(comparison_data, key=lambda x: x.job_count, reverse=True)
            sorted_by_salary = sorted(comparison_data, key=lambda x: x.avg_salary, reverse=True)
            
            for i, industry_data in enumerate(comparison_data):
                industry_data.job_rank = next(i for i, industry in enumerate(sorted_by_jobs) if industry.industry == industry_data.industry) + 1
                industry_data.salary_rank = next(i for i, industry in enumerate(sorted_by_salary) if industry.industry == industry_data.industry) + 1
            
            return comparison_data
        except Exception as e:
            logger.error(f"获取行业比较数据失败: {e}")
            raise
    
    def get_industry_overview(self) -> IndustryOverview:
        """获取行业概览数据"""
        try:
            overview_data = self.db_manager.get_industry_overview()
            
            total_industries = overview_data['total_industries'][0]
            total_jobs = overview_data['total_jobs'][0]
            avg_salary_overall = overview_data['avg_salary_overall'][0] if overview_data['avg_salary_overall'][0] else 0
            top_industries_data = overview_data['top_industries']
            
            # 构建顶级行业列表
            top_industries = []
            for row in top_industries_data:
                industry, job_count, avg_salary = row
                top_industries.append(IndustryStatistics(
                    industry=industry,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=0,  # 这里可以单独查询
                    percentage=round((job_count / total_jobs) * 100, 2)
                ))
            
            # 计算薪资范围分布
            salary_ranges = self._calculate_salary_ranges()
            
            return IndustryOverview(
                total_industries=total_industries,
                total_jobs=total_jobs,
                avg_salary_overall=round(avg_salary_overall, 2),
                top_industries=top_industries,
                salary_ranges=salary_ranges
            )
        except Exception as e:
            logger.error(f"获取行业概览数据失败: {e}")
            raise
    
    def _calculate_salary_ranges(self) -> Dict[str, int]:
        """计算薪资范围分布"""
        try:
            query = """
                SELECT 
                    CASE 
                        WHEN (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                              CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2 < 5 THEN '0-5K'
                        WHEN (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                              CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2 < 10 THEN '5-10K'
                        WHEN (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                              CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2 < 15 THEN '10-15K'
                        WHEN (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                              CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2 < 25 THEN '15-25K'
                        WHEN (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                              CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2 < 35 THEN '25-35K'
                        ELSE '35K+'
                    END as salary_range,
                    COUNT(*) as count
                FROM data 
                WHERE company_type IS NOT NULL 
                AND salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
                GROUP BY salary_range
                ORDER BY 
                    CASE salary_range
                        WHEN '0-5K' THEN 1
                        WHEN '5-10K' THEN 2
                        WHEN '10-15K' THEN 3
                        WHEN '15-25K' THEN 4
                        WHEN '25-35K' THEN 5
                        WHEN '35K+' THEN 6
                    END
            """
            
            results = self.db_manager.execute_query(query)
            return {row[0]: row[1] for row in results}
        except Exception as e:
            logger.error(f"计算薪资范围分布失败: {e}")
            return {}
