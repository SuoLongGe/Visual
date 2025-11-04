# 城市分析API接口文档

## 概述

本文档描述了按 `city` 城市进行分类的分析API接口，提供各城市的平均薪资、职位分布等数据分析功能。

---

## 📊 接口列表

### 1. 城市招聘分布分析
**接口地址**: `GET /api/charts/city`

**功能描述**: 获取各城市的招聘职位分布和平均薪资数据

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | int | 否 | 1000 | 返回的城市数量限制（默认返回所有数据） |
| min_jobs | int | 否 | 0 | 最小职位数量过滤 |

**请求示例**:
```bash
# 获取所有城市数据（默认）
GET /api/charts/city

# 获取所有城市数据，过滤最小职位数
GET /api/charts/city?min_jobs=100

# 限制返回数量（可选）
GET /api/charts/city?limit=10&min_jobs=100
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取城市分析数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "chart_config": {
      "type": "horizontal_bar",
      "title": "城市招聘分布",
      "subtitle": "显示所有城市",
      "x_axis": {
        "field": "job_count",
        "label": "职位数量"
      },
      "y_axis": {
        "field": "city",
        "label": "城市"
      },
      "data": [
        {
          "city": "北京",
          "job_count": 15000,
          "percentage": 25.5,
          "avg_salary": 18.5,
          "company_count": 1200
        },
        {
          "city": "上海",
          "job_count": 12000,
          "percentage": 20.3,
          "avg_salary": 22.8,
          "company_count": 800
        }
      ],
      "total": 58800,
      "last_updated": "2024-01-15T10:30:00.000000"
    }
  }
}
```

---

### 2. 城市详细信息
**接口地址**: `GET /api/charts/city/detail/{city_name}`

**功能描述**: 获取特定城市的详细分析数据，包括薪资分布、行业分布、经验分布等

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| city_name | string | 是 | 城市名称（URL路径参数） |

**请求示例**:
```bash
GET /api/charts/city/detail/北京
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取城市 北京 详细数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "city_name": "北京",
    "basic_info": {
      "total_jobs": 15000,
      "avg_salary": 18.5,
      "company_count": 1200,
      "industry_count": 15
    },
    "salary_distribution": [
      {
        "range": "0-5K",
        "count": 500,
        "percentage": 3.3
      },
      {
        "range": "5-10K",
        "count": 2000,
        "percentage": 13.3
      },
      {
        "range": "10-15K",
        "count": 4000,
        "percentage": 26.7
      },
      {
        "range": "15-25K",
        "count": 6000,
        "percentage": 40.0
      },
      {
        "range": "25-35K",
        "count": 2000,
        "percentage": 13.3
      },
      {
        "range": "35K+",
        "count": 500,
        "percentage": 3.3
      }
    ],
    "industry_distribution": [
      {
        "industry": "互联网",
        "count": 5000,
        "avg_salary": 20.5,
        "percentage": 33.3
      },
      {
        "industry": "金融",
        "count": 3000,
        "avg_salary": 22.5,
        "percentage": 20.0
      }
    ],
    "experience_distribution": [
      {
        "experience": "1-3年",
        "count": 6000,
        "avg_salary": 15.2,
        "percentage": 40.0
      },
      {
        "experience": "3-5年",
        "count": 5000,
        "avg_salary": 20.8,
        "percentage": 33.3
      }
    ]
  }
}
```

---

### 3. 城市比较分析
**接口地址**: `POST /api/charts/city/compare`

**功能描述**: 比较多个城市的数据，提供排名和对比分析

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| cities | array | 是 | 要比较的城市名称数组 |

