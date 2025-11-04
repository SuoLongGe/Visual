#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验相关数据模型
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ExperienceStatistics:
    """经验统计数据"""
    experience: str
    job_count: int
    avg_salary: float
    company_count: int
    percentage: float


@dataclass
class ExperienceSalaryDistribution:
    """经验薪资分布"""
    salary_range: str
    count: int
    percentage: float


@dataclass
class ExperienceCityDistribution:
    """经验城市分布"""
    city: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class ExperienceIndustryDistribution:
    """经验行业分布"""
    industry: str
    count: int
    avg_salary: float
    percentage: float


@dataclass
class ExperienceDetail:
    """经验详细信息"""
    experience_name: str
    basic_info: Dict[str, Any]
    salary_distribution: List[ExperienceSalaryDistribution]
    city_distribution: List[ExperienceCityDistribution]
    industry_distribution: List[ExperienceIndustryDistribution]


@dataclass
class ExperienceComparison:
    """经验比较数据"""
    experience: str
    job_count: int
    avg_salary: float
    company_count: int
    city_count: int
    industry_count: int
    job_rank: int
    salary_rank: int


@dataclass
class ExperienceOverview:
    """经验概览数据"""
    total_experience_levels: int
    total_jobs: int
    avg_salary_overall: float
    top_experience_levels: List[ExperienceStatistics]
    salary_ranges: Dict[str, int]
    experience_distribution: Dict[str, int]
