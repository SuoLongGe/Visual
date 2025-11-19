# Q2 职位画像分析接口文档

## 基础信息

- **基础URL**: `http://localhost:5001/api/positions`
- **返回格式**: JSON
- **字符编码**: UTF-8

## 接口列表

### 1. 获取平行坐标图数据

获取多个职位的平行坐标数据，用于展示职位在薪酬、技能要求、行业分布和热度四个维度的对比。

**接口地址**: `/parallel`

**请求方式**: `GET`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| job_titles | string | 是 | 职位名称（可重复传递，最多3个） | `bfbc45b05c5a4425210cd2cb3d84ae09GC` |

**请求示例**:

```bash
# 单个职位
curl "http://localhost:5001/api/positions/parallel?job_titles=bfbc45b05c5a4425210cd2cb3d84ae09GC"

# 多个职位（最多3个）
curl "http://localhost:5001/api/positions/parallel?job_titles=bfbc45b05c5a4425210cd2cb3d84ae09GC&job_titles=c9a30a5443d04270fb0f49d437c3376bAy&job_titles=9e7afc7cdb61931eb7d2cc8398b80ecfSQ"
```

**返回示例**: 

```json
{
  "status": "sucess",
  "code": 200,
  "message": "获取平行坐标数据成功",
  "timestamp": "2025-11-15T16:10:16.123456",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "data": {
    "dimensions": [
      "薪资待遇",
      "技能要求",
      "行业集中度",
      "职业热度"
    ],
    "positions": [
      {
        "job_title": "bfbc45b05c5a4425210cd2cb3d84ae09GC",
        "values": [
          46.9,
          51.8,
          38.1,
          33.6
        ],
        "details": {
          "salary": "93.87K",
          "experience": "4.33",
          "education": "6.02",
          "industry_entropy": 3.10,
          "job_frequency": 3358
        }
      },
      {
        "job_title": "c9a30a5443d04270fb0f49d437c3376bAy",
        "values": [
          66.7,
          58.6,
          53.4,
          26.3
        ],
        "details": {
          "salary": "133.31K",
          "experience": "5.06",
          "education": "6.66",
          "industry_entropy": 2.33,
          "job_frequency": 2633
        }
      }
    ]
  }
}
```

**字段说明**:

#### 响应字段

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `status` | string | 响应状态，固定为 "success" |
| `code` | integer | HTTP状态码，成功时为200 |
| `message` | string | 响应消息 |
| `timestamp` | string | 响应时间戳（ISO 8601格式） |
| `request_id` | string | 请求唯一标识符（UUID） |
| `data` | object | 响应数据对象 |
| `data.dimensions` | array[string] | 维度名称数组，固定为 ["薪资待遇", "技能要求", "行业集中度", "职业热度"] |
| `data.positions` | array[object] | 职位数据数组，最多3个职位 |
| `data.positions[].job_title` | string | 职位名称 |
| `data.positions[].values` | array[float] | 四个维度的归一化值（0-100范围），顺序对应dimensions数组 |
| `data.positions[].values[0]` | float | 薪资待遇维度值（0-100） |
| `data.positions[].values[1]` | float | 技能要求维度值（0-100） |
| `data.positions[].values[2]` | float | 行业集中度维度值（0-100） |
| `data.positions[].values[3]` | float | 职业热度维度值（0-100） |
| `data.positions[].details` | object | 详细信息对象 |
| `data.positions[].details.salary` | string | 中位数薪资（格式：XX.XXK） |
| `data.positions[].details.experience` | string | 平均经验要求排名 |
| `data.positions[].details.education` | string | 平均学历要求排名 |
| `data.positions[].details.industry_entropy` | float | 行业分布香农熵值 |
| `data.positions[].details.job_frequency` | integer | 职位出现频率（记录数） |

#### 维度计算说明

**第一维：薪资待遇**
- **数据来源**: `median_salary`（中位数薪资，单位：K）
- **计算方式**: 基于全局薪资范围（排除最大的两个异常值）进行归一化
- **归一化范围**: 0-100，值越大表示薪资越高
- **公式**: `(median_salary - min_salary) / (max_salary - min_salary) * 100`

**第二维：技能要求**
- **数据来源**: `skill_score`（技能分数，已由数据库计算）
- **计算方式**: 基于全局技能分数范围进行归一化
- **归一化范围**: 0-100，值越大表示技能要求越高
- **公式**: `(skill_score - min_skill) / (max_skill - min_skill) * 100`

