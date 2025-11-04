# 行业分析API接口文档

## 概述

本文档描述了按 `company_type` 进行分类的行业分析API接口，提供各行业类别的平均薪资、职位分布等数据分析功能。

---

## 📊 接口列表

### 1. 行业招聘分布分析
**接口地址**: `GET /api/charts/industry`

**功能描述**: 获取各行业的招聘职位分布和平均薪资数据

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | int | 否 | 1000 | 返回的行业数量限制（默认返回所有数据） |
| min_jobs | int | 否 | 0 | 最小职位数量过滤 |

**请求示例**:
```bash
# 获取所有行业数据（默认）
GET /api/charts/industry

# 获取所有行业数据，过滤最小职位数
GET /api/charts/industry?min_jobs=100

# 限制返回数量（可选）
GET /api/charts/industry?limit=10&min_jobs=100
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取行业分析数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "chart_config": {
      "type": "horizontal_bar",
      "title": "行业招聘分布",
      "subtitle": "显示所有行业",
      "x_axis": {
        "field": "job_count",
        "label": "职位数量"
      },
      "y_axis": {
        "field": "industry",
        "label": "行业类型"
      },
      "data": [
        {
          "industry": "互联网",
          "job_count": 15000,
          "percentage": 25.5,
          "avg_salary": 18.5,
          "company_count": 1200
        },
        {
          "industry": "金融",
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

### 2. 各行业平均薪资分析
**接口地址**: `GET /api/charts/industry/salary`

**功能描述**: 专门分析各行业的平均薪资水平，按薪资高低排序

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | int | 否 | 1000 | 返回的行业数量限制（默认返回所有数据） |
| min_jobs | int | 否 | 0 | 最小职位数量过滤 |

**请求示例**:
```bash
# 获取所有行业薪资数据（默认）
GET /api/charts/industry/salary

# 获取所有行业薪资数据，过滤最小职位数
GET /api/charts/industry/salary?min_jobs=50

