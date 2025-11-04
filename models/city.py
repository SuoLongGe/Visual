#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市相关数据模型
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class CityBasicInfo:
    """城市基本信息"""
    total_jobs: int
    avg_salary: float
    company_count: int
    industry_count: int


@dataclass
class CitySalaryDistribution:
    """城市薪资分布"""
    range: str
    count: int
    percentage: float


@dataclass
class CityIndustryDistribution:
    """城市行业分布"""
    industry: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class CityExperienceDistribution:
    """城市经验分布"""
    experience: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class CityDetail:
    """城市详细信息"""
    city_name: str
    basic_info: CityBasicInfo
    salary_distribution: List[CitySalaryDistribution]
    industry_distribution: List[CityIndustryDistribution]
    experience_distribution: List[CityExperienceDistribution]


@dataclass
class CityStatistics:
    """城市统计数据"""
    city: str
    job_count: int
    percentage: float
    avg_salary: float
    company_count: int


@dataclass
class CityComparison:
    """城市比较数据"""
    city: str
    job_count: int
    avg_salary: float
    company_count: int
    industry_count: int
    job_rank: int
    salary_rank: int


@dataclass
class OverviewData:
    """概览数据"""
    total_records: int
    data_quality: Dict[str, float]
    last_updated: str
    data_sources: List[Dict[str, Any]]
    statistics: Dict[str, Any]
