#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业相关数据模型
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class IndustryStatistics:
    """行业统计数据"""
    industry: str
    job_count: int
    avg_salary: float
    company_count: int
    percentage: float


@dataclass
class IndustrySalaryDistribution:
    """行业薪资分布"""
    salary_range: str
    count: int
    percentage: float


@dataclass
class IndustryCityDistribution:
    """行业城市分布"""
    city: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class IndustryExperienceDistribution:
    """行业经验分布"""
    experience: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class IndustryDetail:
    """行业详细信息"""
    industry_name: str
    basic_info: Dict[str, Any]
    salary_distribution: List[IndustrySalaryDistribution]
    city_distribution: List[IndustryCityDistribution]
    experience_distribution: List[IndustryExperienceDistribution]


@dataclass
class IndustryComparison:
    """行业比较数据"""
    industry: str
    job_count: int
    avg_salary: float
    company_count: int
    city_count: int
    job_rank: int
    salary_rank: int


@dataclass
class IndustryOverview:
    """行业概览数据"""
    total_industries: int
    total_jobs: int
    avg_salary_overall: float
    top_industries: List[IndustryStatistics]
    salary_ranges: Dict[str, int]