# 限制返回数量（可选）
GET /api/charts/industry/salary?limit=15&min_jobs=50
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取行业薪资分析数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "chart_config": {
      "type": "bar",
      "title": "各行业平均薪资分析",
      "subtitle": "显示所有行业",
      "x_axis": {
        "field": "avg_salary",
        "label": "平均薪资 (K)"
      },
      "y_axis": {
        "field": "industry",
        "label": "行业类型"
      },
      "data": [
        {
          "industry": "金融",
          "avg_salary": 22.8,
          "job_count": 12000,
          "company_count": 800,
          "percentage": 20.3
        },
        {
          "industry": "互联网",
          "avg_salary": 18.5,
          "job_count": 15000,
          "company_count": 1200,
          "percentage": 25.5
        }
      ],
      "summary": {
        "highest_salary": {
          "industry": "金融",
          "avg_salary": 22.8
        },
        "lowest_salary": {
          "industry": "制造业",
          "avg_salary": 12.3
        },
        "overall_avg": 16.7
      },
      "last_updated": "2024-01-15T10:30:00.000000"
    }
  }
}
```

---

### 3. 行业概览数据
**接口地址**: `GET /api/charts/industry/overview`

**功能描述**: 获取行业整体概览信息，包括总行业数、热门行业等

**请求参数**: 无

**请求示例**:
```bash
GET /api/charts/industry/overview
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取行业概览数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "total_industries": 25,
    "total_jobs": 58800,
    "avg_salary_overall": 16.7,
    "top_industries": [
      {
        "industry": "互联网",
        "job_count": 15000,
        "avg_salary": 18.5,
        "percentage": 25.5
      },
      {
        "industry": "金融",
        "job_count": 12000,
        "avg_salary": 22.8,
        "percentage": 20.3
      }
    ],
    "salary_ranges": {
      "0-5K": 5000,
      "5-10K": 15000,
      "10-15K": 20000,
      "15-25K": 15000,
      "25-35K": 3000,
      "35K+": 800
    },
    "last_updated": "2024-01-15T10:30:00.000000"
  }
}
```

---

### 4. 行业详细信息
**接口地址**: `GET /api/charts/industry/detail/{industry_name}`

**功能描述**: 获取特定行业的详细分析数据，包括薪资分布、城市分布、经验分布等

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| industry_name | string | 是 | 行业名称（URL路径参数） |

**请求示例**:
```bash
GET /api/charts/industry/detail/互联网
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取行业 互联网 详细数据成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "industry_name": "互联网",
    "basic_info": {
      "total_jobs": 15000,
      "avg_salary": 18.5,
      "company_count": 1200,
      "city_count": 45
    },
    "salary_distribution": [
      {
        "salary_range": "0-5K",
        "count": 500,
        "percentage": 3.3
      },
      {
        "salary_range": "5-10K",
        "count": 2000,
        "percentage": 13.3
      },
      {
        "salary_range": "10-15K",
        "count": 4000,
        "percentage": 26.7
      },
      {
        "salary_range": "15-25K",
        "count": 6000,
        "percentage": 40.0
      },
      {
        "salary_range": "25-35K",
        "count": 2000,
        "percentage": 13.3
      },
      {
        "salary_range": "35K+",
        "count": 500,
        "percentage": 3.3
      }
    ],
    "city_distribution": [
      {
        "city": "北京",
        "count": 5000,
        "avg_salary": 20.5,
        "percentage": 33.3
      },
      {
        "city": "上海",
        "count": 4000,
        "avg_salary": 19.8,
        "percentage": 26.7
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

### 5. 行业比较分析
**接口地址**: `POST /api/charts/industry/compare`

**功能描述**: 比较多个行业的数据，提供排名和对比分析

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| industries | array | 是 | 要比较的行业名称数组 |

**请求示例**:
```bash
POST /api/charts/industry/compare
Content-Type: application/json

{
  "industries": ["互联网", "金融", "制造业"]
}
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "行业比较数据获取成功",
  "timestamp": "2024-01-15T10:30:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "industries": [
      {
        "industry": "互联网",
        "job_count": 15000,
        "avg_salary": 18.5,
        "company_count": 1200,
        "city_count": 45,
        "job_rank": 1,
        "salary_rank": 2
      },
      {
        "industry": "金融",
        "job_count": 12000,
        "avg_salary": 22.8,
        "company_count": 800,
        "city_count": 35,
        "job_rank": 2,
        "salary_rank": 1
      },
      {
        "industry": "制造业",
        "job_count": 8000,
        "avg_salary": 12.3,
        "company_count": 600,
        "city_count": 25,
        "job_rank": 3,
        "salary_rank": 3
      }
    ],
    "comparison_summary": {
      "total_industries": 3,
      "highest_job_count": {
        "industry": "互联网",
        "job_count": 15000
      },
      "highest_avg_salary": {
        "industry": "金融",
        "avg_salary": 22.8
      },
      "most_companies": {
        "industry": "互联网",
        "company_count": 1200
      }
    }
  }
}
```

---

## 🔧 使用示例

### Python调用示例

```python
import requests

# 获取行业薪资分析
response = requests.get('http://localhost:5000/api/charts/industry/salary?limit=10')
data = response.json()

if data['status'] == 'success':
    industries = data['data']['chart_config']['data']
    for industry in industries:
        print(f"{industry['industry']}: 平均薪资 {industry['avg_salary']}K")
```

### JavaScript调用示例

```javascript
// 获取行业比较数据
async function compareIndustries(industries) {
  try {
    const response = await fetch('http://localhost:5000/api/charts/industry/compare', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        industries: industries
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('行业比较数据:', data.data);
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

### 行业分类
- 基于 `company_type` 字段进行分类
- 包含: 互联网、金融、制造业、教育、医疗等

### 数据过滤
- 只统计有效薪资数据（格式为 "数字-数字"）
- 排除 `company_type` 为空的记录
- 支持最小职位数量过滤

---

## 🚀 快速开始

1. 启动服务器:
```bash
python start_server.py
```

2. 测试接口:
```bash
python test_industry_api.py
```

3. 访问接口:
```bash
# 获取所有行业薪资数据
curl "http://localhost:5000/api/charts/industry/salary"

# 获取所有行业分布数据
curl "http://localhost:5000/api/charts/industry"
```

---

## 📝 注意事项

1. **参数验证**: 所有接口都包含参数验证，无效参数会返回400错误
2. **数据限制**: `limit` 参数默认值为1000，基本等于无限制，可根据需要调整
3. **错误处理**: 统一的错误响应格式，包含详细的错误信息
4. **性能优化**: 建议使用适当的 `min_jobs` 参数过滤小数据量行业
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

# 测试所有行业接口
python test_industry_api.py
```
