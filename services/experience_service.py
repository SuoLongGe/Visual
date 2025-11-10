#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验相关业务逻辑服务
"""

import logging
from typing import List, Optional, Dict

from models.experience import (
    ExperienceStatistics, ExperienceDetail, ExperienceComparison,
    ExperienceSalaryDistribution, ExperienceCityDistribution, ExperienceIndustryDistribution,
    ExperienceOverview
)
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class ExperienceService:
    """经验业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_experience_statistics(self, limit: int = 1000, min_jobs: int = 0) -> List[ExperienceStatistics]:
        """获取经验统计数据"""
        try:
            results = self.db_manager.get_experience_statistics(limit, min_jobs)
            total_jobs = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM data WHERE experience IS NOT NULL", 
                fetch_one=True
            )[0]
            
            experience_stats = []
            for row in results:
                experience, job_count, avg_salary, company_count = row
                percentage = (job_count / total_jobs) * 100 if total_jobs > 0 else 0
                
                experience_stats.append(ExperienceStatistics(
                    experience=experience,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count,
                    percentage=round(percentage, 2)
                ))
            
            return experience_stats
        except Exception as e:
            logger.error(f"获取经验统计数据失败: {e}")
            raise
    
    def get_experience_detail(self, experience_name: str) -> Optional[ExperienceDetail]:
        """获取经验详细信息"""
        try:
            experience_data = self.db_manager.get_experience_detail(experience_name)
            
            basic_info = experience_data['basic']
            if not basic_info or basic_info[0] == 0:
                return None
            
            # 构建基本信息
            basic = {
                "total_jobs": basic_info[0],
                "avg_salary": round(basic_info[1], 2) if basic_info[1] else 0,
                "company_count": basic_info[2],
                "city_count": basic_info[3],
                "industry_count": basic_info[4]
            }
            
            # 构建薪资分布
            salary_distribution = [
                ExperienceSalaryDistribution(
                    salary_range=row[0],
                    count=row[1],
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in experience_data['salary']
            ]
            
            # 构建城市分布
            city_distribution = [
                ExperienceCityDistribution(
                    city=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in experience_data['city']
            ]
            
            # 构建行业分布
            industry_distribution = [
                ExperienceIndustryDistribution(
                    industry=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in experience_data['industry']
            ]
            
            return ExperienceDetail(
                experience_name=experience_name,
                basic_info=basic,
                salary_distribution=salary_distribution,
                city_distribution=city_distribution,
                industry_distribution=industry_distribution
            )
        except Exception as e:
            logger.error(f"获取经验详细数据失败: {e}")
            raise
    
    def compare_experiences(self, experiences: List[str]) -> List[ExperienceComparison]:
        """比较多个经验级别的数据"""
        try:
            results = self.db_manager.get_experience_comparison(experiences)
            
            if not results:
                return []
            
            # 构建比较数据
            comparison_data = []
            for row in results:
                experience, job_count, avg_salary, company_count, city_count, industry_count = row
                comparison_data.append(ExperienceComparison(
                    experience=experience,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count,
                    city_count=city_count,
                    industry_count=industry_count,
                    job_rank=0,  # 将在下面计算
                    salary_rank=0  # 将在下面计算
                ))
            
            # 计算排名
            sorted_by_jobs = sorted(comparison_data, key=lambda x: x.job_count, reverse=True)
            sorted_by_salary = sorted(comparison_data, key=lambda x: x.avg_salary, reverse=True)
            
            for i, experience_data in enumerate(comparison_data):
                experience_data.job_rank = next(i for i, exp in enumerate(sorted_by_jobs) if exp.experience == experience_data.experience) + 1
                experience_data.salary_rank = next(i for i, exp in enumerate(sorted_by_salary) if exp.experience == experience_data.experience) + 1
            
            return comparison_data
        except Exception as e:
            logger.error(f"获取经验比较数据失败: {e}")
            raise
    
    def get_experience_overview(self) -> ExperienceOverview:
        """获取经验概览数据"""
        try:
            overview_data = self.db_manager.get_experience_overview()
            
            total_experience_levels = overview_data['total_experience_levels'][0]
            total_jobs = overview_data['total_jobs'][0]
            avg_salary_overall = overview_data['avg_salary_overall'][0] if overview_data['avg_salary_overall'][0] else 0
            top_experience_levels_data = overview_data['top_experience_levels']
            experience_distribution_data = overview_data['experience_distribution']
            
            # 构建顶级经验级别列表
            top_experience_levels = []
            for row in top_experience_levels_data:
                experience, job_count, avg_salary = row
                top_experience_levels.append(ExperienceStatistics(
                    experience=experience,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=0,  # 这里可以单独查询
                    percentage=round((job_count / total_jobs) * 100, 2)
                ))
            
            # 计算薪资范围分布
            salary_ranges = self._calculate_salary_ranges()
            
            # 构建经验分布
            experience_distribution = {row[0]: row[1] for row in experience_distribution_data}
            
            return ExperienceOverview(
                total_experience_levels=total_experience_levels,
                total_jobs=total_jobs,
                avg_salary_overall=round(avg_salary_overall, 2),
                top_experience_levels=top_experience_levels,
                salary_ranges=salary_ranges,
                experience_distribution=experience_distribution
            )
        except Exception as e:
            logger.error(f"获取经验概览数据失败: {e}")
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
                WHERE experience IS NOT NULL 
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