**第三维：行业集中度**
- **数据来源**: `total_shannon_entropy`（香农熵值）
- **计算方式**: 
  1. 先归一化熵值：`(entropy - min_entropy) / (max_entropy - min_entropy) * 100`
  2. 然后反向处理：`100 - 归一化熵值`
- **归一化范围**: 0-100，值越大表示行业集中度越高
- **说明**: 熵值越小表示行业分布越集中，因此需要反向处理

**第四维：职业热度**
- **数据来源**: `records_count`（职位在数据集中出现的次数）
- **计算方式**: 基于全局记录数范围进行归一化
- **归一化范围**: 0-100，值越大表示职位热度越高
- **公式**: `(records_count - min_count) / (max_count - min_count) * 100`

---

### 2. 获取桑基图数据

获取职位特征到薪资结果的流动路径数据，展示技能要求、行业特性、市场需求与薪酬结果之间的转化关系。

**接口地址**: `/sankey`

**请求方式**: `GET`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| mode | string | 是 | 模式：`all`（整体模式）或 `compare`（对比模式） | `all` |
| job_titles | string | 否 | 职位名称（对比模式必填，可重复传递，最多3个） | `数据分析师` |
| dimensions | string | 否 | 维度选择（可重复传递，可选值：`skill_level`、`industry_spread`、`market_demand`） | `skill_level` |

**请求示例**:

```bash
# 整体模式（默认全部维度）
curl "http://localhost:5001/api/positions/sankey?mode=all"

# 整体模式（指定维度）
curl "http://localhost:5001/api/positions/sankey?mode=all&dimensions=skill_level&dimensions=industry_spread"

# 对比模式（单个职位）
curl "http://localhost:5001/api/positions/sankey?mode=compare&job_titles=数据分析师"

# 对比模式（多个职位，指定维度）
curl "http://localhost:5001/api/positions/sankey?mode=compare&job_titles=数据分析师&job_titles=算法工程师&dimensions=skill_level&dimensions=market_demand"
```

**返回示例（整体模式）**:

```json
{
  "status": "success",
  "code": 200,
  "message": "获取桑基图数据成功",
  "timestamp": "2025-11-19T10:30:00.123456",
  "request_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "data": {
    "nodes": [
      {
        "name": "技能要求-低",
        "category": "技能要求"
      },
      {
        "name": "技能要求-中",
        "category": "技能要求"
      },
      {
        "name": "技能要求-高",
        "category": "技能要求"
      },
      {
        "name": "行业分布-集中",
        "category": "行业分布"
      },
      {
        "name": "行业分布-分散",
        "category": "行业分布"
      },
      {
        "name": "市场需求-低",
        "category": "市场需求"
      },
      {
        "name": "市场需求-中",
        "category": "市场需求"
      },
      {
        "name": "市场需求-高",
        "category": "市场需求"
      },
      {
        "name": "薪资-低",
        "category": "薪资结果"
      },
      {
        "name": "薪资-中",
        "category": "薪资结果"
      },
      {
        "name": "薪资-高",
        "category": "薪资结果"
      }
    ],
    "links": [
      {
        "source": "技能要求-低",
        "target": "行业分布-集中",
        "value": 1250
      },
      {
        "source": "行业分布-集中",
        "target": "市场需求-中",
        "value": 800
      },
      {
        "source": "市场需求-中",
        "target": "薪资-中",
        "value": 650
      }
    ],
    "categories": [
      {
        "name": "技能要求"
      },
      {
        "name": "行业分布"
      },
      {
        "name": "市场需求"
      },
      {
        "name": "薪资结果"
      }
    ]
  }
}
```

**返回示例（对比模式）**:

```json
{
  "status": "success",
  "code": 200,
  "message": "获取桑基图数据成功",
  "timestamp": "2025-11-19T10:30:00.123456",
  "request_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "data": {
    "nodes": [
      {
        "name": "数据分析师",
        "category": "职位"
      },
      {
        "name": "算法工程师",
        "category": "职位"
      },
      {
        "name": "技能要求-中",
        "category": "技能要求"
      },
      {
        "name": "技能要求-高",
        "category": "技能要求"
      },
      {
        "name": "薪资-中",
        "category": "薪资结果"
      },
      {
        "name": "薪资-高",
        "category": "薪资结果"
      }
    ],
    "links": [
      {
        "source": "数据分析师",
        "target": "技能要求-中",
        "value": 3358
      },
      {
        "source": "算法工程师",
        "target": "技能要求-高",
        "value": 2633
      },
      {
        "source": "技能要求-中",
        "target": "薪资-中",
        "value": 3358
      },
      {
        "source": "技能要求-高",
        "target": "薪资-高",
        "value": 2633
      }
    ],
    "categories": [
      {
        "name": "职位"
      },
      {
        "name": "技能要求"
      },
      {
        "name": "薪资结果"
      }
    ]
  }
}
```

