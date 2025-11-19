#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职位画像分析服务
用于处理职位平行坐标图、桑基图、嵌套柱状图等业务逻辑
"""

import logging
from typing import List, Dict, Any, Optional
from database.Q3 import DatabaseManager

logger = logging.getLogger(__name__)


class PositionService:
    """职位画像分析服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_parallel_coordinates_data(self, job_titles: List[str]) -> Dict[str, Any]:
        """
        获取平行坐标图数据
        返回职位在四个维度（薪资、技能、行业集中度、职业热度）的对比数据
        
        Args:
            job_titles: 职位名称数组，最多3个
            
        Returns:
            包含dimensions和positions的字典
        """
        if not job_titles or len(job_titles) == 0:
            raise ValueError("职位名称列表不能为空")
        
        if len(job_titles) > 3:
            raise ValueError("最多只能选择3个职位")
        
        # 构建查询条件
        placeholders = ','.join(['%s'] * len(job_titles))
        query = f"""
            SELECT 
                job_title,
                median_salary,
                skill_score,
                total_shannon_entropy,
                records_count,
                avg_experience_rank,
                avg_education_rank
            FROM job_summary_by_title
            WHERE job_title IN ({placeholders})
        """
        
        results = self.db_manager.execute_query(query, tuple(job_titles))
        
        if not results:
            raise ValueError("未找到指定的职位数据")
        
        # 先获取所有数据，用于计算归一化范围
        data_list = []
        for row in results:
            job_title = row[0]
            median_salary = float(row[1]) if row[1] else 0.0
            skill_score = float(row[2]) if row[2] else 0.0
            shannon_entropy = float(row[3]) if row[3] else 0.0
            records_count = int(row[4]) if row[4] else 0
            avg_experience_rank = float(row[5]) if row[5] else 0.0
            avg_education_rank = float(row[6]) if row[6] else 0.0
            
            data_list.append({
                'job_title': job_title,
                'median_salary': median_salary,
                'skill_score': skill_score,
                'shannon_entropy': shannon_entropy,
                'records_count': records_count,
                'avg_experience_rank': avg_experience_rank,
                'avg_education_rank': avg_education_rank
            })
        
        # 计算归一化范围（基于所有职位数据）
        if data_list:
            salaries = [d['median_salary'] for d in data_list if d['median_salary'] > 0]
            skill_scores = [d['skill_score'] for d in data_list if d['skill_score'] > 0]
            entropies = [d['shannon_entropy'] for d in data_list if d['shannon_entropy'] > 0]
            counts = [d['records_count'] for d in data_list if d['records_count'] > 0]
            
            # 获取全局范围（查询整个表的最大最小值）
            # 对于薪资，需要排除最大的两个值
            try:
                # 先获取所有薪资值，排除最大的两个
                salary_query = """
                    SELECT CAST(median_salary AS DECIMAL(10,2)) as salary
                    FROM job_summary_by_title
                    WHERE median_salary IS NOT NULL
                    ORDER BY salary DESC
                """
                all_salaries = self.db_manager.execute_query(salary_query)
                
                if all_salaries and len(all_salaries) > 2:
                    # 排除最大的两个值，获取剩余的最大值
                    salaries_sorted = sorted([float(row[0]) for row in all_salaries], reverse=True)
                    max_salary = salaries_sorted[2] if len(salaries_sorted) > 2 else salaries_sorted[-1]
                    min_salary = min(salaries_sorted)
                else:
                    # 如果数据不足，使用所有数据的范围
                    if all_salaries:
                        salaries_list = [float(row[0]) for row in all_salaries]
                        min_salary, max_salary = min(salaries_list), max(salaries_list)
                    else:
                        min_salary, max_salary = 0, 200
                
                # 获取其他维度的范围
                other_range_query = """
                    SELECT 
                        MIN(CAST(skill_score AS DECIMAL(10,2))) as min_skill,
                        MAX(CAST(skill_score AS DECIMAL(10,2))) as max_skill,
                        MIN(CAST(total_shannon_entropy AS DECIMAL(10,2))) as min_entropy,
                        MAX(CAST(total_shannon_entropy AS DECIMAL(10,2))) as max_entropy,
                        MIN(CAST(records_count AS UNSIGNED)) as min_count,
                        MAX(CAST(records_count AS UNSIGNED)) as max_count
                    FROM job_summary_by_title
                """
                other_range = self.db_manager.execute_query(other_range_query, fetch_one=True)
                
                if other_range and other_range[0] is not None:
                    min_skill, max_skill = float(other_range[0] or 0), float(other_range[1] or 10)
                    min_entropy, max_entropy = float(other_range[2] or 0), float(other_range[3] or 5)
                    min_count, max_count = int(other_range[4] or 0), int(other_range[5] or 10000)
                else:
                    min_skill, max_skill = 0, 10
                    min_entropy, max_entropy = 0, 5
                    min_count, max_count = 0, 10000
                
                logger.info(f"薪资范围（排除最大2个值）: {min_salary:.2f} - {max_salary:.2f}")
            except Exception as e:
                logger.warning(f"获取全局范围失败，使用默认值: {e}")
                # 使用默认范围
                min_salary, max_salary = 0, 200
                min_skill, max_skill = 0, 10
                min_entropy, max_entropy = 0, 5
                min_count, max_count = 0, 10000
        else:
            min_salary, max_salary = 0, 200
            min_skill, max_skill = 0, 10
            min_entropy, max_entropy = 0, 5
            min_count, max_count = 0, 10000
        
        # 归一化函数
        def normalize(value, min_val, max_val):
            if max_val == min_val:
                return 50.0  # 如果范围相同，返回中间值
            return max(0, min(100, ((value - min_val) / (max_val - min_val)) * 100))
        
        positions = []
        for data in data_list:
            # 第一维：薪资待遇（归一化到0-100）
            salary_value = normalize(data['median_salary'], min_salary, max_salary)
            
            # 第二维：技能要求（归一化到0-100）
            skill_value = normalize(data['skill_score'], min_skill, max_skill)
            
            # 第三维：行业分布集中度（香农熵反向处理：熵值小=集中度高）
            # 先归一化熵值，然后反向
            entropy_normalized = normalize(data['shannon_entropy'], min_entropy, max_entropy)
            concentration_value = 100 - entropy_normalized  # 反向：集中度 = 100 - 归一化熵值
            
            # 第四维：职业热度（归一化到0-100）
            heat_value = normalize(data['records_count'], min_count, max_count)
            
            positions.append({
                "job_title": data['job_title'],
                "values": [
                    round(salary_value, 1),
                    round(skill_value, 1),
                    round(concentration_value, 1),
                    round(heat_value, 1)
                ],
                "details": {
                    "salary": f"{data['median_salary']:.2f}K",
                    "experience": f"{data['avg_experience_rank']:.2f}",
                    "education": f"{data['avg_education_rank']:.2f}",
                    "industry_entropy": round(data['shannon_entropy'], 2),
                    "job_frequency": data['records_count']
                }
            })
        
        return {
            "dimensions": ["薪资待遇", "技能要求", "行业集中度", "职业热度"],
            "positions": positions
        }
    
    def get_sankey_data(self, mode: str = 'all', job_titles: Optional[List[str]] = None, 
                       dimensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取桑基图数据
        展示职位特征到薪资结果的流动路径
        
        Args:
            mode: 显示模式，'all'(整体)或'compare'(对比)
            job_titles: 对比模式下指定的职位名称数组
            dimensions: 选择的维度列表，可选值：skill_level, industry_spread, market_demand
            
        Returns:
            包含nodes、links和categories的字典
        """
        # 默认使用全部维度
        if not dimensions:
            dimensions = ['skill_level', 'industry_spread', 'market_demand']
        # 构建查询条件
        where_clause = ""
        params = None
        
        if mode == 'compare' and job_titles:
            if len(job_titles) == 0:
                raise ValueError("对比模式下职位名称列表不能为空")
            placeholders = ','.join(['%s'] * len(job_titles))
            where_clause = f"WHERE job_title IN ({placeholders})"
            params = tuple(job_titles)
        
        # 查询数据
        query = f"""
            SELECT 
                job_title,
                skill_level,
                industry_spread,
                market_demand,
                salary_level
            FROM job_summary_by_title
            {where_clause}
        """
        
        results = self.db_manager.execute_query(query, params)
        
        if not results:
            raise ValueError("未找到符合条件的职位数据")
        
        # 定义节点映射
        skill_level_map = {
            '初级': '初级技能',
            '中级': '中级技能',
            '高级': '高级技能'
        }
        
        industry_spread_map = {
            '集中': '行业集中',
            '中等': '行业中等',
            '分散': '行业分散'
        }
        
        market_demand_map = {
            '冷门': '市场冷门',
            '普通': '市场普通',
            '热门': '市场热门'
        }
        
        salary_level_map = {
            '低': '低薪资',
            '中低': '中低薪资',
            '中高': '中高薪资',
            '高': '高薪资'
        }
        
        # 统计流量数据
        # 第一层到第二层的流量统计
        layer1_to_layer2 = {}
        # 第二层到第三层的流量统计
        layer2_to_layer3 = {}
        
        # 收集所有出现的节点
        skill_nodes = set()
        industry_nodes = set()
        demand_nodes = set()
        combination_nodes = set()
        salary_nodes = set()
        
        # 根据选择的维度确定使用哪些维度
        use_skill = 'skill_level' in dimensions
        use_industry = 'industry_spread' in dimensions
        use_demand = 'market_demand' in dimensions
        
        for row in results:
            job_title = row[0]
            skill_level = row[1] if row[1] else '中级'
            industry_spread = row[2] if row[2] else '中等'
            market_demand = row[3] if row[3] else '普通'
            salary_level = row[4] if row[4] else '中低'
            
            # 映射到节点名称
            skill_node = skill_level_map.get(skill_level, '中级技能')
            industry_node = industry_spread_map.get(industry_spread, '行业中等')
            demand_node = market_demand_map.get(market_demand, '市场普通')
            salary_node = salary_level_map.get(salary_level, '中低薪资')
            
            # 根据选择的维度添加到节点集合
            if use_skill:
                skill_nodes.add(skill_node)
            if use_industry:
                industry_nodes.add(industry_node)
            if use_demand:
                demand_nodes.add(demand_node)
            salary_nodes.add(salary_node)
            
            # 根据选择的维度定义特征组合规则
            combination = None
            selected_features = []
            
            if use_skill and use_industry and use_demand:
                # 三个维度：使用原有的组合逻辑
                if skill_level == '高级' and industry_spread == '集中':
                    combination = '高技能+行业集中'
                elif skill_level == '高级' and industry_spread == '分散':
                    combination = '高技能+行业分散'
                elif skill_level == '中级' and market_demand in ['普通', '热门']:
                    combination = '中级技能+市场需求'
                elif skill_level == '初级':
                    combination = '初级技能+新兴领域'
                else:
                    combination = f'{skill_node}+{industry_node}'
            elif use_skill and use_industry:
                # 技能 + 行业
                combination = f'{skill_node}+{industry_node}'
            elif use_skill and use_demand:
                # 技能 + 市场需求
                combination = f'{skill_node}+{demand_node}'
            elif use_industry and use_demand:
                # 行业 + 市场需求
                combination = f'{industry_node}+{demand_node}'
            
            combination_nodes.add(combination)
            
            # 统计第一层到第二层的流量
            if use_skill:
                key1 = (skill_node, combination)
                layer1_to_layer2[key1] = layer1_to_layer2.get(key1, 0) + 1
            
            if use_industry:
                key2 = (industry_node, combination)
                layer1_to_layer2[key2] = layer1_to_layer2.get(key2, 0) + 1
            
            if use_demand:
                key3 = (demand_node, combination)
                layer1_to_layer2[key3] = layer1_to_layer2.get(key3, 0) + 1
            
            # 统计第二层到第三层的流量
            # 组合 -> 薪资
            key4 = (combination, salary_node)
            layer2_to_layer3[key4] = layer2_to_layer3.get(key4, 0) + 1
        
        # 构建节点列表
        nodes = []
        categories = []
        
        # 第一层：基础特征节点（根据选择的维度）
        if use_skill:
            for node in sorted(skill_nodes):
                nodes.append({"name": node, "category": "技能要求"})
            categories.append("技能要求")
        
        if use_industry:
            for node in sorted(industry_nodes):
                nodes.append({"name": node, "category": "行业分布"})
            categories.append("行业分布")
        
        if use_demand:
            for node in sorted(demand_nodes):
                nodes.append({"name": node, "category": "市场需求"})
            categories.append("市场需求")
        
        # 第二层：特征组合节点
        for node in sorted(combination_nodes):
            nodes.append({"name": node, "category": "特征组合"})
        categories.append("特征组合")
        
        # 第三层：薪资结果节点
        salary_order = {'低薪资': 0, '中低薪资': 1, '中高薪资': 2, '高薪资': 3}
        for node in sorted(salary_nodes, key=lambda x: salary_order.get(x, 999)):
            nodes.append({"name": node, "category": "薪资结果"})
        categories.append("薪资结果")
        
        # 构建连接列表
        links = []
        
        # 第一层到第二层的连接
        for (source, target), value in layer1_to_layer2.items():
            links.append({
                "source": source,
                "target": target,
                "value": value
            })
        
        # 第二层到第三层的连接
        for (source, target), value in layer2_to_layer3.items():
            links.append({
                "source": source,
                "target": target,
                "value": value
            })
        
        return {
            "nodes": nodes,
            "links": links,
            "categories": categories
        }
    
    def get_nested_bar_data(self, job_titles: List[str], detail_job: Optional[str] = None) -> Dict[str, Any]:
        """
        获取多维度嵌套柱状图数据
        
        Args:
            job_titles: 职位名称数组，最多3个
            detail_job: 详细分析的单个职位名称（可选）
            
        Returns:
            包含macro_comparison和micro_analysis的字典
        """
        if not job_titles or len(job_titles) == 0:
            raise ValueError("职位名称列表不能为空")
        
        if len(job_titles) > 3:
            raise ValueError("最多只能选择3个职位")
        
        # 第一层：宏观对比数据
        macro_comparison = self._get_macro_comparison(job_titles)
        
        # 第二层：微观分析数据（如果指定了detail_job）
        micro_analysis = None
        if detail_job:
            micro_analysis = self._get_micro_analysis(detail_job)
        
        return {
            "macro_comparison": macro_comparison,
            "micro_analysis": micro_analysis
        }
    
    def _get_macro_comparison(self, job_titles: List[str]) -> List[Dict[str, Any]]:
        """
        获取宏观对比数据
        每个职位包含：综合技能分数、行业集中度、平均薪资
        """
        placeholders = ','.join(['%s'] * len(job_titles))
        query = f"""
            SELECT 
                job_title,
                skill_score,
                total_shannon_entropy,
                median_salary,
                avg_experience_rank,
                avg_education_rank,
                records_count
            FROM job_summary_by_title
            WHERE job_title IN ({placeholders})
        """
        
        results = self.db_manager.execute_query(query, tuple(job_titles))
        
        if not results:
            raise ValueError("未找到指定的职位数据")
        
        macro_data = []
        for row in results:
            job_title = row[0]
            skill_score = float(row[1]) if row[1] else 0.0
            shannon_entropy = float(row[2]) if row[2] else 0.0
            median_salary = float(row[3]) if row[3] else 0.0
            avg_experience_rank = float(row[4]) if row[4] else 0.0
            avg_education_rank = float(row[5]) if row[5] else 0.0
            records_count = int(row[6]) if row[6] else 0
            
            # 计算综合技能分数（经验和学历各占50%），乘以10放大显示
            comprehensive_skill = (avg_experience_rank * 0.5 + avg_education_rank * 0.5) * 10
            
            # 行业集中度：香农熵越小，集中度越高，所以用100减去
            industry_concentration = max(0, 100 - shannon_entropy)
            
            macro_data.append({
                "job_title": job_title,
                "skill_score": round(comprehensive_skill, 2),
                "industry_concentration": round(industry_concentration, 2),
                "avg_salary": round(median_salary, 2),
                "avg_experience_rank": round(avg_experience_rank, 2),
                "avg_education_rank": round(avg_education_rank, 2),
                "records_count": records_count
            })
        
        return macro_data
    
    def _get_micro_analysis(self, job_title: str) -> Dict[str, Any]:
        """
        获取微观分析数据
        包含：薪资统计（箱线图数据）、与所有职位的对比
        使用 job_summary_by_title 表中已有的统计数据
        """
        # 获取该职位的统计数据
        query = """
            SELECT 
                job_title,
                min_salary,
                q1_salary,
                median_salary,
                q3_salary,
                max_salary,
                median_salary as avg_salary,
                skill_score,
                records_count
            FROM job_summary_by_title
            WHERE job_title = %s
        """
        result = self.db_manager.execute_query(query, (job_title,), fetch_one=True)
        
        if not result:
            raise ValueError(f"职位 {job_title} 不存在")
        
        # 解析数据
        min_salary = float(result[1]) if result[1] else 0.0
        q1_salary = float(result[2]) if result[2] else 0.0
        median_salary = float(result[3]) if result[3] else 0.0
        q3_salary = float(result[4]) if result[4] else 0.0
        max_salary = float(result[5]) if result[5] else 0.0
        avg_salary = float(result[6]) if result[6] else 0.0
        skill_score = float(result[7]) if result[7] else 0.0
        records_count = int(result[8]) if result[8] else 0
        
        # 构建箱线图统计数据
        salary_statistics = {
            "min": round(min_salary, 2),
            "max": round(max_salary, 2),
            "median": round(median_salary, 2),
            "q1": round(q1_salary, 2),
            "q3": round(q3_salary, 2),
            "avg": round(avg_salary, 2)
        }
        
        # 从 job_city_distribution 表获取城市分布数据
        city_query = """
            SELECT city, count, percent
            FROM job_city_distribution
            WHERE job_title = %s
            ORDER BY CAST(count AS UNSIGNED) DESC
        """
        city_results = self.db_manager.execute_query(city_query, (job_title,))
        
        # 获取前3个城市
        top_cities = []
        all_cities = []
        if city_results:
            for idx, row in enumerate(city_results):
                city_data = {
                    "city": row[0],
                    "count": int(row[1]) if row[1] else 0,
                    "percentage": round(float(row[2]), 2) if row[2] else 0.0
                }
                all_cities.append(city_data)
                if idx < 3:
                    top_cities.append(city_data)
        
        # 获取所有职位的平均数据用于对比
        all_positions_query = """
            SELECT 
                AVG(CAST(median_salary AS DECIMAL(10,2))) as avg_salary,
                AVG(CAST(skill_score AS DECIMAL(10,2))) as avg_skill
            FROM job_summary_by_title
            WHERE median_salary IS NOT NULL AND skill_score IS NOT NULL
        """
        all_positions_result = self.db_manager.execute_query(all_positions_query, fetch_one=True)
        
        all_positions_avg_salary = float(all_positions_result[0]) if all_positions_result[0] else 0.0
        all_positions_skill_avg = float(all_positions_result[1]) if all_positions_result[1] else 0.0
        
        # 计算该职位在所有职位中的百分位
        percentile_query = """
            SELECT COUNT(*) 
            FROM job_summary_by_title
            WHERE CAST(median_salary AS DECIMAL(10,2)) <= %s
        """
        lower_count = self.db_manager.execute_query(percentile_query, (median_salary,), fetch_one=True)[0]
        
        total_positions_query = """
            SELECT COUNT(*) FROM job_summary_by_title WHERE median_salary IS NOT NULL
        """
        total_positions = self.db_manager.execute_query(total_positions_query, fetch_one=True)[0]
        
        position_percentile = (lower_count / total_positions * 100) if total_positions > 0 else 0
        
        return {
            "job_title": job_title,
            "salary_statistics": salary_statistics,
            "top_cities": top_cities,
            "all_cities": all_cities,  # 返回所有城市数据
            "comparison_with_all": {
                "all_positions_avg_salary": round(all_positions_avg_salary, 2),
                "all_positions_skill_avg": round(all_positions_skill_avg, 2),
                "position_percentile": round(position_percentile, 2)
            }
        }

