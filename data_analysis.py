#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析脚本
用于分析招聘数据，按城市分类分析热门职业和薪资水平
"""

import logging
from typing import Dict, List, Tuple, Any
from database import DatabaseManager
from datetime import datetime
import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """处理Decimal类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager('default')
        self.analysis_results = {}
    
    def get_city_list(self, limit: int = 50) -> List[str]:
        """获取主要城市列表"""
        query = """
            SELECT city, COUNT(*) as job_count
            FROM data
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY job_count DESC
            LIMIT %s
        """
        results = self.db_manager.execute_query(query, (limit,))
        return [row[0] for row in results]
    
    def analyze_city_jobs(self, city: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """分析城市的热门职位"""
        query = """
            SELECT 
                job_title,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                MIN(CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED)) as min_salary,
                MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) as max_salary
            FROM data
            WHERE city = %s
            AND job_title IS NOT NULL
            AND salary IS NOT NULL
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY job_title
            ORDER BY job_count DESC
            LIMIT %s
        """
        results = self.db_manager.execute_query(query, (city, top_n))
        
        jobs = []
        for row in results:
            job_title, job_count, avg_salary, min_salary, max_salary = row
            jobs.append({
                'job_title': job_title,
                'job_count': job_count,
                'avg_salary': round(avg_salary, 2) if avg_salary else 0,
                'min_salary': int(min_salary) if min_salary else 0,
                'max_salary': int(max_salary) if max_salary else 0
            })
        
        return jobs
    
    def analyze_city_salary(self, city: str) -> Dict[str, Any]:
        """分析城市的薪资水平"""
        # 总体薪资统计
        overall_query = """
            SELECT 
                COUNT(*) as total_jobs,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary,
                MIN(CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED)) as min_salary,
                MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) as max_salary
            FROM data
            WHERE city = %s
            AND salary IS NOT NULL
            AND salary REGEXP '^[0-9]+-[0-9]+'
        """
        overall_result = self.db_manager.execute_query(overall_query, (city,), fetch_one=True)
        
        # 薪资分布
        distribution_query = """
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
        distribution_results = self.db_manager.execute_query(distribution_query, (city,))
        
        total_jobs = overall_result[0] if overall_result else 0
        salary_distribution = []
        for row in distribution_results:
            salary_range, count = row
            percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
            salary_distribution.append({
                'range': salary_range,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return {
            'total_jobs': total_jobs,
            'avg_salary': round(overall_result[1], 2) if overall_result and overall_result[1] else 0,
            'min_salary': int(overall_result[2]) if overall_result and overall_result[2] else 0,
            'max_salary': int(overall_result[3]) if overall_result and overall_result[3] else 0,
            'distribution': salary_distribution
        }
    
    def analyze_city_industry(self, city: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """分析城市的行业分布"""
        query = """
            SELECT 
                company_type,
                COUNT(*) as job_count,
                AVG((CAST(SUBSTRING_INDEX(salary, '-', 1) AS UNSIGNED) + 
                     CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(salary, '-', 2), '-', -1) AS UNSIGNED)) / 2) as avg_salary
            FROM data
            WHERE city = %s
            AND company_type IS NOT NULL
            AND salary IS NOT NULL
            AND salary REGEXP '^[0-9]+-[0-9]+'
            GROUP BY company_type
            ORDER BY job_count DESC
            LIMIT %s
        """
        results = self.db_manager.execute_query(query, (city, top_n))
        
        industries = []
        for row in results:
            company_type, job_count, avg_salary = row
            industries.append({
                'industry': company_type,
                'job_count': job_count,
                'avg_salary': round(avg_salary, 2) if avg_salary else 0
            })
        
        return industries
    
    def analyze_all_cities(self, city_limit: int = 20, top_jobs: int = 10) -> Dict[str, Any]:
        """分析所有主要城市"""
        logger.info("开始分析城市数据...")
        cities = self.get_city_list(city_limit)
        logger.info(f"找到 {len(cities)} 个主要城市")
        
        all_city_analysis = {}
        
        for i, city in enumerate(cities, 1):
            logger.info(f"正在分析 {city} ({i}/{len(cities)})...")
            
            # 分析热门职位
            top_jobs_list = self.analyze_city_jobs(city, top_jobs)
            
            # 分析薪资水平
            salary_info = self.analyze_city_salary(city)
            
            # 分析行业分布
            industries = self.analyze_city_industry(city, 5)
            
            # 获取城市基本信息
            city_basic = self.db_manager.get_city_detail(city)
            total_jobs = city_basic['basic'][0] if city_basic['basic'] else 0
            company_count = city_basic['basic'][2] if city_basic['basic'] else 0
            
            all_city_analysis[city] = {
                'total_jobs': total_jobs,
                'company_count': company_count,
                'top_jobs': top_jobs_list,
                'salary_analysis': salary_info,
                'top_industries': industries
            }
        
        self.analysis_results = {
            'analysis_date': datetime.now().isoformat(),
            'total_cities_analyzed': len(cities),
            'cities': all_city_analysis
        }
        
        return self.analysis_results
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """获取整体统计数据"""
        stats = self.db_manager.get_overview_statistics()
        
        return {
            'total_records': stats['total_records'][0] if stats['total_records'] else 0,
            'total_cities': stats['total_cities'][0] if stats['total_cities'] else 0,
            'total_companies': stats['total_companies'][0] if stats['total_companies'] else 0,
            'salary_stats': {
                'min': int(stats['salary_stats'][0]) if stats['salary_stats'] and stats['salary_stats'][0] else 0,
                'max': int(stats['salary_stats'][1]) if stats['salary_stats'] and stats['salary_stats'][1] else 0,
                'avg': round(stats['salary_stats'][2], 2) if stats['salary_stats'] and stats['salary_stats'][2] else 0
            }
        }
    
    def save_results(self, filename: str = 'analysis_results.json'):
        """保存分析结果到JSON文件"""
        results = {
            'overall_statistics': self.get_overall_statistics(),
            'city_analysis': self.analysis_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        
        logger.info(f"分析结果已保存到 {filename}")


def main():
    """主函数"""
    analyzer = DataAnalyzer()
    
    # 分析所有主要城市（前20个城市，每个城市前10个热门职位）
    results = analyzer.analyze_all_cities(city_limit=20, top_jobs=10)
    
    # 保存结果
    analyzer.save_results('analysis_results.json')
    
    logger.info("数据分析完成！")
    return results


if __name__ == '__main__':
    main()

