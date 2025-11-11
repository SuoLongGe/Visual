#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库操作工具类
"""

import pymysql
import logging
from contextlib import contextmanager
from typing import List, Tuple, Any, Optional, Dict
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, config_name='default'):
        self.config = config[config_name]
        self.db_config = self.config.get_db_config()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = pymysql.connect(**self.db_config)
            yield connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = True) -> Any:
        """执行查询操作"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """批量执行操作"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.executemany(query, params_list)
                connection.commit()
                return cursor.rowcount
            except Exception as e:
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def get_city_statistics(self, limit: int = 20, min_jobs: int = 0) -> List[Tuple]:
        """获取城市统计数据"""
        query = """
            SELECT 
                city,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count
            FROM data 
            WHERE city IS NOT NULL 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY city 
            HAVING job_count >= %s
            ORDER BY job_count DESC 
            LIMIT %s
        """
        return self.execute_query(query, (min_jobs, limit))
    
    def get_city_detail(self, city_name: str) -> Dict[str, Any]:
        """获取城市详细信息"""
        # 基本信息
        basic_query = """
            SELECT 
                COUNT(*) as total_jobs,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT company_type) as industry_count
            FROM data 
            WHERE city = %s 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
        """
        
        # 薪资分布
        salary_query = """
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
            WHERE city = %s 
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
        
        # 行业分布
        industry_query = """
            SELECT 
                company_type,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE city = %s 
            AND company_type IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY company_type
            ORDER BY count DESC
            LIMIT 10
        """
        
        # 经验分布
        experience_query = """
            SELECT 
                experience,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE city = %s 
            AND experience IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY experience
            ORDER BY count DESC
        """
        
        return {
            'basic': self.execute_query(basic_query, (city_name,), fetch_one=True),
            'salary': self.execute_query(salary_query, (city_name,)),
            'industry': self.execute_query(industry_query, (city_name,)),
            'experience': self.execute_query(experience_query, (city_name,))
        }
    
    def get_city_comparison(self, cities: List[str]) -> List[Tuple]:
        """获取城市比较数据"""
        placeholders = ','.join(['%s'] * len(cities))
        query = f"""
            SELECT 
                city,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT company_type) as industry_count
            FROM data 
            WHERE city IN ({placeholders})
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY city
            ORDER BY job_count DESC
        """
        return self.execute_query(query, cities)
    
    def get_overview_statistics(self) -> Dict[str, Any]:
        """获取概览统计数据"""
        queries = {
            'total_records': "SELECT COUNT(*) FROM data",
            'total_cities': "SELECT COUNT(DISTINCT city) FROM data WHERE city IS NOT NULL",
            'total_companies': "SELECT COUNT(DISTINCT company) FROM data WHERE company IS NOT NULL",
            'salary_stats': """
                SELECT 
                    MIN(CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED)) as min_salary,
                    MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) as max_salary,
                    AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                         CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
                FROM data 
                WHERE salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
            """
        }
        
        results = {}
        for key, query in queries.items():
            results[key] = self.execute_query(query, fetch_one=True)
        
        return results
    
    def get_industry_statistics(self, limit: int = 20, min_jobs: int = 0) -> List[Tuple]:
        """获取行业统计数据"""
        query = """
            SELECT 
                company_type,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count
            FROM data 
            WHERE company_type IS NOT NULL 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY company_type 
            HAVING job_count >= %s
            ORDER BY job_count DESC 
            LIMIT %s
        """
        return self.execute_query(query, (min_jobs, limit))
    
    def get_industry_detail(self, industry_name: str) -> Dict[str, Any]:
        """获取行业详细信息"""
        # 基本信息
        basic_query = """
            SELECT 
                COUNT(*) as total_jobs,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT city) as city_count
            FROM data 
            WHERE company_type = %s 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
        """
        
        # 薪资分布
        salary_query = """
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
            WHERE company_type = %s 
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
        
        # 城市分布
        city_query = """
            SELECT 
                city,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE company_type = %s 
            AND city IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY city
            ORDER BY count DESC
            LIMIT 15
        """
        
        # 经验分布
        experience_query = """
            SELECT 
                experience,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE company_type = %s 
            AND experience IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY experience
            ORDER BY count DESC
        """
        
        return {
            'basic': self.execute_query(basic_query, (industry_name,), fetch_one=True),
            'salary': self.execute_query(salary_query, (industry_name,)),
            'city': self.execute_query(city_query, (industry_name,)),
            'experience': self.execute_query(experience_query, (industry_name,))
        }
    
    def get_industry_comparison(self, industries: List[str]) -> List[Tuple]:
        """获取行业比较数据"""
        placeholders = ','.join(['%s'] * len(industries))
        query = f"""
            SELECT 
                company_type,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT city) as city_count
            FROM data 
            WHERE company_type IN ({placeholders})
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY company_type
            ORDER BY job_count DESC
        """
        return self.execute_query(query, industries)
    
    def get_industry_overview(self) -> Dict[str, Any]:
        """获取行业概览数据"""
        queries = {
            'total_industries': "SELECT COUNT(DISTINCT company_type) FROM data WHERE company_type IS NOT NULL",
            'total_jobs': "SELECT COUNT(*) FROM data WHERE company_type IS NOT NULL",
            'avg_salary_overall': """
                SELECT AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                           CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
                FROM data 
                WHERE company_type IS NOT NULL 
                AND salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
            """,
            'top_industries': """
                SELECT 
                    company_type,
                    COUNT(*) as job_count,
                    AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                         CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
                FROM data 
                WHERE company_type IS NOT NULL 
                AND salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
                GROUP BY company_type
                ORDER BY job_count DESC
                LIMIT 10
            """
        }
        
        results = {}
        for key, query in queries.items():
            if key == 'top_industries':
                results[key] = self.execute_query(query)
            else:
                results[key] = self.execute_query(query, fetch_one=True)
        
        return results
    
    def get_experience_statistics(self, limit: int = 1000, min_jobs: int = 0) -> List[Tuple]:
        """获取经验统计数据"""
        query = """
            SELECT 
                experience,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count
            FROM data 
            WHERE experience IS NOT NULL 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY experience 
            HAVING job_count >= %s
            ORDER BY job_count DESC 
            LIMIT %s
        """
        return self.execute_query(query, (min_jobs, limit))
    
    def get_experience_detail(self, experience_name: str) -> Dict[str, Any]:
        """获取经验详细信息"""
        # 基本信息
        basic_query = """
            SELECT 
                COUNT(*) as total_jobs,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT city) as city_count,
                COUNT(DISTINCT company_type) as industry_count
            FROM data 
            WHERE experience = %s 
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
        """
        
        # 薪资分布
        salary_query = """
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
            WHERE experience = %s 
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
        
        # 城市分布
        city_query = """
            SELECT 
                city,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE experience = %s 
            AND city IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY city
            ORDER BY count DESC
            LIMIT 15
        """
        
        # 行业分布
        industry_query = """
            SELECT 
                company_type,
                COUNT(*) as count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data 
            WHERE experience = %s 
            AND company_type IS NOT NULL
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY company_type
            ORDER BY count DESC
            LIMIT 10
        """
        
        return {
            'basic': self.execute_query(basic_query, (experience_name,), fetch_one=True),
            'salary': self.execute_query(salary_query, (experience_name,)),
            'city': self.execute_query(city_query, (experience_name,)),
            'industry': self.execute_query(industry_query, (experience_name,))
        }
    
    def get_experience_comparison(self, experiences: List[str]) -> List[Tuple]:
        """获取经验比较数据"""
        placeholders = ','.join(['%s'] * len(experiences))
        query = f"""
            SELECT 
                experience,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                COUNT(DISTINCT company) as company_count,
                COUNT(DISTINCT city) as city_count,
                COUNT(DISTINCT company_type) as industry_count
            FROM data 
            WHERE experience IN ({placeholders})
            AND salary IS NOT NULL 
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY experience
            ORDER BY job_count DESC
        """
        return self.execute_query(query, experiences)
    
    def get_experience_overview(self) -> Dict[str, Any]:
        """获取经验概览数据"""
        queries = {
            'total_experience_levels': "SELECT COUNT(DISTINCT experience) FROM data WHERE experience IS NOT NULL",
            'total_jobs': "SELECT COUNT(*) FROM data WHERE experience IS NOT NULL",
            'avg_salary_overall': """
                SELECT AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                           CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
                FROM data 
                WHERE experience IS NOT NULL 
                AND salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
            """,
            'top_experience_levels': """
                SELECT 
                    experience,
                    COUNT(*) as job_count,
                    AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                         CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
                FROM data 
                WHERE experience IS NOT NULL 
                AND salary IS NOT NULL 
                AND salary REGEXP '^[0-9]+-[0-9]+'
                GROUP BY experience
                ORDER BY job_count DESC
                LIMIT 10
            """,
            'experience_distribution': """
                SELECT 
                    experience,
                    COUNT(*) as count
                FROM data 
                WHERE experience IS NOT NULL
                GROUP BY experience
                ORDER BY count DESC
            """
        }
        
        results = {}
        for key, query in queries.items():
            if key in ['top_experience_levels', 'experience_distribution']:
                results[key] = self.execute_query(query)
            else:
                results[key] = self.execute_query(query, fetch_one=True)
        
        return results
    
    def get_experience_education_salary(self) -> List[Tuple]:
        """
        获取经验-学历-薪资组合数据，用于三维柱状图
        使用映射表将编码转换为中文标签
        """
        query = """
            SELECT 
                COALESCE(exp_mapping.experience_label, d.experience, '未知') as experience,
                COALESCE(edu_mapping.education_label, d.education, '未知') as education,
                AVG(COALESCE(d.median_annual_salary,
                    (CAST(SUBSTRING_INDEX(d.salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(d.salary, '-', 2), '-', -1) AS UNSIGNED)) / 2)) as avg_salary,
                COUNT(*) as job_count
            FROM data d
            LEFT JOIN experience_mapping exp_mapping ON d.experience = exp_mapping.experience_code
            LEFT JOIN education_mapping edu_mapping ON d.education = edu_mapping.education_code
            WHERE d.experience IS NOT NULL
            AND d.education IS NOT NULL
            AND (d.median_annual_salary IS NOT NULL OR 
                 (d.salary IS NOT NULL AND d.salary REGEXP '^[0-9]+-[0-9]+'))
            GROUP BY COALESCE(exp_mapping.experience_label, d.experience, '未知'),
                     COALESCE(edu_mapping.education_label, d.education, '未知')
            ORDER BY experience, education
        """
        return self.execute_query(query)
    
    def get_boxplot_data(self, experience: str = None, education: str = None, 
                         city: str = None, company_type: str = None) -> List[Tuple]:
        """
        获取箱线图数据
        根据经验、学历、城市、公司类型筛选，返回薪资分布数据
        注意：experience和education参数应该是映射后的中文标签，需要先转换为编码进行筛选
        """
        # 构建WHERE条件
        conditions = []
        params = []
        
        # 处理经验和学历筛选：如果传入的是中文标签，需要先查找对应的编码
        if experience:
            # 先查找经验编码
            exp_code_query = """
                SELECT experience_code FROM experience_mapping 
                WHERE experience_label = %s LIMIT 1
            """
            exp_result = self.execute_query(exp_code_query, params=(experience,))
            if exp_result and len(exp_result) > 0:
                conditions.append("d.experience = %s")
                params.append(exp_result[0][0])
            else:
                # 如果找不到映射，直接使用原值（可能是编码）
                conditions.append("COALESCE(exp_mapping.experience_label, d.experience, '未知') = %s")
                params.append(experience)
        
        if education:
            # 先查找学历编码
            edu_code_query = """
                SELECT education_code FROM education_mapping 
                WHERE education_label = %s LIMIT 1
            """
            edu_result = self.execute_query(edu_code_query, params=(education,))
            if edu_result and len(edu_result) > 0:
                conditions.append("d.education = %s")
                params.append(edu_result[0][0])
            else:
                # 如果找不到映射，直接使用原值（可能是编码）
                conditions.append("COALESCE(edu_mapping.education_label, d.education, '未知') = %s")
                params.append(education)
        
        if city:
            conditions.append("d.city = %s")
            params.append(city)
        
        if company_type:
            conditions.append("d.company_type = %s")
            params.append(company_type)
        
        # 基础条件：薪资必须有效
        conditions.append("(d.median_annual_salary IS NOT NULL OR (d.salary IS NOT NULL AND d.salary REGEXP '^[0-9]+-[0-9]+'))")
        
        where_clause = " AND ".join(conditions)
        
        # 查询薪资数据（用于计算统计量）
        # 注意：这里返回的是原始数据，用于计算统计量，不需要映射
        query = f"""
            SELECT 
                d.city,
                d.company_type,
                COALESCE(d.median_annual_salary,
                    (CAST(SUBSTRING_INDEX(d.salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(d.salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as salary
            FROM data d
            LEFT JOIN experience_mapping exp_mapping ON d.experience = exp_mapping.experience_code
            LEFT JOIN education_mapping edu_mapping ON d.education = edu_mapping.education_code
            WHERE {where_clause}
        """
        
        # 如果params是列表，转换为元组（MySQL连接器需要）
        if params and isinstance(params, list):
            params = tuple(params)
        return self.execute_query(query, params=params if params else None)
    
    def get_radar_bubble_data(self) -> List[Tuple]:
        """
        获取雷达气泡图数据
        返回每个经验等级下，各城市的岗位数量、平均薪资、岗位类型分布等信息
        用于计算香农熵和绘制雷达气泡图
        """
        query = """
            SELECT 
                experience,
                city,
                COUNT(*) as job_count,
                AVG(COALESCE(median_annual_salary, 
                    (CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2)) as avg_salary,
                GROUP_CONCAT(DISTINCT job_title ORDER BY job_title SEPARATOR ',') as job_titles
            FROM data
            WHERE experience IS NOT NULL
            AND city IS NOT NULL
            AND (median_annual_salary IS NOT NULL OR 
                 (salary IS NOT NULL AND salary REGEXP '^[0-9]+-[0-9]+'))
            GROUP BY experience, city
            ORDER BY experience, job_count DESC
        """
        return self.execute_query(query)
    
    def get_parallel_coordinates_data(self) -> List[Tuple]:
        """
        获取平行坐标图数据
        返回包含城市、经验、学历、薪资、公司类型、岗位多样性等所有维度的数据
        用于绘制平行坐标图
        使用映射表将编码转换为中文标签，确保所有经验等级和学历要求都包含在内
        
        注意：直接使用数据表中的 shannon_entropy 字段，不再计算
        """
        query = """
            SELECT 
                COALESCE(d.city, '未知') as city,
                COALESCE(exp_mapping.experience_label, d.experience, '未知') as experience,
                COALESCE(edu_mapping.education_label, d.education, '未知') as education,
                COALESCE(d.company_type, '未知') as company_type,
                AVG(COALESCE(d.median_annual_salary, 
                    (CAST(SUBSTRING_INDEX(d.salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(d.salary, '-', 2), '-', -1) AS UNSIGNED)) / 2)) as avg_salary,
                AVG(COALESCE(d.shannon_entropy, 0)) as avg_shannon_entropy,
                COUNT(*) as job_count
            FROM data d
            LEFT JOIN experience_mapping exp_mapping ON d.experience = exp_mapping.experience_code
            LEFT JOIN education_mapping edu_mapping ON d.education = edu_mapping.education_code
            WHERE (d.median_annual_salary IS NOT NULL OR 
                 (d.salary IS NOT NULL AND d.salary REGEXP '^[0-9]+-[0-9]+'))
            GROUP BY d.city, 
                     COALESCE(exp_mapping.experience_label, d.experience, '未知'), 
                     COALESCE(edu_mapping.education_label, d.education, '未知'), 
                     COALESCE(d.company_type, '未知')
            ORDER BY job_count DESC
            LIMIT 1000
        """
        return self.execute_query(query)