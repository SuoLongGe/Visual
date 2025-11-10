#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口测试脚本
用于测试问题五的两个接口
"""

import requests
import json
import sys
from datetime import datetime

# 设置输出编码为UTF-8，避免Windows下的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API基础地址
BASE_URL = "http://localhost:5000/api"

def print_response(response, title):
    """格式化打印响应结果"""
    print("\n" + "=" * 60)
    print(f"[测试] {title}")
    print("=" * 60)
    print(f"状态码: {response.status_code}")
    print(f"URL: {response.url}")
    print("\n响应内容:")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print("=" * 60)

def test_job_ranking():
    """测试职位综合排名接口"""
    print("\n[测试] 接口: 获取职位综合排名数据")
    url = f"{BASE_URL}/industry/ranking/jobs"
    
    try:
        response = requests.get(url, timeout=10)
        print_response(response, "职位综合排名数据")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                jobs = data.get('data', {}).get('jobs', [])
                print(f"\n[成功] 获取 {len(jobs)} 个职位数据")
                if jobs:
                    print("\n前3个职位预览:")
                    for i, job in enumerate(jobs[:3], 1):
                        print(f"  {i}. {job.get('job_title')}")
                        print(f"     记录数: {job.get('records_count')}")
                        print(f"     教育排名: {job.get('education_rank')}")
                        print(f"     经验排名: {job.get('experience_rank')}")
                        print(f"     综合得分: {job.get('composite_score')}")
            else:
                print(f"\n[错误] 接口返回错误: {data.get('message')}")
        else:
            print(f"\n[错误] HTTP错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n[错误] 连接失败！请确保服务器已启动 (python app.py 或 python start_server.py)")
    except requests.exceptions.Timeout:
        print("\n[错误] 请求超时")
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")

def test_industry_trend_rose():
    """测试行业双环嵌套玫瑰图接口"""
    print("\n[测试] 接口: 获取行业双环嵌套玫瑰图数据")
    url = f"{BASE_URL}/industry/trend/rose"
    
    try:
        response = requests.get(url, timeout=10)
        print_response(response, "行业趋势玫瑰图数据")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                industries = data.get('data', {}).get('industries', [])
                print(f"\n[成功] 获取 {len(industries)} 个行业数据")
                if industries:
                    print("\n前3个行业预览:")
                    for i, industry in enumerate(industries[:3], 1):
                        print(f"  {i}. {industry.get('company_type')}")
                        print(f"     全国职位数: {industry.get('national_job_count')}")
                        print(f"     平均中位薪资: {industry.get('avg_median_salary')}")
                        print(f"     平均经验排名: {industry.get('avg_experience_rank')}")
                        print(f"     平均教育排名: {industry.get('avg_education_rank')}")
            else:
                print(f"\n[错误] 接口返回错误: {data.get('message')}")
        else:
            print(f"\n[错误] HTTP错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n[错误] 连接失败！请确保服务器已启动 (python app.py 或 python start_server.py)")
    except requests.exceptions.Timeout:
        print("\n[错误] 请求超时")
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("API接口测试工具")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    print("\n提示: 请确保服务器已启动 (运行 python app.py)")
    
    # 测试两个接口
    test_job_ranking()
    test_industry_trend_rose()
    
    print("\n" + "=" * 60)
    print("[完成] 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

