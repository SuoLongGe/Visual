#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市相关业务逻辑服务
"""
import logging
from typing import List, Optional
from datetime import datetime

from models.city import (
    CityBasicInfo, CityDetail, CityStatistics, CityComparison,
    CitySalaryDistribution, CityIndustryDistribution, CityExperienceDistribution,
    OverviewData
)
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class CityService:
    """城市业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_overview_data(self) -> OverviewData:
        """获取数据概览"""
        try:
            stats = self.db_manager.get_overview_statistics()
            
            total_records = stats['total_records'][0]
            total_cities = stats['total_cities'][0]
            total_companies = stats['total_companies'][0]
            salary_stats = stats['salary_stats']
            
            return OverviewData(
                total_records=total_records,
                data_quality={
                    "completeness": 95.5,
                    "accuracy": 98.2,
                    "consistency": 97.8
                },
                last_updated=datetime.now().isoformat(),
                data_sources=[{
                    "name": "JobWanted.xlsx",
                    "records": total_records,
                    "last_modified": datetime.now().isoformat()
                }],
                statistics={
                    "total_companies": total_companies,
                    "total_cities": total_cities,
                    "salary_range": {
                        "min": int(salary_stats[0]) if salary_stats[0] else 0,
                        "max": int(salary_stats[1]) if salary_stats[1] else 0,
                        "median": int(salary_stats[2]) if salary_stats[2] else 0
                    }
                }
            )
        except Exception as e:
            logger.error(f"获取数据概览失败: {e}")
            raise
    
    def get_city_statistics(self, limit: int = 20, min_jobs: int = 0) -> List[CityStatistics]:
        """获取城市统计数据"""
        try:
            results = self.db_manager.get_city_statistics(limit, min_jobs)
            total_jobs = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM data WHERE city IS NOT NULL", 
                fetch_one=True
            )[0]
            
            city_stats = []
            for row in results:
                city, job_count, avg_salary, company_count = row
                percentage = (job_count / total_jobs) * 100 if total_jobs > 0 else 0
                
                city_stats.append(CityStatistics(
                    city=city,
                    job_count=job_count,
                    percentage=round(percentage, 2),
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count
                ))
            
            return city_stats
        except Exception as e:
            logger.error(f"获取城市统计数据失败: {e}")
            raise
    
    def get_city_detail(self, city_name: str) -> Optional[CityDetail]:
        """获取城市详细信息"""
        try:
            city_data = self.db_manager.get_city_detail(city_name)
            
            basic_info = city_data['basic']
            if not basic_info or basic_info[0] == 0:
                return None
            
            # 构建基本信息
            basic = CityBasicInfo(
                total_jobs=basic_info[0],
                avg_salary=round(basic_info[1], 2) if basic_info[1] else 0,
                company_count=basic_info[2],
                industry_count=basic_info[3]
            )
            
            # 构建薪资分布
            salary_distribution = [
                CitySalaryDistribution(
                    range=row[0],
                    count=row[1],
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in city_data['salary']
            ]
            
            # 构建行业分布
            industry_distribution = [
                CityIndustryDistribution(
                    industry=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in city_data['industry']
            ]
            
            # 构建经验分布
            experience_distribution = [
                CityExperienceDistribution(
                    experience=row[0],
                    count=row[1],
                    avg_salary=round(row[2], 2) if row[2] else 0,
                    percentage=round((row[1] / basic_info[0]) * 100, 2)
                )
                for row in city_data['experience']
            ]
            
            return CityDetail(
                city_name=city_name,
                basic_info=basic,
                salary_distribution=salary_distribution,
                industry_distribution=industry_distribution,
                experience_distribution=experience_distribution
            )
        except Exception as e:
            logger.error(f"获取城市详细数据失败: {e}")
            raise
    
    def compare_cities(self, cities: List[str]) -> List[CityComparison]:
        """比较多个城市的数据"""
        try:
            results = self.db_manager.get_city_comparison(cities)
            
            if not results:
                return []
            
            # 构建比较数据
            comparison_data = []
            for row in results:
                city, job_count, avg_salary, company_count, industry_count = row
                comparison_data.append(CityComparison(
                    city=city,
                    job_count=job_count,
                    avg_salary=round(avg_salary, 2) if avg_salary else 0,
                    company_count=company_count,
                    industry_count=industry_count,
                    job_rank=0,  # 将在下面计算
                    salary_rank=0  # 将在下面计算
                ))
            
            # 计算排名
            sorted_by_jobs = sorted(comparison_data, key=lambda x: x.job_count, reverse=True)
            sorted_by_salary = sorted(comparison_data, key=lambda x: x.avg_salary, reverse=True)
            
            for i, city_data in enumerate(comparison_data):
                city_data.job_rank = next(i for i, city in enumerate(sorted_by_jobs) if city.city == city_data.city) + 1
                city_data.salary_rank = next(i for i, city in enumerate(sorted_by_salary) if city.city == city_data.city) + 1
            
            return comparison_data
        except Exception as e:
            logger.error(f"获取城市比较数据失败: {e}")
            raise