**字段说明**:

#### 响应字段

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.nodes` | array[object] | 节点数组 |
| `data.nodes[].name` | string | 节点名称 |
| `data.nodes[].category` | string | 节点分类 |
| `data.links` | array[object] | 连接数组 |
| `data.links[].source` | string | 源节点名称 |
| `data.links[].target` | string | 目标节点名称 |
| `data.links[].value` | integer | 流量值（职位数量） |
| `data.categories` | array[object] | 分类数组 |
| `data.categories[].name` | string | 分类名称 |

#### 维度说明

**技能要求 (skill_level)**
- **低**: skill_score < 33.33百分位
- **中**: 33.33百分位 ≤ skill_score < 66.67百分位
- **高**: skill_score ≥ 66.67百分位

**行业分布 (industry_spread)**
- **集中**: total_shannon_entropy < 中位数
- **分散**: total_shannon_entropy ≥ 中位数

**市场需求 (market_demand)**
- **低**: records_count < 33.33百分位
- **中**: 33.33百分位 ≤ records_count < 66.67百分位
- **高**: records_count ≥ 66.67百分位

**薪资结果**
- **低**: median_salary < 33.33百分位
- **中**: 33.33百分位 ≤ median_salary < 66.67百分位
- **高**: median_salary ≥ 66.67百分位

---

### 3. 获取嵌套柱状图数据

获取多维度嵌套柱状图数据，展示职位的综合技能分数（柱子高度）和行业集中度（点状图密集度），支持宏观对比和微观分析两种视图。

**接口地址**: `/nested_bar`

**请求方式**: `GET`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| job_titles | string | 是 | 职位名称（可重复传递，最多3个） | `数据分析师` |
| detail_job | string | 否 | 详细分析的职位名称（微观模式） | `数据分析师` |

**请求示例**:

```bash
# 宏观对比模式（多个职位）
curl "http://localhost:5001/api/positions/nested_bar?job_titles=数据分析师&job_titles=算法工程师&job_titles=机器学习工程师"

# 微观分析模式（单个职位详情）
curl "http://localhost:5001/api/positions/nested_bar?job_titles=数据分析师&job_titles=算法工程师&detail_job=数据分析师"
```

**返回示例（宏观对比模式）**:

```json
{
  "status": "success",
  "code": 200,
  "message": "获取嵌套柱状图数据成功",
  "timestamp": "2025-11-19T10:30:00.123456",
  "request_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "data": {
    "macro_comparison": [
      {
        "job_title": "数据分析师",
        "skill_score": 518.0,
        "industry_concentration": 38.1,
        "avg_salary": 93.87,
        "avg_experience_rank": 4.33,
        "avg_education_rank": 6.02
      },
      {
        "job_title": "算法工程师",
        "skill_score": 586.0,
        "industry_concentration": 53.4,
        "avg_salary": 133.31,
        "avg_experience_rank": 5.06,
        "avg_education_rank": 6.66
      },
      {
        "job_title": "机器学习工程师",
        "skill_score": 612.5,
        "industry_concentration": 45.2,
        "avg_salary": 145.20,
        "avg_experience_rank": 5.20,
        "avg_education_rank": 6.80
      }
    ]
  }
}
```

**返回示例（微观分析模式）**:

```json
{
  "status": "success",
  "code": 200,
  "message": "获取嵌套柱状图数据成功",
  "timestamp": "2025-11-19T10:30:00.123456",
  "request_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "data": {
    "micro_analysis": {
      "job_title": "数据分析师",
      "salary_statistics": {
        "min": 52.66,
        "q1": 61.57,
        "median": 70.48,
        "q3": 79.38,
        "max": 88.29,
        "avg": 70.48
      },
      "top_cities": [
        {
          "city": "北京",
          "count": "1200",
          "percentage": "35.7"
        },
        {
          "city": "上海",
          "count": "980",
          "percentage": "29.2"
        },
        {
          "city": "深圳",
          "count": "650",
          "percentage": "19.4"
        }
      ],
      "all_cities": [
        {
          "city": "北京",
          "count": "1200",
          "percentage": "35.7"
        },
        {
          "city": "上海",
          "count": "980",
          "percentage": "29.2"
        },
        {
          "city": "深圳",
          "count": "650",
          "percentage": "19.4"
        },
        {
          "city": "杭州",
          "count": "320",
          "percentage": "9.5"
        },
        {
          "city": "广州",
          "count": "208",
          "percentage": "6.2"
        }
      ],
      "comparison_with_all": {
        "all_positions_avg_salary": 85.50,
        "all_positions_skill_avg": 550.0,
        "position_percentile": 45.6
      }
    }
  }
}
```

**字段说明**:

#### 宏观对比模式字段

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.macro_comparison` | array[object] | 宏观对比数据数组 |
| `data.macro_comparison[].job_title` | string | 职位名称 |
| `data.macro_comparison[].skill_score` | float | 综合技能分数（已乘以10） |
| `data.macro_comparison[].industry_concentration` | float | 行业集中度（0-100） |
| `data.macro_comparison[].avg_salary` | float | 平均薪资（K） |
| `data.macro_comparison[].avg_experience_rank` | float | 平均经验要求排名 |
| `data.macro_comparison[].avg_education_rank` | float | 平均学历要求排名 |

