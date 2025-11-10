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
from database import DatabaseManager

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
    # 颜色用的 0-1（来自 10 分制除以 10）
    avg_experience_rank: float
    avg_education_rank: float
    # 原始 10 分制均值（直接来自数据库映射均值）
    avg_experience_rank_10: Optional[float] = None
    avg_education_rank_10: Optional[float] = None
    # 依据本次查询数据做 min-max 归一化（0-1），供外环半径直接使用（×10）
    avg_experience_rank_normalized: float = 0.0
    avg_education_rank_normalized: float = 0.0
    
    @property
    def industry_name(self) -> str:
        """生成可读的行业名称"""
        # 如果 company_type 以 type_ 开头，提取后面的部分
        if self.company_type.startswith('type_'):
            return self.company_type[5:]  # 移除 'type_' 前缀
        return self.company_type


class TrendService:
    """行业趋势业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager = None, base_path: str = None):
        """
        初始化服务
        :param db_manager: 数据库管理器，用于从数据库读取数据
        :param base_path: 数据文件基础路径，默认为当前工作目录（用于其他Excel文件）
        """
        self.db_manager = db_manager
        
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
        # 优先从数据库读取；若数据库不可用或异常，优雅降级到 Excel
        if self.db_manager:
            try:
                logger.info("从数据库读取职位排名数据")
                db_result = self._get_job_ranking_from_db(top_n)
                # 若数据库空数据则尝试回退到 Excel
                if not db_result:
                    logger.warning("数据库未返回职位排名数据，回退到Excel")
                    return self._get_job_ranking_from_excel(top_n)
                return db_result
            except Exception as e:
                logger.warning(f"数据库读取职位排名失败，将回退到Excel。原因: {e}", exc_info=True)
                # 继续回退到 Excel
        try:
            logger.info(f"从Excel文件读取职位排名数据，文件路径: {self.job_summary_path}")
            return self._get_job_ranking_from_excel(top_n)
        except Exception as e:
            logger.error(f"获取职位排名数据失败（Excel回退也失败）: {e}", exc_info=True)
            raise
    
    def _get_job_ranking_from_db(self, top_n: int = 5) -> List[JobRanking]:
        """从数据库读取职位排名数据"""
        query = """
            SELECT 
                job_title,
                records_count_norm,
                avg_education_rank,
                avg_experience_rank
            FROM job_summary
            WHERE job_title IS NOT NULL
            AND records_count_norm IS NOT NULL
            AND avg_education_rank IS NOT NULL
            AND avg_experience_rank IS NOT NULL
            ORDER BY job_title
        """
        
        results = self.db_manager.execute_query(query)
        logger.info(f"从数据库读取到 {len(results)} 条记录")
        
        # 转换为DataFrame以便处理
        if not results:
            logger.warning("数据库中没有找到职位排名数据")
            return []
        
        # 构建数据字典列表
        data_list = []
        for row in results:
            data_list.append({
                'job_title': row[0],
                'records_count_norm': float(row[1]) if row[1] is not None else 0.0,
                'avg_education_rank': float(row[2]) if row[2] is not None else 0.0,
                'avg_experience_rank': float(row[3]) if row[3] is not None else 0.0
            })
        
        df = pd.DataFrame(data_list)
        
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
                records_count_norm=float(row['records_count_norm']),
                education_rank=float(row['education_norm']),
                experience_rank=float(row['experience_norm']),
                composite_score=float(row['composite_score'])
            )
            job_rankings.append(job_ranking)
        
        logger.info("职位排名数据获取成功")
        return job_rankings
    
    def _get_job_ranking_from_excel(self, top_n: int = 5) -> List[JobRanking]:
        """从Excel文件读取职位排名数据（备用方法）"""
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
    
    def get_industry_trend_rose(self) -> List[IndustryTrend]:
        """
        获取行业双环嵌套玫瑰图数据（仅从数据库读取）
        
        :return: 行业趋势列表
        """
        if not self.db_manager:
            raise RuntimeError("数据库未配置，无法获取行业趋势数据")
        
        # 直接从已汇总好的 national_industry_stats 表读取数值列
        # 该表包含以下列（经验/学历为 0-1 归一化值）：
        # company_type, national_job_count, avg_median_salary, avg_experience_rank, avg_education_rank
        query = """
            SELECT
                company_type,
                national_job_count,
                avg_median_salary,
                avg_experience_rank,
                avg_education_rank
            FROM national_industry_stats
            WHERE company_type IS NOT NULL
            ORDER BY national_job_count DESC
        """
        
        results = self.db_manager.execute_query(query)
        
        # 收集原始均值，自动识别 0-10 与 0-1 两种刻度
        tmp_rows: List[Dict[str, Any]] = []
        exp_values_raw: List[float] = []
        edu_values_raw: List[float] = []
        
        for row in results:
            company_type = str(row[0]) if row[0] is not None else ""
            national_job_count = int(row[1]) if row[1] is not None else 0
            avg_median_salary = float(row[2]) if row[2] is not None else 0.0
            exp_raw = float(row[3]) if row[3] is not None else None
            edu_raw = float(row[4]) if row[4] is not None else None
            tmp_rows.append({
                'company_type': company_type,
                'national_job_count': national_job_count,
                'avg_median_salary': avg_median_salary,
                'exp_raw': exp_raw,  # 可能为 0-10 或 0-1
                'edu_raw': edu_raw,
            })
            if exp_raw is not None:
                exp_values_raw.append(exp_raw)
            if edu_raw is not None:
                edu_values_raw.append(edu_raw)
        
        def clamp01(x: float) -> float:
            if x is None:
                return 0.0
            if x < 0.0:
                return 0.0
            if x > 1.0:
                return 1.0
            return x
        
        industry_trends: List[IndustryTrend] = []
        # 外环经验要求分档配置（浅绿到深绿）
        exp_max_10 = 5.56
        exp_min_10 = 4.04
        exp_range_10 = exp_max_10 - exp_min_10 if 5.56 > 4.04 else 1.0
        color_scale = [
            ('bucket1', '#F6FFED'),  # 最浅绿
            ('bucket2', '#B7EB8F'),
            ('bucket3', '#73D13D'),
            ('bucket4', '#52C41A'),
            ('bucket5', '#389E0D'),  # 最深绿
        ]
        def bucket_by_experience(val10: Optional[float]) -> Dict[str, Any]:
            if val10 is None:
                return {'outer_ring_bucket': 'bucket1', 'outer_ring_color': color_scale[0][1], 'outer_ring_norm': 0.0}
            norm = (val10 - exp_min_10) / exp_range_10
            # clamp to [0,1]
            if norm < 0.0:
                norm = 0.0
            if norm > 1.0:
                norm = 1.0
            # 分档：>=0.8/0.6/0.4/0.2
            if norm >= 0.8:
                bucket, color = color_scale[4]
            elif norm >= 0.6:
                bucket, color = color_scale[3]
            elif norm >= 0.4:
                bucket, color = color_scale[2]
            elif norm >= 0.2:
                bucket, color = color_scale[1]
            else:
                bucket, color = color_scale[0]
            return {'outer_ring_bucket': bucket, 'outer_ring_color': color, 'outer_ring_norm': round(norm, 4)}
        for item in tmp_rows:
            # 自动识别刻度：若大多数值 > 1，则视为 0-10，需要 /10
            exp_value = item['exp_raw']
            edu_value = item['edu_raw']
            exp_10 = exp_value if exp_value is not None else None
            edu_10 = edu_value if edu_value is not None else None
            # 将值转换为 0-1
            def to_01(v: Optional[float]) -> Optional[float]:
                if v is None:
                    return None
                # 若输入大于 1，认为是 0-10 刻度
                return v / 10.0 if v > 1.0 else v
            exp_norm_0_1 = clamp01(to_01(exp_value)) if exp_value is not None else 0.0
            edu_norm_0_1 = clamp01(to_01(edu_value)) if edu_value is not None else 0.0
            avg_experience_rank_color = exp_norm_0_1
            avg_education_rank_color = edu_norm_0_1
            bucket_info = bucket_by_experience(exp_10)
            
            industry_trends.append(
                IndustryTrend(
                    company_type=item['company_type'],
                    national_job_count=item['national_job_count'],
                    avg_median_salary=round(item['avg_median_salary'], 2),
                    avg_experience_rank=round(avg_experience_rank_color, 4),
                    avg_education_rank=round(avg_education_rank_color, 4),
                    # 同步返回 10 分制原值，便于前端需要时使用
                    avg_experience_rank_10=(round(exp_10, 2) if exp_10 is not None else None),
                    avg_education_rank_10=(round(edu_10, 2) if edu_10 is not None else None),
                    avg_experience_rank_normalized=round(exp_norm_0_1, 4),
                    avg_education_rank_normalized=round(edu_norm_0_1, 4),
                )
            )
            # 动态给最后一个对象扩展外环颜色与分档信息
            industry_trends[-1].__dict__.update(bucket_info)
        
        return industry_trends