**请求示例**:
```bash
POST /api/charts/city/compare
Content-Type: application/json

{
  "cities": ["北京", "上海", "深圳"]
}
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "城市比较数据获取成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "cities": [
      {
        "city": "北京",
        "job_count": 15000,
        "avg_salary": 18.5,
        "company_count": 1200,
        "industry_count": 15,
        "job_rank": 1,
        "salary_rank": 2
      },
      {
        "city": "上海",
        "job_count": 12000,
        "avg_salary": 22.8,
        "company_count": 800,
        "industry_count": 12,
        "job_rank": 2,
        "salary_rank": 1
      },
      {
        "city": "深圳",
        "job_count": 8000,
        "avg_salary": 16.3,
        "company_count": 600,
        "industry_count": 10,
        "job_rank": 3,
        "salary_rank": 3
      }
    ],
    "comparison_summary": {
      "total_cities": 3,
      "highest_job_count": {
        "city": "北京",
        "job_count": 15000
      },
      "highest_avg_salary": {
        "city": "上海",
        "avg_salary": 22.8
      },
      "most_companies": {
        "city": "北京",
        "company_count": 1200
      }
    }
  }
}
```

---

### 4. 数据概览
**接口地址**: `GET /api/overview`

**功能描述**: 获取数据集的整体概览信息

**请求参数**: 无

**请求示例**:
```bash
GET /api/overview
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取数据概览成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "total_records": 400000,
    "data_quality": {
      "completeness": 95.5,
      "accuracy": 98.2,
      "consistency": 97.8
    },
    "last_updated": "2024-01-15T10:30:00.000000",
    "data_sources": [
      "招聘网站",
      "企业官网",
      "第三方数据平台"
    ],
    "statistics": {
      "total_companies": 15000,
      "total_cities": 200,
      "salary_range": {
        "min": 3.0,
        "max": 100.0,
        "median": 15.0
      }
    }
  }
}
```

## 🔧 使用示例

### Python调用示例

```python
import requests

# 获取城市分析数据
response = requests.get('http://localhost:5000/api/charts/city')
data = response.json()

if data['status'] == 'success':
    cities = data['data']['chart_config']['data']
    for city in cities:
        print(f"{city['city']}: {city['job_count']} 个职位, 平均薪资 {city['avg_salary']}K")
```

### JavaScript调用示例

```javascript
// 获取城市详细数据
async function getCityDetail(cityName) {
  try {
    const response = await fetch(`http://localhost:5000/api/charts/city/detail/${cityName}`);
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('城市数据:', data.data);
      return data.data;
    }
  } catch (error) {
    console.error('获取数据失败:', error);
  }
}

// 比较城市数据
async function compareCities(cities) {
  try {
    const response = await fetch('http://localhost:5000/api/charts/city/compare', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        cities: cities
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('城市比较数据:', data.data);
      return data.data;
    }
  } catch (error) {
    console.error('获取数据失败:', error);
  }
}
```

---

## 📈 数据说明

### 薪资计算方式
- 薪资字段格式: "10-15K"
- 计算方法: (最低薪资 + 最高薪资) / 2
- 单位: 千元(K)

### 城市分类
- 基于 `city` 字段进行分类
- 包含: 北京、上海、深圳、广州、杭州等主要城市

### 数据过滤
- 只统计有效薪资数据（格式为 "数字-数字"）
- 排除 `city` 为空的记录
- 支持最小职位数量过滤

---

## 🚀 快速开始

1. 启动服务器:
```bash
python start_server.py
```

2. 测试接口:
```bash
python test_city_api.py
```

3. 访问接口:
```bash
# 获取所有城市数据
curl "http://localhost:5000/api/charts/city"

# 获取城市详细数据
curl "http://localhost:5000/api/charts/city/detail/北京"
```

---

## 📝 注意事项

1. **参数验证**: 所有接口都包含参数验证，无效参数会返回400错误
2. **数据限制**: `limit` 参数默认值为1000，基本等于无限制，可根据需要调整
3. **错误处理**: 统一的错误响应格式，包含详细的错误信息
4. **性能优化**: 建议使用适当的 `min_jobs` 参数过滤小数据量城市
5. **缓存建议**: 对于频繁查询的数据，建议在前端实现缓存机制

## 🚨 错误响应格式

所有接口在出错时都会返回统一的错误格式：

```json
{
  "status": "error",
  "code": 400,
  "message": "参数验证失败",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 🔍 实际测试

运行测试脚本验证API响应：

```bash
# 测试实际API响应格式
python test_real_api.py

# 测试所有城市接口
python test_city_api.py
```
