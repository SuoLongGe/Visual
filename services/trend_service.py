#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业趋势与新兴职位相关业务逻辑服务
"""

import logging
import pandas as pd
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class JobRanking:
    """职位排名数据"""
    job_title: str
    records_count_norm: float  # 归一化后的记录数量 (0-1)
    education_rank: float  # 归一化后的学历排名 (0-1)
    experience_rank: float  # 归一化后的经验排名 (0-1)
    composite_score: float  # 综合得分


@dataclass
class IndustryTrend:
    """行业趋势数据"""
    company_type: str
    national_job_count: int
    avg_median_salary: float
    avg_experience_rank: float
    avg_education_rank: float
    
    @property
    def industry_name(self) -> str:
        """生成可读的行业名称"""
        # 如果 company_type 以 type_ 开头，提取后面的部分
        if self.company_type.startswith('type_'):
            return self.company_type[5:]  # 移除 'type_' 前缀
        return self.company_type


class TrendService:
    """行业趋势业务逻辑服务"""
    
    def __init__(self, base_path: str = None):
        """
        初始化服务
        :param base_path: 数据文件基础路径，默认为当前工作目录
        """
        if base_path is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(current_dir)
        
        self.base_path = base_path
        self.job_summary_path = os.path.join(
            base_path, 'dataset', 'dataset', 'job_summary.xlsx'
        )
        self.industry_stats_path = os.path.join(
            base_path, 'dataset', 'dataset', '第四题', 'national_industry_stats.xlsx'
        )
    
    def get_job_ranking(self, top_n: int = 5) -> List[JobRanking]:
        """
        获取职位综合排名数据
        计算综合指标：composite_score = education_norm × records_count_norm × experience_norm
        其中：
        - education_norm = avg_education_rank / 10.0 (归一化到0-1)
        - experience_norm = avg_experience_rank / 10.0 (归一化到0-1)
        - records_count_norm = 直接从数据表读取（已归一化到0-1）
        
        示例：如果 education_norm=0.666, records_count_norm=0.782, experience_norm=0.506
        则 composite_score = 0.666 × 0.782 × 0.506 ≈ 0.264
        
        :param top_n: 返回前N名，默认5
        :return: 职位排名列表
        """
        try:
            logger.info(f"开始读取职位排名数据，文件路径: {self.job_summary_path}")
            
            # 检查文件是否存在
            if not os.path.exists(self.job_summary_path):
                raise FileNotFoundError(f"找不到数据文件: {self.job_summary_path}")
            
            # 读取Excel文件，使用engine='openpyxl'以提高性能
            logger.info("正在读取Excel文件...")
            df = pd.read_excel(self.job_summary_path, engine='openpyxl')
            logger.info(f"Excel文件读取完成，共 {len(df)} 行数据")
            
            # 去除重复的job_title，只保留第一个
            df_unique = df.drop_duplicates(subset=['job_title'], keep='first').copy()
            logger.info(f"去重后剩余 {len(df_unique)} 个职位")
            
            # 计算归一化的education和experience
            df_unique['education_norm'] = df_unique['avg_education_rank'] / 10.0
            df_unique['experience_norm'] = df_unique['avg_experience_rank'] / 10.0
            
            # 计算综合指标：X = education * count * experience
            df_unique['composite_score'] = (
                df_unique['education_norm'] * 
                df_unique['records_count_norm'] * 
                df_unique['experience_norm']
            )
            
            # 按综合指标排序，取前N名
            df_sorted = df_unique.nlargest(top_n, 'composite_score')
            logger.info(f"已排序，返回前 {top_n} 名职位")
            
            # 构建返回数据
            job_rankings = []
            for _, row in df_sorted.iterrows():
                job_ranking = JobRanking(
                    job_title=str(row['job_title']),
                    records_count_norm=float(row['records_count_norm']),  # 使用归一化后的记录数量
                    education_rank=float(row['education_norm']),
                    experience_rank=float(row['experience_norm']),
                    composite_score=float(row['composite_score'])
                )
                job_rankings.append(job_ranking)
            
            logger.info("职位排名数据获取成功")
            return job_rankings
            
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            raise FileNotFoundError(f"找不到数据文件: {self.job_summary_path}")
        except Exception as e:
            logger.error(f"获取职位排名数据失败: {e}", exc_info=True)
            raise
    
    def get_industry_trend_rose(self) -> List[IndustryTrend]:
        """
        获取行业双环嵌套玫瑰图数据
        从 national_industry_stats.xlsx 读取数据
        
        :return: 行业趋势列表
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(self.industry_stats_path)
            
            # 构建返回数据
            industry_trends = []
            for _, row in df.iterrows():
                # 计算归一化的experience和education
                avg_experience_rank = float(row.get('avg_experience_rank', 0)) / 10.0
                avg_education_rank = float(row.get('avg_education_rank', 0)) / 10.0
                
                industry_trend = IndustryTrend(
                    company_type=str(row.get('company_type', '')),
                    national_job_count=int(row.get('national_job_count', 0)),
                    avg_median_salary=float(row.get('avg_median_salary', 0)),
                    avg_experience_rank=avg_experience_rank,
                    avg_education_rank=avg_education_rank
                )
                industry_trends.append(industry_trend)
            
            return industry_trends
            
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            raise FileNotFoundError(f"找不到数据文件: {self.industry_stats_path}")
        except Exception as e:
            logger.error(f"获取行业趋势数据失败: {e}")
            raise