#### 微观分析模式字段

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.micro_analysis` | object | 微观分析数据对象 |
| `data.micro_analysis.job_title` | string | 职位名称 |
| `data.micro_analysis.salary_statistics` | object | 薪资统计信息 |
| `data.micro_analysis.salary_statistics.min` | float | 最小值（K） |
| `data.micro_analysis.salary_statistics.q1` | float | 下四分位数（K） |
| `data.micro_analysis.salary_statistics.median` | float | 中位数（K） |
| `data.micro_analysis.salary_statistics.q3` | float | 上四分位数（K） |
| `data.micro_analysis.salary_statistics.max` | float | 最大值（K） |
| `data.micro_analysis.salary_statistics.avg` | float | 平均值（K） |
| `data.micro_analysis.top_cities` | array[object] | 前三城市分布 |
| `data.micro_analysis.top_cities[].city` | string | 城市名称 |
| `data.micro_analysis.top_cities[].count` | string | 职位数量 |
| `data.micro_analysis.top_cities[].percentage` | string | 百分比 |
| `data.micro_analysis.all_cities` | array[object] | 所有城市分布（按数量降序） |
| `data.micro_analysis.comparison_with_all` | object | 与全局对比 |
| `data.micro_analysis.comparison_with_all.all_positions_avg_salary` | float | 全局平均薪资（K） |
| `data.micro_analysis.comparison_with_all.all_positions_skill_avg` | float | 全局平均技能分数 |
| `data.micro_analysis.comparison_with_all.position_percentile` | float | 该职位在全局的百分位排名 |

#### 数据说明

**综合技能分数**
- 来源：`skill_score` 字段（已乘以10用于更好的可视化）
- 计算：基于经验要求、学历要求等多个维度的综合评分
- 用途：柱子高度表示

**行业集中度**
- 来源：基于 `total_shannon_entropy` 计算
- 范围：0-100，值越大表示行业越集中
- 用途：点状图密集度表示

**城市分布**
- 来源：`job_city_distribution` 表
- 排序：按职位数量降序
- 用途：微观分析中展示职位地域分布

---

## 错误码说明

| 错误码 | 说明 | 可能原因 |
|-------|------|---------|
| 400 | 请求参数错误 | 缺少必填参数、参数格式错误、职位数量超限 |
| 404 | 数据不存在 | 指定的职位在数据库中不存在 |
| 500 | 服务器内部错误 | 数据库连接失败、数据处理异常 |

## 注意事项

1. **职位名称**：所有接口的职位名称参数都区分大小写
2. **数量限制**：平行坐标图和嵌套柱状图最多支持3个职位对比
3. **维度选择**：桑基图至少需要选择2个维度（不包括薪资结果）
4. **数据来源**：所有数据来自 `job_summary_by_title` 和 `job_city_distribution` 表
5. **归一化处理**：部分数值已进行归一化处理，便于可视化展示
6. **缓存策略**：建议客户端对相同参数的请求进行缓存，减少服务器压力